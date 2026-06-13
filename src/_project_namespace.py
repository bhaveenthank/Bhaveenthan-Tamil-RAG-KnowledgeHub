from __future__ import annotations

from pathlib import Path
from typing import Iterable


def extend_project_path(
    package_file: str, package_name: str, project: str | Iterable[str]
) -> list[str]:
    """Return the legacy package path plus its new project package path."""
    package_dir = Path(package_file).resolve().parent
    repo_root = package_dir.parents[1]
    paths = [str(package_dir)]
    projects = [project] if isinstance(project, str) else list(project)
    for project_name in projects:
        project_package_dir = repo_root / "projects" / project_name / "src" / package_name
        if project_package_dir.is_dir():
            paths.append(str(project_package_dir))
    return paths
