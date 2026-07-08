import csv
import json
from collections import defaultdict
from pathlib import Path

from knowledge.build_pozhippurai_links_v4 import (
    ALLOWED_RELATIONSHIPS,
    DEFAULT_GOLD_SEED,
    MANUAL_DECISIONS,
    classify_relationship_v4,
    clean_primary_links,
    load_v4_gold_seed,
    run_linking_v4,
    secondary_no_link_rows,
    split_source_phrase_v4,
    validate_clean_links,
)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


GOLD_FIELDS = [
    "gold_id",
    "paadal_phrase",
    "correct_pozhippurai_span",
    "manual_decision",
    "primary_relationship_type",
    "updated_confidence",
    "target_field_preference",
    "reviewer_note",
]


def gold_row(gold_id: str, source: str, target: str, rel: str, field: str = "pozhppurai") -> dict[str, str]:
    return {
        "gold_id": gold_id,
        "paadal_phrase": source,
        "correct_pozhippurai_span": target,
        "manual_decision": "ACCEPT",
        "primary_relationship_type": rel,
        "updated_confidence": "high",
        "target_field_preference": field,
        "reviewer_note": "fixture",
    }


def test_default_v4_gold_seed_loads_and_is_valid() -> None:
    rules, meta = load_v4_gold_seed(DEFAULT_GOLD_SEED)
    assert meta["gold_seed_rows"] == 60
    assert meta["gold_rules_loaded"] == 60
    assert meta["invalid_rows"] == []
    assert {rule.manual_decision for rule in rules} <= MANUAL_DECISIONS
    assert {rule.relationship_type for rule in rules} <= ALLOWED_RELATIONSHIPS
    assert any(rule.target_field == "kurippurai" for rule in rules)


def test_v4_relationship_classifier_and_splitter_examples() -> None:
    assert classify_relationship_v4("அரவம்", "பறைபோல ஆரவாரம்") == "glosses_word"
    assert classify_relationship_v4("வெண்தலை கலனா", "பிரமனது வெண்மையான தலையோட்டை") == "interprets_image"
    assert classify_relationship_v4("வாசமலர் தூவ, பாசவினை போமே", "பாசங்களும் வினைகளும் நீங்கும்") == "theological_explanation"
    assert classify_relationship_v4("நீலமாமிடற்று ஆலவாயிலான்", "நீலநிறம் பொருந்திய கண்டத்தினை உடைய திரு ஆலவாய் இறைவனை") == "describes_entity"
    assert classify_relationship_v4("உதிரும் மயிர் இடு", "உடலிலிருந்து பிரிக்கப்பட்ட மயிர் நீங்கிய") == "explains_phrase"

    assert split_source_phrase_v4("பரக்கும் மிழலையீர்! கரக்கை தவிர்மினே!") == [
        "பரக்கும் மிழலையீர்",
        "கரக்கை தவிர்மினே",
    ]
    assert "கண் புகார்" in split_source_phrase_v4("கண் புகார்; பிணி அறியார்; கற்றாரும் கேட்டாரும்")[0]
    assert split_source_phrase_v4("ஆலநீழலார், ஆலவாயிலார், காலகாலனார், பால் அது ஆமினே") == [
        "ஆலநீழலார்",
        "ஆலவாயிலார்",
        "காலகாலனார்",
        "பால் அது ஆமினே",
    ]


def test_v4_kurippurai_fallback_case_handling_and_iob(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    qa_bundle = tmp_path / "qa"
    gold_seed = tmp_path / "gold.csv"
    output_root = tmp_path / "v4"
    paadal_text = (
        "பொய்யார் நீலமாமிடற்று ஆலவாயிலான் ஆலவாயிலார் காலகாலனார் "
        "வாசமலர் தூவ, பாசவினை போமே வெண்தலை கலனா அரவம் உதிரும் மயிர் இடு"
    )
    pozhppurai = (
        "நீலநிறம் பொருந்திய கண்டத்தினை உடைய திரு ஆலவாய் இறைவனை. "
        "ஆலவாய் இறைவரை. "
        "காலனுக்குக் காலனாய் அவனை அழித்தருளிய பெருவீரரும். "
        "மணம் பொருந்திய மலர்களால் அருச்சித்துவரின் உம் பாசங்களும் அவற்றால் விளைந்த வினைகளும் நீங்கும். "
        "பிரமனது வெண்மையான தலையோட்டை உண்கலனாக் கொண்டு உலகெலாம். "
        "பறைபோல ஆரவாரம். "
        "உடலிலிருந்து பிரிக்கப்பட்ட மயிர் நீங்கிய."
    )
    write_jsonl(
        table_root / "paadalgal.jsonl",
        [{"paadal_id": "p1", "paadal_text": paadal_text, "thirumurai_no": 1, "thogupu_id": "t1"}],
    )
    write_jsonl(
        table_root / "commentaries.jsonl",
        [
            {
                "commentary_id": "p1_commentary",
                "paadal_id": "p1",
                "pozhppurai": pozhppurai,
                "kurippurai": "பொய்யும் சொல்லாதவர்களுக்கு உரிய பொருள்.",
            }
        ],
    )
    for name in [
        "paadal_pozhippurai_links_v3_corrected_usable.csv",
        "paadal_pozhippurai_links_v3_split_suggestions.csv",
        "paadal_pozhippurai_links_v3_unresolved_only.csv",
        "paadal_pozhippurai_phase3_clean_decision_table.csv",
        "paadal_pozhippurai_link_qa_samples_focused_reviewed.csv",
    ]:
        write_csv(qa_bundle / name, [], fieldnames=["qa_id"])
    write_csv(
        gold_seed,
        [
            gold_row("G1", "பொய்யார்", "பொய்யும் சொல்லாதவர்களுக்கு", "glosses_word", "kurippurai"),
            gold_row("G2", "நீலமாமிடற்று ஆலவாயிலான்", "நீலநிறம் பொருந்திய கண்டத்தினை உடைய திரு ஆலவாய் இறைவனை", "describes_entity"),
            gold_row("G3", "ஆலவாயிலார்", "ஆலவாய் இறைவரை", "describes_entity"),
            gold_row("G4", "காலகாலனார்", "காலனுக்குக் காலனாய் அவனை அழித்தருளிய பெருவீரரும்", "describes_entity"),
            gold_row("G5", "வாசமலர் தூவ, பாசவினை போமே", "பாசங்களும் அவற்றால் விளைந்த வினைகளும் நீங்கும்", "theological_explanation"),
            gold_row("G6", "வெண்தலை கலனா", "பிரமனது வெண்மையான தலையோட்டை", "interprets_image"),
            gold_row("G7", "அரவம்", "பறைபோல ஆரவாரம்", "glosses_word"),
            gold_row("G8", "உதிரும் மயிர் இடு", "உடலிலிருந்து பிரிக்கப்பட்ட மயிர் நீங்கிய", "explains_phrase"),
        ],
        fieldnames=GOLD_FIELDS,
    )

    summary = run_linking_v4(
        table_root=table_root,
        entity_root=tmp_path / "entities",
        seed_dir=tmp_path / "seed",
        qa_bundle=qa_bundle,
        gold_seed=gold_seed,
        output_root=output_root,
        report_path=tmp_path / "report.md",
    )

    assert summary["validation"]["status"] == "VALID"
    assert summary["kurippurai_fallback_count"] >= 1
    full = [
        json.loads(line)
        for line in (output_root / "paadal_pozhippurai_links_v4_full.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    positives = [row for row in full if row["method"] == "v4_gold_seed_exact_or_morphology_match"]
    assert {row["relationship_type"] for row in positives} <= ALLOWED_RELATIONSHIPS
    assert any(row["target_field"] == "kurippurai" and row["target_text"] == "பொய்யும் சொல்லாதவர்களுக்கு" for row in positives)
    assert any(row["target_text"].endswith("இறைவனை") for row in positives)
    assert any(row["target_text"].endswith("இறைவரை") for row in positives)
    assert any(row["target_text"].endswith("பெருவீரரும்") for row in positives)

    sides_by_link: dict[str, set[str]] = defaultdict(set)
    for line in (output_root / "paadal_pozhippurai_links_v4_corrected_usable.iob.conll").read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        token, label, link_id, side, relationship, confidence = line.split("\t")
        assert relationship in ALLOWED_RELATIONSHIPS
        assert confidence in {"high", "medium"}
        sides_by_link[link_id].add(side)
    assert sides_by_link
    assert all("paadal" in sides and (("pozhppurai" in sides) or ("kurippurai" in sides)) for sides in sides_by_link.values())
    primary = read_jsonl(output_root / "paadal_pozhippurai_links_v4_primary_clean_links.jsonl")
    secondary = read_jsonl(output_root / "paadal_pozhippurai_links_v4_secondary_no_link.jsonl")
    assert primary
    assert all(row["relationship_type"] != "unlinked" and row["target_text"] for row in primary)
    assert all(row["secondary_table_reason"] in {"empty_pozhippurai", "unresolved_link"} for row in secondary)


def test_primary_clean_links_remove_parent_duplicates_and_punctuation(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    paadal_text = "அடி ஒன்று, அடி இரண்டு-"
    pozhppurai = "முதல் உரை. இரண்டாம் உரை."
    paadal_rows = [{"paadal_id": "p1", "paadal_text": paadal_text, "thirumurai_no": 1}]
    commentary_rows = [{"commentary_id": "c1", "paadal_id": "p1", "pozhppurai": pozhppurai}]
    write_jsonl(table_root / "paadalgal.jsonl", paadal_rows)
    write_jsonl(table_root / "commentaries.jsonl", commentary_rows)
    links = [
        {
            "link_id": "parent",
            "paadal_id": "p1",
            "commentary_id": "c1",
            "thirumurai_no": 1,
            "source_start_char": 0,
            "source_end_char": len(paadal_text),
            "source_text": paadal_text,
            "target_field": "pozhppurai",
            "target_start_char": 0,
            "target_end_char": len(pozhppurai),
            "target_text": pozhppurai,
            "relationship_type": "explains_line",
            "confidence": "low",
            "score": 0.2,
            "manual_review_required": True,
        },
        {
            "link_id": "child_1",
            "paadal_id": "p1",
            "commentary_id": "c1",
            "thirumurai_no": 1,
            "source_start_char": 0,
            "source_end_char": 10,
            "source_text": "அடி ஒன்று,",
            "target_field": "pozhppurai",
            "target_start_char": 0,
            "target_end_char": 10,
            "target_text": "முதல் உரை.",
            "relationship_type": "explains_phrase",
            "confidence": "high",
            "score": 0.9,
            "manual_review_required": False,
        },
        {
            "link_id": "child_2_low",
            "paadal_id": "p1",
            "commentary_id": "c1",
            "thirumurai_no": 1,
            "source_start_char": 11,
            "source_end_char": len(paadal_text),
            "source_text": "அடி இரண்டு-",
            "target_field": "pozhppurai",
            "target_start_char": 12,
            "target_end_char": len(pozhppurai),
            "target_text": "இரண்டாம் உரை.",
            "relationship_type": "explains_phrase",
            "confidence": "low",
            "score": 0.3,
            "manual_review_required": True,
        },
        {
            "link_id": "child_2_high",
            "paadal_id": "p1",
            "commentary_id": "c1",
            "thirumurai_no": 1,
            "source_start_char": 11,
            "source_end_char": len(paadal_text),
            "source_text": "அடி இரண்டு-",
            "target_field": "pozhppurai",
            "target_start_char": 12,
            "target_end_char": len(pozhppurai),
            "target_text": "இரண்டாம் உரை.",
            "relationship_type": "explains_phrase",
            "confidence": "high",
            "score": 0.8,
            "manual_review_required": False,
        },
        {
            "link_id": "empty",
            "paadal_id": "p2",
            "commentary_id": "c2",
            "source_text": "இல்லை",
            "target_text": "",
            "relationship_type": "unlinked",
            "confidence": "no_link",
        },
    ]

    primary = clean_primary_links(links, paadal_rows=paadal_rows, commentary_rows=commentary_rows)
    secondary = secondary_no_link_rows(links, commentary_rows)

    assert [row["link_id"] for row in primary] == ["child_1", "child_2_high"]
    assert primary[0]["source_text"] == "அடி ஒன்று"
    assert primary[1]["source_text"] == "அடி இரண்டு"
    assert secondary[0]["secondary_table_reason"] == "empty_pozhippurai"
    assert validate_clean_links(table_root, primary)["status"] == "VALID"
