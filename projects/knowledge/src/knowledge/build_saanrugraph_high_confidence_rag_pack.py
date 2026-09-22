from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

DATASET_VERSION = "saanrugraph-high-confidence-rag-v1"
PHASE2_VERSION = "saanrugraph-thevaram-1-7-phase2-cleaned-v1"
DEFAULT_PHASE2_ROOT = Path("data/processed/saanrugraph_phase2")
DEFAULT_NORMALIZED_ROOT = Path("data/processed/thevaram_normalized")
DEFAULT_OUTPUT_ROOT = Path("data/processed/saanrugraph_high_confidence_rag")
DEFAULT_RAG_OUTPUT_ROOT = Path("data/processed/saanrugraph_rag")
DEFAULT_REPORT_PATH = Path("docs/research/saanrugraph_high_confidence_rag_plan.md")

RELATION_TO_CAPABILITY = {
    "glosses_word": {
        "capability_id": "word_gloss",
        "capability_name": "Word meaning from Pozhippurai",
        "question_type": "direct_lexical",
        "question_tamil_template": "இந்த பாடலில் `{source}` என்பதன் பொருள் என்ன?",
        "question_english_template": "What does `{source}` mean in this Paadal according to the Pozhippurai?",
    },
    "explains_phrase": {
        "capability_id": "phrase_explanation",
        "capability_name": "Phrase explanation",
        "question_type": "commentary_dependent",
        "question_tamil_template": "`{source}` என்ற பாடல் பகுதியை பொழிப்புரை எப்படி விளக்குகிறது?",
        "question_english_template": "How does the Pozhippurai explain the phrase `{source}`?",
    },
    "explains_line": {
        "capability_id": "line_explanation",
        "capability_name": "Line-level explanation",
        "question_type": "commentary_dependent",
        "question_tamil_template": "இந்த பாடல் வரிக்கு உரை விளக்கம் என்ன: `{source}`?",
        "question_english_template": "What is the commentary explanation for this Paadal line: `{source}`?",
    },
    "interprets_image": {
        "capability_id": "poetic_image_interpretation",
        "capability_name": "Poetic image and iconography interpretation",
        "question_type": "poetic_imagery",
        "question_tamil_template": "`{source}` என்ற உருவக/திருவுருவப் படிமம் என்ன அர்த்தம் தருகிறது?",
        "question_english_template": "What does the poetic or iconographic image `{source}` mean?",
    },
    "describes_entity": {
        "capability_id": "entity_description",
        "capability_name": "Entity, deity, object, and place description",
        "question_type": "entity_or_place",
        "question_tamil_template": "`{source}` குறித்து பொழிப்புரை என்ன சொல்கிறது?",
        "question_english_template": "What does the Pozhippurai say about `{source}`?",
    },
    "theological_explanation": {
        "capability_id": "theological_explanation",
        "capability_name": "Devotional or theological explanation",
        "question_type": "theology_or_devotion",
        "question_tamil_template": "`{source}` என்பதில் உள்ள பக்தி/தத்துவப் பொருள் என்ன?",
        "question_english_template": "What devotional or theological meaning is explained for `{source}`?",
    },
}


def stable_hash(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def select_balanced_questions(rows: list[dict[str, Any]], per_capability: int = 20) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for relation in RELATION_TO_CAPABILITY:
        relation_rows = [row for row in rows if row["relationship_type"] == relation]
        relation_rows = sorted(
            relation_rows,
            key=lambda row: stable_hash("qa", relation, row["paadal_id"], row["link_id"]),
        )
        selected.extend(relation_rows[:per_capability])
    return selected


def evidence_path(row: dict[str, Any]) -> str:
    return (
        f"Thirumurai {row['thirumurai_no']} > "
        f"Pathigam {row.get('pathigam_id', '')} > "
        f"Paadal {row.get('paadal_id', '')} > "
        f"source[{row.get('source_start_char', '')}:{row.get('source_end_char', '')}] > "
        f"pozhippurai[{row.get('target_start_char', '')}:{row.get('target_end_char', '')}]"
    )


def enrich_high_confidence_rows(
    candidates: list[dict[str, str]],
    paadal_by_id: dict[str, dict[str, Any]],
    commentary_by_paadal_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in candidates:
        if row.get("confidence") != "high":
            continue
        if row.get("manual_review_required") == "True":
            continue
        paadal = paadal_by_id.get(row["paadal_id"], {})
        commentary = commentary_by_paadal_id.get(row["paadal_id"], {})
        capability = RELATION_TO_CAPABILITY[row["relationship_type"]]
        rows.append(
            {
                "dataset_version": DATASET_VERSION,
                "phase2_dataset_version": PHASE2_VERSION,
                "link_id": row["link_id"],
                "paadal_id": row["paadal_id"],
                "commentary_id": row["commentary_id"],
                "thirumurai_no": row["thirumurai_no"],
                "pathigam_id": row["pathigam_id"],
                "hymn_id": row["hymn_id"],
                "global_song_no": paadal.get("global_song_no", ""),
                "capability_id": capability["capability_id"],
                "capability_name": capability["capability_name"],
                "question_type": capability["question_type"],
                "relationship_type": row["relationship_type"],
                "confidence": row["confidence"],
                "score": row["score"],
                "source_text": row["source_text"],
                "target_text": row["target_text"],
                "source_start_char": row["source_start_char"],
                "source_end_char": row["source_end_char"],
                "target_start_char": row["target_start_char"],
                "target_end_char": row["target_end_char"],
                "full_paadal_text": paadal.get("paadal_text", ""),
                "full_pozhippurai": commentary.get("pozhppurai", ""),
                "source_url": paadal.get("source_url", ""),
                "commentary_url": paadal.get("commentary_url", ""),
                "evidence_path": evidence_path(row),
                "quality_flags": row.get("quality_flags", ""),
                "diagnostic_note": row.get("diagnostic_note", ""),
            }
        )
    return rows


def build_capabilities(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_relation = Counter(row["relationship_type"] for row in rows)
    by_capability = Counter(row["capability_id"] for row in rows)
    capabilities = []
    for relation, config in RELATION_TO_CAPABILITY.items():
        capabilities.append(
            {
                "dataset_version": DATASET_VERSION,
                "capability_id": config["capability_id"],
                "capability_name": config["capability_name"],
                "relationship_type": relation,
                "question_type": config["question_type"],
                "high_confidence_evidence_paths": by_relation[relation],
                "recommended_min_questions": 20,
                "can_support_rag_now": by_capability[config["capability_id"]] >= 20,
                "paper_claim": (
                    "Supported in high-confidence evidence subset; answers must cite "
                    "Paadal and Pozhippurai spans."
                ),
            }
        )
    return capabilities


def build_questions(rows: list[dict[str, Any]], per_capability: int = 20) -> list[dict[str, Any]]:
    questions = []
    for index, row in enumerate(select_balanced_questions(rows, per_capability), start=1):
        config = RELATION_TO_CAPABILITY[row["relationship_type"]]
        questions.append(
            {
                "question_id": f"HC_QA_{index:03d}",
                "dataset_version": DATASET_VERSION,
                "capability_id": row["capability_id"],
                "capability_name": row["capability_name"],
                "question_type": row["question_type"],
                "question_tamil": config["question_tamil_template"].format(source=row["source_text"]),
                "question_english": config["question_english_template"].format(source=row["source_text"]),
                "gold_answer_outline": row["target_text"],
                "gold_link_id": row["link_id"],
                "gold_paadal_id": row["paadal_id"],
                "gold_commentary_id": row["commentary_id"],
                "gold_relationship_type": row["relationship_type"],
                "gold_evidence_path": row["evidence_path"],
                "gold_source_text": row["source_text"],
                "gold_target_text": row["target_text"],
                "full_paadal_text": row["full_paadal_text"],
                "full_pozhippurai": row["full_pozhippurai"],
                "source_url": row["source_url"],
                "commentary_url": row["commentary_url"],
                "scoring_notes": (
                    "Correct answer should include the gold target meaning, cite the evidence path, "
                    "and avoid unsupported claims beyond the shown Paadal/Pozhippurai."
                ),
            }
        )
    return questions


def build_chunk_text(row: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            f"Paadal span:\n{row['source_text']}",
            f"Pozhippurai explanation:\n{row['target_text']}",
            f"Full Paadal:\n{row['full_paadal_text']}",
            f"Evidence path:\n{row['evidence_path']}",
        ]
    )


def build_rag_corpus(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rag_rows: list[dict[str, Any]] = []
    for row in rows:
        record_id = f"saanrugraph_rag_{row['link_id']}"
        rag_rows.append(
            {
                "dataset_version": DATASET_VERSION,
                "record_id": record_id,
                "chunk_id": f"{record_id}_chunk_001",
                "chunk_type": "high_confidence_paadal_pozhippurai_evidence_path",
                "link_id": row["link_id"],
                "paadal_id": row["paadal_id"],
                "commentary_id": row["commentary_id"],
                "thirumurai_no": row["thirumurai_no"],
                "pathigam_id": row["pathigam_id"],
                "hymn_id": row["hymn_id"],
                "global_song_no": row["global_song_no"],
                "relationship_type": row["relationship_type"],
                "capability_id": row["capability_id"],
                "capability_name": row["capability_name"],
                "question_type": row["question_type"],
                "confidence": row["confidence"],
                "score": row["score"],
                "source_text": row["source_text"],
                "target_text": row["target_text"],
                "full_paadal_text": row["full_paadal_text"],
                "full_pozhippurai": row["full_pozhippurai"],
                "source_start_char": row["source_start_char"],
                "source_end_char": row["source_end_char"],
                "target_start_char": row["target_start_char"],
                "target_end_char": row["target_end_char"],
                "evidence_path": row["evidence_path"],
                "source_url": row["source_url"],
                "commentary_url": row["commentary_url"],
                "chunk_text": build_chunk_text(row),
                "retrieval_fields": {
                    "paadal_span": row["source_text"],
                    "pozhippurai_explanation": row["target_text"],
                    "full_paadal": row["full_paadal_text"],
                    "evidence_path": row["evidence_path"],
                    "capability": row["capability_name"],
                    "relationship_type": row["relationship_type"],
                },
                "citation": {
                    "source_name": "TamilVU",
                    "citation_text": row["evidence_path"],
                    "source_url": row["source_url"],
                    "commentary_url": row["commentary_url"],
                    "thirumurai_no": row["thirumurai_no"],
                    "paadal_id": row["paadal_id"],
                    "link_id": row["link_id"],
                },
            }
        )
    return rag_rows


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        "# SaanruGraph High-Confidence RAG Plan",
        "",
        f"Dataset version: `{DATASET_VERSION}`",
        "",
        "## Decision",
        "",
        "Use only high-confidence Paadal to Pozhippurai links for the time-limited RAG paper path.",
        "This supports a precision-first claim: the chatbot answers only when it has a high-confidence evidence path.",
        "",
        "## Core Counts",
        "",
        f"- High-confidence evidence paths: `{summary['high_confidence_rows']}`",
        f"- RAG corpus records: `{summary['rag_corpus_rows']}`",
        f"- Golden QA questions: `{summary['golden_questions']}`",
        f"- Questions per main capability: `{summary['questions_per_capability']}`",
        "",
        "## Capabilities",
        "",
        "| Capability | Relation | Evidence paths | QA questions |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in summary["capabilities"]:
        lines.append(
            f"| {row['capability_name']} | `{row['relationship_type']}` | "
            f"{row['high_confidence_evidence_paths']:,} | {row['recommended_min_questions']} |"
        )
    lines.extend(
        [
            "",
            "## Phase 4 RAG Corpus",
            "",
            "The trusted retrieval base is written locally as:",
            "",
            "- `data/processed/saanrugraph_rag/high_confidence_rag_corpus.jsonl`",
            "- `data/processed/saanrugraph_rag/high_confidence_rag_corpus.csv`",
            "",
            "Each record is one high-confidence evidence path with `Paadal span`, "
            "`Pozhippurai explanation`, `Full Paadal`, and `Evidence path` in a single "
            "ready-to-index `chunk_text` field.",
            "",
            "## What This Lets You Claim",
            "",
            "- The system can answer with exact Paadal and Pozhippurai evidence paths.",
            "- The first evaluation can focus on high-precision grounded retrieval and answer citation.",
            "- Medium/low confidence linker hardening becomes future work, not a blocker for the paper.",
            "",
            "## What You Should Not Claim Yet",
            "",
            "- Do not claim full-corpus coverage.",
            "- Do not claim all Paadal spans are linked.",
            "- Do not claim final RAG accuracy until the 120-question benchmark is run.",
            "",
            "## Recommended Scores To Report",
            "",
            "- Retrieval Recall@5",
            "- Evidence Path Recall",
            "- Answer correctness",
            "- Citation precision",
            "- Citation recall",
            "- Unsupported answer rate",
            "",
        ]
    )
    return "\n".join(lines)


def build_pack(
    *,
    phase2_root: Path = DEFAULT_PHASE2_ROOT,
    normalized_root: Path = DEFAULT_NORMALIZED_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    rag_output_root: Path = DEFAULT_RAG_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT_PATH,
    per_capability: int = 20,
) -> dict[str, Any]:
    candidates = read_csv(phase2_root / "final_link_candidate_pool.csv")
    paadal_rows = read_jsonl(normalized_root / "paadalgal.jsonl")
    commentary_rows = read_jsonl(normalized_root / "commentaries.jsonl")
    paadal_by_id = {row["paadal_id"]: row for row in paadal_rows}
    commentary_by_paadal_id = {row["paadal_id"]: row for row in commentary_rows}

    high_rows = enrich_high_confidence_rows(candidates, paadal_by_id, commentary_by_paadal_id)
    rag_corpus = build_rag_corpus(high_rows)
    capabilities = build_capabilities(high_rows)
    questions = build_questions(high_rows, per_capability=per_capability)

    summary = {
        "dataset_version": DATASET_VERSION,
        "phase2_dataset_version": PHASE2_VERSION,
        "high_confidence_rows": len(high_rows),
        "rag_corpus_rows": len(rag_corpus),
        "golden_questions": len(questions),
        "questions_per_capability": per_capability,
        "confidence_filter": "confidence == high and manual_review_required != True",
        "relationship_distribution": dict(sorted(Counter(row["relationship_type"] for row in high_rows).items())),
        "thirumurai_distribution": dict(sorted(Counter(row["thirumurai_no"] for row in high_rows).items())),
        "capabilities": capabilities,
        "outputs": {
            "high_confidence_evidence_paths_csv": str(output_root / "high_confidence_evidence_paths.csv"),
            "rag_corpus_jsonl": str(rag_output_root / "high_confidence_rag_corpus.jsonl"),
            "rag_corpus_csv": str(rag_output_root / "high_confidence_rag_corpus.csv"),
            "capabilities_csv": str(output_root / "rag_capabilities_high_confidence.csv"),
            "golden_questions_csv": str(output_root / "golden_questions_120_high_confidence.csv"),
            "report": str(report_path),
        },
    }

    output_root.mkdir(parents=True, exist_ok=True)
    write_csv(output_root / "high_confidence_evidence_paths.csv", high_rows)
    write_jsonl(output_root / "high_confidence_evidence_paths.jsonl", high_rows)
    rag_output_root.mkdir(parents=True, exist_ok=True)
    write_csv(rag_output_root / "high_confidence_rag_corpus.csv", rag_corpus)
    write_jsonl(rag_output_root / "high_confidence_rag_corpus.jsonl", rag_corpus)
    write_json(rag_output_root / "high_confidence_rag_corpus_summary.json", summary)
    write_csv(output_root / "rag_capabilities_high_confidence.csv", capabilities)
    write_json(output_root / "rag_capabilities_high_confidence.json", capabilities)
    write_csv(output_root / "golden_questions_120_high_confidence.csv", questions)
    write_jsonl(output_root / "golden_questions_120_high_confidence.jsonl", questions)
    write_json(output_root / "high_confidence_rag_summary.json", summary)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build high-confidence-only SaanruGraph RAG pack.")
    parser.add_argument("--phase2-root", type=Path, default=DEFAULT_PHASE2_ROOT)
    parser.add_argument("--normalized-root", type=Path, default=DEFAULT_NORMALIZED_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--rag-output-root", type=Path, default=DEFAULT_RAG_OUTPUT_ROOT)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--per-capability", type=int, default=20)
    args = parser.parse_args()
    summary = build_pack(
        phase2_root=args.phase2_root,
        normalized_root=args.normalized_root,
        output_root=args.output_root,
        rag_output_root=args.rag_output_root,
        report_path=args.report_path,
        per_capability=args.per_capability,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
