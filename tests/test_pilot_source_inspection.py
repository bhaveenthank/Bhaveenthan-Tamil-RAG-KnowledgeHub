import json
from pathlib import Path

from corpus.inspect_pilot_sources import (
    build_fixture_plan,
    inspect_sources,
    load_plan,
    remaining_pilots,
)


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "data/processed/corpus_registry/pilot_category_plan.json"


def copy_plan(tmp_path: Path) -> None:
    target = tmp_path / "data/processed/corpus_registry/pilot_category_plan.json"
    target.parent.mkdir(parents=True)
    target.write_text(PLAN.read_text(encoding="utf-8"), encoding="utf-8")


def test_inspection_recognizes_verified_pilots() -> None:
    plan = load_plan(PLAN)
    fixtures = build_fixture_plan(plan)

    assert fixtures["verified_categories"] == ["saivam", "dictionaries"]
    assert fixtures["remaining_category_count"] == 4
    assert {"saivam", "dictionaries"}.isdisjoint(
        {item["category_id"] for item in fixtures["fixtures"]}
    )


def test_remaining_categories_and_fixture_contract() -> None:
    plan = load_plan(PLAN)
    remaining = remaining_pilots(plan)
    fixtures = build_fixture_plan(plan)["fixtures"]

    assert {pilot["category_id"] for pilot in remaining} == {
        "grammar",
        "sangam_literature",
        "twentieth_century_prose",
        "encyclopedias",
    }
    assert all(item["fixture_needed"] is True for item in fixtures)
    assert all(item["target_fixture_count"] == 3 for item in fixtures)
    assert all(item["risk_level"] in {"low", "medium", "high"} for item in fixtures)


def test_dry_run_does_not_write_output(tmp_path) -> None:
    copy_plan(tmp_path)
    summary = inspect_sources(base_dir=tmp_path, dry_run=True)

    assert summary["network_requests"] == 0
    assert summary["writes"] == 0
    assert not (
        tmp_path / "data/processed/corpus_registry/pilot_fixture_plan.json"
    ).exists()
    assert not (tmp_path / "tests/fixtures/pilot_categories").exists()
    assert not (tmp_path / "reports/pilot-source-inspection-report.md").exists()


def test_generation_creates_plan_directories_and_report(tmp_path) -> None:
    copy_plan(tmp_path)
    summary = inspect_sources(base_dir=tmp_path)
    fixture_plan_path = (
        tmp_path / "data/processed/corpus_registry/pilot_fixture_plan.json"
    )
    fixture_plan = json.loads(fixture_plan_path.read_text(encoding="utf-8"))

    assert summary["fixture_directories"] == 4
    assert summary["target_fixture_count"] == 12
    assert fixture_plan["network_access"] is False
    for item in fixture_plan["fixtures"]:
        readme = (
            tmp_path
            / "tests/fixtures/pilot_categories"
            / item["category_id"]
            / "README.md"
        )
        assert readme.exists()
        assert item["parser_family"] in readme.read_text(encoding="utf-8")
    report = tmp_path / "reports/pilot-source-inspection-report.md"
    assert report.exists()
    assert "dictionary_parser" in report.read_text(encoding="utf-8")


def test_script_contains_no_network_or_ingestion_path() -> None:
    script = (
        ROOT / "src/corpus/inspect_pilot_sources.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "urlopen",
        "fetch_html",
        "ingest_category(",
    ):
        assert forbidden not in script
