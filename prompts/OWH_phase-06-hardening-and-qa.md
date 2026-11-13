# OWH Phase 06: Hardening, security & QA

**Model:** Opus 5.5 (`/model opus`) · **Depends on:** 05 · **Branch:** `phase-06-hardening-and-qa` · **Gate:** review

## Read first
`CLAUDE.md`, `prompts/OWH_shared-instructions.md`, spec §3.3 (S1–S7) and R2, R5, `docs/OWH_FINDINGS.md`, SECURITY.md. Phase Log entries for 03, 04 and 05, and every follow-up recorded in the Phase Log.

## Goal
Evidence that the deployed setup is safe, survives upgrades and network loss, and costs only what Nick expects; every follow-up closed or explicitly deferred.

## Tasks
1. `docs/OWH_THREAT-MODEL.md`: assets (key, chats, admin account), trust boundaries (laptop / OpenRouter / upstream providers), where the key is stored (key file, `webui.db`, upgrade backups, manual backups, snapshots), threats and mitigations, residual risks. Include S6: assess port 8080 on all interfaces under host networking now that a paid key sits behind the login; **recommend** options (firewall rule, binding) to Nick with an Option | Pros | Cons table; apply nothing to the live container or firewall without his explicit yes (ADR either way).
2. **Secret sweep** (print only file names and counts, never matches): gitleaks over full git history; search for the key prefix in `~/.local/state/owh/owh.log`, `~/.bash_history`, `~/.local/state/open-webui-toggle.log`, `docker inspect open-webui`, `docker logs open-webui` (since OWH apply), the repo, and `~/Documents` (must be 0 hits outside expected stores). Check permissions of every expected store.
3. **Upgrade survival (R2)** on the testbed: `up` → `apply` (fake or real key; real only with cheap verify) → recreate the container on the same volume with the same recipe `open-webui-upgrade` uses (read the script: `~/.local/bin/open-webui-upgrade`; do not run it against the live instance) → `status` unchanged → `down`. Also confirm by reading the script that its post-upgrade checks do not depend on the OpenAI connection.
4. **Offline (R5)** on the testbed with the real allowlist: disconnect the upstream (point at a closed port, or `docker network disconnect` for the bridge testbed), measure `/api/models` time and that local chat works; record against the Phase 03 numbers.
5. **Spend guard**: confirm via the key-info endpoint (redacted) that the key's limit equals Nick's answer to Q2; document what the user sees in Open WebUI when the limit or account credit is exhausted (from findings/docs; do not exhaust it for real).
6. **Code QA**: coverage ≥ 90 %, ruff, shellcheck, dependency licence audit (dev deps only) → THIRD_PARTY_NOTICES; review `owh-openrouter` for error paths that could leak secrets (grep for `print(`/logging of request bodies); fix anything found with tests.
7. Close every Phase Log follow-up (fix, or defer with a reason and an owner question if Nick must decide).

## Out of scope
New features; changing the live container, firewall or Open WebUI env without Nick's explicit approval.

## Tests
`make check`; `OWH_TESTBED=1 uv run pytest -m testbed`; the sweep and measurement transcripts (redacted).

## Acceptance criteria
- Threat model written; S6 recommendation presented to Nick and his decision recorded (ADR).
- Secret sweep shows the key only in the expected stores, with correct permissions.
- Upgrade-survival and offline checks passed and recorded with numbers.
- No open follow-ups without an owner or a deferral reason; no `owh-test*` leftovers.

## Phase-specific docs
`docs/OWH_THREAT-MODEL.md`, SECURITY.md, `docs/OWH_FINDINGS.md` (measurements), OSMods `Open WebUI.md` (verified results, any exposure change), CHANGELOG, ADRs. Then the standard close-out checklist.
