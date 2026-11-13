# OWH Phase 05: Rehearsal & live deploy

**Model:** Opus 5.5 (`/model opus`) · **Depends on:** 04 · **Branch:** `phase-05-rehearsal-and-live-deploy` · **Gate:** owner

**Nick must be present:** he creates the key, types the key and the admin password at hidden prompts, and checks the UI. Never run this phase in hands-off mode.

## Read first
`CLAUDE.md`, `prompts/OWH_shared-instructions.md`, spec §3 (all), `docs/OWH_FINDINGS.md`, `docs/OWH_USER-GUIDE.md`, the OSMods notes `/home/nick/Documents/04 Resources/OSMods/OSMODs README.md` and `Open WebUI.md`. Phase Log entries for 03 and 04. **Owner questions 1, 2 and 3 must be answered before Task 3; if any is still open, stop and ask Nick.**

## Goal
The live Open WebUI offers the local Ollama models and the allowlisted OpenRouter models side by side, each chat going to the right backend, with a dedicated, spend-limited key; fully documented and reversible.

## Tasks
1. **Answers.** Question 1 was answered 2026-11-13 12:16 CST (ADR-0014: eight model IDs, listed in the Owner questions row). Ask Nick for questions 2–3 if still open. Record each answer with a timestamp in the plan (`Answered <TS>: …`) and as ADRs. Write the confirmed IDs into `config/openrouter-models.txt` and run `uv run owh-openrouter models` (all known, prices shown).
2. **Key.** Nick creates a new key on openrouter.ai named e.g. "Open WebUI (laptop)" with the agreed limit and applies the privacy settings (Q3). Then he runs `uv run --project /home/nick/Work/OpenWebUI owh-openrouter set-key` himself **in a separate terminal window** (hidden prompt; Claude Code's `!` has no terminal, so the CLI refuses there, corrected 2026-11-13 13:05 CST). Confirm with redacted output only. Confirm the ai-provider key file was not touched (`stat` mtime unchanged).
3. **Install.** `make install`; `owh-openrouter --help` works from a new shell.
4. **Rehearsal** on the testbed with the **real** key and real OpenRouter: `owh-testbed.sh up`, then `owh-openrouter --webui-url http://127.0.0.1:18080 apply --email owh-test@localhost --password-stdin < ~/.local/state/owh/testbed/admin-password` (global options go **before** the command; the password never reaches argv), one chat with the cheapest allowlisted model (prompt "Reply with the word OK.", spend < $0.01), confirm in `/api/models` and the reply; title generated locally (per ADR-0005 evidence method); `owh-openrouter --webui-url http://127.0.0.1:18080 remove --email owh-test@localhost --password-stdin < …`; `down`. The rehearsal's snapshot stays in `~/.local/state/owh/snapshots/`, tagged with the testbed URL; the live `remove` ignores it (ADR-0015). `make test-testbed` (fake OpenRouter) passed in Phase 04 and can be re-run first as a smoke test.
5. **Backup** the live DB, local only, as a consistent copy through SQLite's backup API (the DB is in WAL mode, so a plain `docker cp` of `webui.db` misses recent writes; commands in `docs/OWH_USER-GUIDE.md`), to `~/.local/share/open-webui-backups/webui.db.<stamp>.pre-owh.bak` (chmod 0600). The live container must be running for `apply`; if it is stopped, ask Nick to start it with `open-webui-start` (silent) rather than the toggle.
6. **Live apply.** `owh-openrouter apply --dry-run` (show Nick the redacted diff), then `apply` (Nick types the e-mail and password at the prompts in a separate terminal window, not through `!`). Then `status`. The real `GET /api/v1/key` body (label, limit, `limit_reset`) is shown by `set-key` and `status`; record which fields it has in `docs/OWH_FINDINGS.md`.
7. **Verify with Nick in the UI** (http://localhost:8080): the picker shows local models (incl. the default `Qwen3 8B (Web)`) and the prefixed OpenRouter models; a new chat defaults to local; one chat on a local model and one on an OpenRouter model both answer; OpenRouter Activity shows the call under the new key; the chat title of the OpenRouter chat was generated locally. Record what was checked and the spend.
8. **OSMods documentation** (mandatory, same session): update `Open WebUI.md`: new section "OpenRouter models (OWH, <TS>)" (what, why, how to use, files and paths incl. the key file, snapshots, launcher, where the key also lives per S3, how to add/remove models, rotate the key, undo with `owh-openrouter remove` or restore the pre-owh DB backup); correct "Everything stays local except web-search queries" to state that chats with `OR.` models go to OpenRouter (S4); update the "Container configuration" and "Models" sections. Update `OSMODs README.md` (at-a-glance table, section 5, "Where things live", "Last updated"). Cross-link `[[AI Provider Switch]]` (separate key, shared account credit).

## Out of scope
Threat model, upgrade-survival and offline tests (Phase 06); container env changes of any kind.

## Tests
`make check`; the rehearsal transcript; `owh-openrouter status` on the live instance; a second `apply` on live is a no-op.

## Acceptance criteria
- Nick confirms in-session that both backends work from the picker (quote him in the Phase Log).
- Live `status` shows the OpenRouter connection with the allowlist and the local task model; re-apply is a no-op.
- Pre-OWH DB backup exists (0600, outside `~/Documents`); snapshot exists in `~/.local/state/owh/snapshots/`.
- OSMods `Open WebUI.md` and README updated; total OpenRouter spend in this phase recorded (≤ $0.25).

## Phase-specific docs
`docs/OWH_USER-GUIDE.md` (final steps as actually run), README, CHANGELOG, ADRs for Q1–Q3 answers, OSMods notes, vault note. Then the standard close-out checklist.
