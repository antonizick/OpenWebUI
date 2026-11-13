# OWH Phase 03: Verification spike

**Model:** Opus 5.5 (`/model opus`) · **Depends on:** 01 · **Branch:** `phase-03-verification-spike` · **Gate:** auto

May run in parallel with Phase 02. This phase writes findings, a testbed script and ADR updates, not product code.

## Read first
`CLAUDE.md`, `prompts/OWH_shared-instructions.md`, spec §2 (starting point) and all of §3 (especially R1–R6, R9, S1–S4), ADR-0003, -0004, -0005, -0007. Phase Log entries for Phase 00 and 01. Owner question 1 (you propose its answer; you do not decide it).

## Goal
Every assumption the CLI will rely on is checked against the **real** Open WebUI v0.13.3 (on a throwaway container) and OpenRouter's **real** public API, and written down in `docs/OWH_FINDINGS.md` with evidence, so Phase 04 builds on facts. Also produce a priced model shortlist for Nick.

## Tasks
1. `scripts/owh-testbed.sh up|down|status|reset` (shellcheck-clean): runs `ghcr.io/open-webui/open-webui:v0.13.3` (already on disk; do not pull another tag) as container `owh-test-owu`, volume `owh-test-owu-data`, **bridge network** with `-p 127.0.0.1:18080:8080`, env `OLLAMA_BASE_URL` pointing at the host Ollama (`http://host.docker.internal:11434` with `--add-host=host.docker.internal:host-gateway`; Ollama listens on 127.0.0.1 only, so if that fails, use `--network host` with `PORT=18080` instead and record which works), `WEBUI_SECRET_KEY` random per run, telemetry off. `up` creates the first admin (`owh-test@localhost`, random password kept in a 0600 file under the scratch/state dir, never committed) via the signup API. `down` removes container **and** volume. Never touches `open-webui` or its volume.
2. **Open WebUI connection API (0.13.3).** Find the real endpoints and payloads by reading the container's backend source (`/app/backend/open_webui/routers/openai.py`, `config.py`, `routers/tasks.py`, `routers/auths.py`) and confirming each on the testbed: sign-in endpoint and token type; GET/POST of the OpenAI connection config (URLs, keys, `api_configs` per index: `enable`, `prefix_id` and how it renders in the model ID and name, `model_ids` filter, `tags`, `connection_type`, headers support for R9); the connection-verify endpoint; how `/api/models` lists models from both backends; whether an empty-key `api.openai.com` connection at index 0 causes errors/delays (R1).
3. **Persistence (R2, ADR-0004).** Show that a config set through the API is stored in the `config` table, survives `docker rm` + recreate of the testbed container on the same volume, and wins over `OPENAI_API_BASE_URLS`/`OPENAI_API_KEYS` env vars (or document exactly when env wins, e.g. `ENABLE_PERSISTENT_CONFIG`).
4. **Task model (R3, ADR-0005).** Find the task-config endpoint; set the external task model to a local Ollama model; verify with a fake OpenAI-compatible upstream (a tiny local server recording requests, standing in for OpenRouter) that, for a chat on a prefixed external model, title/tag/follow-up generation requests go to Ollama and only the chat completion goes to the upstream. Mark ADR-0005 Accepted or supersede it, with a timestamp.
5. **Offline behaviour (R5).** With the external connection pointed at an unroutable/closed address and at a slow (sleeping) server: measure the `/api/models` time and UI model-list behaviour; identify the setting that caps it (expected `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST` / `AIOHTTP_CLIENT_TIMEOUT_OPENAI_MODEL_LIST`; confirm in source) and its default; recommend whether OWH should tune it (it would be a container env change, which ADR-0004 avoids; say so).
6. **OpenRouter facts (R6).** Without a key: `GET https://openrouter.ai/api/v1/models` (public): field names for ID, name, context length and pricing (units!). Read OpenRouter's docs for the key-info endpoint and response, key format, and error codes for invalid key and insufficient credit. Note any `/api/v1/key` behaviour you can only confirm in Phase 05 with the real key. No paid calls in this phase.
7. **Model shortlist (owner question 1).** From the live models list, propose 4–6 IDs covering: a strong general model, a cheap fast model, a long-context model, a strong coding model, optionally one free model; give for each the exact ID, context length, input/output $/M tokens **as fetched, with the fetch timestamp**. Write it into the Owner questions row 1 as "Proposed: …" (status stays `Open`) and into `docs/OWH_FINDINGS.md`. Do not write it into `config/openrouter-models.txt`.
8. Write `docs/OWH_FINDINGS.md`: one section per task, each finding with evidence (source file + line, or the command and output with secrets removed) and a "consequence for Phase 04" line. Update Phase 04's prompt where a finding changes an assumption (endpoints, prefix format, payload shapes).
9. `scripts/owh-testbed.sh down` and confirm `docker ps -a`, `docker volume ls` show nothing named `owh-test*`.

## Out of scope
The CLI (Phase 04). Any change to the live `open-webui` container, its volume or its config (read-only only). Paid OpenRouter calls.

## Tests
`shellcheck scripts/owh-testbed.sh`; `up` → `status` → `down` twice in a row works (idempotent); `gitleaks detect` clean.

## Acceptance criteria
- `docs/OWH_FINDINGS.md` answers each of tasks 2–7 with evidence.
- ADR-0005 has a final status; any finding that contradicts spec R1–R9 has a spec amendment and ADR.
- Owner question 1 has a priced proposal; Phase 04's prompt reflects the findings.
- No `owh-test*` container or volume remains; the live `open-webui` container's start time and config are unchanged (compare `docker inspect -f '{{.State.StartedAt}}' open-webui` before and after).

## Phase-specific docs
`docs/OWH_FINDINGS.md`, `docs/OWH_ARCHITECTURE.md` (real endpoints), ADRs, spec amendment if needed, CHANGELOG. Then the standard close-out checklist.
