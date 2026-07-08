import json
from pathlib import Path

from validation.thevaram_table_quality import audit_tables


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def base_tables(root: Path) -> None:
    schema = "thevaram-relational-v1"
    write_jsonl(
        root / "thirumurai_books.jsonl",
        [
            {
                "schema_version": schema,
                "thirumurai_no": 1,
                "corpus_id": "thirumurai_01",
                "title": "Mudhalaam Thirumurai",
                "work_id": "thevaram",
                "work_title": "தேவாரம்",
                "author": "Tirugnanasambandar",
                "nayanmar": "Tirugnanasambandar",
                "source_url": "https://www.tamilvu.org/slet/l4110/l4110lft.jsp",
                "verified_navigation": True,
            }
        ],
    )
    write_jsonl(
        root / "paadal_thogupugal.jsonl",
        [
            {
                "schema_version": schema,
                "thogupu_id": "thirumurai_01_thogupu_1529",
                "thirumurai_no": 1,
                "ordinal": 1,
                "title": "திருப்பிரமபுரம் - நட்டபாடை",
                "paadapatta_thalam": "திருப்பிரமபுரம்",
                "title_note": "",
                "pann": "நட்டபாடை",
                "source_url": "https://www.tamilvu.org/slet/l4110/l4110son.jsp?subid=1529",
                "source_subid": "1529",
            }
        ],
    )
    write_jsonl(
        root / "paadalgal.jsonl",
        [
            {
                "schema_version": schema,
                "paadal_id": "thirumurai_01_paadal_1",
                "thogupu_id": "thirumurai_01_thogupu_1529",
                "thirumurai_no": 1,
                "global_song_no": "1",
                "source_song_no": "1",
                "local_song_no": "1",
                "verse_index_in_thogupu": 1,
                "paadal_text": "தோடுடைய செவியன்\nவிடையேறி",
                "tokenized_paadal": ["தோடுடைய", "செவியன்", "விடையேறி"],
                "source_url": "https://www.tamilvu.org/slet/l4110/l4110son.jsp?subid=1529",
                "commentary_url": "https://www.tamilvu.org/slet/l4110/l4110uri.jsp?song_no=1&book_id=109&head_id=59&sub_id=1529",
                "source_parameters": {
                    "song_no": "1",
                    "book_id": "109",
                    "head_id": "59",
                    "sub_id": "1529",
                },
            }
        ],
    )
    write_jsonl(
        root / "commentaries.jsonl",
        [
            {
                "schema_version": schema,
                "commentary_id": "thirumurai_01_paadal_1_commentary",
                "paadal_id": "thirumurai_01_paadal_1",
                "kurippurai": "குறிப்பு ஒன்று",
                "pozhppurai": "பொழிப்பு ஒன்று",
                "extraction_status": "success",
                "warnings": [],
            }
        ],
    )
    write_jsonl(
        root / "text_spans.jsonl",
        [
            {
                "schema_version": schema,
                "span_id": "thirumurai_01_paadal_1_paadal_text_1",
                "parent_id": "thirumurai_01_paadal_1",
                "field_name": "paadal_text",
                "span_type": "paadal_line",
                "start_char": 0,
                "end_char": 15,
                "text": "தோடுடைய செவியன்",
                "metadata": {"line_no": "1"},
            },
            {
                "schema_version": schema,
                "span_id": "thirumurai_01_paadal_1_kurippurai_1",
                "parent_id": "thirumurai_01_paadal_1",
                "field_name": "kurippurai",
                "span_type": "commentary_kurippurai",
                "start_char": 0,
                "end_char": 14,
                "text": "குறிப்பு ஒன்று",
                "metadata": {"line_no": "1"},
            },
        ],
    )


def issue_codes(report: dict[str, object]) -> set[str]:
    return {issue["code"] for issue in report["issues"]}


def test_audit_accepts_consistent_minimal_tables(tmp_path: Path) -> None:
    base_tables(tmp_path)

    report = audit_tables(tmp_path)

    assert report["issue_counts"] == {}


def test_audit_flags_broken_foreign_keys_and_offsets(tmp_path: Path) -> None:
    base_tables(tmp_path)
    paadal_path = tmp_path / "paadalgal.jsonl"
    paadal = json.loads(paadal_path.read_text(encoding="utf-8").splitlines()[0])
    paadal["thogupu_id"] = "missing_thogupu"
    write_jsonl(paadal_path, [paadal])
    span_path = tmp_path / "text_spans.jsonl"
    spans = [json.loads(line) for line in span_path.read_text(encoding="utf-8").splitlines()]
    spans[0]["text"] = "தவறான வரி"
    write_jsonl(span_path, spans)

    report = audit_tables(tmp_path)

    assert {"missing_thogupu_fk", "span_text_mismatch"} <= issue_codes(report)


def test_audit_flags_html_artifacts_and_empty_success_commentary(tmp_path: Path) -> None:
    base_tables(tmp_path)
    write_jsonl(
        tmp_path / "commentaries.jsonl",
        [
            {
                "schema_version": "thevaram-relational-v1",
                "commentary_id": "thirumurai_01_paadal_1_commentary",
                "paadal_id": "thirumurai_01_paadal_1",
                "kurippurai": "",
                "pozhppurai": "",
                "extraction_status": "success",
                "warnings": [],
            }
        ],
    )
    paadal_path = tmp_path / "paadalgal.jsonl"
    paadal = json.loads(paadal_path.read_text(encoding="utf-8").splitlines()[0])
    paadal["paadal_text"] = "<br>bad"
    write_jsonl(paadal_path, [paadal])

    report = audit_tables(tmp_path)

    assert {"html_artifact_in_text", "empty_success_commentary"} <= issue_codes(report)
