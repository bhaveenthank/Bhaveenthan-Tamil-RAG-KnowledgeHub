import json
from pathlib import Path

from analytics.build_occurrence_index import build_occurrence_index, build_index_rows
from analytics.search_occurrences import build_example_results, search_occurrences
from knowledge.analyze_knowledge_readiness import analyze_knowledge_readiness


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_index_creation_and_metadata_preservation(tmp_path: Path) -> None:
    source = tmp_path / "normalized" / "sample_normalized.jsonl"
    write_jsonl(
        source,
        [
            {
                "corpus_id": "sample",
                "category_id": "verse",
                "record_id": "r1",
                "record_type": "verse_record",
                "author": "அப்பர்",
                "title": "சந்திரன் பாடல்",
                "verse_text": "சந்திரன் நிலா மதி",
                "source_url": "https://example.test/r1",
            }
        ],
    )

    rows, manifest = build_index_rows([source])

    assert manifest["indexed_records"] == 1
    assert "verse_text" in manifest["indexed_fields"]
    assert rows[0]["record_id"] == "r1"
    assert rows[0]["source_url"] == "https://example.test/r1"


def test_occurrence_search_and_expanded_search() -> None:
    rows = [
        {
            "corpus_id": "sample",
            "category_id": "verse",
            "record_id": "r1",
            "record_type": "verse_record",
            "field_name": "verse_text",
            "text": "சந்திரன் நிலா மதி திங்கள்",
            "author": "புலவர்",
            "title": "நிலா",
            "source_url": "https://example.test/r1",
            "commentary_url": "",
            "source_metadata": {},
        }
    ]

    literal = search_occurrences("சந்திரன்", index_rows=rows)
    expanded = search_occurrences("சந்திரன்", expand_query=True, index_rows=rows)

    assert literal["occurrence_count"] == 1
    assert expanded["occurrence_count"] >= 4
    assert {"சந்திரன்", "நிலா", "மதி", "திங்கள்"} <= set(expanded["matched_terms"])
    assert expanded["results"][0]["source_url"] == "https://example.test/r1"


def test_no_duplicate_results_and_deterministic_output() -> None:
    rows = [
        {
            "corpus_id": "sample",
            "category_id": "verse",
            "record_id": "r1",
            "record_type": "verse_record",
            "field_name": "verse_text",
            "text": "மதி மதி",
            "author": "",
            "title": "",
            "source_url": "https://example.test/r1",
            "commentary_url": "",
            "source_metadata": {},
        }
    ]

    first = search_occurrences("மதி", index_rows=rows)
    second = search_occurrences("மதி", index_rows=rows)
    keys = [result["deterministic_key"] for result in first["results"]]

    assert first == second
    assert len(keys) == len(set(keys))
    assert first["occurrence_count"] == 2


def test_build_outputs_and_examples(tmp_path: Path) -> None:
    source = tmp_path / "normalized_categories" / "dictionary_normalized.jsonl"
    output = tmp_path / "analytics" / "occurrence_index.jsonl"
    manifest_path = tmp_path / "analytics" / "manifest.json"
    report_path = tmp_path / "reports" / "report.md"
    write_jsonl(
        source,
        [
            {
                "category_id": "dictionaries",
                "record_id": "d1",
                "record_type": "dictionary_entry",
                "definition": "சிவன் கடவுள்",
                "entry_headword": "அ",
                "source_url": "https://example.test/d1",
            }
        ],
    )

    manifest = build_occurrence_index(
        output=output,
        manifest_path=manifest_path,
        report_path=report_path,
        input_dirs=(source.parent,),
    )
    examples = build_example_results([])

    assert output.exists()
    assert manifest_path.exists()
    assert report_path.exists()
    assert manifest["indexed_records"] == 1
    assert len(examples["examples"]) == 4
    assert all(example["occurrence_count"] == 0 for example in examples["examples"])


def test_readiness_includes_occurrence_coverage(tmp_path: Path) -> None:
    manifest = tmp_path / "occurrence_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "indexed_records": 10,
                "indexed_field_entries": 20,
                "indexed_fields": ["verse_text", "title"],
            }
        ),
        encoding="utf-8",
    )

    analysis = analyze_knowledge_readiness(
        Path("data/knowledge"),
        occurrence_manifest_path=manifest,
    )

    assert analysis["evidence_readiness_score"] == 62.5
    assert analysis["occurrence_coverage"]["occurrence_index_available"] is True
    assert analysis["occurrence_coverage"]["aggregation_performed"] is False


def test_no_scraping_or_llm_dependencies() -> None:
    text = "\n".join(
        Path(path).read_text(encoding="utf-8").lower()
        for path in (
            "src/analytics/build_occurrence_index.py",
            "src/analytics/search_occurrences.py",
        )
    )

    for forbidden in ("requests", "httpx", "urlopen", "openai", "anthropic", "google.cloud"):
        assert forbidden not in text
