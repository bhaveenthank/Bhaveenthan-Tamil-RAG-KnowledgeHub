from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from retrieval.hybrid_retriever import HybridRetriever
from retrieval.query_expander import QueryExpander

DEFAULT_ENRICHED = Path("data/processed/enriched/irandaam_thirumurai_enriched.jsonl")
DEFAULT_OUTPUT = Path("data/processed/eval/query_expansion_results.json")
DEFAULT_REPORT = Path("reports/query-expansion-evaluation-report.md")
DEFAULT_TOP_K = 5
EVALUATION_CASES = (
    {"query_id": "author_appar", "query": "அப்பர் பாடல்கள்"},
    {"query_id": "concept_moon", "query": "சந்திரன் வரும் பாடல்கள்"},
    {"query_id": "deity_siva", "query": "சிவன் பற்றிய பாடல்கள்"},
    {"query_id": "device_simile", "query": "உவமை உள்ள பாடல்கள்"},
)
TEXT_FIELDS = (
    "verse_text_normalized",
    "pozhppurai_normalized",
    "kurippurai_normalized",
    "metadata_text",
    "author",
    "hymn_title",
)


def load_records(path: Path) -> dict[str, dict[str, Any]]:
    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {record["record_id"]: record for record in records}


def compact_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rank": result.get("rank"),
            "parent_record_id": result.get("parent_record_id") or result.get("record_id"),
            "chunk_id": result.get("chunk_id"),
            "hybrid_score": result.get("hybrid_score", result.get("score", 0.0)),
            "matched_modes": result.get("matched_modes", []),
        }
        for result in results
    ]


def evidence_rank(
    results: list[dict[str, Any]],
    records: dict[str, dict[str, Any]],
    terms: list[str],
) -> tuple[int | None, int]:
    hits = 0
    first_rank = None
    for result in results:
        record_id = result.get("parent_record_id") or result.get("record_id")
        record = records.get(record_id, {})
        searchable = " ".join(str(record.get(field, "")) for field in TEXT_FIELDS)
        if terms and any(term in searchable for term in terms):
            hits += 1
            first_rank = first_rank or int(result.get("rank", 0))
    return first_rank, hits


def assess_change(
    baseline_rank: int | None,
    baseline_hits: int,
    expanded_rank: int | None,
    expanded_hits: int,
) -> str:
    baseline_key = (baseline_rank is not None, -(baseline_rank or 10**9), baseline_hits)
    expanded_key = (expanded_rank is not None, -(expanded_rank or 10**9), expanded_hits)
    if expanded_key > baseline_key:
        return "improved"
    if expanded_key < baseline_key:
        return "degraded"
    return "neutral"


def evaluate(
    retriever: Any,
    expander: QueryExpander,
    records: dict[str, dict[str, Any]],
    cases: tuple[dict[str, str], ...] = EVALUATION_CASES,
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, Any]:
    query_results = []
    for case in cases:
        expansion = expander.expand(case["query"])
        baseline = retriever.search(case["query"], filters={}, top_k=top_k)
        expanded = retriever.search(expansion["expanded_query_text"], filters={}, top_k=top_k)
        evidence_terms = expansion["expanded_terms"]
        baseline_rank, baseline_hits = evidence_rank(baseline, records, evidence_terms)
        expanded_rank, expanded_hits = evidence_rank(expanded, records, evidence_terms)
        baseline_ids = [
            result.get("parent_record_id") or result.get("record_id") for result in baseline
        ]
        expanded_ids = [
            result.get("parent_record_id") or result.get("record_id") for result in expanded
        ]
        query_results.append(
            {
                "query_id": case["query_id"],
                "query": case["query"],
                "expansion": expansion,
                "baseline_results": compact_results(baseline),
                "expanded_results": compact_results(expanded),
                "retrieved_contexts_changed": baseline_ids != expanded_ids,
                "baseline_evidence": {
                    "first_rank": baseline_rank,
                    "top_k_hits": baseline_hits,
                },
                "expanded_evidence": {
                    "first_rank": expanded_rank,
                    "top_k_hits": expanded_hits,
                },
                "assessment": assess_change(
                    baseline_rank,
                    baseline_hits,
                    expanded_rank,
                    expanded_hits,
                ),
            }
        )

    counts = {
        outcome: sum(result["assessment"] == outcome for result in query_results)
        for outcome in ("improved", "degraded", "neutral")
    }
    return {
        "evaluation_version": "query-expansion-evaluation-v1",
        "retrieval_mode": "hybrid",
        "top_k": top_k,
        "assessment_method": (
            "Compare ranks and counts of top-k records containing curated expansion terms; "
            "this is a deterministic evidence proxy, not human relevance judgment."
        ),
        "summary": {
            "queries_tested": len(query_results),
            "queries_expanded": sum(
                result["expansion"]["expansion_applied"] for result in query_results
            ),
            "retrieval_results_changed": sum(
                result["retrieved_contexts_changed"] for result in query_results
            ),
            **counts,
        },
        "query_results": query_results,
    }


def render_report(evaluation: dict[str, Any]) -> str:
    summary = evaluation["summary"]
    lines = [
        "# Query Expansion Evaluation Report",
        "",
        "## Summary",
        "",
        f"- Queries tested: `{summary['queries_tested']}`",
        f"- Queries expanded: `{summary['queries_expanded']}`",
        f"- Retrieval result sets changed: `{summary['retrieval_results_changed']}`",
        f"- Improved: `{summary['improved']}`",
        f"- Degraded: `{summary['degraded']}`",
        f"- Neutral: `{summary['neutral']}`",
        "",
        "Assessment uses a deterministic corpus-evidence proxy: the first rank and count of top-k records containing curated expansion terms. It is not a substitute for Tamil researcher relevance judgments.",
        "",
        "## Query Results",
        "",
        "| Query | Registries | Expanded Query | Changed | Baseline Hits | Expanded Hits | Assessment |",
        "| --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for result in evaluation["query_results"]:
        expansion = result["expansion"]
        lines.append(
            f"| {result['query']} | {', '.join(expansion['matched_registries']) or '-'} "
            f"| {expansion['expanded_query_text']} "
            f"| {'yes' if result['retrieved_contexts_changed'] else 'no'} "
            f"| {result['baseline_evidence']['top_k_hits']} "
            f"| {result['expanded_evidence']['top_k_hits']} "
            f"| {result['assessment']} |"
        )
    lines.extend(
        [
            "",
            "## Known Limitations",
            "",
            "- The curated registries are intentionally small and do not cover inflected or sandhi forms.",
            "- Expansion can increase lexical recall while also introducing broad aliases or imagery cues.",
            "- The current corpus is Irandaam Thirumurai; an Appar query cannot be fully evaluated against an author corpus that is not indexed.",
            "- Human relevance labels are still required before treating these outcomes as retrieval quality metrics.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(evaluation: dict[str, Any], output: Path, report: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report.write_text(render_report(evaluation), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare baseline and registry-expanded hybrid retrieval")
    parser.add_argument("--enriched", type=Path, default=DEFAULT_ENRICHED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    retriever: Any | None = None,
    expander: QueryExpander | None = None,
) -> int:
    args = parse_args(argv)
    evaluation = evaluate(
        retriever or HybridRetriever(),
        expander or QueryExpander(),
        load_records(args.enriched),
        top_k=args.top_k,
    )
    write_outputs(evaluation, args.output, args.report)
    summary = evaluation["summary"]
    print(
        "Query expansion evaluation complete: "
        f"queries={summary['queries_tested']} improved={summary['improved']} "
        f"degraded={summary['degraded']} neutral={summary['neutral']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
