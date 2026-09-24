from __future__ import annotations

import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest
from copier import run_copy

ROOT = Path(__file__).parents[1]


def run(*command: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


@pytest.fixture(
    scope="module", params=[("library", "3.11", False), ("app", "3.14", True)]
)
def rendered_project(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> tuple[Path, str, str, bool]:
    project_type, python_min, publish = request.param
    project_name = f"sample-{project_type}"
    source = tmp_path_factory.mktemp(f"source-{project_type}")
    destination = tmp_path_factory.mktemp(project_name) / project_name
    shutil.copytree(
        ROOT,
        source,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", ".pytest_cache", ".ruff_cache", ".ty_cache"
        ),
    )
    run_copy(
        src_path=str(source),
        dst_path=str(destination),
        data={
            "project_name": project_name,
            "description": f"A sample {project_type}.",
            "project_type": project_type,
            "author_name": "Test Author",
            "author_email": "test@example.com",
            "github_username": "example",
            "python_min": python_min,
            "publish_to_pypi": publish,
        },
        defaults=True,
        unsafe=True,
    )
    return destination, project_type, python_min, publish


def test_rendered_structure(
    rendered_project: tuple[Path, str, str, bool],
) -> None:
    destination, project_type, python_min, publish = rendered_project
    project_name = destination.name
    package_name = project_name.replace("-", "_")

    pyproject = (destination / "pyproject.toml").read_text()
    metadata = tomllib.loads(pyproject)
    assert metadata["project"]["name"] == project_name
    assert metadata["project"]["requires-python"] == f">={python_min}"
    assert (destination / "src" / package_name / "py.typed").is_file()
    assert (destination / "uv.lock").is_file()
    assert (destination / ".copier-answers.yml").is_file()

    main_file = destination / "src" / package_name / "__main__.py"
    release_file = destination / ".github" / "workflows" / "release.yml"
    justfile = (destination / "justfile").read_text()
    workflow = (destination / ".github" / "workflows" / "test.yml").read_text()

    assert main_file.exists() is (project_type == "app")
    assert ("[project.scripts]" in pyproject) is (project_type == "app")
    assert ("\nrun *args:\n" in justfile) is (project_type == "app")
    assert release_file.exists() is publish

    expected_versions = [
        version for version in ("3.11", "3.12", "3.13", "3.14") if version >= python_min
    ]
    matrix = ", ".join(f'"{version}"' for version in expected_versions)
    assert f"python-version: [{matrix}]" in workflow


def test_rendered_toolchain(
    rendered_project: tuple[Path, str, str, bool],
) -> None:
    destination, project_type, _, _ = rendered_project
    project_name = destination.name
    package_name = project_name.replace("-", "_")

    run("uv", "lock", cwd=destination)
    run("uv", "sync", "--locked", "--all-groups", cwd=destination)
    run("just", "lint", cwd=destination)
    run("just", "fmt-check", cwd=destination)
    run("just", "typecheck", cwd=destination)
    run("just", "test", cwd=destination)
    run("just", "build", cwd=destination)
    run("uv", "run", "prek", "validate-config", "prek.toml", cwd=destination)
    run("just", "check", cwd=destination)

    version = run(
        "uv",
        "run",
        "python",
        "-c",
        f"from {package_name} import __version__; print(__version__)",
        cwd=destination,
    )
    assert version.stdout.strip() == "0.1.0"

    if project_type == "app":
        command = run("uv", "run", project_name, cwd=destination)
        module = run("uv", "run", "python", "-m", package_name, cwd=destination)
        assert command.stdout == f"Hello from {project_name}!\n"
        assert module.stdout == command.stdout
