import csv
import json
from collections import defaultdict
from pathlib import Path

from knowledge.link_thevaram_pozhippurai_v3 import ALLOWED_RELATIONSHIPS, run_linking_v3


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def usable_row(
    qa_id: str,
    source: str,
    target: str,
    relationship: str,
    confidence: str = "high",
    status: str = "usable_corrected",
) -> dict[str, str]:
    return {
        "qa_id": qa_id,
        "paadal_id": "fixture_paadal_1",
        "commentary_id": "fixture_paadal_1_commentary",
        "source_text": source,
        "target_text": target,
        "final_source_text": source,
        "final_target_text": target,
        "final_relationship_type": relationship,
        "corrected_relationship_type_final": relationship,
        "updated_confidence": confidence,
        "manual_decision": "ACCEPT",
        "clean_phase3_status": status,
        "manual_review_required": "NO",
        "reviewer_notes": "fixture",
    }


def split_row(parent: str, split_id: str, source: str, target: str, relationship: str) -> dict[str, str]:
    return {
        "parent_qa_id": parent,
        "split_link_id": split_id,
        "source_text": source,
        "target_text": target,
        "relationship_type": relationship,
        "updated_confidence": "high",
        "reviewer_notes": "fixture split",
        "manual_decision": "ACCEPT_SPLIT_LINK",
    }


def build_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    table_root = tmp_path / "tables"
    qa_bundle = tmp_path / "qa"
    output_root = tmp_path / "v3"
    paadal_text = "\n".join(
        [
            "புக்கிட்டு, புண்ணியனே! வெரு உறப் முயல்கின்ற",
            "ஓர் தூ வெண்மதி சூடி கரக்கை தவிர்மினே",
            "செந்நெல் அம் கழனிப் பழனத்து அறிவு ஒணா உருவத்து எம் அடிகளுக்கு இடம் அரசிலியே.",
            "மறி படக் கிடந்த கையர்",
            "தோடு உடைய செவியன், விடை ஏறி, ஓர் தூ வெண்மதி சூடி,",
            "பரக்கும் மிழலையீர்! கரக்கை தவிர்மினே!",
            "கண் புகார்; பிணி அறியார்; கற்றாரும் கேட்டாரும்",
        ]
    )
    pozhppurai = " ".join(
        [
            "தேடப் புகுந்து. புண்ணியனே. அஞ்சுமாறு. முயல்கின்ற.",
            "ஒப்பற்ற தூய வெண்மையான பிறையை முடிமிசைச் சூடி.",
            "எமக்கு அளிக்கும் காசில் உள்ள குறையைப் போக்கியருளுக.",
            "செந்நெல் விளையும் அழகிய வயல்களை உடைய சோலைகளின்.",
            "அறியமுடியாதவாறும் அழலுருவாய் ஓங்கி நிமிர்ந்த திருவுருவத்தைக் கொண்டருளிய எம் அடிகளுக்கு உகந்த இடம் திரு அரசிலியேயாகும்.",
            "கையில் மான் குட்டியை ஏந்தி.",
            "தோடணிந்த திருச்செவியை உடைய.",
            "உமையம்மையை இடப்பாகத்தே உடையவனாய், விடை மீது ஏறி.",
            "எங்கும் பரவிய புகழ் உடைய திருவீழிமிழலையில் உறைபவரே.",
            "இடுக்கண் அடையார். நோய் உறார்.",
            "அவன் புகழைக் கற்றவரும் கேட்டவரும்.",
        ]
    )
    write_jsonl(
        table_root / "paadalgal.jsonl",
        [
            {
                "paadal_id": "fixture_paadal_1",
                "paadal_text": paadal_text,
                "thirumurai_no": 1,
                "thogupu_id": "fixture_thogupu",
            }
        ],
    )
    write_jsonl(
        table_root / "commentaries.jsonl",
        [
            {
                "commentary_id": "fixture_paadal_1_commentary",
                "paadal_id": "fixture_paadal_1",
                "pozhppurai": pozhppurai,
                "kurippurai": "fixture kurippurai",
            }
        ],
    )
    write_csv(
        qa_bundle / "paadal_pozhippurai_links_v3_corrected_usable.csv",
        [
            usable_row("PPL_QA_002", "புக்கிட்டு", "தேடப் புகுந்து", "explains_phrase"),
            usable_row("PPL_QA_003", "புண்ணியனே", "புண்ணியனே", "glosses_word"),
            usable_row("PPL_QA_012", "வெரு உறப்", "அஞ்சுமாறு", "glosses_word"),
            usable_row("PPL_QA_013", "முயல்கின்ற", "முயல்கின்ற", "glosses_word"),
            usable_row("PPL_QA_014", "ஓர் தூ வெண்மதி சூடி", "ஒப்பற்ற தூய வெண்மையான பிறையை முடிமிசைச் சூடி", "interprets_image"),
            usable_row("PPL_QA_015", "கரக்கை தவிர்மினே", "எமக்கு அளிக்கும் காசில் உள்ள குறையைப் போக்கியருளுக", "theological_explanation"),
            usable_row("PPL_QA_016", "செந்நெல் அம் கழனிப் பழனத்து", "செந்நெல் விளையும் அழகிய வயல்களை உடைய சோலைகளின்", "explains_phrase"),
            usable_row("PPL_QA_017", "அறிவு ஒணா உருவத்து எம் அடிகளுக்கு இடம் அரசிலியே", "அறியமுடியாதவாறும் அழலுருவாய் ஓங்கி நிமிர்ந்த திருவுருவத்தைக் கொண்டருளிய எம் அடிகளுக்கு உகந்த இடம் திரு அரசிலியேயாகும்", "theological_explanation"),
            usable_row("PPL_QA_018", "மறி படக் கிடந்த கையர்", "கையில் மான் குட்டியை ஏந்தி", "interprets_image"),
        ],
    )
    write_csv(
        qa_bundle / "paadal_pozhippurai_links_v3_split_suggestions.csv",
        [
            split_row("PPL_QA_001", "SPLIT_001", "தோடு உடைய செவியன்", "தோடணிந்த திருச்செவியை உடைய", "describes_entity"),
            split_row("PPL_QA_001", "SPLIT_002", "விடை ஏறி", "உமையம்மையை இடப்பாகத்தே உடையவனாய், விடை மீது ஏறி", "describes_entity"),
            split_row("PPL_QA_001", "SPLIT_003", "ஓர் தூ வெண்மதி சூடி", "ஒப்பற்ற தூய வெண்மையான பிறையை முடிமிசைச் சூடி", "interprets_image"),
            split_row("PPL_QA_005", "SPLIT_004", "பரக்கும் மிழலையீர்", "எங்கும் பரவிய புகழ் உடைய திருவீழிமிழலையில் உறைபவரே", "describes_entity"),
            split_row("PPL_QA_005", "SPLIT_005", "கரக்கை தவிர்மினே", "எமக்கு அளிக்கும் காசில் உள்ள குறையைப் போக்கியருளுக", "theological_explanation"),
            split_row("PPL_QA_007", "SPLIT_006", "கண் புகார்; பிணி அறியார்", "இடுக்கண் அடையார். நோய் உறார்", "explains_phrase"),
            split_row("PPL_QA_007", "SPLIT_007", "கற்றாரும் கேட்டாரும்", "அவன் புகழைக் கற்றவரும் கேட்டவரும்", "explains_phrase"),
        ],
    )
    write_csv(qa_bundle / "paadal_pozhippurai_phase3_clean_decision_table.csv", [])
    write_csv(
        qa_bundle / "paadal_pozhippurai_links_v3_unresolved_only.csv",
        [usable_row("PPL_QA_BAD", "11", "unresolved target", "glosses_word", "low", "manual_review_required_no_visible_target")],
    )
    return table_root, qa_bundle, output_root


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_v3_gold_rules_splits_outputs_and_iob_pairing(tmp_path: Path) -> None:
    table_root, qa_bundle, output_root = build_fixture(tmp_path)

    summary = run_linking_v3(
        table_root=table_root,
        entity_root=tmp_path / "entities",
        seed_dir=tmp_path / "seed",
        qa_bundle=qa_bundle,
        output_root=output_root,
        report_path=tmp_path / "report.md",
    )

    assert summary["validation"]["status"] == "VALID"
    full = read_jsonl(output_root / "paadal_pozhippurai_links_v3_full.jsonl")
    positives = [row for row in full if row["confidence"] in {"high", "medium"} and not row["manual_review_required"]]
    assert {row["relationship_type"] for row in positives} <= ALLOWED_RELATIONSHIPS
    expected = {
        ("புக்கிட்டு", "தேடப் புகுந்து", "explains_phrase"),
        ("புண்ணியனே", "புண்ணியனே", "glosses_word"),
        ("வெரு உறப்", "அஞ்சுமாறு", "glosses_word"),
        ("முயல்கின்ற", "முயல்கின்ற", "glosses_word"),
        ("ஓர் தூ வெண்மதி சூடி", "ஒப்பற்ற தூய வெண்மையான பிறையை முடிமிசைச் சூடி", "interprets_image"),
        ("கரக்கை தவிர்மினே", "எமக்கு அளிக்கும் காசில் உள்ள குறையைப் போக்கியருளுக", "theological_explanation"),
        ("செந்நெல் அம் கழனிப் பழனத்து", "செந்நெல் விளையும் அழகிய வயல்களை உடைய சோலைகளின்", "explains_phrase"),
        ("அறிவு ஒணா உருவத்து எம் அடிகளுக்கு இடம் அரசிலியே", "அறியமுடியாதவாறும் அழலுருவாய் ஓங்கி நிமிர்ந்த திருவுருவத்தைக் கொண்டருளிய எம் அடிகளுக்கு உகந்த இடம் திரு அரசிலியேயாகும்", "theological_explanation"),
        ("மறி படக் கிடந்த கையர்", "கையில் மான் குட்டியை ஏந்தி", "interprets_image"),
        ("தோடு உடைய செவியன்", "தோடணிந்த திருச்செவியை உடைய", "describes_entity"),
        ("விடை ஏறி", "உமையம்மையை இடப்பாகத்தே உடையவனாய், விடை மீது ஏறி", "describes_entity"),
        ("பரக்கும் மிழலையீர்", "எங்கும் பரவிய புகழ் உடைய திருவீழிமிழலையில் உறைபவரே", "describes_entity"),
        ("கண் புகார்; பிணி அறியார்", "இடுக்கண் அடையார். நோய் உறார்", "explains_phrase"),
        ("கற்றாரும் கேட்டாரும்", "அவன் புகழைக் கற்றவரும் கேட்டவரும்", "explains_phrase"),
    }
    found = {(row["source_text"], row["target_text"], row["relationship_type"]) for row in positives}
    assert expected <= found
    assert all(row["confidence"] == "high" for row in positives if (row["source_text"], row["target_text"], row["relationship_type"]) in expected)
    assert "unresolved target" not in {row["target_text"] for row in positives}

    sides_by_link: dict[str, set[str]] = defaultdict(set)
    for line in (output_root / "paadal_pozhippurai_links_v3_corrected_usable.iob.conll").read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        token, label, link_id, side, relationship, confidence = line.split("\t")
        assert relationship in ALLOWED_RELATIONSHIPS
        assert label.startswith(("B-", "I-"))
        assert confidence in {"high", "medium"}
        sides_by_link[link_id].add(side)
    assert sides_by_link
    assert all(sides == {"paadal", "pozhppurai"} for sides in sides_by_link.values())

    assert (output_root / "paadal_pozhippurai_links_v3_manual_review_pack.csv").exists()
    assert (output_root / "paadal_pozhippurai_links_v3_summary.json").exists()
