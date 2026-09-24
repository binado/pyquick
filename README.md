# pyquick

An opinionated [Copier](https://copier.readthedocs.io/) template for small,
typed Python projects. Generated projects use uv, uv_build, Ruff, ty, pytest,
prek, Just, and GitHub Actions.

## Create a project

Copier runs `uv lock` after rendering, so the template must be trusted:

```console
uvx copier@9.18.2 copy --trust gh:binado/pyquick my-project
```

The questionnaire can generate either a library or a dependency-free command
line application. PyPI trusted publishing is optional for both variants.

Copier selects the newest release tag by default. This template therefore uses
PEP 440-compatible tags such as `v1.0.0`.

## Update a generated project

From the generated project directory:

```console
uvx copier@9.18.2 update --trust
```

Review the changes, run `just check`, and commit both the template updates and
the refreshed `uv.lock`.

## Develop the template

```console
just setup
just check
```

`just test` renders both supported project variants into temporary directories
and validates their complete development workflow.
