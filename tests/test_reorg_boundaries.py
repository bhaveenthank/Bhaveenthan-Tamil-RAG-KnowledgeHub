from __future__ import annotations

import importlib.util
import sys
import ast
import tomllib
from pathlib import Path

SCRIPT = Path("scripts/check-boundaries.py")
SPEC = importlib.util.spec_from_file_location("check_boundaries", SCRIPT)
assert SPEC and SPEC.loader
check_boundaries = importlib.util.module_from_spec(SPEC)
sys.modules["check_boundaries"] = check_boundaries
SPEC.loader.exec_module(check_boundaries)

ALLOWED_TRANSITIONAL_EDGES = check_boundaries.ALLOWED_TRANSITIONAL_EDGES
PACKAGE_PROJECT = check_boundaries.PACKAGE_PROJECT
PROJECT_PACKAGES = check_boundaries.PROJECT_PACKAGES
ROOT = Path(__file__).resolve().parents[1]


def test_project_package_ownership_is_complete() -> None:
    for project, packages in PROJECT_PACKAGES.items():
        assert packages, project
        for package in packages:
            assert PACKAGE_PROJECT[package] == project


def test_validation_is_parser_owned_after_extraction_qa_move() -> None:
    assert PACKAGE_PROJECT["validation"] == "parser"


def test_normalizer_parser_debt_is_retired() -> None:
    assert ("corpus", "parsers") not in ALLOWED_TRANSITIONAL_EDGES
    assert ("corpus", "scraper") not in ALLOWED_TRANSITIONAL_EDGES


def test_strict_boundaries_are_clean() -> None:
    violations = [
        violation
        for path in check_boundaries.source_files()
        for violation in check_boundaries.scan_file(path, strict=True)
    ]

    assert violations == []


def test_transitional_edges_reference_known_packages() -> None:
    for source, target in ALLOWED_TRANSITIONAL_EDGES:
        assert source in PACKAGE_PROJECT
        assert target in PACKAGE_PROJECT
        assert PACKAGE_PROJECT[source] != PACKAGE_PROJECT[target]


def test_console_scripts_resolve_to_project_modules() -> None:
    pyproject_paths = [
        ROOT / "pyproject.toml",
        *sorted((ROOT / "projects").glob("*/pyproject.toml")),
    ]
    search_roots = [
        ROOT / "src",
        ROOT / "shared/tvu-common/src",
        ROOT / "shared/tvu-schemas/src",
        *sorted((ROOT / "projects").glob("*/src")),
    ]
    missing: list[str] = []
    for pyproject_path in pyproject_paths:
        config = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        scripts = config.get("project", {}).get("scripts", {})
        for name, target in scripts.items():
            module_name, attr_name = target.split(":", 1)
            module_path = Path(*module_name.split(".")).with_suffix(".py")
            source = next(
                (root / module_path for root in search_roots if (root / module_path).exists()),
                None,
            )
            if source is None:
                missing.append(f"{pyproject_path}:{name}:{target}:module")
                continue
            tree = ast.parse(source.read_text(encoding="utf-8"))
            has_attr = any(
                isinstance(node, ast.FunctionDef) and node.name == attr_name
                for node in tree.body
            )
            if not has_attr:
                missing.append(f"{pyproject_path}:{name}:{target}:attr")

    assert missing == []
