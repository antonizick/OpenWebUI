# Contributing

This is a single-owner project (public from 2026-11-13 17:31 CST, MIT licence) built with the **phased-project method**: work is split into phases in [`OWH_IMPLEMENTATION_PLAN.md`](OWH_IMPLEMENTATION_PLAN.md), each with its own prompt in `prompts/`.

- Start a session in Claude Code with `/phase` (next eligible), `/phase NN` or `/phase status`. Add work with `/phase-add`. Read [`CLAUDE.md`](CLAUDE.md) and [`prompts/OWH_shared-instructions.md`](prompts/OWH_shared-instructions.md) first.
- A phase is claimed with a status-only commit on `main`, then built on `phase-NN-<slug>` in the worktree `../OpenWebUI-phase-NN`.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`...).
- Enable the secret-scan hook once per clone: `git config core.hooksPath scripts/git-hooks` (needs `gitleaks`).
- From Phase 02 on, `make check` (pytest, ruff, shellcheck, gitleaks) must pass before a phase closes.
- Never commit secrets, personal data, database copies or `.env` files.
