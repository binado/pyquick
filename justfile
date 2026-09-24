default:
    @just --list

setup:
    uv sync --all-groups

fmt:
    uv run ruff check --fix tests
    uv run ruff format tests

lint:
    uv run ruff check tests

fmt-check:
    uv run ruff format --check tests

typecheck:
    uv run ty check

test *args:
    uv run pytest {{args}}

check: lint fmt-check typecheck test
    uv lock --check
