import json
from pathlib import Path

from corpus.normalize_thevaram_tables import normalize_tables


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
        root / "thirumurai_books.jsonl",
        [
            {
                "schema_version": "thevaram-relational-v1",
                "thirumurai_no": 1,
                "corpus_id": " thirumurai_01 ",
                "title": " Mudhalaam   Thirumurai ",
                "work_id": "thevaram",
                "work_title": "தேவாரம்",
                "author": "Tirugnanasambandar",
                "nayanmar": "Tirugnanasambandar",
                "source_url": " https://www.tamilvu.org/slet/l4110/l4110lft.jsp ",
            }
        ],
    )
    write_jsonl(
        root / "paadal_thogupugal.jsonl",
        [
            {
                "schema_version": "thevaram-relational-v1",
                "thogupu_id": "thirumurai_01_thogupu_1529",
                "thirumurai_no": 1,
                "ordinal": 1,
                "title": "திருப்பிரமபுரம்   - நட்டபாடை",
                "paadapatta_thalam": " திருப்பிரமபுரம் ",
                "title_note": "",
                "pann": " நட்டபாடை ",
                "source_url": "https://www.tamilvu.org/slet/l4110/l4110son.jsp?subid=1529",
                "source_subid": "1529",
            }
        ],
    )
    write_jsonl(
        root / "paadalgal.jsonl",
        [
            {
                "schema_version": "thevaram-relational-v1",
                "paadal_id": "thirumurai_01_paadal_1",
                "thogupu_id": "thirumurai_01_thogupu_1529",
                "thirumurai_no": 1,
                "global_song_no": "1",
                "source_song_no": "1",
                "local_song_no": "1",
                "verse_index_in_thogupu": 1,
                "paadal_text": "  தோடு  உடைய செவியன்\r\nகாடு\tஉடைய   சுடலை  ",
                "tokenized_paadal": ["stale"],
                "source_url": "https://www.tamilvu.org/slet/l4110/l4110son.jsp?subid=1529",
                "commentary_url": "https://www.tamilvu.org/slet/l4110/l4110uri.jsp?song_no=1&sub_id=1529",
                "source_parameters": {" song_no ": " 1 ", "sub_id": "1529"},
            }
        ],
    )
    write_jsonl(
        root / "commentaries.jsonl",
        [
            {
                "schema_version": "thevaram-relational-v1",
                "commentary_id": "thirumurai_01_paadal_1_commentary",
                "paadal_id": "thirumurai_01_paadal_1",
                "kurippurai": "  குறிப்பு  ஒன்று  ",
                "pozhppurai": "பொழிப்பு\u00a0ஒன்று\n  பொழிப்பு இரண்டு ",
                "extraction_status": " success ",
                "warnings": ["  note  one  "],
            }
        ],
    )
    write_jsonl(
        root / "text_spans.jsonl",
        [
            {
                "schema_version": "thevaram-relational-v1",
                "span_id": "old",
                "parent_id": "thirumurai_01_paadal_1",
                "field_name": "paadal_text",
                "span_type": "paadal_line",
                "start_char": 0,
                "end_char": 5,
                "text": "wrong",
                "metadata": {"line_no": "1"},
            }
        ],
    )


def test_normalization_preserves_line_breaks_and_rebuilds_spans(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "normalized"
    seed_tables(source)

    report = normalize_tables(source, output)

    paadal = read_jsonl(output / "paadalgal.jsonl")[0]
    commentary = read_jsonl(output / "commentaries.jsonl")[0]
    spans = read_jsonl(output / "text_spans.jsonl")

    assert paadal["paadal_text"] == "தோடு உடைய செவியன்\nகாடு உடைய சுடலை"
    assert paadal["tokenized_paadal"] == [
        "தோடு",
        "உடைய",
        "செவியன்",
        "காடு",
        "உடைய",
        "சுடலை",
    ]
    assert paadal["source_parameters"] == {"song_no": "1", "sub_id": "1529"}
    assert commentary["pozhppurai"] == "பொழிப்பு ஒன்று\nபொழிப்பு இரண்டு"
    assert commentary["warnings"] == ["note one"]
    assert report["newline_counts_before"] == {"paadal_text": 1, "commentary_text": 1}
    assert report["newline_counts_after"] == {"paadal_text": 1, "commentary_text": 1}
    assert [span["text"] for span in spans] == [
        "தோடு உடைய செவியன்",
        "காடு உடைய சுடலை",
        "குறிப்பு ஒன்று",
        "பொழிப்பு ஒன்று",
        "பொழிப்பு இரண்டு",
    ]
    for span in spans:
        parent_text = (
            paadal["paadal_text"]
            if span["field_name"] == "paadal_text"
            else commentary[span["field_name"]]
        )
        assert parent_text[span["start_char"] : span["end_char"]] == span["text"]


def test_normalization_writes_summary(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "normalized"
    seed_tables(source)

    normalize_tables(source, output)

    summary = json.loads((output / "normalization_summary.json").read_text(encoding="utf-8"))
    assert summary["normalization_version"] == "thevaram-normalized-v1"
    assert summary["counts"]["paadalgal"] == 1
    assert summary["changed_fields"]["paadalgal"]["paadal_text"] == 1
