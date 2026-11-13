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

Open WebUI (the container image `ghcr.io/open-webui/open-webui`) and OpenRouter (a hosted API) are external software and services that OWH configures and calls. They are not part of this repository and are governed by their own licences and terms.

Development tools (uv, pytest, ruff, shellcheck, gitleaks) are used from the host or CI and are not redistributed. Dependencies added in later phases are listed here with their licences.
