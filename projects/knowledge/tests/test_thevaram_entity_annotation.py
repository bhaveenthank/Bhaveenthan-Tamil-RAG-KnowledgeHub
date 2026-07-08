import json
from pathlib import Path

from knowledge.annotate_thevaram_entities import annotate, load_seed_terms, slug_id
from knowledge.annotate_thevaram_entities_v3 import run_v3


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def seed_tsvs(seed_dir: Path) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / "thevaram_deity_spans.tsv").write_text(
        "sent_id\tsource\tsource_url\tsource_line\tspan\tlabel\tnote\n"
        "D1\ts\turl\tவிடை ஏறிய எம்பெருமான்\tவிடை ஏறிய எம்பெருமான்\tSIVA\tSiva epithet\n",
        encoding="utf-8",
    )
    (seed_dir / "thevaram_sacred_object_audit.tsv").write_text(
        "id\tsource\turl\ttext\tspans\tnote\n"
        "SO1\ts\turl\tதூ வெண்மதி\tதூ வெண்மதி=>moon\tobject\n",
        encoding="utf-8",
    )
    (seed_dir / "thevaram_body_part_audit.tsv").write_text(
        "id\tsource\turl\ttext\tspans\tnote\n"
        "BP1\ts\turl\tசெவியன்\tசெவியன்=>ear\tbody\n"
        "BP2\ts\turl\tகை\tகை=>hand\ttoo broad\n",
        encoding="utf-8",
    )
    (seed_dir / "thevaram_nature_audit.tsv").write_text(
        "id\tsource\turl\ttext\tspans\tnote\n"
        "NA1\ts\turl\tதூ வெண்மதி\tதூ வெண்மதி=>moon\tnature\n",
        encoding="utf-8",
    )
    (seed_dir / "thevaram_action_audit.tsv").write_text(
        "id\tsource\turl\ttext\tspans\tnote\n"
        "AC1\ts\turl\tவிடை ஏறி\tவிடை ஏறி=>riding bull\taction\n",
        encoding="utf-8",
    )
    (seed_dir / "thevaram_theology_audit.tsv").write_text(
        "id\tsource\turl\ttext\tspans\tnote\n"
        "TH1\ts\turl\tஅருள் செய்த\tஅருள் செய்த=>grace\ttheology\n",
        encoding="utf-8",
    )


def seed_review_decisions(review_dir: Path) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    hand_id = f"body_part_{slug_id('கை')}"
    ear_id = f"body_part_{slug_id('செவியன்')}"
    nature_moon_id = f"nature_{slug_id('தூ வெண்மதி')}"
    sacred_moon_id = f"sacred_object_{slug_id('தூ வெண்மதி')}"
    (review_dir / "entity_v1_all_alias_review_decisions.csv").write_text(
        "alias,entity_type,entity_id,alias_id,observed_mentions,decision,v2_rule,gloss,source_seed_id,source_file,field_counts,thirumurai_counts\n"
        f"கை,BODY_PART,{hand_id},term_body_part_5fd99798ad7b,13894,REJECT_OR_EXCLUDE,Standalone கை too noisy; require longer context.,hand,BP2,thevaram_body_part_audit.tsv,,\n"
        f"செவியன்,BODY_PART,{ear_id},term_body_part_00b165c66f47,1,KEEP,Keep eared-one epithet.,ear,BP1,thevaram_body_part_audit.tsv,,\n"
        f"தூ வெண்மதி,NATURE,{nature_moon_id},term_nature_9e1c0a473ba4,1,KEEP,Keep moon imagery.,moon,NA1,thevaram_nature_audit.tsv,,\n"
        f"தூ வெண்மதி,SACRED_OBJECT,{sacred_moon_id},term_sacred_object_0b8806c2f394,1,KEEP,Keep worn moon as sacred object.,moon,SO1,thevaram_sacred_object_audit.tsv,,\n",
        encoding="utf-8",
    )


def seed_tables(table_root: Path) -> None:
    write_jsonl(
        table_root / "paadalgal.jsonl",
        [
            {
                "paadal_id": "thirumurai_01_paadal_1",
                "thogupu_id": "thirumurai_01_thogupu_1",
                "thirumurai_no": 1,
                "paadal_text": "தோடு உடைய செவியன்\nகை கொண்டு விடை ஏறி ஓர் தூ வெண்மதி சூடி",
            }
        ],
    )
    write_jsonl(
        table_root / "commentaries.jsonl",
        [
            {
                "commentary_id": "thirumurai_01_paadal_1_commentary",
                "paadal_id": "thirumurai_01_paadal_1",
                "kurippurai": "விடை ஏறிய எம்பெருமான் அருள் செய்தான்",
                "pozhppurai": "தூ வெண்மதி குறித்து உரை",
            }
        ],
    )
    write_jsonl(
        table_root / "paadal_thogupugal.jsonl",
        [
            {
                "thogupu_id": "thirumurai_01_thogupu_1",
                "thirumurai_no": 1,
                "title": "திருவாரூர் - நட்டபாடை",
                "paadapatta_thalam": "திருவாரூர்",
                "pann": "நட்டபாடை",
            }
        ],
    )


def test_load_seed_terms_from_six_datasets(tmp_path: Path) -> None:
    seed_tsvs(tmp_path)

    terms = load_seed_terms(tmp_path, review_dir=tmp_path / "review")
    labels = {(term.entity_type, term.term) for term in terms}

    assert ("DEITY", "விடை ஏறிய எம்பெருமான்") in labels
    assert ("SACRED_OBJECT", "தூ வெண்மதி") in labels
    assert ("BODY_PART", "செவியன்") in labels
    assert ("NATURE", "தூ வெண்மதி") in labels
    assert ("ACTION", "விடை ஏறி") in labels
    assert ("THEOLOGICAL_CONCEPT", "அருள் செய்த") in labels


def test_annotate_thevaram_entities_outputs_valid_offsets(tmp_path: Path) -> None:
    seed_dir = tmp_path / "seeds"
    review_dir = tmp_path / "review"
    table_root = tmp_path / "tables"
    output_root = tmp_path / "annotations"
    seed_tsvs(seed_dir)
    seed_review_decisions(review_dir)
    seed_tables(table_root)

    summary = annotate(
        table_root=table_root,
        seed_dir=seed_dir,
        review_dir=review_dir,
        output_root=output_root,
        report_path=tmp_path / "report.md",
    )
    mentions = read_jsonl(output_root / "entity_mentions.jsonl")

    assert summary["validation"]["status"] == "VALID"
    assert summary["counts"]["entity_mentions"] >= 6
    assert any(row["entity_type"] == "BODY_PART" and row["mention_text"] == "செவியன்" for row in mentions)
    assert any(row["entity_type"] == "NATURE" and row["mention_text"] == "தூ வெண்மதி" for row in mentions)
    assert any(row["entity_type"] == "SACRED_OBJECT" and row["mention_text"] == "தூ வெண்மதி" for row in mentions)
    assert any(row["entity_type"] == "DEITY" for row in mentions)
    assert not any(row["entity_type"] == "BODY_PART" and row["mention_text"] == "கை" for row in mentions)
    assert any(row["review_status"] == "auto_accepted" for row in mentions)
    assert summary["suppressed_counts_by_reason"]["review_decision_exclude"] >= 1
    assert {row["thirumurai_no"] for row in mentions} == {1}

    text_by_key = {
        ("paadalgal", "thirumurai_01_paadal_1", "paadal_text"): "தோடு உடைய செவியன்\nகை கொண்டு விடை ஏறி ஓர் தூ வெண்மதி சூடி",
        ("commentaries", "thirumurai_01_paadal_1_commentary", "kurippurai"): "விடை ஏறிய எம்பெருமான் அருள் செய்தான்",
        ("commentaries", "thirumurai_01_paadal_1_commentary", "pozhppurai"): "தூ வெண்மதி குறித்து உரை",
    }
    for mention in mentions:
        key = (mention["target_table"], mention["target_id"], mention["field_name"])
        source_text = text_by_key[key]
        assert source_text[mention["start_char"] : mention["end_char"]] == mention["mention_text"]


def test_annotate_thevaram_entities_v3_expands_ontology_and_relationships(tmp_path: Path) -> None:
    seed_dir = tmp_path / "seeds"
    review_dir = tmp_path / "review"
    table_root = tmp_path / "tables"
    output_root = tmp_path / "annotations_v3"
    seed_tsvs(seed_dir)
    seed_review_decisions(review_dir)
    seed_tables(table_root)
    paadal_path = table_root / "paadalgal.jsonl"
    paadal = read_jsonl(paadal_path)[0]
    paadal["paadal_text"] += "\nஈசன் நீலகண்டன் செஞ்சடை திரிசூலம் கொண்டு திரிபுரம் செற்று திருவாரூர் மேவினார்"
    write_jsonl(paadal_path, [paadal])

    summary = run_v3(
        table_root=table_root,
        seed_dir=seed_dir,
        review_dir=review_dir,
        output_root=output_root,
        report_path=tmp_path / "v3_report.md",
    )
    mentions = read_jsonl(output_root / "entity_mentions.jsonl")
    relationships = read_jsonl(output_root / "entity_relationships.jsonl")
    types = {row["entity_type"] for row in mentions}

    assert summary["schema_version"] == "thevaram-entity-annotation-v3"
    assert summary["validation"]["status"] == "VALID"
    assert {"DIVINE_EPITHET", "MYTHOLOGICAL_EVENT", "TEMPLE", "WEAPON"} <= types
    assert any(row["entity_type"] == "DEITY" and row["mention_text"] == "ஈசன்" for row in mentions)
    assert any(row["entity_type"] == "TEMPLE" and row["mention_text"] == "திருவாரூர்" for row in mentions)
    assert any(row["relationship_type"] == "performed_by" for row in relationships)
    assert any(row["relationship_source"] == "v3_curated_ontology" for row in relationships)
