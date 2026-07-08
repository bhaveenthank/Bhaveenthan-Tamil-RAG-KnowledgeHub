from pathlib import Path

from projects.parser.tests.test_thevaram_table_quality import base_tables
from validation.thevaram_manual_qa import render_report


def test_manual_qa_report_contains_samples_and_review_prompts(tmp_path: Path) -> None:
    base_tables(tmp_path)

    report = render_report(tmp_path, sample_count=1)

    assert "# Thevaram Manual QA Samples" in report
    assert "## What To Check In Each Sample" in report
    assert "Sample 1" in report
    assert "தோடுடைய செவியன்" in report
