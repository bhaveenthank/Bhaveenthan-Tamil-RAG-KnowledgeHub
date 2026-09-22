from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

PHASE2_VERSION = "saanrugraph-thevaram-1-7-phase2-cleaned-v1"
PHASE3_VERSION = "saanrugraph-thevaram-1-7-gold-annotation-v1"
DEFAULT_PHASE2_ROOT = Path("data/processed/saanrugraph_phase2")
DEFAULT_NORMALIZED_ROOT = Path("data/processed/thevaram_normalized")
DEFAULT_OUTPUT_ROOT = Path("data/processed/saanrugraph_phase3")
DEFAULT_GUIDELINE_PATH = Path("docs/research/saanrugraph_phase3_annotation_guideline.md")
DEFAULT_REPORT_PATH = Path("docs/research/saanrugraph_phase3_gold_annotation_set.md")

RELATION_LABELS = [
    "glosses_word",
    "explains_phrase",
    "explains_line",
    "interprets_image",
    "describes_entity",
    "theological_explanation",
]
GOLD_LABELS = ["link", "partial_link", "no_link", "unsure"]
SAMPLE_TARGETS = {
    "high_confidence": 120,
    "medium_confidence": 150,
    "low_confidence": 150,
    "true_missing_pozhippurai": 50,
    "hard_negative_same_paadal": 30,
}


def stable_score(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_pipe_or_list(value: str) -> list[str]:
    text = (value or "").strip()
    if not text or text == "[]":
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text.replace("'", '"'))
            return [str(item) for item in parsed if str(item)]
        except json.JSONDecodeError:
            return []
    return [part for part in text.split("|") if part]


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def token_set(value: str) -> set[str]:
    return set(re.findall(r"[\u0B80-\u0BFF0-9௦-௯A-Za-z]+", compact(value)))


def lexical_overlap(source: str, target: str) -> float:
    left = token_set(source)
    right = token_set(target)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def hard_case_tags(row: dict[str, str]) -> list[str]:
    tags = set(parse_pipe_or_list(row.get("issue_tags_after", "")))
    penalties = set(parse_pipe_or_list(row.get("penalties_applied", "")))
    quality = set(parse_pipe_or_list(row.get("quality_flags", "")))
    relation = row.get("relationship_type", "")

    if lexical_overlap(row.get("source_text", ""), row.get("target_text", "")) <= 0.10:
        tags.add("low_lexical_overlap")
    if "ambiguous_span" in tags or "ambiguous_margin_penalty" in penalties:
        tags.add("ambiguous_commentary")
    if "missing_anchor" in tags or "missing_entity_anchor_penalty" in penalties:
        tags.add("no_shared_entity_or_missing_anchor")
    if "short_but_valid_single_token" in quality:
        tags.add("single_token_phrase")
    if relation == "interprets_image":
        tags.add("poetic_imagery")
    if relation == "theological_explanation":
        tags.add("theological_interpretation")
    if "broad_or_unsplit_target" in tags or "target_too_broad_penalty" in penalties:
        tags.add("broad_commentary_target")
    if "polysemy_context" in tags or "polysemy_without_context_penalty" in penalties:
        tags.add("polysemy_context")
    return sorted(tags)


def enrich_link_row(
    row: dict[str, str],
    *,
    gold_id: str,
    selection_stratum: str,
    paadal_by_id: dict[str, dict[str, Any]],
    commentary_by_paadal_id: dict[str, dict[str, Any]],
    annotation_prior_label: str,
) -> dict[str, Any]:
    paadal = paadal_by_id.get(row.get("paadal_id", ""), {})
    commentary = commentary_by_paadal_id.get(row.get("paadal_id", ""), {})
    tags = hard_case_tags(row)
    return {
        "gold_id": gold_id,
        "dataset_version": PHASE3_VERSION,
        "phase2_dataset_version": PHASE2_VERSION,
        "selection_stratum": selection_stratum,
        "annotation_prior_label": annotation_prior_label,
        "annotator1_label": "",
        "annotator2_label": "",
        "final_gold_label": "",
        "annotator1_relation_label": "",
        "annotator2_relation_label": "",
        "final_relation_label": "",
        "exact_pozhippurai_span_reviewed": "",
        "corrected_target_start_char": "",
        "corrected_target_end_char": "",
        "review_confidence": "",
        "reviewer_note": "",
        "allowed_gold_labels": "|".join(GOLD_LABELS),
        "allowed_relation_labels": "|".join(RELATION_LABELS),
        "hard_case_tags": "|".join(tags),
        "link_id": row.get("link_id", ""),
        "paadal_id": row.get("paadal_id", ""),
        "commentary_id": row.get("commentary_id", ""),
        "thirumurai_no": row.get("thirumurai_no", ""),
        "pathigam_id": row.get("pathigam_id", ""),
        "hymn_id": row.get("hymn_id", ""),
        "global_song_no": paadal.get("global_song_no", ""),
        "source_url": paadal.get("source_url", ""),
        "commentary_url": paadal.get("commentary_url", ""),
        "model_confidence": row.get("confidence", ""),
        "model_score": row.get("score", ""),
        "model_relation_label": row.get("relationship_type", ""),
        "source_field": row.get("source_field", ""),
        "source_start_char": row.get("source_start_char", ""),
        "source_end_char": row.get("source_end_char", ""),
        "source_text": row.get("source_text", ""),
        "target_field": row.get("target_field", ""),
        "target_start_char": row.get("target_start_char", ""),
        "target_end_char": row.get("target_end_char", ""),
        "target_text": row.get("target_text", ""),
        "full_paadal_text": paadal.get("paadal_text", ""),
        "full_pozhippurai": commentary.get("pozhppurai", ""),
        "full_kurippurai": commentary.get("kurippurai", ""),
        "quality_flags": row.get("quality_flags", ""),
        "issue_tags_after": row.get("issue_tags_after", ""),
        "penalties_applied": row.get("penalties_applied", ""),
        "diagnostic_note": row.get("diagnostic_note", ""),
    }


def choose_rows(rows: list[dict[str, str]], *, count: int, key: str) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: stable_score(key, row.get("link_id", ""), row.get("source_text", "")))[:count]


def stratified_link_samples(rows: list[dict[str, str]]) -> list[tuple[str, dict[str, str]]]:
    selected: list[tuple[str, dict[str, str]]] = []
    used_link_ids: set[str] = set()

    for confidence, stratum in [
        ("high", "high_confidence"),
        ("medium", "medium_confidence"),
        ("low", "low_confidence"),
    ]:
        candidates = [row for row in rows if row.get("confidence") == confidence]
        relation_buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in candidates:
            relation_buckets[row.get("relationship_type", "")].append(row)

        target = SAMPLE_TARGETS[stratum]
        per_relation = max(1, target // len(RELATION_LABELS))
        stratum_rows: list[dict[str, str]] = []
        for relation in RELATION_LABELS:
            stratum_rows.extend(
                choose_rows(relation_buckets.get(relation, []), count=per_relation, key=f"{stratum}:{relation}")
            )
        if len(stratum_rows) < target:
            remaining = [row for row in candidates if row.get("link_id") not in {r.get("link_id") for r in stratum_rows}]
            stratum_rows.extend(choose_rows(remaining, count=target - len(stratum_rows), key=f"{stratum}:fill"))

        for row in stratum_rows[:target]:
            if row.get("link_id") not in used_link_ids:
                selected.append((stratum, row))
                used_link_ids.add(row.get("link_id", ""))

    return selected


def missing_commentary_samples(rows: list[dict[str, str]], count: int) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: stable_score("missing", row.get("paadal_id", "")))[:count]


def hard_negative_samples(rows: list[dict[str, str]], count: int) -> list[dict[str, str]]:
    by_paadal: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_paadal[row.get("paadal_id", "")].append(row)

    negatives: list[dict[str, str]] = []
    for paadal_id, group in sorted(by_paadal.items()):
        if len(group) < 2:
            continue
        ordered = sorted(group, key=lambda row: row.get("source_start_char", ""))
        for first, second in zip(ordered, ordered[1:]):
            if first.get("target_text") == second.get("target_text"):
                continue
            if first.get("relationship_type") == second.get("relationship_type"):
                continue
            synthetic = dict(first)
            synthetic["link_id"] = f"hard_negative::{first.get('link_id')}::{second.get('link_id')}"
            synthetic["target_text"] = second.get("target_text", "")
            synthetic["target_start_char"] = second.get("target_start_char", "")
            synthetic["target_end_char"] = second.get("target_end_char", "")
            synthetic["relationship_type"] = "candidate_no_link"
            synthetic["issue_tags_after"] = "shared_paadal_wrong_target|hard_negative"
            synthetic["penalties_applied"] = "hard_negative_same_paadal"
            negatives.append(synthetic)
            break
    return sorted(negatives, key=lambda row: stable_score("hard-negative", row["link_id"]))[:count]


def cohen_kappa(pairs: list[tuple[str, str]]) -> dict[str, Any]:
    pairs = [(a, b) for a, b in pairs if a and b]
    if not pairs:
        return {"status": "pending_manual_annotation", "pair_count": 0, "observed_agreement": None, "cohen_kappa": None}
    labels = sorted({label for pair in pairs for label in pair})
    total = len(pairs)
    observed = sum(1 for a, b in pairs if a == b) / total
    a_counts = Counter(a for a, _ in pairs)
    b_counts = Counter(b for _, b in pairs)
    expected = sum((a_counts[label] / total) * (b_counts[label] / total) for label in labels)
    kappa = 1.0 if expected == 1.0 else (observed - expected) / (1 - expected)
    return {
        "status": "computed",
        "pair_count": total,
        "observed_agreement": round(observed, 4),
        "cohen_kappa": round(kappa, 4),
        "labels": labels,
    }


def build_guideline() -> str:
    relation_lines = "\n".join(f"- `{label}`" for label in RELATION_LABELS)
    gold_lines = "\n".join(f"- `{label}`" for label in GOLD_LABELS)
    return f"""# SaanruGraph Phase 3 Annotation Guideline

Dataset version: `{PHASE3_VERSION}`

## Goal

Create a trusted gold set for Paadal to Pozhippurai linking evaluation. The human label is the authority. The model confidence and prior label are shown only to help sampling diagnostics; do not copy them blindly.

## What To Annotate

For each row, compare `source_text` from the Paadal with `target_text` from the Pozhippurai. Use `full_paadal_text` and `full_pozhippurai` as context.

## Allowed Link Labels

{gold_lines}

Use:

- `link` when the target span directly explains the source span.
- `partial_link` when the target explains part of the source span or is too broad but still contains the explanation.
- `no_link` when the target is unrelated, only shares an entity, or explains a different phrase.
- `unsure` when a Tamil literary/scholarly judgment is needed.

## Allowed Relation Labels

{relation_lines}

Relation definitions:

- `glosses_word`: explains a single word or lexical form.
- `explains_phrase`: explains a phrase shorter than a full line.
- `explains_line`: explains the whole paadal line.
- `interprets_image`: explains poetic imagery, symbol, iconography, or metaphorical image.
- `describes_entity`: explains a deity, place, body part, object, person, or named entity.
- `theological_explanation`: explains grace, karma, liberation, devotion, worship, doctrine, or spiritual result.

## Exact Span Correction

If `target_text` is too broad or slightly wrong, fill:

- `exact_pozhippurai_span_reviewed`
- `corrected_target_start_char` if easy
- `corrected_target_end_char` if easy

If exact character offsets are hard, the exact text span alone is enough for Phase 3.

## Double Annotation

The file `gold_double_annotation_subset_100.csv` should be independently labeled by two people if possible. Fill `annotator1_label` and `annotator2_label`; agreement can then be calculated.

## Important Rules

- Do not mark empty Pozhippurai rows as linker errors. They are true missing-commentary coverage cases.
- A shared word or shared entity alone is not enough for `link`.
- A valid explanation may be in reverse order compared with the Paadal.
- Single-token spans can be valid, especially deity/object/theology words.
- Prefer `partial_link` over `link` when the target span is too broad.
"""


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        "# SaanruGraph Phase 3 Gold Annotation Set",
        "",
        f"Dataset version: `{PHASE3_VERSION}`",
        "",
        "## Output Files",
        "",
        "| Output | Path |",
        "| --- | --- |",
        "| Gold annotation dataset | `data/processed/saanrugraph_phase3/gold_linking_dataset_500.csv` |",
        "| Double annotation subset | `data/processed/saanrugraph_phase3/gold_double_annotation_subset_100.csv` |",
        "| Relation distribution | `data/processed/saanrugraph_phase3/relation_distribution_table.csv` |",
        "| Agreement summary | `data/processed/saanrugraph_phase3/agreement_summary.json` |",
        "| Machine summary | `data/processed/saanrugraph_phase3/gold_annotation_summary.json` |",
        "| Annotation guideline | `docs/research/saanrugraph_phase3_annotation_guideline.md` |",
        "",
        "## Sample Composition",
        "",
        "| Stratum | Rows |",
        "| --- | ---: |",
    ]
    for stratum, count in summary["selection_strata"].items():
        lines.append(f"| `{stratum}` | {count:,} |")
    lines.extend(["", "## Relation Distribution", "", "| Model relation label | Rows |", "| --- | ---: |"])
    for relation, count in summary["model_relation_distribution"].items():
        lines.append(f"| `{relation}` | {count:,} |")
    lines.extend(["", "## Hard Case Coverage", "", "| Hard case tag | Rows |", "| --- | ---: |"])
    for tag, count in summary["hard_case_tag_distribution"].items():
        lines.append(f"| `{tag}` | {count:,} |")
    lines.extend(
        [
            "",
            "## Agreement Status",
            "",
            "Agreement is pending because manual labels have not been filled yet.",
            "After at least 100 rows are double annotated, compute observed agreement and Cohen's kappa from `annotator1_label` and `annotator2_label`.",
            "",
        ]
    )
    return "\n".join(lines)


def build_phase3(
    *,
    phase2_root: Path = DEFAULT_PHASE2_ROOT,
    normalized_root: Path = DEFAULT_NORMALIZED_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    guideline_path: Path = DEFAULT_GUIDELINE_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
) -> dict[str, Any]:
    candidate_rows = read_csv(phase2_root / "final_link_candidate_pool.csv")
    missing_rows = read_csv(phase2_root / "missing_commentary_report.csv")
    paadal_rows = read_jsonl(normalized_root / "paadalgal.jsonl")
    commentary_rows = read_jsonl(normalized_root / "commentaries.jsonl")

    paadal_by_id = {str(row.get("paadal_id", "")): row for row in paadal_rows}
    commentary_by_paadal_id = {str(row.get("paadal_id", "")): row for row in commentary_rows}

    output_rows: list[dict[str, Any]] = []
    counter = 1
    for stratum, row in stratified_link_samples(candidate_rows):
        output_rows.append(
            enrich_link_row(
                row,
                gold_id=f"SG_GOLD_{counter:04d}",
                selection_stratum=stratum,
                paadal_by_id=paadal_by_id,
                commentary_by_paadal_id=commentary_by_paadal_id,
                annotation_prior_label="link_candidate",
            )
        )
        counter += 1

    for row in missing_commentary_samples(missing_rows, SAMPLE_TARGETS["true_missing_pozhippurai"]):
        paadal = paadal_by_id.get(row.get("paadal_id", ""), {})
        output_rows.append(
            {
                "gold_id": f"SG_GOLD_{counter:04d}",
                "dataset_version": PHASE3_VERSION,
                "phase2_dataset_version": PHASE2_VERSION,
                "selection_stratum": "true_missing_pozhippurai",
                "annotation_prior_label": "no_link_missing_commentary",
                "annotator1_label": "",
                "annotator2_label": "",
                "final_gold_label": "",
                "annotator1_relation_label": "",
                "annotator2_relation_label": "",
                "final_relation_label": "",
                "exact_pozhippurai_span_reviewed": "",
                "corrected_target_start_char": "",
                "corrected_target_end_char": "",
                "review_confidence": "",
                "reviewer_note": "",
                "allowed_gold_labels": "|".join(GOLD_LABELS),
                "allowed_relation_labels": "|".join(RELATION_LABELS),
                "hard_case_tags": "missing_commentary|no_link_case",
                "link_id": "",
                "paadal_id": row.get("paadal_id", ""),
                "commentary_id": row.get("commentary_id", ""),
                "thirumurai_no": row.get("thirumurai_no", ""),
                "pathigam_id": row.get("pathigam_id", ""),
                "hymn_id": row.get("pathigam_id", ""),
                "global_song_no": row.get("global_song_no", ""),
                "source_url": row.get("source_url", ""),
                "commentary_url": row.get("commentary_url", ""),
                "model_confidence": "none",
                "model_score": "",
                "model_relation_label": "unlinked",
                "source_field": "paadal_text",
                "source_start_char": "",
                "source_end_char": "",
                "source_text": row.get("paadal_text_preview", ""),
                "target_field": "pozhppurai",
                "target_start_char": "",
                "target_end_char": "",
                "target_text": "",
                "full_paadal_text": paadal.get("paadal_text", row.get("paadal_text_preview", "")),
                "full_pozhippurai": "",
                "full_kurippurai": "",
                "quality_flags": "missing_pozhippurai",
                "issue_tags_after": "true_missing_pozhippurai",
                "penalties_applied": "",
                "diagnostic_note": row.get("explanation", ""),
            }
        )
        counter += 1

    for row in hard_negative_samples(candidate_rows, SAMPLE_TARGETS["hard_negative_same_paadal"]):
        enriched = enrich_link_row(
            row,
            gold_id=f"SG_GOLD_{counter:04d}",
            selection_stratum="hard_negative_same_paadal",
            paadal_by_id=paadal_by_id,
            commentary_by_paadal_id=commentary_by_paadal_id,
            annotation_prior_label="no_link_hard_negative",
        )
        enriched["model_confidence"] = "synthetic_no_link"
        enriched["model_score"] = ""
        enriched["diagnostic_note"] = (
            "Synthetic hard negative: source span is paired with a different target span "
            "from the same Paadal to test shared-context false positives."
        )
        output_rows.append(enriched)
        counter += 1

    output_rows = sorted(output_rows, key=lambda row: row["gold_id"])
    double_subset = output_rows[:100]

    relation_distribution = [
        {"model_relation_label": relation, "rows": count}
        for relation, count in sorted(Counter(row["model_relation_label"] for row in output_rows).items())
    ]
    agreement = cohen_kappa([(row["annotator1_label"], row["annotator2_label"]) for row in double_subset])

    hard_counter: Counter[str] = Counter()
    for row in output_rows:
        hard_counter.update(parse_pipe_or_list(row["hard_case_tags"]))

    summary = {
        "dataset_version": PHASE3_VERSION,
        "phase2_dataset_version": PHASE2_VERSION,
        "total_rows": len(output_rows),
        "double_annotation_subset_rows": len(double_subset),
        "selection_strata": dict(sorted(Counter(row["selection_stratum"] for row in output_rows).items())),
        "annotation_prior_distribution": dict(sorted(Counter(row["annotation_prior_label"] for row in output_rows).items())),
        "model_confidence_distribution": dict(sorted(Counter(row["model_confidence"] for row in output_rows).items())),
        "model_relation_distribution": dict(sorted(Counter(row["model_relation_label"] for row in output_rows).items())),
        "hard_case_tag_distribution": dict(sorted(hard_counter.items())),
        "agreement": agreement,
        "outputs": {
            "gold_dataset_csv": str(output_root / "gold_linking_dataset_500.csv"),
            "gold_dataset_jsonl": str(output_root / "gold_linking_dataset_500.jsonl"),
            "double_annotation_subset_csv": str(output_root / "gold_double_annotation_subset_100.csv"),
            "relation_distribution_csv": str(output_root / "relation_distribution_table.csv"),
            "agreement_summary_json": str(output_root / "agreement_summary.json"),
            "annotation_guideline": str(guideline_path),
            "report": str(report_path),
        },
    }

    output_root.mkdir(parents=True, exist_ok=True)
    fieldnames = list(output_rows[0])
    write_csv(output_root / "gold_linking_dataset_500.csv", output_rows, fieldnames)
    write_jsonl(output_root / "gold_linking_dataset_500.jsonl", output_rows)
    write_csv(output_root / "gold_double_annotation_subset_100.csv", double_subset, fieldnames)
    write_csv(output_root / "relation_distribution_table.csv", relation_distribution)
    write_json(output_root / "agreement_summary.json", agreement)
    write_json(output_root / "gold_annotation_summary.json", summary)
    guideline_path.parent.mkdir(parents=True, exist_ok=True)
    guideline_path.write_text(build_guideline(), encoding="utf-8")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build SaanruGraph Phase 3 gold annotation set.")
    parser.add_argument("--phase2-root", type=Path, default=DEFAULT_PHASE2_ROOT)
    parser.add_argument("--normalized-root", type=Path, default=DEFAULT_NORMALIZED_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--guideline-path", type=Path, default=DEFAULT_GUIDELINE_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    args = parser.parse_args()
    summary = build_phase3(
        phase2_root=args.phase2_root,
        normalized_root=args.normalized_root,
        output_root=args.output_root,
        guideline_path=args.guideline_path,
        report_path=args.report_path,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
