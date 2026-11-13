# Changelog

All notable changes are recorded here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Release headings carry a timestamp (`YYYY-MM-DD HH:MM TZ`).

## [Unreleased]

### Added
- Phase 00: specification with amendments, ADR log, implementation plan, shared instructions, phase prompts, `/phase` and `/phase-add` commands, `CLAUDE.md`.
- Phase 01: README, LICENSE, NOTICE, THIRD_PARTY_NOTICES, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, ignore files, `.editorconfig`, gitleaks config, pre-commit hook (`scripts/git-hooks/pre-commit` and pre-commit framework), GitHub CI/templates/Dependabot, `docs/OWH_ARCHITECTURE.md`.
- Phase 02: `owh-openrouter` scaffold (uv project, argparse CLI with `set-key`, `models`, `apply`, `status`, `remove` stubs), implemented `paths`, `secrets` (redaction, 0600 key file) and `allowlist`, fake Open WebUI and OpenRouter test servers, `Makefile` (`check`, `test`, `lint`, `install`, `uninstall`), CI jobs for pytest, ruff and shellcheck, Dependabot for uv, empty `config/openrouter-models.txt`.
- Phase 03: `scripts/owh-testbed.sh` (throwaway Open WebUI v0.13.3 testbed: `up`, `down`, `status`, `reset`, `token`; host network bound to `127.0.0.1:18080`), `docs/OWH_FINDINGS.md` (verified Open WebUI connection/task APIs, persistence, offline behaviour, OpenRouter API facts, priced model shortlist), ADR-0011…0013, spec Amendments v2, real-endpoint table in `docs/OWH_ARCHITECTURE.md`.

- Phase 04: working `owh-openrouter`:
  - `set-key`: hidden prompt or `--from-file`, control characters rejected, format check, live check via `GET /api/v1/key`, atomic 0600 write, overwrite only with confirmation or `--force`.
  - `models`: live prices in $/M, unknown IDs flagged (exit 1), `--search` and `--json`.
  - `apply`: `--dry-run`, R1 placement, `prefix_id: "OR"`, `model_ids` = allowlist, local task model per ADR-0005, snapshot before the first write, verify after, no-op on re-run.
  - `status`: `--json` and `--no-login`.
  - `remove`: surgical restore from the earliest snapshot of the same Open WebUI, `--snapshot`, `--delete-key`.
  - Exit codes 0–5, action log `~/.local/state/owh/owh.log`, secret scrubbing, no redirects, loopback-only Open WebUI unless `--allow-remote`.
  - New modules `net`, `plan`, `errors`.
  - Testbed integration test (`make test-testbed`), coverage gate 90 % (`pytest-cov`), `docs/OWH_USER-GUIDE.md` draft, ADR-0015…0017.

- Phase 05: OpenRouter live on the real Open WebUI (eight allowlisted `OR.` models next to the local ones, local task model `qwen3:4b-instruct`); launcher `~/.local/bin/owh-openrouter` installed; confirmed allowlist in `config/openrouter-models.txt`; real `/api/v1/key` fields in `docs/OWH_FINDINGS.md` §6a; ADR-0018…0020; spec Amendments v3; user guide with the steps as run.

### Changed
- Phase 05: hidden prompts refuse with exit 3 instead of a traceback (or an echoing fallback) when there is no terminal; `owh-testbed.sh` waits up to 300 s for a cold start and creates the admin on an existing container; owner questions 2 and 3 answered (no spend management in OWH; OpenRouter privacy allows logging/training providers); SECURITY, README and architecture updated.
- Phase 04: fakes aligned with the Phase 03 findings (full 19-field task config with 422 on a partial update, `null` on a missing `ENABLE_OPENAI_API`, OpenRouter error shape, public `/models`). `secrets.write_key` is now atomic (temp file and rename). The Phase 05 prompt now uses the real command syntax.
- Phase 03: ADR-0005 (local task model) Accepted; spec R9 corrected (Open WebUI always sends OpenRouter attribution headers); Phase 04 and 06 prompts and the shared instructions updated with the findings.
