# OWH Phase 02: Tool scaffold & quality gates

**Model:** Sonnet 5.5 (`/model sonnet`) · **Depends on:** 01 · **Branch:** `phase-02-tool-scaffold` · **Gate:** auto

May run in parallel with Phase 03 (different files). If both touch `CHANGELOG.md` or the plan, keep both sides at merge.

## Read first
`CLAUDE.md`, `prompts/OWH_shared-instructions.md`, spec §3.2 R7, §3.3, ADR-0006. Phase Log entry for Phase 01.

## Goal
A working Python project skeleton for `owh-openrouter` with its command surface stubbed, fake servers for tests, a `Makefile`, and CI running every quality gate green, so Phase 04 only writes behaviour.

## Tasks
1. `pyproject.toml` (uv, `requires-python = ">=3.11"`, **no runtime dependencies**; dev group: `pytest`, `ruff`; pin versions in `uv.lock`; check each licence and add to `THIRD_PARTY_NOTICES.md` as dev-only). Console script `owh-openrouter = "owh_openrouter.cli:main"`.
2. `src/owh_openrouter/`: `cli.py` (argparse with subcommands `set-key`, `models`, `apply [--dry-run]`, `status`, `remove`, global `--webui-url` default `http://127.0.0.1:8080`, `--openrouter-url` default from findings or `https://openrouter.ai/api/v1` until Phase 03 confirms, `--state-dir`, `--config-dir`, `--json`); each stub exits 2 with "not implemented". Modules with interfaces only: `paths.py` (XDG paths, mode checks), `secrets.py` (key file read/write with 0700/0600 enforcement, `redact()` showing first 9 chars + length), `webui.py` (Open WebUI client: signin, get/update connection config, get/update task config, list models), `openrouter.py` (key info, list models), `allowlist.py` (parse `config/openrouter-models.txt`: one ID per line, `#` comments, duplicates rejected), `snapshot.py`.
3. Implement now (small, pure, fully tested): `paths.py`, `secrets.redact`, the key-file permission logic (refuse to read a key file that is group/world readable), and `allowlist.py`.
4. `tests/fakes/`: a fake Open WebUI and a fake OpenRouter on `http.server` in a thread, bound to `127.0.0.1:0`, with in-memory state and a request log (so tests can assert the key never appears where it should not). Endpoint shapes start as the spec's *expected* list (R6) and are marked `# TODO(phase-04): align with docs/OWH_FINDINGS.md`.
5. `Makefile`: `check` (pytest, ruff check, ruff format --check, shellcheck `scripts/*.sh scripts/git-hooks/*`, gitleaks), `test`, `lint`, `install` (writes a launcher `~/.local/bin/owh-openrouter` that runs `uv run --project /home/nick/Work/OpenWebUI owh-openrouter "$@"`, or `uv tool install .`; pick one, ADR) and `uninstall`. Do **not** run `make install` in this phase.
6. CI (`.github/workflows/ci.yml`): jobs for `uv sync --locked`, pytest, ruff, shellcheck, gitleaks; actions pinned by SHA. Dependabot: add the `uv`/pip ecosystem if supported, else document.
7. `config/openrouter-models.txt` with a header comment explaining the format and **no model IDs yet** (Phase 03 proposes, Nick confirms in Phase 05).

## Out of scope
Real HTTP behaviour against Open WebUI or OpenRouter (Phase 04); the testbed (Phase 03).

## Tests
Unit tests for `paths`, `redact`, key-file permissions (0644 file refused, 0600 accepted, dir created 0700), allowlist parsing (comments, blanks, duplicates, invalid characters); a smoke test that both fakes start and answer.

## Acceptance criteria
- `make check` passes locally and CI is green on the pushed branch/merge.
- `uv run owh-openrouter --help` lists all five subcommands.
- No runtime dependency in `pyproject.toml`.

## Phase-specific docs
README (dev setup: `uv sync`, `make check`), `docs/OWH_ARCHITECTURE.md` (module map), CHANGELOG, THIRD_PARTY_NOTICES, ADR for the install method. Then the standard close-out checklist.
