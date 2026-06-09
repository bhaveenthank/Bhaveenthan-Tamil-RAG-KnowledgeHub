import json

from corpus.audit_corpus_readiness import (
    FAILURE_CATEGORIES,
    audit_records,
    main,
    render_report,
)


def records() -> list[dict]:
    return [
        {
            "schema_version": "unified-thirumurai-v1",
            "record_id": "r1",
            "corpus_id": "thirumurai_02",
            "thirumurai_no": 2,
            "collection": "Thirumurai",
            "canonical_title": "Irandaam Thirumurai",
            "author": "Tirugnanasambandar",
            "nayanmar": "Tirugnanasambandar",
            "hymn_id": "1664",
            "pathigam_id": "1664",
            "song_no": "1470",
            "verse_no": "1",
            "title": "திருப்பூந்தராய்",
            "place": "திருப்பூந்தராய்",
            "deity": "Siva",
            "verse_text": "தமிழ் பாடல் வரி சந்திரன் திங்கள் மதி நிலவு நீளமாக உள்ளது",
            "pozhppurai": "தமிழ் பொழிப்புரை",
            "kurippurai": "தமிழ் குறிப்புரை",
            "source_url": "https://www.tamilvu.org/hymn?subid=1664",
            "commentary_url": "https://www.tamilvu.org/commentary?song_no=1470&sub_id=1664",
            "metadata": {
                "canonical_id": "canonical-r1",
                "source_record_id": "source-r1",
                "citation_text": "citation",
            },
        }
    ]


def chunks() -> list[dict]:
    return [
        {"chunk_type": chunk_type, "parent_record_id": "r1"}
        for chunk_type in (
            "verse_only",
            "pozhppurai_only",
            "kurippurai_only",
            "verse_plus_commentary",
            "metadata_context",
        )
    ]


def registry() -> dict:
    return {
        "corpora": [
            {
                "corpus_id": f"thirumurai_{number:02d}",
                "status": "available" if number == 2 else "planned",
            }
            for number in range(1, 13)
        ]
    }


def test_audit_has_required_sections_and_checks() -> None:
    audit = audit_records(records(), chunks(), registry(), input_sha256="abc")

    assert {
        "summary",
        "scores",
        "field_coverage",
        "issue_counts",
        "parser_readiness",
        "citation_readiness",
        "retrieval_readiness",
        "analytical_readiness",
        "scaling_risks",
        "failure_attribution_categories",
        "recommendations",
    } <= audit.keys()
    assert len(audit["analytical_readiness"]["capabilities"]) == 12


def test_scores_are_deterministic_and_bounded() -> None:
    first = audit_records(records(), chunks(), registry(), input_sha256="abc")
    second = audit_records(records(), chunks(), registry(), input_sha256="abc")

    assert first == second
    assert all(0 <= value <= 100 for value in first["scores"].values())


def test_issue_categories_are_valid() -> None:
    audit = audit_records(records(), chunks(), registry())

    assert audit["failure_attribution_categories"] == list(FAILURE_CATEGORIES)


def test_report_is_generated() -> None:
    report = render_report(audit_records(records(), chunks(), registry()))

    assert "Readiness Scores" in report
    assert "Capability Readiness" in report
    assert "Scaling Risks" in report
    assert "Synonym Readiness" in report


def test_cli_writes_json_and_report_without_mutating_input(tmp_path) -> None:
    input_path = tmp_path / "corpus.jsonl"
    chunks_path = tmp_path / "chunks.jsonl"
    registry_path = tmp_path / "registry.json"
    output_path = tmp_path / "audit.json"
    report_path = tmp_path / "audit.md"
    input_path.write_text(
        json.dumps(records()[0], ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    chunks_path.write_text(
        "".join(json.dumps(chunk, sort_keys=True) + "\n" for chunk in chunks()),
        encoding="utf-8",
    )
    registry_path.write_text(json.dumps(registry()), encoding="utf-8")
    before = input_path.read_bytes()

    result = main(
        [
            "--input",
            str(input_path),
            "--chunks",
            str(chunks_path),
            "--registry",
            str(registry_path),
            "--output",
            str(output_path),
            "--report",
            str(report_path),
        ]
    )

    assert result == 0
    assert input_path.read_bytes() == before
    assert output_path.exists()
    assert report_path.exists()


def test_audit_module_has_no_scraping_dependency() -> None:
    import corpus.audit_corpus_readiness as module

    source_names = set(module.__dict__)
    assert "requests" not in source_names
    assert "BeautifulSoup" not in source_names
