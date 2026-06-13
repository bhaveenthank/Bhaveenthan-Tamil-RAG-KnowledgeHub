from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any

if __package__ in {None, ""}:
    for parent in Path(__file__).resolve().parents:
        shared_src = parent / "shared/tvu-common/src"
        legacy_src = parent / "src"
        if shared_src.is_dir() and legacy_src.is_dir():
            sys.path.insert(0, str(shared_src))
            sys.path.insert(0, str(legacy_src))
            break
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.evaluation_artifacts import (
    load_evaluation_manifest,
    resolve_manifest_output,
    verify_manifest_output_checksum,
    write_evaluation_manifest,
)

DEFAULT_BENCHMARK = Path("data/processed/eval/retrieval_benchmark_results.json")
DEFAULT_GOLDEN = Path("data/processed/eval/golden_queries.jsonl")
DEFAULT_LEXICAL_INDEX = Path("data/processed/indexes/irandaam_thirumurai_lexical_index.json")
DEFAULT_OUTPUT = Path("data/processed/eval/retrieval_failure_analysis.json")
DEFAULT_REPORT = Path("reports/retrieval-error-analysis-report.md")

CATEGORY_EXPLANATIONS = {
    "exact identifier mismatch": "The query expects an exact corpus identifier that semantic similarity does not preserve reliably.",
    "hymn/song reference mismatch": "The query names a hymn, place, or song reference, but semantic ranking preferred conceptually related text.",
    "rare term mismatch": "The exact Tamil term occurs in relatively few records and was not represented strongly enough by the multilingual embedding.",
    "classical Tamil phrase mismatch": "The query depends on literal classical Tamil wording; semantic similarity did not behave like exact token matching.",
    "metadata mismatch": "The query targets metadata or absence/presence state that is not directly encoded in verse-plus-commentary text.",
    "chunking limitation": "The expected evidence belongs to a chunk type that is not present in the semantic index.",
    "embedding limitation": "The multilingual embedding did not place the expected record within the top semantic results.",
    "unknown": "The available benchmark evidence is insufficient for a stronger automatic classification.",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def benchmark_path_from_manifest(manifest_path: Path) -> Path:
    manifest = load_evaluation_manifest(manifest_path)
    if manifest.get("evaluation_type") != "retrieval_benchmark":
        raise ValueError(
            f"expected retrieval_benchmark manifest, got {manifest.get('evaluation_type')!r}"
        )
    benchmark_path = resolve_manifest_output(manifest_path, manifest, "results")
    verify_manifest_output_checksum(manifest_path, manifest, "results", benchmark_path)
    return benchmark_path


def extract_literal_term(query_text: str) -> str:
    match = re.search(r"records containing\s+(.+)$", query_text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else query_text.strip()


def classify_failure(
    query: dict[str, Any],
    lexical_index: dict[str, Any] | None = None,
) -> tuple[str, float, str, dict[str, Any]]:
    query_type = query.get("query_type", "")
    query_text = query.get("query_text", "")
    filters = query.get("required_filters", {})
    expected_chunks = query.get("expected_chunk_ids", [])
    term = extract_literal_term(query_text)
    term_frequency = len((lexical_index or {}).get("term_to_record_ids", {}).get(term, []))
    evidence = {"literal_term": term, "lexical_document_frequency": term_frequency}

    if query_type in {"exact_lookup", "manual_spot_check"}:
        category, confidence = "exact identifier mismatch", 0.98
    elif query_type == "exact_title" or filters.get("song_no") or filters.get("hymn_id"):
        category, confidence = "hymn/song reference mismatch", 0.95
    elif query_type in {"metadata", "commentary"} or "missing " in query_text.lower():
        category, confidence = "metadata mismatch", 0.98
    elif expected_chunks and not any(chunk_id.endswith("verse_plus_commentary") for chunk_id in expected_chunks):
        category, confidence = "chunking limitation", 0.90
    elif query_type == "keyword" and 0 < term_frequency <= 13:
        category, confidence = "rare term mismatch", 0.88
    elif query_type == "keyword" and re.search(r"[\u0B80-\u0BFF]", term):
        category, confidence = "classical Tamil phrase mismatch", 0.84
    elif query_type in {"keyword", "mixed"}:
        category, confidence = "embedding limitation", 0.78
    else:
        category, confidence = "unknown", 0.50

    return category, confidence, CATEGORY_EXPLANATIONS[category], evidence


def first_relevant_rank(query_result: dict[str, Any]) -> int | None:
    expected_records = set(query_result.get("missing_expected_record_ids", []))
    expected_chunks = set(query_result.get("missing_expected_chunk_ids", []))
    for result in query_result.get("results", []):
        if result.get("record_id") in expected_records or result.get("chunk_id") in expected_chunks:
            return int(result["rank"])
    if query_result.get("reciprocal_rank", 0):
        return round(1 / query_result["reciprocal_rank"])
    return None


def score_summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "minimum": None, "maximum": None, "mean": None, "median": None}
    ordered = sorted(values)
    return {
        "count": len(values),
        "minimum": round(ordered[0], 8),
        "maximum": round(ordered[-1], 8),
        "mean": round(mean(ordered), 8),
        "median": round(median(ordered), 8),
    }


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "rank": result.get("rank"),
        "record_id": result.get("record_id"),
        "chunk_id": result.get("chunk_id"),
        "similarity_score": result.get("similarity_score", result.get("score")),
        "citation_text": result.get("citation_text", ""),
    }


def hybrid_recovery(semantic_query: dict[str, Any], hybrid_query: dict[str, Any] | None) -> dict[str, Any]:
    if not hybrid_query:
        return {"recovered": False, "hybrid_rank": None, "top_result": {}, "lexical_correction": {}}
    expected_records = set(semantic_query.get("missing_expected_record_ids", []))
    expected_chunks = set(semantic_query.get("missing_expected_chunk_ids", []))
    relevant = next(
        (
            result
            for result in hybrid_query.get("results", [])
            if result.get("record_id") in expected_records or result.get("chunk_id") in expected_chunks
        ),
        None,
    )
    if not relevant:
        return {"recovered": False, "hybrid_rank": None, "top_result": compact_result(hybrid_query["results"][0]) if hybrid_query.get("results") else {}, "lexical_correction": {}}
    return {
        "recovered": bool(hybrid_query.get("passed")),
        "hybrid_rank": relevant.get("rank"),
        "top_result": {
            "record_id": relevant.get("record_id"),
            "chunk_id": relevant.get("chunk_id"),
            "hybrid_score": relevant.get("hybrid_score", relevant.get("score")),
            "matched_modes": relevant.get("matched_modes", []),
            "matched_fields": relevant.get("matched_fields", []),
        },
        "lexical_correction": {
            "normalized_lexical_score": relevant.get("normalized_lexical_score", 0.0),
            "normalized_semantic_score": relevant.get("normalized_semantic_score", 0.0),
            "exact_match_boost": relevant.get("exact_match_boost", 0.0),
            "metadata_filter_boost": relevant.get("metadata_filter_boost", 0.0),
            "lexical_fields": relevant.get("matched_fields", []),
        },
    }


def analyze(
    benchmark: dict[str, Any],
    golden_queries: list[dict[str, Any]],
    lexical_index: dict[str, Any],
    benchmark_sha256: str = "",
) -> dict[str, Any]:
    golden_by_id = {query["query_id"]: query for query in golden_queries}
    semantic_queries = benchmark["semantic"]["query_results"]
    hybrid_by_id = {query["query_id"]: query for query in benchmark.get("hybrid", {}).get("query_results", [])}
    failures = []
    successes = []

    for semantic in semantic_queries:
        golden = golden_by_id.get(semantic["query_id"], {})
        merged = {**golden, **semantic}
        scores = [
            float(result.get("similarity_score", result.get("score", 0.0)))
            for result in semantic.get("results", [])
        ]
        rank = first_relevant_rank(semantic)
        if semantic["passed"]:
            successes.append(
                {
                    "query_id": semantic["query_id"],
                    "query_type": semantic["query_type"],
                    "first_relevant_rank": rank,
                    "top_similarity_score": scores[0] if scores else None,
                }
            )
            continue

        category, confidence, explanation, evidence = classify_failure(merged, lexical_index)
        recovery = hybrid_recovery(semantic, hybrid_by_id.get(semantic["query_id"]))
        failures.append(
            {
                "query_id": semantic["query_id"],
                "query": semantic["query_text"],
                "query_type": semantic["query_type"],
                "required_filters": golden.get("required_filters", {}),
                "expected_record_ids": golden.get("expected_record_ids", semantic.get("missing_expected_record_ids", [])),
                "expected_chunk_ids": golden.get("expected_chunk_ids", semantic.get("missing_expected_chunk_ids", [])),
                "retrieved_records": [compact_result(result) for result in semantic.get("results", [])],
                "retrieved_ranks": [result.get("rank") for result in semantic.get("results", [])],
                "similarity_scores": scores,
                "top_similarity_score": scores[0] if scores else None,
                "expected_first_rank": rank,
                "failure_category": category,
                "confidence": confidence,
                "explanation": explanation,
                "classification_evidence": evidence,
                "hybrid_recovery": recovery,
            }
        )

    category_counts = Counter(item["failure_category"] for item in failures)
    failure_total = len(failures)
    all_failed_scores = [score for item in failures for score in item["similarity_scores"]]
    all_success_scores = [
        float(result.get("similarity_score", result.get("score", 0.0)))
        for query in semantic_queries
        if query["passed"]
        for result in query.get("results", [])
    ]
    success_ranks = [item["first_relevant_rank"] for item in successes if item["first_relevant_rank"]]
    recovered = [item for item in failures if item["hybrid_recovery"]["recovered"]]

    return {
        "analysis_version": "retrieval-error-analysis-v1",
        "source_benchmark_sha256": benchmark_sha256,
        "summary": {
            "semantic_queries": len(semantic_queries),
            "semantic_successes": len(successes),
            "semantic_failures": failure_total,
            "hybrid_recoveries": len(recovered),
            "hybrid_recovery_rate": round(len(recovered) / failure_total, 4) if failure_total else 0.0,
            "remaining_hybrid_failures": failure_total - len(recovered),
        },
        "failure_categories": {
            category: {
                "count": count,
                "percentage": round(100 * count / failure_total, 2) if failure_total else 0.0,
            }
            for category, count in sorted(category_counts.items())
        },
        "rank_distributions": {
            "semantic_success_first_relevant_ranks": dict(sorted(Counter(success_ranks).items())),
            "semantic_failures_beyond_top_10": sum(item["expected_first_rank"] is None for item in failures),
        },
        "similarity_score_distributions": {
            "failed_query_results": score_summary(all_failed_scores),
            "successful_query_results": score_summary(all_success_scores),
            "failed_top_scores": score_summary(
                [item["top_similarity_score"] for item in failures if item["top_similarity_score"] is not None]
            ),
            "successful_top_scores": score_summary(
                [item["top_similarity_score"] for item in successes if item["top_similarity_score"] is not None]
            ),
        },
        "success_cases": successes,
        "failures": failures,
    }


def render_report(analysis: dict[str, Any]) -> str:
    summary = analysis["summary"]
    lines = [
        "# Retrieval Error Analysis Report",
        "",
        "## Executive Summary",
        "",
        f"- Semantic queries analyzed: `{summary['semantic_queries']}`",
        f"- Semantic successes: `{summary['semantic_successes']}`",
        f"- Semantic failures: `{summary['semantic_failures']}`",
        f"- Semantic failures rescued by hybrid: `{summary['hybrid_recoveries']}`",
        f"- Hybrid recovery rate: `{summary['hybrid_recovery_rate'] * 100:.2f}%`",
        f"- Remaining hybrid failures: `{summary['remaining_hybrid_failures']}`",
        "",
        "## Failure Categories",
        "",
        "| Category | Count | Percentage |",
        "| --- | ---: | ---: |",
    ]
    for category, values in analysis["failure_categories"].items():
        lines.append(f"| {category} | {values['count']} | {values['percentage']:.2f}% |")

    failed_scores = analysis["similarity_score_distributions"]["failed_query_results"]
    success_scores = analysis["similarity_score_distributions"]["successful_query_results"]
    lines.extend(
        [
            "",
            "## Retrieval Score Analysis",
            "",
            "| Population | Results | Minimum | Mean | Median | Maximum |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
            f"| Failed semantic queries | {failed_scores['count']} | {failed_scores['minimum']} | {failed_scores['mean']} | {failed_scores['median']} | {failed_scores['maximum']} |",
            f"| Successful semantic queries | {success_scores['count']} | {success_scores['minimum']} | {success_scores['mean']} | {success_scores['median']} | {success_scores['maximum']} |",
            "",
            f"- Failed queries with no expected result in top 10: `{analysis['rank_distributions']['semantic_failures_beyond_top_10']}`",
            "",
            "Similarity magnitude alone did not separate success from failure. Exact identifiers, literal Tamil terms, and metadata state require lexical evidence.",
            "",
            "## Query-Level Failures",
            "",
            "| Query | Type | Category | Confidence | Semantic Top Record | Top Score | Hybrid Recovered | Hybrid Rank |",
            "| --- | --- | --- | ---: | --- | ---: | --- | ---: |",
        ]
    )
    for item in analysis["failures"]:
        top = item["retrieved_records"][0] if item["retrieved_records"] else {}
        recovery = item["hybrid_recovery"]
        lines.append(
            f"| `{item['query_id']}` | {item['query_type']} | {item['failure_category']} | {item['confidence']:.2f} | `{top.get('record_id', '')}` | {item['top_similarity_score']} | `{recovery['recovered']}` | {recovery['hybrid_rank'] or ''} |"
        )

    lines.extend(
        [
            "",
            "## Hybrid Diagnostics",
            "",
            "| Query | Matched Modes | Lexical Normalized | Semantic Normalized | Exact Boost | Metadata Boost |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in analysis["failures"]:
        recovery = item["hybrid_recovery"]
        correction = recovery["lexical_correction"]
        top = recovery["top_result"]
        lines.append(
            f"| `{item['query_id']}` | `{top.get('matched_modes', [])}` | {correction.get('normalized_lexical_score', 0)} | {correction.get('normalized_semantic_score', 0)} | {correction.get('exact_match_boost', 0)} | {correction.get('metadata_filter_boost', 0)} |"
        )

    lines.extend(
        [
            "",
            "## Major Findings",
            "",
            "- Literal Tamil title and keyword queries are not safely replaceable with semantic similarity.",
            "- Queries about missing commentary fields are metadata predicates; their absence is not represented by verse-plus-commentary vectors.",
            "- Hybrid retrieval recovered semantic failures by restoring exact lexical terms, title matches, commentary availability signals, and metadata filters.",
            "- Similarity scores overlap substantially between successful and failed queries, so a global similarity threshold alone is not a sufficient fix.",
            "",
            "## Recommendations",
            "",
            "1. Keep lexical-heavy hybrid retrieval as the default candidate for future RAG.",
            "2. Route identifiers, titles, song numbers, hymn IDs, `pann`, and commentary availability predicates through lexical/metadata retrieval.",
            "3. Use semantic retrieval for conceptual expansion after precise lexical candidates are secured.",
            "4. Preserve deterministic boosts and citations in any future RAG retriever.",
            "5. Expand the golden set with natural Tamil research questions before interpreting semantic quality as production-ready.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(
    analysis: dict[str, Any],
    output_path: Path,
    report_path: Path,
    *,
    manifest_path: Path | None = None,
    source_artifacts: list[str] | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(analysis), encoding="utf-8")
    write_evaluation_manifest(
        evaluation_type="retrieval_failure_analysis",
        producer="evaluation.analyze_retrieval_failures",
        record_count=int(analysis["summary"]["semantic_failures"]),
        outputs={"results": output_path, "report": report_path},
        manifest_path=manifest_path,
        source_artifacts=source_artifacts or [],
        modes=["semantic", "hybrid"],
        metrics=analysis["summary"],
        warnings=[
            f"remaining_hybrid_failures:{analysis['summary']['remaining_hybrid_failures']}"
            for _ in [None]
            if int(analysis["summary"].get("remaining_hybrid_failures") or 0) > 0
        ],
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze semantic retrieval failures and hybrid recoveries")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--benchmark-manifest", type=Path)
    parser.add_argument("--golden-queries", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--lexical-index", type=Path, default=DEFAULT_LEXICAL_INDEX)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--manifest", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    benchmark_path = (
        benchmark_path_from_manifest(args.benchmark_manifest)
        if args.benchmark_manifest
        else args.benchmark
    )
    benchmark = load_json(benchmark_path)
    golden_queries = load_jsonl(args.golden_queries)
    lexical_index = load_json(args.lexical_index)
    analysis = analyze(
        benchmark,
        golden_queries,
        lexical_index,
        benchmark_sha256=sha256_file(benchmark_path),
    )
    write_outputs(
        analysis,
        args.output,
        args.report,
        manifest_path=args.manifest,
        source_artifacts=[
            str(args.benchmark_manifest or benchmark_path),
            str(args.golden_queries),
            str(args.lexical_index),
        ],
    )
    summary = analysis["summary"]
    print(
        "Retrieval diagnostics complete: "
        f"semantic_failures={summary['semantic_failures']} "
        f"hybrid_recoveries={summary['hybrid_recoveries']} "
        f"remaining={summary['remaining_hybrid_failures']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
