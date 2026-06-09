import json

from evaluation.build_question_taxonomy import (
    CATEGORIES,
    QUESTION_GROUPS,
    build_questions,
    main,
    render_report,
    summarize,
    validate_questions,
)


def test_exactly_100_questions_with_deterministic_ids() -> None:
    questions = build_questions()

    assert len(questions) == 100
    assert [question["question_id"] for question in questions] == [
        f"q_{index:03d}" for index in range(1, 101)
    ]


def test_jsonl_schema_is_valid() -> None:
    questions = build_questions()

    assert validate_questions(questions) == []
    encoded = "\n".join(json.dumps(question, ensure_ascii=False) for question in questions)
    decoded = [json.loads(line) for line in encoded.splitlines()]
    assert decoded == questions


def test_all_required_categories_are_present() -> None:
    questions = build_questions()

    assert set(question["category"] for question in questions) == set(CATEGORIES)
    assert all(QUESTION_GROUPS[category] for category in CATEGORIES)


def test_category_counts_are_deterministic() -> None:
    summary = summarize(build_questions())

    assert summary["category_counts"] == {
        "A. Basic lookup": 12,
        "B. Verse identification": 12,
        "C. Word occurrence": 12,
        "D. Synonym expansion": 10,
        "E. Deity and epithet": 12,
        "F. Simile and metaphor": 12,
        "G. Poet/Nayanmar comparison": 10,
        "H. Cross-hymn and cross-corpus": 12,
        "I. Failure diagnosis": 8,
    }


def test_report_generation_contains_architecture_recommendations() -> None:
    report = render_report(summarize(build_questions()))

    assert "Current RAG context builder can answer lookup/retrieval questions." in report
    assert "Analytical questions require an additional corpus analysis layer." in report
    assert "Tamil literary synonym lexicon" in report
    assert "multi-corpus metadata normalization" in report


def test_cli_generates_dataset_and_report_without_llm(tmp_path, monkeypatch) -> None:
    output = tmp_path / "questions.jsonl"
    report = tmp_path / "report.md"

    def forbidden_network_call(*_args, **_kwargs):
        raise AssertionError("No LLM or network call is allowed")

    monkeypatch.setattr("urllib.request.urlopen", forbidden_network_call)
    result = main(["--output", str(output), "--report", str(report)])

    assert result == 0
    assert len(output.read_text(encoding="utf-8").splitlines()) == 100
    assert report.exists()


def test_validate_only_preserves_dataset(tmp_path) -> None:
    output = tmp_path / "questions.jsonl"
    report = tmp_path / "report.md"
    assert main(["--output", str(output), "--report", str(report)]) == 0
    before = output.read_bytes()

    assert main(
        ["--output", str(output), "--report", str(report), "--validate-only"]
    ) == 0
    assert output.read_bytes() == before
