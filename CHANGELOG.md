# Changelog

All notable changes are recorded here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Release headings carry a timestamp (`YYYY-MM-DD HH:MM TZ`).

## [Unreleased]

### Added
- Phase 00: specification with amendments, ADR log, implementation plan, shared instructions, phase prompts, `/phase` and `/phase-add` commands, `CLAUDE.md`.
- Phase 01: README, LICENSE, NOTICE, THIRD_PARTY_NOTICES, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, ignore files, `.editorconfig`, gitleaks config, pre-commit hook (`scripts/git-hooks/pre-commit` and pre-commit framework), GitHub CI/templates/Dependabot, `docs/OWH_ARCHITECTURE.md`.
- Phase 02: `owh-openrouter` scaffold (uv project, argparse CLI with `set-key`, `models`, `apply`, `status`, `remove` stubs), implemented `paths`, `secrets` (redaction, 0600 key file) and `allowlist`, fake Open WebUI and OpenRouter test servers, `Makefile` (`check`, `test`, `lint`, `install`, `uninstall`), CI jobs for pytest, ruff and shellcheck, Dependabot for uv, empty `config/openrouter-models.txt`.
