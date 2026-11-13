# Shared Instructions for Every Phase

Read this file in full before starting any phase. Each phase prompt assumes it.

**Phase IDs.** `NN` in this file is the phase ID: two digits, optionally with a lower-case letter suffix for a phase inserted after another one with `/phase-add` (`09a`, `15a`, `15b`…). An inserted phase is a normal phase with its own claim, branch and worktree; `15a` sorts after `15` and before `16`.

## 1. Orientation and claim (every phase, before writing code)
1. Read `CLAUDE.md`, `OWH_IMPLEMENTATION_PLAN.md` (including the Phase Log and Owner questions) and the spec sections named in your phase prompt. Always read the Amendments.
2. Confirm that every phase listed under "Depends on" is `✅ Complete`. If one is not, stop and tell Nick.
3. Read the Phase Log entries of the dependency phases; they may record deviations that change what you build.
4. If an owner question this phase needs is still open, ask Nick before doing the affected work. (Hands-off mode: block-with-question, §1b.)
5. **Claim the phase on `main`** by following §1a. This is the first file change of every phase session. Do not start the Tasks until the claim is verified.
6. If the prompt is ambiguous or contradicts the spec, prefer the spec's Amendments. If it is still unclear, ask Nick before guessing on anything user-visible or hard to reverse. (Hands-off mode: block-with-question, §1b.)

## 1a. Claiming a phase (mandatory; other agents may be running in parallel)
Nick and other agents read the Status column from `main`. A status change made only on a phase branch, or left uncommitted in a worktree, is invisible to them. So every phase is claimed with a commit on `main` **before** any other work.
1. In the main checkout (`/home/nick/Work/OpenWebUI`), check that `git branch --show-current` prints `main` and that `git status --short OWH_IMPLEMENTATION_PLAN.md` prints nothing. If either check fails, stop and tell Nick. Never commit another agent's uncommitted changes.
2. Look for an existing claim: the phase's row on `main`, `git branch --list 'phase-NN-*'` and `git worktree list`. If the row is already `🔄 In progress`, or a branch or worktree exists, do not claim again; follow the resume rules in `/phase`.
3. Set the phase's Status cell to `🔄 In progress`, then commit **only that file** to `main`: `git commit -m "chore(plan): start phase NN" -- OWH_IMPLEMENTATION_PLAN.md`.
4. In the Obsidian project note, set the phase's row to `🔄 In progress`, update its `updated:` field and add a timestamped log line: "Phase NN started (claim commit `<hash>`, branch `phase-NN-<slug>`, worktree `../OpenWebUI-phase-NN`)".
5. Create the worktree and branch from that commit: `git worktree add ../OpenWebUI-phase-NN -b phase-NN-<slug> main`, then install the project's dependencies inside it if it has any. Do all of the phase's work in the worktree, using absolute paths or `cd <worktree> && …` in every command, because the shell may reset to the main checkout between commands. Never switch the main checkout off `main`: other agents commit their claims there.
6. Verify: `git show main:OWH_IMPLEMENTATION_PLAN.md | grep '^| NN '` must show `🔄 In progress`.

If the phase ends `⛔ Blocked`, commit that status to `main` the same way (`chore(plan): phase NN blocked`) so that `main` doesn't show a stale `🔄`. A `✅ Complete` status reaches `main` through the merge.

## 1b. Hands-off mode: block-with-question (PhaseHypervisor contract 1)
Applies only in hands-off mode (`/phase NN --auto` or `PHX_AUTO=1`, set only by PhaseHypervisor); manual sessions ignore this section. Wherever a manual session would ask Nick (an open owner question this phase needs, an ambiguity you must not guess, the risk rule in `CLAUDE.md`, or a failure you cannot fix within scope), do this instead, then end the session:
1. In the worktree, commit all work on the phase branch: `wip(phase-NN): blocked, <short reason>`. Do not merge; keep the branch and worktree.
2. In the main checkout, in `OWH_IMPLEMENTATION_PLAN.md`:
   - add an Owner questions row `| <next #> | <question> | Open (asked <TS>, Phase NN, auto mode). Proposed default: <default> | Phase NN |` (or, for an existing open question, name this phase in its Status cell and keep it `Open`);
   - set the phase's Status to `⛔ Blocked`;
   - add a Phase Log entry `### <TS>: Phase NN: <title> (⛔ Blocked)` with bullets: `- **Timeline:** started <claim TS> (claim commit <hash>) · blocked <TS> to (open)`, then `- **Model:** …`, then `- **Question:** #<id>: <question>`, then what is done, what remains and where to resume.
3. Commit only that file to `main`: `git commit -m "chore(plan): phase NN blocked" -- OWH_IMPLEMENTATION_PLAN.md`, and push `main` if a remote exists.
   Then refresh the timeline on `main` (§4a) in its own commit, `docs(plan): refresh timeline`.
4. In the Obsidian note: row `⛔ Blocked`, `updated:` field, and a timestamped log line naming the question.
5. Final message: what was done, the question and its proposed default, then the `PHX-RESULT` line with `"status":"blocked"` and the question IDs (see `/phase`).

A question is **open** while its Status cell starts with `Open`; `Answered …`, `Decided …` and `Deferred …` are not open.

**Resuming** a `⛔ Blocked` phase in hands-off mode: if a question needed by it is still open, refuse without changing anything. Otherwise set the row to `🔄 In progress`, change `blocked <TS> to (open)` to `blocked <TS> to <TS now>` in its Timeline, commit only the plan file to `main` (`chore(plan): resume phase NN`), refresh the timeline on `main` (§4a) as `docs(plan): refresh timeline`, update the Obsidian note, then run `git merge main` in the worktree, read the answer and continue as a normal resume.

## 2. Target repository layout (evolves; keep `docs/OWH_ARCHITECTURE.md` in sync)
```
OpenWebUI/
├── CLAUDE.md, README.md, LICENSE, NOTICE, SECURITY.md, CONTRIBUTING.md,
│   CODE_OF_CONDUCT.md, CHANGELOG.md, THIRD_PARTY_NOTICES.md      (not prefixed)
├── OWH_IMPLEMENTATION_PLAN.md                                   (prefixed)
├── OWH_Brainstorming.md                                         (owner's source note; do not edit)
├── Makefile                      install / uninstall / test / lint (Phase 02+)
├── pyproject.toml, uv.lock       (Phase 02)
├── .gitignore, .dockerignore, .editorconfig, .pre-commit-config.yaml (gitleaks)
├── .github/                      CI (pytest, ruff, shellcheck, gitleaks), templates, Dependabot
├── .claude/commands/phase.md, phase-add.md
├── config/openrouter-models.txt  allowlist, one OpenRouter model ID per line (Phase 04/05)
├── src/owh_openrouter/           the CLI package (Phase 02 skeleton, Phase 04 real)
├── tests/                        pytest; fakes/ = fake Open WebUI and fake OpenRouter servers
├── scripts/
│   ├── phase_timeline.py         timeline generator (identical in every repo; do not edit here)
│   └── owh-testbed.sh            throwaway Open WebUI container up/down (Phase 03)
├── docs/
│   ├── OWH_SPECIFICATION.md, OWH_DECISIONS.md, OWH_TIMELINE.svg   (prefixed)
│   ├── OWH_ARCHITECTURE.md, OWH_FINDINGS.md, OWH_USER-GUIDE.md,
│   │   OWH_THREAT-MODEL.md, OWH_FINAL-REPORT.md                   (prefixed, added by phases)
└── prompts/OWH_shared-instructions.md, OWH_phase-NN-<slug>.md, OWH_change-request-template.md (prefixed)

Outside the repo (never committed):
~/.config/owh/openrouter.key      dedicated key, dir 0700 / file 0600
~/.local/state/owh/               pre-apply snapshots (0600, contain the key), owh.log (no secrets)
~/.local/bin/owh-openrouter       installed launcher (make install)
```

## 3. Conventions
- **Prefix.** Project documents carry the project prefix `OWH_` (see `CLAUDE.md`). New project-specific documents follow the same rule; convention-bound files (`README.md`, `LICENSE`, `CHANGELOG.md`, `CLAUDE.md`…) keep their names.
- **Timestamps, not dates.** Every place that records when (Phase Log, ADRs, amendments, owner questions, vault log, "Last updated", changelog release headings) uses `YYYY-MM-DD HH:MM TZ`. Run `date '+%Y-%m-%d %H:%M %Z'` when you write each one; do not guess or copy an earlier timestamp.
- **Never touch the live Open WebUI before Phase 05.** Phases 03 and 04 use only the throwaway testbed (`scripts/owh-testbed.sh`: container `owh-test-owu`, volume `owh-test-owu-data`, image `ghcr.io/open-webui/open-webui:v0.13.3`, published on `127.0.0.1:18080` only). Read-only inspection of the live container/DB is allowed (`mode=ro` SQLite URI, `docker inspect`, `GET` endpoints). Remove every testbed container and volume you create before close-out.
- **Never start, stop or restart the live `open-webui` or `prometheus-ollama` units** outside Phase 05, and in Phase 05 only as its prompt says. Never use `open-webui-toggle` (it speaks aloud).
- **Secrets (spec S1–S3).** The OpenRouter key and the admin password are read only from a hidden prompt (`getpass`) or the 0600 key file; never in argv, env exported to children, logs, test fixtures, commit messages or chat output. Tests use obviously fake keys (`sk-or-v1-TESTKEY…`). Print at most the first 9 characters and the length.
- **Never fabricate external facts** (model IDs, prices, endpoint shapes, version numbers). Check them against the live API or the real software and cite where they came from in `docs/OWH_FINDINGS.md`.
- **Spend.** Live OpenRouter calls in any phase use only cheap models and tiny prompts; total spend per phase ≤ $0.25 unless Nick agrees otherwise. Record what was spent.
- Python ≥ 3.11, stdlib only at runtime; type hints; `ruff` formatting; Conventional Commits.
- Host OS changes (files in `~/.local/bin`, `~/.config`, units, Open WebUI settings) are documented in `/home/nick/Documents/04 Resources/OSMods/` (read `OSMODs README.md` first; the existing entry is `Open WebUI.md`).

## 4. Phase close-out checklist (all items required)
- [ ] All acceptance criteria in the phase prompt are met, with a short verification note for each.
- [ ] Tests, lint and type checks pass: `make check` (= `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `shellcheck scripts/*.sh`, `gitleaks detect --no-banner`). Before Phase 02 lands, `gitleaks detect --no-banner` and `shellcheck` on any shell file.
- [ ] `OWH_IMPLEMENTATION_PLAN.md`: Status set (`✅ Complete` or `⛔ Blocked`, icon plus word; a `⛔ Blocked` status is also committed to `main` per §1a), Phase Log entry added (timestamp, summary, deviations, follow-ups, test counts).
- [ ] **Timeline bullet written** as the first bullet of the Phase Log entry: *started* = the claim commit's time (`git log -1 --format=%cd --date=format-local:'%Y-%m-%d %H:%M %Z' <claim hash>`), *finished* = `date '+%Y-%m-%d %H:%M %Z'` taken as the last step before the final commit, *merged* = the merge time or `not merged yet`, plus `blocked <TS> to <TS>` for any `⛔` interval. Never reuse an earlier timestamp.
- [ ] `CHANGELOG.md` `[Unreleased]` updated (a release heading carries a timestamp, not just a date).
- [ ] README, SECURITY, `OWH_ARCHITECTURE`, guides, THIRD_PARTY_NOTICES, ignore files updated where affected.
- [ ] ADR added for any notable choice (timestamped in both the entry and its row in the index table at the top of `docs/OWH_DECISIONS.md`); spec amendment added if the spec changed.
- [ ] Later phase prompts corrected if your work changed their assumptions.
- [ ] Obsidian project note updated (status icons, `updated:` field and a timestamped log line).
- [ ] OS-modification log (`/home/nick/Documents/04 Resources/OSMods/`) updated if the host system was modified.
- [ ] Work committed on the phase branch. Once the phase is `✅ Complete` and every check passes, merge it into `main` without asking (fast-forward where possible), from the main checkout. Conflicts in `OWH_IMPLEMENTATION_PLAN.md` and the changelog are expected when phases ran in parallel: keep every row and entry from both sides, and use the branch's final status for this phase's row. Then push `main` if a remote exists (create a **private** GitHub repo if the plan calls for one), `git worktree remove ../OpenWebUI-phase-NN` and `git branch -d phase-NN-<slug>`. Do not merge a `⛔ Blocked` phase or one with failing checks. Making a repo public or publishing a release needs Nick's explicit confirmation (hands-off mode: block-with-question, §1b).
- [ ] **Timeline refreshed on `main`** after the merge (§4a), committed as `docs(plan): refresh timeline` and pushed.
- [ ] Final message to Nick: what was built, how to try it, what's next, and any open questions. In hands-off mode, its last line is the `PHX-RESULT` line (see `/phase`).

## 4a. Visual timeline (`scripts/phase_timeline.py`)
The plan's `## Timeline` block, `docs/OWH_TIMELINE.svg`, the vault note's timeline and the final report's timeline (once it exists) are generated. Refresh them **only on `main`, never on a phase branch**, so parallel branches never conflict over them:
`python3 scripts/phase_timeline.py --write --vault-note "/home/nick/Documents/02 Projects/OWH Implementation Plan.md"`, then commit the plan, the SVG and the final report (if present) together: `docs(plan): refresh timeline`.
- When: after the merge at close-out, after the `⛔` commit (§1b) and after the resume commit. The claim commit stays status-only, but refresh in its own `docs(plan): refresh timeline` commit right after it so the running phase shows at once. Under `phx` the supervisor also does this itself while a phase runs, so a miss here is repaired.
- If the block or the SVG ever conflicts, take either side and re-run `--write`; never merge it by hand.
- `python3 scripts/phase_timeline.py --check` exits 1 when the outputs are stale (right after a claim this is expected).

