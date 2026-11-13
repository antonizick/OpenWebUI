# OpenWebUI Hybrid (OWH): Agent Instructions

These rules apply to every AI agent working in this repository. They are **mandatory**.

## What this project is
OWH ("OpenWebUI Hybrid") adds Nick's OpenRouter account as a second backend to his local Open WebUI (Docker container `open-webui`, v0.13.3, host network, port 8080), next to the local Ollama (`127.0.0.1:11434`), so the model picker offers local and cloud models and each chat goes to the backend of the model chosen. The deliverable is a small Python CLI, `owh-openrouter` (stdlib only at runtime; uv, pytest and ruff for dev), that stores a dedicated OpenRouter key, manages a curated model allowlist, and writes the OpenRouter connection into Open WebUI's stored config through its admin API (idempotent, with snapshot and `remove`), plus the docs for using, rotating and undoing it. Nothing in the container, its unit, the `Super+Alt+O` toggle, OCC or `open-webui-upgrade` changes.

**Live-system rule:** the live Open WebUI is changed **only in Phase 05**, after a local DB backup. Every other phase uses the throwaway testbed (`scripts/owh-testbed.sh`) or read-only inspection. See `prompts/OWH_shared-instructions.md` §3.

## Naming and timestamps (mandatory)
- **Project prefix: `OWH`.** Project documents are named `OWH_<NAME>` (`OWH_IMPLEMENTATION_PLAN.md`, `docs/OWH_DECISIONS.md`, `prompts/OWH_phase-NN-<slug>.md`…) so they can be told apart from other projects' documents without their path. Any new project-specific document gets the prefix. `CLAUDE.md`, `README.md`, `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md` and the like keep their conventional names.
- **Timestamps everywhere a date is recorded** (Phase Log, ADRs, amendments, owner questions, vault log, "Last updated"): `YYYY-MM-DD HH:MM TZ`, from `date '+%Y-%m-%d %H:%M %Z'` at the moment you write it. Never a bare date, never guessed.

## Source-of-truth documents (read before working)
| File | Purpose |
|---|---|
| `docs/OWH_SPECIFICATION.md` | Canonical spec. **The Amendments section overrides earlier sections.** |
| `OWH_IMPLEMENTATION_PLAN.md` | Phase table, status, owner questions, phase log. **Keep it accurate.** |
| `prompts/OWH_shared-instructions.md` | Conventions and close-out checklist for every phase |
| `prompts/OWH_phase-NN-*.md` | The prompt for the phase you are executing (start sessions with `/phase`) |
| `docs/OWH_DECISIONS.md` | ADR log; append, never rewrite |

## Mandatory documentation upkeep
Documentation is part of the deliverable. A phase is **not complete** until all of the following are done:
1. `OWH_IMPLEMENTATION_PLAN.md`: set the phase's status as icon plus word (`🔄 In progress` when you start; `✅ Complete` or `⛔ Blocked` at the end) and add a timestamped Phase Log entry whose **first bullet is the Timeline** (`started` = the claim commit's time, `finished` = `date` as your last step, `merged`, any `blocked` interval; format in the plan's Phase Log header), then built, deviations, follow-ups, tests. **`🔄 In progress` must be committed to `main` before any other work** (the claim protocol in `prompts/OWH_shared-instructions.md` §1a), because parallel agents read the status from `main`. A status that exists only on a phase branch or in a worktree does not count.
2. `CHANGELOG.md`: add entries under `[Unreleased]`.
3. Update every affected document: README, SECURITY, `docs/OWH_ARCHITECTURE.md`, guides, THIRD_PARTY_NOTICES, `.gitignore` / `.dockerignore`.
4. `docs/OWH_DECISIONS.md`: add an ADR for any non-trivial choice or deviation. If the spec changes, add an amendment.
5. **Later phase prompts:** if your work changes an assumption a later prompt relies on, edit that prompt.
6. The Obsidian project note `/home/nick/Documents/02 Projects/OWH Implementation Plan.md`: update the status table (icons), the `updated:` field and add a timestamped log line.
7. Any host OS change must also be documented in `/home/nick/Documents/04 Resources/OSMods/` (read its README first).

## Risk rule (mandatory)
Sessions may run with bypassed permissions. **If an action looks high-risk, irreversible or a bad idea, stop and ask Nick instead of doing it.** In an interactive session, ask. In a hands-off session (`/phase NN --auto` or `PHX_AUTO=1`, started by PhaseHypervisor), block the phase with the question recorded (block-with-question, `prompts/OWH_shared-instructions.md` §1b). Examples: deleting data you did not create, touching another project's files outside the scope your prompt names, changing system-wide config not covered by the prompt, spending money beyond a stated cap, making a repo public, publishing a release, force-pushing shared history.

## Engineering rules
- Stay within the phase's scope; record out-of-scope findings as follow-ups in the Phase Log.
- Tests, lint and type checks must pass before a phase closes. Run `make check` (pytest, ruff check, ruff format --check, shellcheck, gitleaks).
- Never commit secrets, personal data, private recordings, model weights or `.env` files.
- Follow the security and privacy baseline in the spec's Amendments.
- Pin and lock dependencies, and check licences before adding one.
- Git: branch `phase-NN-<slug>` in its own worktree `../OpenWebUI-phase-NN`; the main checkout stays on `main`. Conventional Commits, commit at checkpoints. **Git authority (standing instruction from Nick):** commit, merge, push and create **private** GitHub repos without asking, at checkpoints and at close-out. Only making a repo **public**, publishing a GitHub **release**, or force-pushing shared history needs Nick's explicit confirmation (in hands-off mode: block-with-question). If an action looks high-risk or a bad idea, stop and ask anyway.
- Reference machine: Nick's laptop: Omarchy (Arch) Linux, kernel 7.2.8, RTX 2070 Max-Q 8 GB, Docker 29.9.2, Python 3.14.8, uv 0.13.0, gh 2.103.2 (`antonizick`), gitleaks, shellcheck, jq, Ollama 0.40.7. `~/Documents` (the Obsidian vault) syncs to Drive, and `~/Documents/02 Projects/Work` is a symlink to `~/Work`, so treat repo files as synced: never put secrets or DB copies in the repo or the vault.
