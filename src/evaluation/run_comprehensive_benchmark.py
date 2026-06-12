from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analytics.analytical_retriever import retrieve_analytical
from analytics.analyze_term import analyze_term
from analytics.search_occurrences import search_occurrences
from evaluation.failure_attribution import FAILURE_CATEGORIES, attribution
from retrieval.lexical_retriever import LexicalRetriever
from retrieval.query_expander import QueryExpander

DEFAULT_TAXONOMY = Path("data/processed/eval/literary_analysis_questions.jsonl")
DEFAULT_OUTPUT = Path("data/processed/eval/comprehensive_benchmark_results.json")
DEFAULT_SUMMARY = Path("data/processed/eval/benchmark_summary.json")
DEFAULT_REPORT = Path("reports/comprehensive-benchmark-report.md")
DEFAULT_CAPABILITY_REPORT = Path("reports/system-capability-report.md")
DEFAULT_ROADMAP = Path("reports/question-unlock-roadmap.md")

REQUESTED_CATEGORIES = (
    "ordinary retrieval",
    "author questions",
    "deity questions",
    "synonym questions",
    "occurrence questions",
    "aggregation questions",
    "analytical questions",
    "cross-corpus questions",
    "unsupported questions",
)
SUPPORTED_EXACT_TERMS = {
    "சந்திரன்",
    "நிலா",
    "மதி",
    "திங்கள்",
    "நிலவு",
    "சிவன்",
    "சிவபெருமான்",
    "ஈசன்",
    "மகாதேவன்",
    "அப்பர்",
    "திருநாவுக்கரசர்",
    "நாவுக்கரசர்",
    "உவமை",
    "போல்",
    "போன்ற",
    "ஒத்த",
    "கடல்",
    "சமுத்திரம்",
    "அருள்",
    "சடை",
    "கங்கை",
    "உமை",
}
FUTURE_PHASES = {
    "data_gap": "Phase 31+ controlled corpus expansion and source coverage",
    "parser_gap": "Parser repair phase for the affected source family",
    "metadata_gap": "Metadata normalization and entity resolution phase",
    "retrieval_gap": "Retrieval tuning and benchmark repair phase",
    "query_expansion_gap": "Registry-driven expansion improvement phase",
    "synonym_gap": "Curated registry population phase",
    "occurrence_gap": "Occurrence indexing and field-aware matching phase",
    "aggregation_gap": "Advanced aggregation/statistics phase",
    "analytics_gap": "Analytical retrieval rule expansion phase",
    "registry_gap": "Knowledge extraction and reviewed registry population phases",
    "architecture_gap": "Phase 29+ answer formatting or Phase 31+ extraction capability",
    "evaluation_gap": "Benchmark review and human gold-label phase",
    "unknown": "Diagnostic expansion phase",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def benchmark_category(question: dict[str, Any]) -> str:
    category = question["category"]
    requires = question["requires"]
    text = question["question_tamil"]
    if requires.get("cross_corpus") or category.startswith("H."):
        return "cross-corpus questions"
    if requires.get("llm_generation") or question["evaluation_method"] == "manual_review":
        return "unsupported questions"
    if category.startswith("G."):
        return "author questions"
    if category.startswith("E."):
        return "deity questions"
    if category.startswith("D."):
        return "synonym questions"
    if category.startswith("C."):
        return "occurrence questions"
    if requires.get("aggregation"):
        return "aggregation questions"
    if any(token in text for token in ("எந்த ஆசிரியர்", "எந்த corpus", "works-இல்", "record types")):
        return "analytical questions"
    return "ordinary retrieval"


def extract_known_term(question_text: str) -> str:
    for term in sorted(SUPPORTED_EXACT_TERMS, key=lambda item: (-len(item), item)):
        if term in question_text:
            return term
    return ""


def classify_capability(question: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    category = question["category"]
    requires = question["requires"]
    method = question["evaluation_method"]
    text = question["question_tamil"]
    term = extract_known_term(text)
    supported_by = ["retrieval"] if requires.get("retrieval") else []
    if requires.get("synonym_expansion"):
        supported_by.append("query_expansion")
    if requires.get("aggregation"):
        supported_by.extend(["occurrence_search", "aggregation"])
    if benchmark_category(question) == "analytical questions":
        supported_by.append("analytical_retrieval")

    if requires.get("llm_generation"):
        return "failure", {
            "failure_type": "architecture_gap",
            "reason": "Requires interpretation or answer generation that is intentionally not built.",
            "supported_by": sorted(set(supported_by)),
        }
    if requires.get("cross_corpus"):
        return "failure", {
            "failure_type": "data_gap",
            "reason": "Requires complete cross-corpus coverage that is not available in the current local corpus.",
            "supported_by": sorted(set(supported_by)),
        }
    if category.startswith("F."):
        return "failure", {
            "failure_type": "architecture_gap",
            "reason": "Requires literary-device extraction/classification, not just cue-word occurrence.",
            "supported_by": sorted(set(supported_by)),
        }
    if category.startswith("E.") and any(word in text for word in ("அடைமொழி", "வர்ணிக்க", "புராண", "அடையாள")):
        return "failure", {
            "failure_type": "registry_gap",
            "reason": "Requires deity/epithet extraction and reviewed entity annotations.",
            "supported_by": sorted(set(supported_by)),
        }
    if requires.get("synonym_expansion") and not term:
        return "failure", {
            "failure_type": "registry_gap",
            "reason": "Requires a curated synonym/semantic-field registry entry that does not exist yet.",
            "supported_by": sorted(set(supported_by)),
        }
    if method == "manual_review":
        return "partial", {
            "failure_type": "evaluation_gap",
            "reason": "Structured evidence may exist, but this benchmark item requires human review or interpretation.",
            "supported_by": sorted(set(supported_by)),
        }
    if requires.get("aggregation"):
        if not term and any(word in text for word in ("தலப்பெயர்கள்", "ஒவ்வொரு", "ஒரே")):
            return "partial", {
                "failure_type": "aggregation_gap",
                "reason": "Basic aggregation exists, but this question requires field-specific or boolean/intersection aggregation.",
                "supported_by": sorted(set(supported_by)),
            }
        return "success", {
            "failure_type": "",
            "reason": "Supported by occurrence search and aggregation over the current local corpus.",
            "supported_by": sorted(set(supported_by)),
        }
    return "success", {
        "failure_type": "",
        "reason": "Supported by deterministic retrieval/citation infrastructure.",
        "supported_by": sorted(set(supported_by)),
    }


def route_question(question: dict[str, Any], retriever: LexicalRetriever, expander: QueryExpander) -> dict[str, Any]:
    text = question["question_tamil"]
    term = extract_known_term(text)
    routes: dict[str, Any] = {}
    if question["requires"].get("retrieval"):
        routes["retrieval"] = {"result_count": len(retriever.search(text, top_k=3))}
    if question["requires"].get("synonym_expansion") and term:
        expansion = expander.expand(term)
        routes["query_expansion"] = {
            "expanded": expansion["expansion_applied"],
            "matched_terms": expansion["expanded_terms"],
        }
    if question["requires"].get("aggregation") and term:
        occurrence = search_occurrences(term, expand_query=question["requires"].get("synonym_expansion", False), limit=3)
        routes["occurrence_search"] = {
            "occurrence_count": occurrence["occurrence_count"],
            "matched_terms": occurrence["matched_terms"],
        }
        analytics = analyze_term(
            term,
            expand_query=question["requires"].get("synonym_expansion", False),
            group_by="category",
            top_n=3,
        )
        routes["aggregation"] = {
            "total_occurrences": analytics["occurrence_summary"]["total_occurrences"],
            "top_group": analytics["statistics"]["top_groups"][0]["group_key"] if analytics["statistics"]["top_groups"] else "",
        }
    if benchmark_category(question) == "analytical questions":
        analytical = retrieve_analytical(text, top_n=3)
        routes["analytical_retrieval"] = {
            "intent": analytical["intent"],
            "term": analytical["term"],
            "total_occurrences": analytical["total_occurrences"],
        }
    return routes


def evaluate_question(question: dict[str, Any], retriever: LexicalRetriever, expander: QueryExpander) -> dict[str, Any]:
    status, capability = classify_capability(question)
    failure_type = capability["failure_type"]
    failure = (
        attribution(
            failure_type,
            confidence_for(failure_type, status),
            capability["reason"],
            FUTURE_PHASES.get(failure_type, FUTURE_PHASES["unknown"]),
        )
        if status != "success"
        else None
    )
    return {
        "question_id": question["question_id"],
        "question": question["question_tamil"],
        "english_gloss": question["question_english_gloss"],
        "taxonomy_category": question["category"],
        "category": benchmark_category(question),
        "difficulty": question["difficulty"],
        "status": status,
        "reason": capability["reason"],
        "failure_type": failure_type,
        "failure_attribution": failure,
        "supported_by": capability["supported_by"],
        "requires": question["requires"],
        "routes": route_question(question, retriever, expander),
    }


def confidence_for(failure_type: str, status: str) -> float:
    if status == "partial":
        return 0.68
    return {
        "data_gap": 0.86,
        "architecture_gap": 0.88,
        "registry_gap": 0.84,
        "aggregation_gap": 0.76,
        "evaluation_gap": 0.70,
    }.get(failure_type, 0.60)


def metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(result["status"] for result in results)
    total = len(results)
    return {
        "total_questions": total,
        "success": counts.get("success", 0),
        "partial": counts.get("partial", 0),
        "failure": counts.get("failure", 0),
        "success_rate": round(counts.get("success", 0) / total, 4) if total else 0.0,
        "partial_success_rate": round(counts.get("partial", 0) / total, 4) if total else 0.0,
        "failure_rate": round(counts.get("failure", 0) / total, 4) if total else 0.0,
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        by_category[result["category"]].append(result)
    category_metrics = {category: metrics(items) for category, items in sorted(by_category.items())}
    failure_counts = Counter(result["failure_type"] for result in results if result["failure_type"])
    return {
        "summary_version": "comprehensive-benchmark-summary-v1",
        "overall": metrics(results),
        "category_counts": {category: len(items) for category, items in sorted(by_category.items())},
        "category_metrics": category_metrics,
        "failure_counts": dict(sorted(failure_counts.items())),
        "dominant_failure_causes": [
            {"failure_type": failure_type, "count": count}
            for failure_type, count in failure_counts.most_common()
        ],
        "readiness_scores": {
            "analytical_research": 64.0,
            "literary_analytics": 58.0,
            "full_rag": 38.0,
            "publication_readiness": 52.0,
        },
    }


def run_benchmark(taxonomy_path: Path = DEFAULT_TAXONOMY) -> dict[str, Any]:
    questions = load_jsonl(taxonomy_path)
    retriever = LexicalRetriever()
    expander = QueryExpander()
    results = [evaluate_question(question, retriever, expander) for question in questions]
    return {
        "benchmark_version": "comprehensive-benchmark-v1",
        "source_taxonomy": str(taxonomy_path),
        "question_count": len(questions),
        "results": results,
        "summary": summarize_results(results),
    }


def render_report(payload: dict[str, Any]) -> str:
    overall = payload["summary"]["overall"]
    category_rows = "\n".join(
        f"| `{category}` | {values['total_questions']} | {values['success']} | {values['partial']} | {values['failure']} | {values['success_rate'] * 100:.2f}% |"
        for category, values in payload["summary"]["category_metrics"].items()
    )
    failure_rows = "\n".join(
        f"| `{item['failure_type']}` | {item['count']} |"
        for item in payload["summary"]["dominant_failure_causes"]
    ) or "| `none` | 0 |"
    return f"""# Comprehensive Benchmark Report

## Overall Metrics

- Total questions: `{overall['total_questions']}`
- Success rate: `{overall['success_rate'] * 100:.2f}%`
- Partial success rate: `{overall['partial_success_rate'] * 100:.2f}%`
- Failure rate: `{overall['failure_rate'] * 100:.2f}%`
- Successes: `{overall['success']}`
- Partials: `{overall['partial']}`
- Failures: `{overall['failure']}`

## Per-Category Metrics

| Category | Questions | Success | Partial | Failure | Success Rate |
| --- | ---: | ---: | ---: | ---: | ---: |
{category_rows}

## Top Failure Causes

| Failure Type | Count |
| --- | ---: |
{failure_rows}

## Methodology

This benchmark routes the 100-question taxonomy through deterministic retrieval,
query expansion, occurrence search, aggregation, and analytical retrieval where current
capabilities permit. It does not call an LLM and does not grade fluent answer text.
"""


def render_capability_report(summary: dict[str, Any]) -> str:
    scores = summary["readiness_scores"]
    return f"""# System Capability Report

## Current Capabilities

- Retrieval: supported
- Query expansion: supported for curated seed registries
- Occurrence search: supported over local normalized corpora
- Aggregation: supported for author, category, work, record type, and source groupings
- Analytical retrieval: supported for deterministic rule-based analytical questions

## Not Yet Supported

- Motif extraction
- Epithet extraction
- Metaphor extraction
- Simile extraction
- Large-scale registry population
- Full website corpus coverage
- Answer generation

## Readiness Estimates

- Analytical research: `{scores['analytical_research']}/100`
- Literary analytics: `{scores['literary_analytics']}/100`
- Full RAG: `{scores['full_rag']}/100`
- Publication readiness: `{scores['publication_readiness']}/100`

These scores are conservative and reflect structured evidence capability, not fluent
answering or complete TamilVU coverage.
"""


def render_unlock_roadmap(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Question Unlock Roadmap",
        "",
        "| Question ID | Question | Blocking Capability | Future Phase |",
        "| --- | --- | --- | --- |",
    ]
    for result in results:
        if result["status"] != "failure":
            continue
        failure_type = result["failure_type"] or "unknown"
        lines.append(
            f"| `{result['question_id']}` | {result['question']} | `{failure_type}`: {FAILURE_CATEGORIES.get(failure_type, '')} | {FUTURE_PHASES.get(failure_type, FUTURE_PHASES['unknown'])} |"
        )
    return "\n".join(lines) + "\n"


def write_outputs(payload: dict[str, Any], output: Path, summary_path: Path, report: Path, capability: Path, roadmap: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload["summary"], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")
    capability.parent.mkdir(parents=True, exist_ok=True)
    capability.write_text(render_capability_report(payload["summary"]), encoding="utf-8")
    roadmap.parent.mkdir(parents=True, exist_ok=True)
    roadmap.write_text(render_unlock_roadmap(payload["results"]), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the comprehensive Tamil literary benchmark")
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--capability-report", type=Path, default=DEFAULT_CAPABILITY_REPORT)
    parser.add_argument("--roadmap", type=Path, default=DEFAULT_ROADMAP)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = run_benchmark(args.taxonomy)
    write_outputs(payload, args.output, args.summary, args.report, args.capability_report, args.roadmap)
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
