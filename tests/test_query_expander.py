import json
from pathlib import Path

from evaluation.evaluate_query_expansion import evaluate, render_report, write_outputs
from rag.context_builder import ContextBuilder
from retrieval.expand_query import main as expand_main
from retrieval.query_expander import QueryExpander


class FakeRetriever:
    def __init__(self) -> None:
        self.queries = []

    def search(self, query: str, filters=None, top_k: int = 5) -> list[dict]:
        self.queries.append(query)
        record_id = "r2" if "திருநாவுக்கரசர்" in query else "r1"
        return [
            {
                "rank": 1,
                "record_id": record_id,
                "parent_record_id": record_id,
                "chunk_id": f"{record_id}_verse_plus_commentary",
                "chunk_type": "verse_plus_commentary",
                "matched_modes": ["lexical"],
                "hybrid_score": 1.0,
                "citation_text": record_id,
                "source_urls": {},
                "deterministic_rank_key": record_id,
            }
        ][:top_k]


def write_enriched(path: Path) -> None:
    records = [
        {
            "record_id": "r1",
            "hymn_title": "முதல்",
            "verse_text_normalized": "பொதுப் பாடல்",
            "pozhppurai_normalized": "",
            "kurippurai_normalized": "",
            "metadata_text": "",
            "citation": {"hymn_title": "முதல்", "citation_string": "முதல்"},
        },
        {
            "record_id": "r2",
            "hymn_title": "இரண்டாம்",
            "verse_text_normalized": "திருநாவுக்கரசர் பாடல்",
            "pozhppurai_normalized": "",
            "kurippurai_normalized": "",
            "metadata_text": "அப்பர்",
            "citation": {"hymn_title": "இரண்டாம்", "citation_string": "இரண்டாம்"},
        },
    ]
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
        encoding="utf-8",
    )


def test_author_alias_expansion() -> None:
    result = QueryExpander().expand("அப்பர் பாடல்கள்")

    assert result["expanded_query_text"].startswith("அப்பர் திருநாவுக்கரசர்")
    assert result["matched_registries"] == ["authors"]
    assert "நாவுக்கரசர்" in result["expanded_terms"]


def test_synonym_expansion_has_no_duplicates() -> None:
    result = QueryExpander().expand("சந்திரன் வரும் பாடல்கள்")

    assert result["matched_registries"] == ["synonyms"]
    assert {"சந்திரன்", "நிலா", "மதி", "திங்கள்", "நிலவு"} <= set(result["expanded_terms"])
    assert len(result["expanded_terms"]) == len(set(result["expanded_terms"]))


def test_deity_alias_and_literary_device_expansion() -> None:
    deity = QueryExpander().expand("ஈசன் அருள்")
    device = QueryExpander().expand("உவமை உள்ள பாடல்கள்")

    assert "சிவன்" in deity["expanded_terms"]
    assert deity["matched_registries"] == ["deities"]
    assert {"போல்", "போன்ற", "ஒத்த"} <= set(device["expanded_terms"])
    assert device["matched_registries"] == ["literary_devices"]


def test_deterministic_output() -> None:
    expander = QueryExpander()

    assert expander.expand("மதி உவமை") == expander.expand("மதி உவமை")


def test_cli_output(capsys) -> None:
    assert expand_main(["--query", "அப்பர் பாடல்கள்"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["original_query"] == "அப்பர் பாடல்கள்"
    assert payload["expansion_applied"] is True


def test_context_expansion_is_optional(tmp_path) -> None:
    enriched = tmp_path / "enriched.jsonl"
    write_enriched(enriched)
    retriever = FakeRetriever()
    builder = ContextBuilder(retriever=retriever, enriched_path=enriched)

    baseline = builder.build("அப்பர் பாடல்கள்", top_k=1)
    expanded = builder.build("அப்பர் பாடல்கள்", top_k=1, expand_query=True)

    assert retriever.queries[0] == "அப்பர் பாடல்கள்"
    assert "query_expansion" not in baseline
    assert "திருநாவுக்கரசர்" in retriever.queries[1]
    assert expanded["query"] == "அப்பர் பாடல்கள்"
    assert expanded["query_expansion"]["expansion_applied"] is True


def test_evaluation_and_report_generation(tmp_path) -> None:
    retriever = FakeRetriever()
    records = {
        "r1": {"record_id": "r1", "verse_text_normalized": "பொதுப் பாடல்"},
        "r2": {"record_id": "r2", "verse_text_normalized": "திருநாவுக்கரசர் பாடல்"},
    }
    cases = ({"query_id": "author", "query": "அப்பர் பாடல்கள்"},)

    first = evaluate(retriever, QueryExpander(), records, cases=cases, top_k=1)
    second = evaluate(FakeRetriever(), QueryExpander(), records, cases=cases, top_k=1)
    output = tmp_path / "results.json"
    report = tmp_path / "report.md"
    write_outputs(first, output, report)

    assert first == second
    assert first["summary"]["improved"] == 1
    assert json.loads(output.read_text(encoding="utf-8"))["summary"]["queries_tested"] == 1
    assert "Query Results" in render_report(first)
    assert report.exists()


def test_no_scraping_or_llm_dependencies() -> None:
    sources = [
        Path("src/retrieval/query_expander.py").read_text(encoding="utf-8").lower(),
        Path("src/evaluation/evaluate_query_expansion.py").read_text(encoding="utf-8").lower(),
    ]

    assert all("requests" not in source for source in sources)
    assert all("openai" not in source and "anthropic" not in source for source in sources)
