from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from retrieval.lexical_retriever import LexicalRetriever
from retrieval.hybrid_retriever import DEFAULT_LEXICAL_WEIGHT, DEFAULT_SEMANTIC_WEIGHT, HybridRetriever
from retrieval.semantic_retriever import DEFAULT_VECTOR_MANIFEST, SemanticRetriever

DEFAULT_GOLDEN = Path("data/processed/eval/golden_queries.jsonl")
DEFAULT_RESULTS = Path("data/processed/eval/retrieval_benchmark_results.json")
DEFAULT_REPORT = Path("reports/retrieval-benchmark-report.md")
DEFAULT_SEMANTIC_REPORT = Path("reports/semantic-retrieval-benchmark-report.md")
DEFAULT_HYBRID_REPORT = Path("reports/hybrid-retrieval-benchmark-report.md")
DEFAULT_COMPARISON = Path("reports/retrieval-comparison-report.md")

PENDING = "PENDING_EMBEDDINGS"
PENDING_VECTOR_INDEX = "PENDING_VECTOR_INDEX"
PENDING_HYBRID = "PENDING_HYBRID_IMPLEMENTATION"
HYBRID_ABLATIONS = {
    "lexical-heavy": (0.80, 0.20),
    "balanced": (0.50, 0.50),
    "semantic-heavy": (0.30, 0.70),
}


@dataclass(slots=True)
class ModeResult:
    mode: str
    status: str
    metrics: dict[str, Any]
    query_results: list[dict[str, Any]]
    message: str = ""


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def reciprocal_rank(results: list[dict], expected_record_ids: set[str], expected_chunk_ids: set[str]) -> float:
    for index, result in enumerate(results, start=1):
        if result["record_id"] in expected_record_ids or (result.get("chunk_id") in expected_chunk_ids):
            return 1 / index
    return 0.0


def hit_at(results: list[dict], expected_record_ids: set[str], expected_chunk_ids: set[str], k: int) -> bool:
    top = results[:k]
    return any(result["record_id"] in expected_record_ids or result.get("chunk_id") in expected_chunk_ids for result in top)


def evaluate_query(query: dict, results: list[dict]) -> dict:
    expected_records = set(query.get("expected_record_ids", []))
    expected_chunks = set(query.get("expected_chunk_ids", []))
    found_records = {result["record_id"] for result in results}
    found_chunks = {result.get("chunk_id") for result in results if result.get("chunk_id")}
    relevant_results = [
        result
        for result in results
        if result["record_id"] in expected_records or result.get("chunk_id") in expected_chunks
    ]
    return {
        "query_id": query["query_id"],
        "query_text": query["query_text"],
        "query_type": query["query_type"],
        "result_count": len(results),
        "top_record_id": results[0]["record_id"] if results else "",
        "top_chunk_id": results[0].get("chunk_id", "") if results else "",
        "hit_at_1": hit_at(results, expected_records, expected_chunks, 1),
        "hit_at_3": hit_at(results, expected_records, expected_chunks, 3),
        "hit_at_5": hit_at(results, expected_records, expected_chunks, 5),
        "hit_at_10": hit_at(results, expected_records, expected_chunks, 10),
        "reciprocal_rank": reciprocal_rank(results, expected_records, expected_chunks),
        "exact_match_at_1": bool(results)
        and (results[0]["record_id"] in expected_records or results[0].get("chunk_id") in expected_chunks),
        "expected_min_results_satisfied": len(relevant_results) >= query.get("expected_min_results", 1),
        "missing_expected_record_ids": sorted(expected_records - found_records),
        "missing_expected_chunk_ids": sorted(expected_chunks - found_chunks)[:100],
        "passed": hit_at(results, expected_records, expected_chunks, 10)
        and len(relevant_results) >= query.get("expected_min_results", 1),
        "results": results,
    }


def aggregate_metrics(query_results: list[dict]) -> dict:
    total = len(query_results)
    if total == 0:
        return {
            "queries_evaluated": 0,
            "queries_skipped": 0,
            "recall@1": 0.0,
            "recall@3": 0.0,
            "recall@5": 0.0,
            "recall@10": 0.0,
            "MRR": 0.0,
            "exact_match@1": 0.0,
            "expected_min_results_satisfied": 0,
            "failed_queries": 0,
        }
    return {
        "queries_evaluated": total,
        "queries_skipped": 0,
        "recall@1": sum(result["hit_at_1"] for result in query_results) / total,
        "recall@3": sum(result["hit_at_3"] for result in query_results) / total,
        "recall@5": sum(result["hit_at_5"] for result in query_results) / total,
        "recall@10": sum(result["hit_at_10"] for result in query_results) / total,
        "MRR": sum(result["reciprocal_rank"] for result in query_results) / total,
        "exact_match@1": sum(result["exact_match_at_1"] for result in query_results) / total,
        "expected_min_results_satisfied": sum(result["expected_min_results_satisfied"] for result in query_results),
        "failed_queries": sum(not result["passed"] for result in query_results),
    }


def run_lexical(golden_queries: list[dict], top_k: int = 10) -> ModeResult:
    retriever = LexicalRetriever()
    query_results = []
    for query in golden_queries:
        results = retriever.search(query["query_text"], filters=query.get("required_filters", {}), top_k=top_k)
        query_results.append(evaluate_query(query, results))
    return ModeResult(
        mode="lexical",
        status="EVALUATED",
        metrics=aggregate_metrics(query_results),
        query_results=query_results,
    )


def run_semantic(golden_queries: list[dict], top_k: int = 10) -> ModeResult:
    if not DEFAULT_VECTOR_MANIFEST.exists():
        return pending_mode("semantic", len(golden_queries), status=PENDING_VECTOR_INDEX)
    retriever = SemanticRetriever()
    query_results = []
    for query in golden_queries:
        results = retriever.search(query["query_text"], filters=query.get("required_filters", {}), top_k=top_k)
        query_results.append(evaluate_query(query, results))
    return ModeResult(
        mode="semantic",
        status="EVALUATED",
        metrics=aggregate_metrics(query_results),
        query_results=query_results,
    )


def run_hybrid(
    golden_queries: list[dict],
    top_k: int = 10,
    lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
    semantic_weight: float = DEFAULT_SEMANTIC_WEIGHT,
    retriever: HybridRetriever | None = None,
) -> ModeResult:
    if not DEFAULT_VECTOR_MANIFEST.exists():
        return pending_mode("hybrid", len(golden_queries), status=PENDING_VECTOR_INDEX)
    retriever = retriever or HybridRetriever(lexical_weight=lexical_weight, semantic_weight=semantic_weight)
    query_results = []
    for query in golden_queries:
        results = retriever.search(query["query_text"], filters=query.get("required_filters", {}), top_k=top_k)
        query_results.append(evaluate_query(query, results))
    result = ModeResult(
        mode="hybrid",
        status="EVALUATED",
        metrics=aggregate_metrics(query_results),
        query_results=query_results,
    )
    result.metrics["lexical_weight"] = lexical_weight
    result.metrics["semantic_weight"] = semantic_weight
    return result


def run_hybrid_ablations(golden_queries: list[dict], top_k: int = 10) -> dict[str, dict[str, Any]]:
    if not DEFAULT_VECTOR_MANIFEST.exists():
        return {}
    output = {}
    for name, (lexical_weight, semantic_weight) in HYBRID_ABLATIONS.items():
        result = run_hybrid(
            golden_queries,
            top_k=top_k,
            lexical_weight=lexical_weight,
            semantic_weight=semantic_weight,
        )
        output[name] = {
            "lexical_weight": lexical_weight,
            "semantic_weight": semantic_weight,
            "status": result.status,
            "metrics": result.metrics,
        }
    return output


def pending_mode(mode: str, total_queries: int, status: str = PENDING) -> ModeResult:
    return ModeResult(
        mode=mode,
        status=status,
        metrics={
            "queries_evaluated": 0,
            "queries_skipped": total_queries,
            "recall@1": None,
            "recall@3": None,
            "recall@5": None,
            "recall@10": None,
            "MRR": None,
            "exact_match@1": None,
            "expected_min_results_satisfied": 0,
            "failed_queries": 0,
        },
        query_results=[],
        message=status,
    )


def mode_to_dict(result: ModeResult) -> dict:
    return {
        "mode": result.mode,
        "status": result.status,
        "metrics": result.metrics,
        "message": result.message,
        "query_results": result.query_results,
    }


def run_modes(
    mode: str,
    golden_queries: list[dict],
    top_k: int = 10,
    lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
    semantic_weight: float = DEFAULT_SEMANTIC_WEIGHT,
    include_ablations: bool = True,
) -> dict:
    modes = ["lexical", "semantic", "hybrid"] if mode == "all" else [mode]
    output = {}
    for item in modes:
        if item == "lexical":
            result = run_lexical(golden_queries, top_k=top_k)
        elif item == "semantic":
            result = run_semantic(golden_queries, top_k=top_k)
        elif item == "hybrid":
            result = run_hybrid(
                golden_queries,
                top_k=top_k,
                lexical_weight=lexical_weight,
                semantic_weight=semantic_weight,
            )
        else:
            raise ValueError(f"unsupported mode: {item}")
        output[item] = mode_to_dict(result)
    if include_ablations and ("hybrid" in output) and output["hybrid"]["status"] == "EVALUATED":
        output["hybrid_ablations"] = run_hybrid_ablations(golden_queries, top_k=top_k)
    return output


def render_metric(value: Any) -> str:
    if value is None:
        return "PENDING"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_benchmark_report(results: dict) -> str:
    lexical = results.get("lexical")
    semantic = results.get("semantic")
    hybrid = results.get("hybrid")
    lines = ["# Retrieval Benchmark Report", ""]
    if lexical:
        metrics = lexical["metrics"]
        lines.extend(
            [
                "## Benchmark Summary",
                "",
                f"- Lexical status: `{lexical['status']}`",
                f"- Queries evaluated: `{metrics['queries_evaluated']}`",
                f"- Recall@1: `{render_metric(metrics['recall@1'])}`",
                f"- Recall@3: `{render_metric(metrics['recall@3'])}`",
                f"- Recall@5: `{render_metric(metrics['recall@5'])}`",
                f"- Recall@10: `{render_metric(metrics['recall@10'])}`",
                f"- MRR: `{render_metric(metrics['MRR'])}`",
                f"- Failed queries: `{metrics['failed_queries']}`",
                "",
                "## Query-Level Results",
                "",
                "| Query ID | Type | Pass | Top Record | Top Chunk | RR |",
                "| --- | --- | --- | --- | --- | ---: |",
            ]
        )
        for item in lexical["query_results"]:
            lines.append(
                f"| `{item['query_id']}` | {item['query_type']} | `{item['passed']}` | `{item['top_record_id']}` | `{item['top_chunk_id']}` | {item['reciprocal_rank']:.3f} |"
            )
        failed = [item for item in lexical["query_results"] if not item["passed"]]
        lines.extend(["", "## Failed Queries", ""])
        if failed:
            for item in failed:
                lines.append(f"- `{item['query_id']}` missing records: `{item['missing_expected_record_ids'][:10]}`")
        else:
            lines.append("- None")
        successes = [item for item in lexical["query_results"] if item["passed"]][:5]
        lines.extend(["", "## Successful Retrieval Examples", ""])
        for item in successes:
            lines.append(f"- `{item['query_id']}` -> `{item['top_record_id']}` / `{item['top_chunk_id']}`")
        lines.extend(["", "## Failed Retrieval Examples", ""])
        if failed:
            for item in failed[:5]:
                lines.append(f"- `{item['query_id']}` returned `{item['top_record_id']}`")
        else:
            lines.append("- None")
    if semantic:
        metrics = semantic["metrics"]
        lines.extend(
            [
                "",
                "## Semantic Retrieval Results",
                "",
                f"- Semantic status: `{semantic['status']}`",
                f"- Queries evaluated: `{metrics['queries_evaluated']}`",
                f"- Recall@1: `{render_metric(metrics['recall@1'])}`",
                f"- Recall@3: `{render_metric(metrics['recall@3'])}`",
                f"- Recall@5: `{render_metric(metrics['recall@5'])}`",
                f"- Recall@10: `{render_metric(metrics['recall@10'])}`",
                f"- MRR: `{render_metric(metrics['MRR'])}`",
                f"- Failed queries: `{metrics['failed_queries']}`",
                "",
                "| Query ID | Type | Pass | Top Record | Top Chunk | RR |",
                "| --- | --- | --- | --- | --- | ---: |",
            ]
        )
        for item in semantic["query_results"]:
            lines.append(
                f"| `{item['query_id']}` | {item['query_type']} | `{item['passed']}` | `{item['top_record_id']}` | `{item['top_chunk_id']}` | {item['reciprocal_rank']:.3f} |"
            )
        failed = [item for item in semantic["query_results"] if not item["passed"]]
        lines.extend(["", "## Semantic Failed Queries", ""])
        if failed:
            for item in failed:
                lines.append(f"- `{item['query_id']}` missing records: `{item['missing_expected_record_ids'][:10]}`")
        else:
            lines.append("- None")
    if hybrid:
        metrics = hybrid["metrics"]
        lines.extend(
            [
                "",
                "## Hybrid Retrieval Results",
                "",
                f"- Hybrid status: `{hybrid['status']}`",
                f"- Lexical weight: `{render_metric(metrics.get('lexical_weight'))}`",
                f"- Semantic weight: `{render_metric(metrics.get('semantic_weight'))}`",
                f"- Queries evaluated: `{metrics['queries_evaluated']}`",
                f"- Recall@1: `{render_metric(metrics['recall@1'])}`",
                f"- Recall@3: `{render_metric(metrics['recall@3'])}`",
                f"- Recall@5: `{render_metric(metrics['recall@5'])}`",
                f"- Recall@10: `{render_metric(metrics['recall@10'])}`",
                f"- MRR: `{render_metric(metrics['MRR'])}`",
                f"- Failed queries: `{metrics['failed_queries']}`",
                "",
                "| Query ID | Type | Pass | Top Record | Top Chunk | RR |",
                "| --- | --- | --- | --- | --- | ---: |",
            ]
        )
        for item in hybrid["query_results"]:
            lines.append(
                f"| `{item['query_id']}` | {item['query_type']} | `{item['passed']}` | `{item['top_record_id']}` | `{item['top_chunk_id']}` | {item['reciprocal_rank']:.3f} |"
            )
        failed = [item for item in hybrid["query_results"] if not item["passed"]]
        lines.extend(["", "## Hybrid Failed Queries", ""])
        if failed:
            for item in failed:
                lines.append(f"- `{item['query_id']}` missing records: `{item['missing_expected_record_ids'][:10]}`")
        else:
            lines.append("- None")
    lines.extend(
        [
            "",
            "## Pending Modes",
            "",
            f"- Semantic benchmark status: `{results.get('semantic', {}).get('status', PENDING_VECTOR_INDEX)}`",
            f"- Hybrid benchmark status: `{results.get('hybrid', {}).get('status', PENDING_HYBRID)}`",
            "",
            "## Recommendation",
            "",
            "Compare lexical and semantic results before implementing hybrid retrieval. Hybrid should combine lexical precision with semantic recall only after this local semantic baseline is reviewed.",
        ]
    )
    return "\n".join(lines)


def render_semantic_report(results: dict) -> str:
    semantic = results.get("semantic") or mode_to_dict(pending_mode("semantic", 0, status=PENDING_VECTOR_INDEX))
    metrics = semantic["metrics"]
    lines = [
        "# Semantic Retrieval Benchmark Report",
        "",
        "## Summary",
        "",
        f"- Status: `{semantic['status']}`",
        f"- Queries evaluated: `{metrics['queries_evaluated']}`",
        f"- Recall@1: `{render_metric(metrics['recall@1'])}`",
        f"- Recall@3: `{render_metric(metrics['recall@3'])}`",
        f"- Recall@5: `{render_metric(metrics['recall@5'])}`",
        f"- Recall@10: `{render_metric(metrics['recall@10'])}`",
        f"- MRR: `{render_metric(metrics['MRR'])}`",
        f"- Exact match@1: `{render_metric(metrics['exact_match@1'])}`",
        f"- Failed queries: `{metrics['failed_queries']}`",
        "",
        "## Query-Level Results",
        "",
        "| Query ID | Type | Pass | Top Record | Top Chunk | RR |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for item in semantic["query_results"]:
        lines.append(
            f"| `{item['query_id']}` | {item['query_type']} | `{item['passed']}` | `{item['top_record_id']}` | `{item['top_chunk_id']}` | {item['reciprocal_rank']:.3f} |"
        )
    failed = [item for item in semantic["query_results"] if not item["passed"]]
    lines.extend(["", "## Failed Queries", ""])
    if failed:
        for item in failed:
            lines.append(
                f"- `{item['query_id']}` top=`{item['top_record_id']}` missing_records=`{item['missing_expected_record_ids'][:10]}` missing_chunks=`{item['missing_expected_chunk_ids'][:10]}`"
            )
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "Semantic retrieval searches only local `verse_plus_commentary` vectors in this phase. Hybrid retrieval remains pending.",
        ]
    )
    return "\n".join(lines)


def render_hybrid_report(results: dict) -> str:
    hybrid = results.get("hybrid") or mode_to_dict(pending_mode("hybrid", 0, status=PENDING_HYBRID))
    metrics = hybrid["metrics"]
    ablations = results.get("hybrid_ablations", {})
    best_name = best_ablation_name(ablations)
    lines = [
        "# Hybrid Retrieval Benchmark Report",
        "",
        "## Summary",
        "",
        f"- Status: `{hybrid['status']}`",
        f"- Lexical weight: `{render_metric(metrics.get('lexical_weight'))}`",
        f"- Semantic weight: `{render_metric(metrics.get('semantic_weight'))}`",
        f"- Queries evaluated: `{metrics['queries_evaluated']}`",
        f"- Recall@1: `{render_metric(metrics['recall@1'])}`",
        f"- Recall@3: `{render_metric(metrics['recall@3'])}`",
        f"- Recall@5: `{render_metric(metrics['recall@5'])}`",
        f"- Recall@10: `{render_metric(metrics['recall@10'])}`",
        f"- MRR: `{render_metric(metrics['MRR'])}`",
        f"- Exact match@1: `{render_metric(metrics['exact_match@1'])}`",
        f"- Failed queries: `{metrics['failed_queries']}`",
        "",
        "## Ablation Table",
        "",
        "| Setting | Lexical Weight | Semantic Weight | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR | Failed |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, item in ablations.items():
        item_metrics = item["metrics"]
        lines.append(
            f"| {name} | {item['lexical_weight']:.2f} | {item['semantic_weight']:.2f} | {render_metric(item_metrics['recall@1'])} | {render_metric(item_metrics['recall@3'])} | {render_metric(item_metrics['recall@5'])} | {render_metric(item_metrics['recall@10'])} | {render_metric(item_metrics['MRR'])} | {item_metrics['failed_queries']} |"
        )
    if not ablations:
        lines.append("| None |  |  |  |  |  |  |  |  |")
    lines.extend(
        [
            "",
            f"- Best ablation: `{best_name or 'none'}`",
            "",
            "## Query-Level Results",
            "",
            "| Query ID | Type | Pass | Top Record | Top Chunk | RR |",
            "| --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for item in hybrid["query_results"]:
        lines.append(
            f"| `{item['query_id']}` | {item['query_type']} | `{item['passed']}` | `{item['top_record_id']}` | `{item['top_chunk_id']}` | {item['reciprocal_rank']:.3f} |"
        )
    failed = [item for item in hybrid["query_results"] if not item["passed"]]
    lines.extend(["", "## Failed Queries", ""])
    if failed:
        for item in failed:
            lines.append(
                f"- `{item['query_id']}` top=`{item['top_record_id']}` missing_records=`{item['missing_expected_record_ids'][:10]}` missing_chunks=`{item['missing_expected_chunk_ids'][:10]}`"
            )
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "Hybrid retrieval combines lexical exactness with semantic recall. These benchmark results should guide the retrieval mode used before any RAG answer generation is built.",
        ]
    )
    return "\n".join(lines)


def best_ablation_name(ablations: dict[str, dict[str, Any]]) -> str:
    if not ablations:
        return ""
    return max(
        ablations,
        key=lambda name: (
            ablations[name]["metrics"]["recall@10"] or 0,
            ablations[name]["metrics"]["MRR"] or 0,
            -(ablations[name]["metrics"]["failed_queries"] or 0),
            name,
        ),
    )


def render_comparison_report(results: dict) -> str:
    lines = [
        "# Retrieval Comparison Report",
        "",
        "| Mode | Status | Queries Evaluated | Recall@10 | MRR | Failed Queries |",
        "| --- | --- | ---: | --- | --- | ---: |",
    ]
    for mode in ["lexical", "semantic", "hybrid"]:
        item = results.get(mode) or mode_to_dict(pending_mode(mode, 0))
        metrics = item["metrics"]
        lines.append(
            f"| {mode} | `{item['status']}` | {metrics['queries_evaluated']} | {render_metric(metrics['recall@10'])} | {render_metric(metrics['MRR'])} | {metrics['failed_queries']} |"
        )
    lexical = results.get("lexical", {}).get("metrics", {})
    semantic = results.get("semantic", {}).get("metrics", {})
    hybrid = results.get("hybrid", {}).get("metrics", {})
    hybrid_improved_semantic = (
        (hybrid.get("recall@10") is not None)
        and (semantic.get("recall@10") is not None)
        and hybrid.get("recall@10", 0) > semantic.get("recall@10", 0)
    )
    hybrid_matched_lexical = (
        (hybrid.get("recall@10") is not None)
        and (lexical.get("recall@10") is not None)
        and hybrid.get("recall@10", 0) >= lexical.get("recall@10", 0)
        and hybrid.get("MRR", 0) >= lexical.get("MRR", 0)
    )
    failed_hybrid = [item for item in results.get("hybrid", {}).get("query_results", []) if not item["passed"]]
    lines.extend(
        [
            "",
            f"- Hybrid improved over semantic: `{hybrid_improved_semantic}`",
            f"- Hybrid matched lexical: `{hybrid_matched_lexical}`",
            f"- Hybrid failed queries: `{len(failed_hybrid)}`",
            "",
            "## Failure Analysis",
            "",
        ]
    )
    if failed_hybrid:
        for item in failed_hybrid[:15]:
            lines.append(f"- `{item['query_id']}` top=`{item['top_record_id']}` missing=`{item['missing_expected_record_ids'][:5]}`")
    else:
        lines.append("- Hybrid had no failed queries.")
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            "Use hybrid retrieval as the default RAG retrieval candidate only if it matches lexical on exact benchmark queries while adding semantic recall. Otherwise keep lexical as the precision baseline and use semantic results as a secondary expansion layer.",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    results: dict,
    results_path: Path,
    report_path: Path,
    semantic_report_path: Path,
    hybrid_report_path: Path,
    comparison_path: Path,
) -> None:
    results_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_benchmark_report(results), encoding="utf-8")
    semantic_report_path.write_text(render_semantic_report(results), encoding="utf-8")
    hybrid_report_path.write_text(render_hybrid_report(results), encoding="utf-8")
    comparison_path.write_text(render_comparison_report(results), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate retrieval modes against golden queries")
    parser.add_argument("--mode", choices=["lexical", "semantic", "hybrid", "all"], default="lexical")
    parser.add_argument("--golden-queries", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--semantic-report", type=Path, default=DEFAULT_SEMANTIC_REPORT)
    parser.add_argument("--hybrid-report", type=Path, default=DEFAULT_HYBRID_REPORT)
    parser.add_argument("--comparison-report", type=Path, default=DEFAULT_COMPARISON)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--lexical-weight", type=float, default=DEFAULT_LEXICAL_WEIGHT)
    parser.add_argument("--semantic-weight", type=float, default=DEFAULT_SEMANTIC_WEIGHT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    golden_queries = load_jsonl(args.golden_queries)
    results = run_modes(
        args.mode,
        golden_queries,
        top_k=args.top_k,
        lexical_weight=args.lexical_weight,
        semantic_weight=args.semantic_weight,
    )
    if args.mode != "all":
        for pending in {"semantic", "hybrid"} - set(results):
            status = PENDING_HYBRID if pending == "hybrid" else PENDING_VECTOR_INDEX
            results[pending] = mode_to_dict(pending_mode(pending, len(golden_queries), status=status))
    write_outputs(results, args.results, args.report, args.semantic_report, args.hybrid_report, args.comparison_report)
    for mode, result in results.items():
        if "metrics" not in result:
            continue
        metrics = result["metrics"]
        print(f"{mode}: {result['status']} queries={metrics['queries_evaluated']} recall@10={render_metric(metrics['recall@10'])} MRR={render_metric(metrics['MRR'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
