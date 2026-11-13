# OWH Phase 04: `owh-openrouter` CLI

**Model:** Opus 5.5 (`/model opus`) · **Depends on:** 02, 03 · **Branch:** `phase-04-owh-openrouter-cli` · **Gate:** auto

## Read first
`CLAUDE.md`, `prompts/OWH_shared-instructions.md`, spec §3 (all), **`docs/OWH_FINDINGS.md` in full** (it overrides the expected endpoint list in spec R6 and anything below that it contradicts), ADR-0002…0007 and any added by Phase 03. Phase Log entries for 02 and 03.

## Goal
`owh-openrouter` does everything needed to add, inspect, change and remove the OpenRouter connection safely and idempotently, proven against the fakes and against the throwaway testbed. Nothing touches the live instance.

## Tasks
1. **`set-key`**: hidden prompt (`getpass`), trim whitespace and reject control characters (the ai-provider history had a key file full of arrow-key escapes), check format, verify live against OpenRouter's key-info endpoint (per findings), then write `~/.config/owh/openrouter.key` atomically (temp file 0600 + rename, dir 0700). Print redacted key, label/limit/usage if the endpoint returns them. Refuse to overwrite without `--force` or a confirmation prompt. `--from-file PATH` for non-interactive tests (file must be 0600).
2. **`models`**: read `config/openrouter-models.txt` (or `--allowlist PATH`), fetch OpenRouter's model list, print a table (ID, name, context, in/out $/M) for allowlisted IDs; flag unknown IDs (exit 1) and show a `--search TEXT` helper over the full list to help Nick pick.
3. **`apply [--dry-run]`**: prompt for the admin email (default from `--email`) and password (hidden); sign in; read the current OpenAI connection config and task config; compute the desired state: the OpenRouter connection (base URL, key from the key file, enabled, prefix per findings, `model_ids` = allowlist after validation), placed per R1 (replace the dead empty-key `api.openai.com` entry; never delete a connection that has a key or a non-default URL; if one exists, append instead and say so); external task model = local model per ADR-0005 if it is installed in Ollama (check `/api/tags`), else leave unchanged and warn. Show a diff with keys redacted. On a real run: write a **snapshot** of the exact prior values to `~/.local/state/owh/snapshots/<timestamp>.json` (0600) **before** the first write, then update, then re-read and verify. A second `apply` with no changes prints "already up to date" and writes nothing.
4. **`status [--json]`**: read-only. Open WebUI reachable and version; connections (URL, enabled, prefix, number of allowlisted models, key redacted, whether it matches the key file); task model; how many OpenRouter models `/api/models` currently lists; OpenRouter key usage/limit if obtainable. Works without the admin password where the endpoint allows; otherwise prompts.
5. **`remove [--snapshot FILE]`**: restore the connection and task values from the earliest OWH snapshot (the pre-OWH state) or the one given; verify; keep the snapshot. Does not delete the key file (`--delete-key` does, with confirmation).
6. **Safety**: the token, password and key never go to argv, env, logs or exceptions (wrap HTTP errors so bodies containing them are redacted); `~/.local/state/owh/owh.log` gets one line per action (timestamp, action, result, redacted key prefix). Only `http://127.0.0.1`/`localhost` Open WebUI URLs accepted unless `--allow-remote`. Timeouts on every request. Exit codes: 0 ok, 1 validation/unknown model, 2 usage, 3 refused, 4 failed (nothing changed), 5 failed after partial change (tell the user to run `remove`).
7. Align the fakes with the findings (remove the Phase 02 `TODO(phase-04)` markers).
8. **Testbed integration test** (`tests/integration/`, marked `@pytest.mark.testbed`, skipped unless `OWH_TESTBED=1`): `owh-testbed.sh up`, a fake OpenRouter on the host standing in for the real one (via `--openrouter-url`), `apply` → `/api/models` shows prefixed models next to Ollama ones → chat completion through the prefixed model reaches the fake → second `apply` is a no-op → `remove` restores the exact pre-apply rows (compare `config` table rows) → `down`.

## Out of scope
The real key, the real OpenRouter (except the free public models list), and the live instance (Phase 05). `make install` (Phase 05).

## Tests
Unit and fake-server tests for every command and error path: bad key format, key rejected (401), unreachable Open WebUI, wrong password, idempotence, snapshot written before write, partial-failure exit 5, unknown allowlist ID, refusal of remote URL, **no secret in any captured stdout/stderr/log/request log except the request to Open WebUI's config endpoint and the OpenRouter auth header**. Coverage ≥ 90 % on `src/`. The testbed integration test passes once.

## Acceptance criteria
- `make check` green; `OWH_TESTBED=1 uv run pytest -m testbed` passed (record time and output summary).
- On the testbed: apply → no-op re-apply → remove restores rows byte-for-byte.
- No `owh-test*` container/volume left; live `open-webui` unchanged (StartedAt compare).

## Phase-specific docs
README (command reference), `docs/OWH_ARCHITECTURE.md`, a first `docs/OWH_USER-GUIDE.md` draft (install, set-key, choose models, apply, status, remove), SECURITY (where the key lives now), CHANGELOG, ADRs for notable choices. Then the standard close-out checklist.
