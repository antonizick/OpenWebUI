# OWH: OpenWebUI Hybrid Implementation Plan

**Spec:** [`docs/OWH_SPECIFICATION.md`](docs/OWH_SPECIFICATION.md). **Decisions:** [`docs/OWH_DECISIONS.md`](docs/OWH_DECISIONS.md). **Agent rules:** [`CLAUDE.md`](CLAUDE.md). **Shared phase instructions:** [`prompts/OWH_shared-instructions.md`](prompts/OWH_shared-instructions.md)
**Last updated:** 2026-11-13 17:32 CST (Phase 07 complete)

> ⚠️ **Mandatory:** every agent that works on this project keeps this file accurate. **Before doing any other work, set your phase to `🔄 In progress` and commit that change to `main`** (claim protocol: `prompts/OWH_shared-instructions.md` §1a). Other agents read this table from `main`. At the end, set it to `✅ Complete` or `⛔ Blocked` and add a Phase Log entry. See `CLAUDE.md`.

## How to run a phase
Open Claude Code in `/home/nick/Work/OpenWebUI` and type one of:
- `/phase`: run the next eligible phase. It checks dependencies, tells you if you're on the wrong model, resumes an `In progress` phase, and asks about any open questions it needs.
- `/phase NN`: run a specific phase.
- `/phase status`: show progress and what's next, without doing any work.
- `/phase-add [after NN] <request or file>`: plan a new lettered phase (`07a`) from a change request. No product work, no claim.

**Optional hands-off runs (PhaseHypervisor):** `phx preflight /home/nick/Work/OpenWebUI` asks the foreseeable questions once, then `phx run /home/nick/Work/OpenWebUI` runs the remaining phases unattended through `/phase NN --auto`, honouring the Gate column. Manual `/phase` stays the standard way; you can switch between the two at any phase boundary, and `/phase` stops if a `phx` supervisor is running this plan.

The agent merges a completed phase into `main` and pushes it without asking (Nick's standing git authority); review its close-out summary.

Each phase is claimed by a `chore(plan): start phase NN` commit on `main` and runs in its own worktree, `../OpenWebUI-phase-NN`, so parallel sessions never share a checkout. `/phase status` flags any branch or worktree whose row is not `🔄 In progress`.

**Parallelism:** after Phase 01, Phases **02** (tool scaffold) and **03** (verification spike) can run in parallel in separate sessions; they touch different files (02: `pyproject.toml`, `src/`, `tests/`, CI; 03: `docs/OWH_FINDINGS.md`, `scripts/owh-testbed.sh`, ADRs). Everything else is sequential.

**Gate column** (read only by PhaseHypervisor; manual `/phase` ignores it): `auto` = may run unattended; `review` = pause for Nick after it; `owner` = Nick starts it. Empty means `auto`.

**Status values:** ⬜ Not started · 🔄 In progress · ⛔ Blocked · ✅ Complete. Always write the icon **and** the word.

## Phases

| Phase | Phase Name | Phase Purpose | AI Model to Use | Depends on | Status | Prompt to Initiate This Phase | Gate |
|---|---|---|---|---|---|---|---|
| 00 | Planning & spec refinement | Review source docs, resolve decisions, write the spec, plan and prompts | Opus 5.5 (`/model opus`) | none | ✅ Complete | n/a (planning session) | owner |
| 01 | Repository foundation & governance | Governance files, secret-scan hook, private GitHub repo | Sonnet 5.5 (`/model sonnet`) | 00 | ✅ Complete | [`prompts/OWH_phase-01-repo-foundation.md`](prompts/OWH_phase-01-repo-foundation.md) | auto |
| 02 | Tool scaffold & quality gates | uv project, CLI skeleton, fakes, pytest/ruff/shellcheck/gitleaks in CI | Sonnet 5.5 (`/model sonnet`) | 01 | ✅ Complete | [`prompts/OWH_phase-02-tool-scaffold.md`](prompts/OWH_phase-02-tool-scaffold.md) | auto |
| 03 | Verification spike | Prove Open WebUI 0.13.3 and OpenRouter API facts on a throwaway container; propose the model shortlist | Opus 5.5 (`/model opus`) | 01 | ✅ Complete | [`prompts/OWH_phase-03-verification-spike.md`](prompts/OWH_phase-03-verification-spike.md) | auto |
| 04 | `owh-openrouter` CLI | `set-key`, `models`, `apply`, `status`, `remove`; idempotent, snapshot/restore, tested against fakes and the testbed | Opus 5.5 (`/model opus`) | 02, 03 | ✅ Complete | [`prompts/OWH_phase-04-owh-openrouter-cli.md`](prompts/OWH_phase-04-owh-openrouter-cli.md) | auto |
| 05 | Rehearsal & live deploy | Real key, rehearsal on the testbed, backup, apply to the live instance, verify both backends in the UI, OSMods docs | Opus 5.5 (`/model opus`) | 04 | ✅ Complete | [`prompts/OWH_phase-05-rehearsal-and-live-deploy.md`](prompts/OWH_phase-05-rehearsal-and-live-deploy.md) | owner |
| 06 | Hardening, security & QA | Threat model, secret scans, upgrade survival, offline behaviour, spend guard, exposure review, follow-ups | Opus 5.5 (`/model opus`) | 05 | ✅ Complete | [`prompts/OWH_phase-06-hardening-and-qa.md`](prompts/OWH_phase-06-hardening-and-qa.md) | review |
| 07 | Release & handover | User guide, final report with timeline, CHANGELOG 1.0.0, vault and OSMods final, private repo pushed | Sonnet 5.5 (`/model sonnet`) | 06 | ✅ Complete | [`prompts/OWH_phase-07-release-and-handover.md`](prompts/OWH_phase-07-release-and-handover.md) | review |

## Timeline
Generated by `scripts/phase_timeline.py` from the Phase Log and git; refreshed on `main` at every close-out, block, resume and `/phase-add`. Do not edit between the markers.

<!-- phase-timeline:start (generated by scripts/phase_timeline.py; do not edit) -->
![OWH timeline](docs/OWH_TIMELINE.svg)

*Generated from the Phase Log Timeline bullets and git, as of 2026-11-13 17:27 CST. ≈ marks a time inferred from git or a heading. Idle gaps over 60 min start a new chart below and are collapsed in the image. Regenerate with `python3 scripts/phase_timeline.py --write`; do not edit by hand.*

```mermaid
gantt
    title OWH session 1, 2026-11-13 10:03 to 13:51 CST
    dateFormat YYYY-MM-DD HH:mm
    axisFormat %H:%M
    section Planning
    Owner brainstorming :done, plan1, 2026-11-13 10:03, 2026-11-13 10:59
    Planning & spec refinement :done, p00, 2026-11-13 11:02, 2026-11-13 11:24
    section Phases
    01 Repository foundation & governance :done, p01s1, 2026-11-13 11:40, 2026-11-13 11:42
    02 Tool scaffold & quality gates :done, p02s1, 2026-11-13 11:44, 2026-11-13 11:46
    03 Verification spike :done, p03s1, 2026-11-13 11:51, 2026-11-13 12:10
    04 owh-openrouter CLI :done, p04s1, 2026-11-13 12:18, 2026-11-13 12:37
    05 Rehearsal & live deploy :done, p05s1, 2026-11-13 12:43, 2026-11-13 13:25
    06 Hardening, security & QA :done, p06s1, 2026-11-13 13:38, 2026-11-13 13:51
```

```mermaid
gantt
    title OWH session 2, 2026-11-13 17:27 to 17:27 CST
    dateFormat YYYY-MM-DD HH:mm
    axisFormat %H:%M
    section Phases
    07 Release & handover :active, p07s2, 2026-11-13 17:27, 2026-11-13 17:28
```

| Phase | Name | Started | Finished | Merged | Active | Blocked | Claim |
|---|---|---|---|---|---:|---:|---|
| plan | Owner brainstorming | 2026-11-13 10:03 CST | 10:59 |  | 56 m |  | n/a |
| 00 | Planning & spec refinement | 2026-11-13 11:02 CST | 11:24 |  | 22 m |  | n/a |
| 01 | Repository foundation & governance | 2026-11-13 11:40 CST | 11:42 | 11:42 | 2 m |  | `a9c405b` |
| 02 | Tool scaffold & quality gates | 2026-11-13 11:44 CST | 11:46 | 11:46 | 2 m |  | `9eb5dff` |
| 03 | Verification spike | 2026-11-13 11:51 CST | 12:10 | 12:10 | 19 m |  | `879a1f8` |
| 04 | `owh-openrouter` CLI | 2026-11-13 12:18 CST | 12:37 | 12:37 | 19 m |  | `2bf3c35` |
| 05 | Rehearsal & live deploy | 2026-11-13 12:43 CST | 13:25 | 13:25 | 42 m |  | `0efb977` |
| 06 | Hardening, security & QA | 2026-11-13 13:38 CST | 13:51 | 13:51 | 13 m |  | `2a6aef1` |
| 07 | Release & handover | 2026-11-13 17:27 CST | (in progress) |  | < 1 m so far |  | `01eb9f7` |

**Totals:** elapsed 7 h 24 m (first recorded start to 2026-11-13 17:27 CST) · active phase time 1 h 37 m (sum over phases) · blocked or paused 0 m · idle 3 h 36 m in 1 gap(s) over 60 min.
<!-- phase-timeline:end -->

### Model rationale
- **Opus 5.5** for 03 (reading Open WebUI's real behaviour and API shapes correctly is the foundation of everything after it), 04 (idempotent config merge, snapshot/restore round-trip, secret handling), 05 (changes a live instance holding Nick's data; judgment over risk) and 06 (security review).
- **Sonnet 5.5** for 01 and 02 (well-specified scaffolding, governance files and CI) and 07 (docs and packaging).

### Dependency graph
```
00 ──> 01 ──┬──> 02 ──┐
            └──> 03 ──┴──> 04 ──> 05 ──> 06 ──> 07
            (02 ∥ 03)
```

### Definition of done (checked in the final phase)
- [x] The Open WebUI model picker shows the local Ollama models **and** the allowlisted OpenRouter models (prefixed); picking either one gets a reply from that backend (verified in the live UI and in OpenRouter Activity for the dedicated key). *Evidence: Phase 05 live `status`; Nick's acceptance; key usage matches (final report §3).*
- [x] New chats still default to the local model; titles, tags and follow-ups are generated locally (ADR-0005 outcome). *Evidence: ADR-0005; findings §4; 1 upstream request per chat.*
- [x] With OpenRouter unreachable, local models still list and work; the measured model-list delay is recorded. *Evidence: findings §8.3: picker 0.12–0.13 s offline; local chat works.*
- [x] The configuration survives a container recreate on the same volume (`open-webui-upgrade` path) with no change to that script. *Evidence: findings §8.2; `tests/integration/test_hardening.py`.*
- [x] `owh-openrouter apply` is idempotent; `remove` restores the pre-apply values exactly (verified on the testbed). *Evidence: Phase 05 live no-op re-apply; Phase 04 testbed 403 rows restored.*
- [x] The key is in none of: the repo and its history (gitleaks clean), logs, `docker inspect`, shell history, process lists. *Evidence: findings §8.1: 0 hits; gitleaks no leaks (Phase 07).*
- [x] The dedicated key has a spending limit; the OpenRouter privacy settings match Nick's answer. *Evidence: key limit $50/month is Nick's on openrouter.ai (ADR-0018); privacy per ADR-0019.*
- [x] Docs current: README, user guide, SECURITY, `docs/OWH_ARCHITECTURE.md`, `docs/OWH_FINAL-REPORT.md` (with the generated timeline), CHANGELOG, OSMods (`Open WebUI.md` + README), vault note. *Evidence: README, user guide, SECURITY, architecture, final report, CHANGELOG 1.0.0, OSMods, vault note.*
- [x] Private GitHub repo `antonizick/OpenWebUI` up to date; every throwaway container, volume and test file removed. *Evidence: `gh repo view` PRIVATE; no `owh-test*` container or volume left.*

## Owner questions
| # | Question | Status / proposed default | Needed by |
|---|---|---|---|
| 1 | Which OpenRouter models go on the allowlist? | Answered 2026-11-13 12:16 CST: all five Phase 03 proposals plus three added by Nick, eight in total: `anthropic/claude-sonnet-5.5`, `anthropic/claude-haiku-5.5`, `google/gemini-4-hydrogen`, `openai/gpt-6.1-terra`, `google/gemma-4-31b-it:free`, `deepseek/deepseek-v4.1-flash-1017`, `xiaomi/mimo-v2.6-pro`, `z-ai/glm-5.3-flash` (ADR-0014; prices in `docs/OWH_FINDINGS.md` §7). Phase 05 writes them to `config/openrouter-models.txt` | Phase 05 |
| 2 | Spending limit for the new dedicated key | Answered 2026-11-13 12:45 CST: no limit from this project; spend is not managed at the application layer, and any limit on the key or account is Nick's on openrouter.ai (ADR-0018) | Phase 05 |
| 3 | OpenRouter account privacy: allow providers that log or train on prompts? | Answered 2026-11-13 12:45 CST: allow them (ADR-0019) | Phase 05 |
| 4 | Licence, if the repo is ever made public | Answered 2026-11-13 17:32 CST: MIT licence and a public repo (ADR-0024) | Phase 07 |

## Phase Log
Newest entries at the bottom. Format: `### YYYY-MM-DD HH:MM TZ: Phase NN: <title> (<status>)` (timestamp from `date '+%Y-%m-%d %H:%M %Z'`, never a bare date). **The first bullet is always the Timeline:** `- **Timeline:** started <TS> (claim commit <hash>) · finished <TS> · merged <TS | not merged yet>` (add ` · blocked <TS> to <TS>` per `⛔` interval; *started* is the claim commit's time). Then bullets: built, deviations, follow-ups, tests.

### 2026-11-13 11:20 CST: Planning: owner brainstorming (✅ Complete)
- **Timeline:** started 2026-11-13 10:03 CST · finished 2026-11-13 10:59 CST
- Nick's own pre-planning, recorded at his request (ADR-0008). Times are the two timestamped entries in `OWH_Brainstorming.md`: 10:03 CST (drafting a prompt for this capability with another AI) and 10:59 CST (the final request sent to Claude Code, quoted in spec §1).
- No repo or system changes; the output is the request that Phase 00 planned from.

### 2026-11-13 11:20 CST: Phase 00: Planning & spec refinement (✅ Complete)
- **Timeline:** started 2026-11-13 11:02 CST · finished 2026-11-13 11:24 CST
- Read `OWH_Brainstorming.md`, the OSMods notes `Open WebUI.md` and `AI Provider Switch.md`, `OpenRouter Analysis.md`, the user units and the live container/DB config (read-only). Found: Open WebUI v0.13.3 in Docker (host network, volume `open-webui`); a dead stored OpenAI connection (`api.openai.com`, empty key); background tasks run on the chat model (`task.model.external=""`).
- Owner decisions (one round): prefix `OWH`; a new dedicated OpenRouter key; a curated prefixed allowlist; configuration scripted via the admin API (ADR-0001…0004). Proposed ADR-0005 (local task model); planning defaults ADR-0006 (stdlib Python CLI), ADR-0007 (throwaway rehearsal), ADR-0008 (brainstorming in the timeline).
- Wrote spec with Amendments (A1–A4, R1–R9, S1–S7), ADR log, this plan (7 build phases), shared instructions, 7 phase prompts, `CLAUDE.md`, `/phase`, `/phase-add`, change-request template, vault note `02 Projects/OWH Implementation Plan.md`.
- Open questions: 1–3 needed by Phase 05; 4 deferred.
- No host system changes in Phase 00. Repo is local only until Phase 01 creates the private GitHub repo.

### 2026-11-13 11:42 CST: Phase 01: Repository foundation & governance (✅ Complete)
- **Timeline:** started 2026-11-13 11:40 CST (claim commit a9c405b) · finished 2026-11-13 11:42 CST · merged 2026-11-13 11:42 CST
- Built: README, LICENSE ("All rights reserved"), NOTICE, THIRD_PARTY_NOTICES, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT (by reference to Contributor Covenant 2.1), CHANGELOG, `.gitignore`, `.dockerignore`, `.editorconfig`, `.gitleaks.toml` (OpenRouter rule + `sk-or-v1-TESTKEY` allowlist), `scripts/git-hooks/pre-commit`, `.pre-commit-config.yaml`, `.github/` (CI with gitleaks-action pinned to commit SHA `e0c47f4` = v3.0.0 and checkout `3d3c42e` = v7.0.1, issue and PR templates, Dependabot for github-actions), `docs/OWH_ARCHITECTURE.md`.
- Deviation (ADR-0009): hook uses `gitleaks git --staged` (gitleaks 8.30.1 has no `protect`); it fails closed if gitleaks is missing.
- Key shape: the real key matches `^sk-or-v1-[0-9a-f]{64}$` (checked with `grep -c`, not printed), so the rule `{40,}` covers it.
- Tests: `gitleaks detect` over history: no leaks. Negative test: a staged file with a random `sk-or-v1-<64 hex>` made `git commit` fail with "leaks found: 1" (exit 1); a `sk-or-v1-TESTKEY…` file passed the hook; scratch files deleted, never committed. `shellcheck` (0.11.0, via its mise install path since the mise shim has no default version) is clean on `scripts/git-hooks/pre-commit`.
- `grep -rn '{'` hits only: `phase-add.md`, two phase prompts, `phase_timeline.py` f-strings and `${ secrets.GITHUB_TOKEN }` in `ci.yml` (all literal).
- Follow-ups: `shellcheck` shim has no global version set in mise (`mise use -g shellcheck@0.11.0`) — Phase 02's `make check` needs it on PATH; `core.hooksPath` must be set in any fresh clone; CI jobs for pytest/ruff arrive in Phase 02.
- No host OS changes (nothing outside the repo and the vault note, `git config core.hooksPath` is repo-local).

### 2026-11-13 11:46 CST: Phase 02: Tool scaffold & quality gates (✅ Complete)
- **Timeline:** started 2026-11-13 11:44 CST (claim commit 9eb5dff) · finished 2026-11-13 11:46 CST · merged 2026-11-13 11:46 CST
- **Model:** ran as Sonnet 5.5 (plan lists Sonnet 5.5)
- Built: `pyproject.toml` (hatchling, no runtime deps, dev group pytest + ruff, `uv.lock`), `src/owh_openrouter/` (`cli.py` with five stub subcommands exiting 2, `paths.py`, `secrets.py`, `allowlist.py` implemented; `webui.py`, `openrouter.py`, `snapshot.py` interface only), `tests/fakes/server.py` (fake Open WebUI and OpenRouter with request log, marked TODO(phase-04)), `Makefile` (`check`, `test`, `lint`, `install`, `uninstall`), CI jobs `python` and `shellcheck` (actions pinned by SHA; `astral-sh/setup-uv` v10.3.3 = `68559e9`), Dependabot `uv` ecosystem, empty `config/openrouter-models.txt`, ADR-0010 (launcher script install), dev licences in THIRD_PARTY_NOTICES.
- Deviation: ruff excludes the vendored `scripts/phase_timeline.py` (identical in every repo, must not be edited).
- Verified: `uv run owh-openrouter --help` lists all five subcommands; `pyproject.toml` has `dependencies = []`; `uv lock --check` clean.
- Tests: 31 passed (paths, redact, key-file permissions 0644/0640/0604/0666 refused and 0600 accepted, allowlist, CLI stubs, fakes smoke). `make check` green with shellcheck 0.11.0 and gitleaks (no leaks) on PATH.
- Follow-ups: the mise `shellcheck` shim still has no global version, so `make lint` fails in a plain shell until Nick runs `mise use -g shellcheck@0.11.0` (a host config change I did not make; I put the mise install dir on PATH for the check). CI result on GitHub is checked after the push. `make install` was not run; the launcher is an OSMods item for Phase 05.
- No host OS changes.

### 2026-11-13 12:10 CST: Phase 03: Verification spike (✅ Complete)
- **Timeline:** started 2026-11-13 11:51 CST (claim commit 879a1f8) · finished 2026-11-13 12:10 CST · merged 2026-11-13 12:10 CST
- **Model:** ran as Opus 5.5 (plan lists Opus 5.5)
- Built: `scripts/owh-testbed.sh` (`up|down|status|reset|token`), `docs/OWH_FINDINGS.md` (one section per task, with evidence and the Phase 04 consequence), ADR-0005 → Accepted, ADR-0011 (testbed on host network bound to 127.0.0.1), ADR-0012 (attribution headers, R9 corrected), ADR-0013 (key validation via `/api/v1/key`), spec Amendments v2 (§3.6), real-endpoint table in `docs/OWH_ARCHITECTURE.md`, owner question 1 proposal.
- Key findings:
  - `prefix_id` is stored as `"OR"` (Open WebUI adds the dot).
  - With `model_ids` set, Open WebUI never fetches OpenRouter's model list: about 0.1 s with the upstream closed, unroutable or slow, against 10.8–11.0 s without (`AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST`, default 10 s). No timeout tuning is needed.
  - `TASK_MODEL_EXTERNAL=qwen3:4b-instruct` keeps title, tags and follow-ups local. End-to-end, there was exactly 1 upstream request per chat.
  - The stored config beats env vars across a container recreate (except with `ENABLE_PERSISTENT_CONFIG=false`).
  - Omitting `ENABLE_OPENAI_API` in `config/update` silently disables all OpenAI connections. The tasks update needs the full object (a partial body is a 422).
  - OpenRouter `/models` returns 200 for invalid keys, so validation must use `/api/v1/key`.
  - Open WebUI always sends `HTTP-Referer`/`X-Title` to openrouter.ai.
- Deviations:
  - The testbed uses `--network host` with `HOST=127.0.0.1 PORT=18080`, because the bridge network could not reach Ollama on 127.0.0.1 (curl exit 28). This is the prompt's fallback plus a loopback bind (ADR-0011).
  - Spec R9 was wrong and is amended.
- Spend: $0.00 (public `/models` only, plus 401 probes with an all-zero fake key).
- Tests:
  - `shellcheck scripts/owh-testbed.sh` clean.
  - `down, down, up, up (no-op), status` ran twice in a row, then a final `down`; all idempotent.
  - `make check` green (31 passed, ruff, shellcheck, gitleaks no leaks).
  - Cleanup: no `owh-test*` container or volume, the fake servers are stopped, and `~/.local/state/owh/` is removed.
  - The live `open-webui` StartedAt was `2026-11-13T17:40:48.65503915Z` before and after, and its config was only read.
- Follow-ups:
  - Phase 04 aligns the fakes with the findings (listed in its prompt).
  - Phase 05 confirms the real `/api/v1/key` body (label, limit, `limit_reset`).
  - The picker shows raw IDs (`OR.anthropic/claude-sonnet-5.5`), not pretty names. Workspace Models could give friendly names later if Nick wants them (not in scope).
  - The mise `shellcheck` shim still needs `mise use -g shellcheck@0.11.0` (host config, not changed).
- No host OS changes. The testbed state dir was created and removed, nothing persists, and the live instance is untouched.

### 2026-11-13 12:37 CST: Phase 04: `owh-openrouter` CLI (✅ Complete)
- **Timeline:** started 2026-11-13 12:18 CST (claim commit 2bf3c35) · finished 2026-11-13 12:37 CST · merged 2026-11-13 12:37 CST
- **Model:** ran as Opus 5.5 (plan lists Opus 5.5)
- Built: the five commands, as specified, with exit codes 0–5 and a 0600 action log `~/.local/state/owh/owh.log`.
  - `set-key`: hidden prompt or `--from-file` (0600), whitespace trimmed, control characters rejected, format `^sk-or-v1-[0-9a-f]{64}$`, live `GET /api/v1/key` with 401/402/429 explained, atomic 0600 write, replace only on confirmation or `--force`.
  - `models`: `--search`, `--json`, $/M from per-token strings, `free`/`variable`.
  - `apply`: `--dry-run`, `--task-model`; R1 placement; snapshot before the first write; verify after.
  - `status`: `--json`, `--no-login`.
  - `remove`: `--snapshot`, `--delete-key`, `--yes`.
  - New modules `net.py` (no redirects, timeouts, scrubbed errors, loopback/https URL rules), `plan.py` (pure desired-state logic and redacted diff) and `errors.py`. The fakes are aligned with the findings (19-field task config with 422, `null` enable, OpenRouter error shape, public `/models`, failure injection).
  - ADR-0015 (surgical `remove`, snapshots tagged with the Open WebUI URL), ADR-0016 (secret handling), ADR-0017 (keep hand-made settings). First `docs/OWH_USER-GUIDE.md` draft.
- Deviations:
  - `remove` restores only what OWH changed (its slot, `ENABLE_OPENAI_API`, `TASK_MODEL_EXTERNAL`), not the whole snapshot, so connections added later survive (ADR-0015).
  - Snapshots carry `webui_url`. This was found while checking the Phase 05 prompt: a testbed rehearsal shares `~/.local/state/owh/`, so its snapshot would otherwise have been the "earliest" one for the live `remove`.
  - Added `--password-stdin` (admin password, one line on stdin) for the rehearsal and tests (ADR-0016).
  - Dev dependency `pytest-cov` (MIT; `coverage` Apache-2.0).
  - The Phase 05 prompt is corrected: global options go before the command, and the rehearsal uses `--password-stdin < admin-password`.
- Tests:
  - `make check` green: 147 passed, 1 skipped (the testbed test), coverage 96.8 % (gate 90 %), ruff, shellcheck 0.11.0, gitleaks no leaks.
  - Error paths covered: bad key formats incl. `TESTKEY` and escape codes, 401/402/429, unreachable Open WebUI or OpenRouter, wrong password, non-admin, idempotence, snapshot before the first write (a failed first write gives exit 4 with the snapshot present), partial failure exit 5 then `remove` repairs it, verify mismatch exit 5, unknown allowlist ID, empty allowlist, remote URL refused, plain-http OpenRouter refused, foreign snapshot refused.
  - A lifecycle secret audit checked every output line and the log. The key reaches Open WebUI only in `POST /openai/config/update` and OpenRouter only as the `Authorization` header of `GET /api/v1/key`. The password goes only to sign-in.
  - **Testbed:** `OWH_TESTBED=1 uv run pytest -m testbed` passed three times: twice at 12:30 CST (the first run also showed a collection error from a helper named `testbed`, since renamed) and once at 12:34–12:35 CST after the snapshot change (1 passed, 40.7 s). Output: "403 config rows restored byte-for-byte (key, value); 5 local + 2 OR models listed; 1 chat reached the fake". The sequence was apply → `/api/models` shows `OR.vendor/model-a`, `OR.vendor/model-b:free` next to the Ollama models → a chat through `OR.vendor/model-a` reached the fake as `vendor/model-a` with the key → `status --json` → a no-op re-apply left the rows identical → `remove` restored all 403 `config` rows.
  - A real OpenRouter public list (12:32 CST, $0) knows all eight ADR-0014 IDs. Prices match ADR-0014, and MiMo is $0.435/M in.
- Cleanup: no `owh-test*` container or volume is left, `~/.local/state/owh/` was removed, and the live `open-webui` StartedAt is `2026-11-13T17:40:48.65503915Z` before and after; it was never contacted.
- Spend: $0.00.
- Follow-ups:
  - The mise `shellcheck` shim still needs `mise use -g shellcheck@0.11.0` (host config, not changed; this run put the install dir on PATH).
  - `owh-testbed.sh down` leaves an empty `~/.local/state/owh/` behind (it removes only `testbed/`). It is harmless, but Phase 06 could tidy it.
  - Snapshots hold prior keys and are never pruned. Phase 06 should decide on retention.
  - `status --no-login` can show only version, key file, key info and snapshots, because the task and model endpoints need a session.
  - Phase 05 records the real `/api/v1/key` fields.
- No host OS changes (`make install` is Phase 05).

### 2026-11-13 13:25 CST: Phase 05: Rehearsal & live deploy (✅ Complete)
- **Timeline:** started 2026-11-13 12:43 CST (claim commit 0efb977) · finished 2026-11-13 13:25 CST · merged 2026-11-13 13:25 CST
- **Model:** ran as Opus 5.5 (plan lists Opus 5.5)
- **Nick's acceptance (in session):** "both backends work, local and OpenRouter chats answered".
- Owner questions answered 2026-11-13 12:45 CST: Q2 no spend management in OWH; any limit is Nick's on openrouter.ai (ADR-0018). Q3 allow logging/training providers (ADR-0019). Spec Amendments v3. Phase 06 prompt (spend guard) adjusted.
- Built and done:
  - `config/openrouter-models.txt` = the eight ADR-0014 IDs; `owh-openrouter models` showed all known with prices.
  - Dedicated key set by Nick with `set-key`: `~/.config/owh/openrouter.key` 0600 (dir 0700), different from the ai-provider key, whose mtime (2026-10-17 11:28:08) is unchanged. `/api/v1/key`: limit 50, `limit_reset` monthly, **`expires_at` 2027-11-13**; all fields in `docs/OWH_FINDINGS.md` §6a.
  - `make install` from the main checkout: `~/.local/bin/owh-openrouter`, works from a new login shell.
  - Rehearsal on the testbed with the real key: apply → 13 models (5 local, 8 `OR.`) → one chat on `OR.z-ai/glm-5.3-flash` replied "OK" ($0.00000766) → Ollama logged 3 `POST /api/chat` (title, tags, follow-ups) and the key's usage equalled that one chat → re-apply no-op → `remove` restored the empty `api.openai.com` entry and task model `''` → `down` (no container or volume left).
  - Backup: `~/.local/share/open-webui-backups/webui.db.20261113-125838.pre-owh.bak` (0600, integrity ok, 403 config rows, 31 chats).
  - Live (Nick in a terminal): `apply --dry-run` (diff identical to the rehearsal), `apply` at 13:03 CST (snapshot `~/.local/state/owh/snapshots/20261113T190320.791540Z.json`, tagged `http://127.0.0.1:8080`), second `apply` "already up to date; nothing written", `status`: connection 0 OpenRouter, prefix OR, 8 allowlisted, task model `qwen3:4b-instruct`, 8 OpenRouter + 5 local models. Container not restarted (StartedAt `2026-11-13T17:40:48.65503915Z` throughout).
  - UI: Nick's OpenRouter chat on `OR.z-ai/glm-5.3-flash` (two turns) got a locally generated title; key usage $0.0173995 = rehearsal + those two turns exactly, so no background task went to OpenRouter.
  - OSMods: `Open WebUI.md` (new section "OpenRouter models (OWH, 2026-11-13 13:05 CST)", corrected "everything stays local", container config and models) and `OSMODs README.md` (at a glance, section 5, where things live, last updated).
- Deviations:
  - `!` has no TTY: the first `set-key` crashed in `getpass` (EOFError, nothing read or written). Fixed: hidden prompts refuse with exit 3 and a hint (ADR-0020, 4 new tests). Nick ran every prompting command in a separate terminal; the Phase 05 prompt and user guide are corrected.
  - Backup through SQLite's backup API instead of `docker cp webui.db`, because the DB is in WAL mode with recent writes in `-wal` (ADR-0020).
  - `owh-testbed.sh`: the cold start (≈1.1 GB embedding download) took ≈150 s, over the 120 s wait, and the rerun skipped admin creation. Now 300 s, and `ensure_admin` runs on an existing container too.
  - Live `apply` ran from the worktree (`uv run --project …-phase-05`), since the launcher points at the main checkout, which lacked the allowlist and fix until this merge.
  - The shipped-allowlist test now pins the eight IDs.
- Spend: build tests $0.0000077 (rehearsal). Nick's own UI check $0.0174. Total key usage $0.0173995 (≤ $0.25).
- Tests: `make check` green: 151 passed, 1 skipped, coverage 96.8 %, ruff, shellcheck, gitleaks no leaks. Rehearsal transcript and live outputs as above.
- Follow-ups (Phase 06 prompt notes added): key expiry warning or rotation reminder before 2027-11-13; `status` shows the masked `label` awkwardly; the rehearsal snapshot (testbed URL, holds the key) sits next to the live one, so include it in snapshot retention; a benign Ollama 500 at 13:07:43 was a client-cancelled request.
- Host OS changes: `~/.local/bin/owh-openrouter`, `~/.config/owh/`, `~/.local/state/owh/`, the pre-OWH backup, and Open WebUI's stored config (connection 0, `TASK_MODEL_EXTERNAL`). All documented in OSMods. **Undo:** `owh-openrouter remove [--delete-key]`, `make uninstall`, revoke the key; or restore the backup.

### 2026-11-13 13:51 CST: Phase 06: Hardening, security & QA (✅ Complete)
- **Timeline:** started 2026-11-13 13:38 CST (claim commit 2a6aef1) · finished 2026-11-13 13:51 CST · merged 2026-11-13 13:51 CST
- **Model:** ran as Opus 5.5 (plan lists Opus 5.5)
- **Nick's decision (in session):** S6 port 8080: "Keep as is, documented" (ADR-0021). He was offered B (bind to `127.0.0.1`) and C (`ufw deny 8080`).
- Built:
  - `docs/OWH_THREAT-MODEL.md`: assets, trust boundaries, every key store with its permissions, threats T1–T13, the S6 options table, a code review for leaks, residual risks.
  - `docs/OWH_FINDINGS.md` §8: sweep, R2, R5, 402, exposure.
  - `tests/integration/test_hardening.py`.
  - Key-expiry warning in `set-key`/`status` and `label` dropped (ADR-0023, 9 new unit tests).
  - Fake OpenRouter `expires_at` and `chat_status`.
  - `owh-testbed.sh down` removes an empty `~/.local/state/owh/`.
  - ADR-0021…0023, spec Amendments v4, dev licence audit (all permissive, matches THIRD_PARTY_NOTICES), and SECURITY / user guide / README / architecture / CHANGELOG / Phase 07 prompt updates.
- **Secret sweep** (counts only; the pattern was passed through an fd, never argv):
  - The OWH key is only in `~/.config/owh/openrouter.key` (0600/0700) and 1 row of the live `webui.db`. That was read with a `--network none` throwaway container with the volume mounted `:ro`; no other table or file.
  - 0 hits in: git history, working trees, `~/Documents`, `~/.bash_history`, `docker inspect`, `docker logs`, the journal, the process list, snapshots, `owh.log`, and the upgrade and manual backups (all pre-OWH).
  - Phase 05's "snapshots contain the key" was wrong: they hold the prior config, which had no key.
- **R2:** testbed recreate with `open-webui-upgrade`'s own `make_recipe`/`create_from_recipe` (sourced from the script). New container healthy in 20 s, 5 OWH rows byte-identical, `status` identical (8 OR, 5 local, task model local). The script's `run_test` checks don't involve the OpenAI connection.
- **R5** (real 8-ID allowlist): `/api/models` was 0.12 s healthy, 0.13 s with the port closed and 0.12 s unroutable (Phase 03: 0.10–0.11 s). A local `qwen3:4b-instruct` chat took 3.02 s with OpenRouter unroutable; an `OR.` chat with the port closed failed with HTTP 500 in 0.04 s.
- **Spend guard:** OWH manages no spend (ADR-0018); the key reports `limit` 50, `limit_reset` monthly. A simulated 402 reaches the user as HTTP 402 with the upstream message, in 0.03 s.
- Host changes: deleted the stale testbed rehearsal snapshot `~/.local/state/owh/snapshots/20261113T185705.631666Z.json` (no key, `webui_url` :18080, ADR-0022). Nothing else. The live container was stopped throughout (Nick stopped it at 13:37 CST, before this phase) and was not started; the firewall was not touched.
- Spend: $0.00 (fake upstream only).
- Tests: `make check` green: 161 passed, 2 skipped, coverage 96.9 %, ruff, shellcheck 0.11.0 (mise install dir on PATH), gitleaks no leaks. `OWH_TESTBED=1 uv run pytest -m testbed`: 2 passed in 206.8 s. No `owh-test*` container or volume left.
- Follow-ups (each with an owner or a deferral reason):
  - **Nick:** `~/.bash_history` has the AI Provider Switch key on an `ai-provider set-key` line. Remove the line and consider rotating that key. Out of OWH's scope; not touched.
  - **Nick (optional):** two 2026-11-09 manual backups in `~/.local/share/open-webui-backups/` are 0644 (the dir is 0700). `chmod 600` them; they are not OWH's files.
  - **Nick (host config, deferred since Phase 01):** `mise use -g shellcheck@0.11.0` so `make lint` works in a plain shell.
  - Deferred, accepted: Tailscale reachability of 8080 could not be checked without root (ADR-0021 residual).
  - Closed: `status --no-login` cannot show connections (Open WebUI needs a session), by design. Friendly picker names are a new feature, not in scope (use `/phase-add` if wanted). An `ENABLE_PERSISTENT_CONFIG` warning is not detectable through the API; T11 documents it, nothing sets it, and the R2 test would catch it. The Phase 05 Ollama 500 was benign.

### 2026-11-13 17:32 CST: Phase 07: Release & handover (✅ Complete)
- **Timeline:** started 2026-11-13 17:27 CST (claim commit 01eb9f7) · finished 2026-11-13 17:32 CST · merged 2026-11-13 17:32 CST
- **Model:** ran as Sonnet 5.5 (plan lists Sonnet 5.5)
- **Nick's decisions (in session):** release option "Make public"; licence MIT (owner question 4 answered, ADR-0024).
- Built: final `docs/OWH_USER-GUIDE.md` (daily use, add or remove a model, spend, troubleshooting table, full undo); `docs/OWH_FINAL-REPORT.md` (what was built, ADRs, Definition-of-done evidence, spend, residual risks, open items, generated timeline block); Definition of done ticked with evidence (all nine items met, none became a follow-up); README (status, licence), CHANGELOG `[1.0.0]`, OSMods `Open WebUI.md` and README, vault note.
- Public-release prep (ADR-0024): LICENSE is MIT, NOTICE and CONTRIBUTING updated; the Wi-Fi LAN and Tailscale addresses and the admin e-mail were removed from the current docs. Git history still holds them (not rewritten). gitleaks over all history: no leaks; no key, DB, `.env` or backup tracked.
- Spend: $0.00 (docs only; build total on the key $0.0173995).
- Tests: `make check` green: 161 passed, 2 skipped, coverage 96.9 %, ruff, shellcheck, gitleaks no leaks. No testbed run (no code changed).
- Follow-ups for Nick (not OWH's): remove the AI Provider Switch key line from `~/.bash_history` and consider rotating that key; optional `chmod 600` of two old manual backups; `mise use -g shellcheck@0.11.0`; rotate the OWH key before 2027-11-13.
- No host OS changes beyond the OSMods text. No GitHub release was created.
