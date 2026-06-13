from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_PACKAGES = {
    "crawler": {"inspector", "tvu_scraper"},
    "parser": {"parsers", "scraper", "validation"},
    "normalizer": {"corpus"},
    "knowledge": {"knowledge"},
    "retrieval": {"analytics", "embeddings", "enrichment", "rag", "retrieval", "vector_index"},
    "evaluation": {"evaluation"},
}

PACKAGE_PROJECT = {
    package: project for project, packages in PROJECT_PACKAGES.items() for package in packages
}

PROJECT_ROOTS = {
    project: Path("projects") / project / "src" for project in PROJECT_PACKAGES
}

# Transitional edges already present before the package split. Keep this empty unless a
# future migration slice intentionally records a temporary edge with an expiry plan.
ALLOWED_TRANSITIONAL_EDGES: set[tuple[str, str]] = set()


@dataclass(slots=True)
class BoundaryViolation:
    path: Path
    source_package: str
    imported_package: str
    line: int


def imported_top_level_names(node: ast.AST) -> list[tuple[str, int]]:
    imports: list[tuple[str, int]] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Import):
            imports.extend((alias.name.split(".")[0], child.lineno) for alias in child.names)
        elif isinstance(child, ast.ImportFrom) and child.module:
            imports.append((child.module.split(".")[0], child.lineno))
    return imports


def source_package_for(path: Path) -> str | None:
    parts = path.parts
    if "src" not in parts:
        return None
    src_index = parts.index("src")
    if len(parts) <= src_index + 1:
        return None
    package = parts[src_index + 1]
    return package if package in PACKAGE_PROJECT else None


def scan_file(path: Path, strict: bool) -> list[BoundaryViolation]:
    source_package = source_package_for(path)
    if not source_package:
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations: list[BoundaryViolation] = []
    for imported_package, line in imported_top_level_names(tree):
        if imported_package not in PACKAGE_PROJECT:
            continue
        if PACKAGE_PROJECT[imported_package] == PACKAGE_PROJECT[source_package]:
            continue
        edge = (source_package, imported_package)
        if not strict and edge in ALLOWED_TRANSITIONAL_EDGES:
            continue
        violations.append(
            BoundaryViolation(
                path=path,
                source_package=source_package,
                imported_package=imported_package,
                line=line,
            )
        )
    return violations


def source_files() -> list[Path]:
    files: list[Path] = []
    for root in PROJECT_ROOTS.values():
        if root.exists():
            files.extend(sorted(root.rglob("*.py")))
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check project package dependency boundaries.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat transitional allowlist edges as violations.",
    )
    args = parser.parse_args(argv)

    violations = [
        violation
        for path in source_files()
        for violation in scan_file(path, strict=args.strict)
    ]
    if violations:
        for violation in violations:
            print(
                f"{violation.path}:{violation.line}: "
                f"{violation.source_package} imports {violation.imported_package}",
                file=sys.stderr,
            )
        return 1

    mode = "strict" if args.strict else "transitional"
    print(f"boundary check passed ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
