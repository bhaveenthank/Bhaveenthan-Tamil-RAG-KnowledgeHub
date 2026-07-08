import json
from pathlib import Path

from knowledge.link_thevaram_pozhippurai import build_links, run_linking, segment_spans


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def seed_tables(root: Path) -> None:
    write_jsonl(
        root / "paadalgal.jsonl",
        [
            {
                "paadal_id": "p1",
                "thirumurai_no": 1,
                "paadal_text": "தோடு உடைய செவியன்\nவிடை ஏறி மதி சூடி",
            },
            {
                "paadal_id": "p2",
                "thirumurai_no": 1,
                "paadal_text": "பாடல் வரி ஒன்று\nபாடல் வரி இரண்டு",
            },
        ],
    )
    write_jsonl(
        root / "commentaries.jsonl",
        [
            {
                "commentary_id": "p1_commentary",
                "paadal_id": "p1",
                "kurippurai": "",
                "pozhppurai": "தோடணிந்த திருச்செவியை உடையவன், விடை மீது ஏறி பிறையைச் சூடி",
            },
            {
                "commentary_id": "p2_commentary",
                "paadal_id": "p2",
                "kurippurai": "",
                "pozhppurai": "",
            },
        ],
    )


def seed_entities(root: Path) -> None:
    write_jsonl(
        root / "entity_mentions.jsonl",
        [
            {
                "target_id": "p1",
                "field_name": "paadal_text",
                "start_char": 0,
                "end_char": 17,
                "entity_type": "BODY_PART",
                "canonical_id": "body_ear",
            },
            {
                "target_id": "p1_commentary",
                "field_name": "pozhppurai",
                "start_char": 0,
                "end_char": 25,
                "entity_type": "BODY_PART",
                "canonical_id": "body_ear",
            },
        ],
    )


def seed_relations(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "thevaram_pozhippurai_paadallink_relations.tsv").write_text(
        "link_id\tpoem_id\tsource_ref\tsource_url\tsource_status\tpaadal_surface\tpaadal_normalized\tpozhppurai_span\trelationship_type\tannotation_note\tconfidence\n"
        "L1\tP1\tref\turl\tseed\tதோடுடையசெவியன்\tதோடு உடைய செவியன்\tதோடணிந்த திருச்செவியை உடைய\tglosses_word\tbody epithet\thigh\n",
        encoding="utf-8",
    )


def test_segment_spans_preserve_offsets() -> None:
    text = "முதல் பகுதி, இரண்டாம் பகுதி. மூன்றாம்"
    spans = segment_spans(text)

    assert [span["text"] for span in spans] == ["முதல் பகுதி,", "இரண்டாம் பகுதி.", "மூன்றாம்"]
    for span in spans:
        assert text[span["start_char"] : span["end_char"]] == span["text"]


def test_pozhippurai_linking_covers_lines_and_validates_offsets(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    entity_root = tmp_path / "entities"
    seed_dir = tmp_path / "seeds"
    seed_tables(table_root)
    seed_entities(entity_root)
    seed_relations(seed_dir)

    links, summary = build_links(table_root=table_root, entity_root=entity_root, seed_dir=seed_dir)

    assert summary["paadal_count"] == 2
    assert summary["link_count"] == 4
    assert summary["no_pozhippurai_paadal_count"] == 1
    assert any(link["link_status"] == "no_pozhippurai" for link in links)
    assert any(link["relationship_type"] == "glosses_word" for link in links)
    for link in links:
        paadal_text = "தோடு உடைய செவியன்\nவிடை ஏறி மதி சூடி" if link["paadal_id"] == "p1" else "பாடல் வரி ஒன்று\nபாடல் வரி இரண்டு"
        assert paadal_text[link["source_start_char"] : link["source_end_char"]] == link["source_text"]
        if link["target_start_char"] is not None:
            pozhppurai = "தோடணிந்த திருச்செவியை உடையவன், விடை மீது ஏறி பிறையைச் சூடி"
            assert pozhppurai[link["target_start_char"] : link["target_end_char"]] == link["target_text"]


def test_sequence_alignment_marks_monotonic_path(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    entity_root = tmp_path / "entities"
    seed_dir = tmp_path / "seeds"
    write_jsonl(
        table_root / "paadalgal.jsonl",
        [
            {
                "paadal_id": "p_align",
                "thirumurai_no": 1,
                "paadal_text": "அ முதல்\nநடுவண் குறிப்பு\nஇறுதி முத்தி",
            }
        ],
    )
    write_jsonl(
        table_root / "commentaries.jsonl",
        [
            {
                "commentary_id": "p_align_commentary",
                "paadal_id": "p_align",
                "kurippurai": "",
                "pozhppurai": "அ முதல் உரை. பொருள் நடுவண். இறுதி முத்தி விளக்கம்.",
            }
        ],
    )

    links, _ = build_links(table_root=table_root, entity_root=entity_root, seed_dir=seed_dir)

    linked = [row for row in links if row["paadal_id"] == "p_align"]
    assert [row["target_text"] for row in linked] == [
        "அ முதல் உரை.",
        "பொருள் நடுவண்.",
        "இறுதி முத்தி விளக்கம்.",
    ]
    assert all(row["features"]["sequence_alignment_method"] == "forward_dynamic_programming" for row in linked)


def test_reverse_order_alignment_handles_bottom_up_commentary(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    entity_root = tmp_path / "entities"
    seed_dir = tmp_path / "seeds"
    write_jsonl(
        table_root / "paadalgal.jsonl",
        [
            {
                "paadal_id": "p_reverse",
                "thirumurai_no": 1,
                "paadal_text": "மேல் வரி சிவன்\nநடு வரி அருள்\nகீழ் வரி முத்தி",
            }
        ],
    )
    write_jsonl(
        table_root / "commentaries.jsonl",
        [
            {
                "commentary_id": "p_reverse_commentary",
                "paadal_id": "p_reverse",
                "kurippurai": "",
                "pozhppurai": "கீழ் வரி முத்தி விளக்கம். நடு வரி அருள் விளக்கம். மேல் வரி சிவன் விளக்கம்.",
            }
        ],
    )

    links, _ = build_links(table_root=table_root, entity_root=entity_root, seed_dir=seed_dir)

    linked = [row for row in links if row["paadal_id"] == "p_reverse"]
    assert [row["target_text"] for row in linked] == [
        "மேல் வரி சிவன் விளக்கம்.",
        "நடு வரி அருள் விளக்கம்.",
        "கீழ் வரி முத்தி விளக்கம்.",
    ]
    assert all(row["features"]["sequence_alignment_method"] == "reverse_dynamic_programming" for row in linked)


def test_synonym_scoring_links_same_meaning_words(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    entity_root = tmp_path / "entities"
    seed_dir = tmp_path / "seeds"
    write_jsonl(
        table_root / "paadalgal.jsonl",
        [{"paadal_id": "p_syn", "thirumurai_no": 1, "paadal_text": "மதி சூடி"}],
    )
    write_jsonl(
        table_root / "commentaries.jsonl",
        [
            {
                "commentary_id": "p_syn_commentary",
                "paadal_id": "p_syn",
                "kurippurai": "",
                "pozhppurai": "நிலாவைச் சூடியவன்.",
            }
        ],
    )

    links, _ = build_links(table_root=table_root, entity_root=entity_root, seed_dir=seed_dir)

    link = next(row for row in links if row["paadal_id"] == "p_syn")
    assert link["target_text"] == "நிலாவைச் சூடியவன்."
    assert link["features"]["synonym_score"] > 0


def test_temple_entity_mentions_support_thalam_links(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    entity_root = tmp_path / "entities"
    seed_dir = tmp_path / "seeds"
    write_jsonl(
        table_root / "paadalgal.jsonl",
        [{"paadal_id": "p_temple", "thirumurai_no": 1, "paadal_text": "திருவாரூர் மேவியான்"}],
    )
    write_jsonl(
        table_root / "commentaries.jsonl",
        [
            {
                "commentary_id": "p_temple_commentary",
                "paadal_id": "p_temple",
                "kurippurai": "",
                "pozhppurai": "திருவாரூரில் எழுந்தருளிய இறைவன்.",
            }
        ],
    )
    write_jsonl(
        entity_root / "entity_mentions.jsonl",
        [
            {
                "target_id": "p_temple",
                "field_name": "paadal_text",
                "start_char": 0,
                "end_char": 9,
                "entity_type": "TEMPLE",
                "entity_subtype": "paadapatta_thalam",
                "canonical_id": "temple_tiruvarur",
            },
            {
                "target_id": "p_temple_commentary",
                "field_name": "pozhppurai",
                "start_char": 0,
                "end_char": 12,
                "entity_type": "TEMPLE",
                "entity_subtype": "paadapatta_thalam",
                "canonical_id": "temple_tiruvarur",
            },
        ],
    )

    links, _ = build_links(table_root=table_root, entity_root=entity_root, seed_dir=seed_dir)

    link = next(row for row in links if row["paadal_id"] == "p_temple")
    assert link["relationship_type"] == "describes_entity"
    assert link["features"]["entity_score"] == 1.0


def test_run_linking_writes_outputs(tmp_path: Path) -> None:
    table_root = tmp_path / "tables"
    entity_root = tmp_path / "entities"
    seed_dir = tmp_path / "seeds"
    output_root = tmp_path / "out"
    seed_tables(table_root)
    seed_entities(entity_root)
    seed_relations(seed_dir)

    result = run_linking(
        table_root=table_root,
        entity_root=entity_root,
        seed_dir=seed_dir,
        output_root=output_root,
        report_path=tmp_path / "report.md",
    )

    assert result["validation"]["status"] == "VALID"
    assert (output_root / "paadal_pozhippurai_links.jsonl").exists()
    assert read_jsonl(output_root / "paadal_pozhippurai_links.jsonl")
