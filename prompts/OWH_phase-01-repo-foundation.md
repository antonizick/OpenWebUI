# OWH Phase 01: Repository foundation & governance

**Model:** Sonnet 5.5 (`/model sonnet`) · **Depends on:** 00 · **Branch:** `phase-01-repo-foundation` · **Gate:** auto

## Read first
`CLAUDE.md`, `prompts/OWH_shared-instructions.md`, and the spec sections §3.3 (security baseline, especially S1) and §3.4 (repository requirement). Phase Log entries for Phase 00 and "Planning: owner brainstorming".

## Goal
The repo has the full governance file set, a secret scan that blocks commits containing keys, and lives in a **private** GitHub repo `antonizick/OpenWebUI` with `main` pushed. No product code yet.

## Tasks
1. `README.md`: what OWH is (one paragraph from `CLAUDE.md`), status ("in development, see `OWH_IMPLEMENTATION_PLAN.md`"), the privacy note from spec S4 in two sentences, and links to the plan, spec and decisions.
2. `LICENSE`: "Copyright (c) 2026 Nick Antonizick. All rights reserved." (private; owner question 4 decides any later licence). `NOTICE` naming the project and that it configures, but does not include, Open WebUI and talks to OpenRouter. `THIRD_PARTY_NOTICES.md` (none bundled yet; Open WebUI and OpenRouter are external services/software, not redistributed).
3. `SECURITY.md`: the secret-handling rules (S1–S3) in plain words, where the key lives, how to rotate it, and "report by email to the owner" (do not write the email address into the file; say "the repository owner").
4. `CONTRIBUTING.md` (phased method, `/phase`, Conventional Commits, `make check` once it exists), `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1, by reference link plus a short summary; do not paste its full text if you cannot reproduce it verbatim), `CHANGELOG.md` (Keep a Changelog, `[Unreleased]` with the Phase 00 and 01 entries).
5. `.gitignore`: Python/uv artefacts, `.venv/`, `*.key`, `*.db`, `*.db-*`, `*.sqlite*`, `*.tar.gz`, `*.tgz`, `.env*`, `owh-state/`, `scratch/`; `.dockerignore` (same plus `.git`), `.editorconfig` (utf-8, lf, 4 spaces py, 2 spaces yaml/md tables untouched).
6. Secret scanning: `.gitleaks.toml` extending the default rules with an explicit OpenRouter rule (`sk-or-v1-[0-9a-f]{40,}`-style; confirm the length against the real key with `wc -c ~/.config/ai-provider/openrouter.key` **without printing it**) and an allowlist for the documented fake test key pattern `sk-or-v1-TESTKEY`. A `.pre-commit-config.yaml` with the gitleaks hook, **and** a plain `scripts/git-hooks/pre-commit` (shell, `gitleaks protect --staged --no-banner`) installed via `git config core.hooksPath scripts/git-hooks`, so the hook works without the pre-commit tool. Run `gitleaks detect --no-banner` over the whole history: must be clean.
7. `.github/`: `workflows/ci.yml` with a gitleaks job now (`gitleaks/gitleaks-action`, pinned to a full commit SHA you look up, not a tag) and placeholders for the Phase 02 jobs; issue templates (bug, change request pointing at `prompts/OWH_change-request-template.md`), PR template with the close-out checklist summary; `dependabot.yml` (github-actions weekly; pip/uv added in Phase 02).
8. `docs/` skeleton: `OWH_ARCHITECTURE.md` with the current/target diagram (Open WebUI → Ollama, Open WebUI → OpenRouter; where config and key live; what `owh-openrouter` touches), kept short.
9. Create the private GitHub repo: check `gh repo view antonizick/OpenWebUI` first (must not exist), then `gh repo create antonizick/OpenWebUI --private --source /home/nick/Work/OpenWebUI --remote origin` and push `main` at close-out (after the merge). **Never `--public`.**

## Out of scope
Python project, CLI code, tests (Phase 02); any contact with Open WebUI or OpenRouter (Phase 03+).

## Tests
`gitleaks detect --no-banner` (history clean); a negative test: stage a scratch file containing a fake-but-rule-matching key outside the allowlist pattern, confirm the hook blocks the commit, then delete the file (never commit it). `shellcheck scripts/git-hooks/pre-commit`.

## Acceptance criteria
- Every file in spec §3.4 exists and is accurate; `grep -rn '{{' .` finds only literal mentions (`.claude/commands/phase-add.md`, docker `--format` strings in prompts).
- The pre-commit hook blocks a staged OpenRouter-shaped key (verified, transcript in the Phase Log).
- `gh repo view antonizick/OpenWebUI --json visibility` prints `PRIVATE`; `main` is pushed.

## Phase-specific docs
README, SECURITY, CHANGELOG, `docs/OWH_ARCHITECTURE.md`, ADR for the hook approach if it differs from the above. Vault note: add the GitHub URL. Then the standard close-out checklist.
