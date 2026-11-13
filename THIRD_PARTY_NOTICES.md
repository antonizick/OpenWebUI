# Third-party notices

No third-party code is bundled or redistributed by this repository, and the tool has no runtime dependencies (ADR-0006).

## Development-only Python dependencies
Locked in `uv.lock`; installed by `uv sync` for tests and linting, never shipped.

| Package | Licence | Use |
|---|---|---|
| pytest | MIT | test runner |
| pluggy, iniconfig | MIT | pytest dependencies |
| packaging | Apache-2.0 or BSD-2-Clause | pytest dependency |
| pygments | BSD-2-Clause | pytest dependency |
| colorama | BSD-3-Clause | pytest dependency (Windows only) |
| ruff | MIT | linter and formatter |
| pytest-cov | MIT | coverage plugin for pytest (Phase 04) |
| coverage | Apache-2.0 | pytest-cov dependency |

Audited 2026-11-13 13:46 CST (Phase 06) against the installed metadata of the locked versions: coverage 7.17.3, iniconfig 2.3.1, packaging 26.3, pluggy 1.7.0, Pygments 2.21.0, pytest 9.2.0, pytest-cov 7.1.0, ruff 0.17.5 (colorama is not installed on Linux). Every licence matches the table, and all are permissive. There are no runtime dependencies.

Open WebUI (the container image `ghcr.io/open-webui/open-webui`) and OpenRouter (a hosted API) are external software and services that OWH configures and calls. They are not part of this repository and are governed by their own licences and terms.

Development tools (uv, pytest, ruff, shellcheck, gitleaks) are used from the host or CI and are not redistributed. Dependencies added in later phases are listed here with their licences.
