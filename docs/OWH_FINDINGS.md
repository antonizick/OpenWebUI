# OWH: Verification Findings (Phase 03, hardening in Phase 06)

**Recorded:** 2026-11-13 12:06 CST (Phase 03, verification spike). **Overrides** the "expected" endpoint list in spec R6 and any earlier assumption it contradicts (spec Amendments v2, §3.6).

**Evidence base.**
- **Source:** the backend copied out of the image `ghcr.io/open-webui/open-webui:v0.13.3` (image ID `46b59158e655`, the same image the live `open-webui` runs) with `docker create` + `docker cp /app/backend/open_webui`. File references below are relative to `/app/backend/open_webui/` in that image, as `file:line`.
- **Testbed:** every behaviour was confirmed on the throwaway testbed (`scripts/owh-testbed.sh`, container `owh-test-owu`, `127.0.0.1:18080`). `/api/version` reported `{"version": "0.13.3"}`.
- **Fake upstream:** a stdlib fake OpenAI-compatible server on `127.0.0.1:18091` stood in for OpenRouter and logged every request. A second copy on `:18092` slept 30 s per request.
- **OpenRouter:** the public API, called with no key or with an obviously invalid all-zero key. No paid calls were made, so **spend was $0.00**.
- **Secrets:** keys are shown as `<TESTKEY>` or redacted; the testbed admin password was never printed.

The live `open-webui` container was only inspected read-only. Its `StartedAt` was `2026-11-13T17:40:48.65503915Z` before and after this phase.

---

## 1. Testbed networking (task 1)
| Attempt | Result |
|---|---|
| Bridge + `--add-host=host.docker.internal:host-gateway`, `curl http://host.docker.internal:11434/api/version` from the image | **fails**: HTTP `000`, curl exit 28 (timeout). Ollama listens on `127.0.0.1:11434` only (`ss -ltnp`), so the bridge gateway cannot reach it |
| `--network host`, `HOST=127.0.0.1`, `PORT=18080` | **works**: `ss -ltn` shows `127.0.0.1:18080` only; Ollama models listed |

`start.sh` honours `HOST` (default `0.0.0.0`) and `PORT` (default `8080`) (`/app/backend/start.sh:31-32`). Binding `HOST=127.0.0.1` keeps the host-network testbed off other interfaces, which is stricter than the prompt's fallback. Recorded as ADR-0011. The image already sets `SCARF_NO_ANALYTICS=true`, `DO_NOT_TRACK=true` and `ANONYMIZED_TELEMETRY=false`. The script sets them again and adds `ENABLE_VERSION_UPDATE_CHECK=false` (`env.py:1198`).

A fresh testbed comes up in about 43 s. Its defaults match the live stored config: one `https://api.openai.com/v1` connection with key `""`, `OPENAI_API_CONFIGS={}`, and `TASK_MODEL`/`TASK_MODEL_EXTERNAL` empty.

**Consequence for Phase 04:** the integration test uses `scripts/owh-testbed.sh up|down`, `token` (prints a fresh admin token) and the admin `owh-test@localhost`. The password is in `~/.local/state/owh/testbed/admin-password` (0600), which `down` deletes. A fake OpenRouter on the host is reachable from the container at `http://127.0.0.1:<port>` because of host networking.

## 2. Open WebUI 0.13.3 connection API (task 2)

### 2.1 Sign-in
- `POST /api/v1/auths/signin` with body `{"email","password"}` (`routers/auths.py:660`, form `models/auths.py:173`) returns `{"token","token_type":"Bearer","expires_at",...,"role"}` (`routers/auths.py:229-231`). It also sets an httponly `token` cookie, which the CLI ignores.
- Authenticate with `Authorization: Bearer <token>`; the cookie is the fallback (`utils/auth.py:402-415`). Testbed: HTTP 200, `token_type: "Bearer"`, a JWT of length 433, `role: "admin"`.
- The signup used by the testbed is `POST /api/v1/auths/signup` with `{"name","email","password"}` (`routers/auths.py:849`). The first signup on an empty DB becomes the admin.

### 2.2 OpenAI-compatible connections
| Endpoint | Auth | Body / response |
|---|---|---|
| `GET /openai/config` | admin | `{"ENABLE_OPENAI_API": bool, "OPENAI_API_BASE_URLS": [..], "OPENAI_API_KEYS": [..], "OPENAI_API_CONFIGS": {..}}` (`routers/openai.py:455`). **Returns the keys in clear text** |
| `POST /openai/config/update` | admin | the same four fields (`OpenAIConfigForm`, `routers/openai.py:460-464`). Echoes the stored result |
| `POST /openai/verify` | admin | `{"url","key","config"?}`. Proxies `GET {url}/models` with the connection's headers and returns the upstream body/status (`routers/openai.py:972-1060`) |
| `GET /openai/models` | user | the merged OpenAI-side list; 503 `OpenAI API is disabled` if `openai.enable` is falsy |

`config/update` rules (`routers/openai.py:467-509`, confirmed on the testbed):
- `OPENAI_API_KEYS` is padded with `""` or truncated to the length of `OPENAI_API_BASE_URLS`.
- `OPENAI_API_CONFIGS` keeps **only string-index keys** `"0".."n-1"`. A URL-keyed entry and an out-of-range `"7"` were silently dropped (testbed: both gone from the echo and from the DB).
- **`ENABLE_OPENAI_API` is optional and defaults to `None`.** Omitting it stored `openai.enable = null`, `/openai/models` then answered 503 `OpenAI API is disabled` and no OpenAI models were listed. **The CLI must always send it explicitly.**
- The update clears the models cache, so the next `/api/models` shows the change. `MODELS_CACHE_TTL` defaults to 1 s (`env.py:1039`).

### 2.3 Per-connection `api_configs` fields
These are known to the storage layer (`models/config.py:44-58`): `enable`, `key`, `prefix_id`, `tags`, `model_ids`, `connection_type`, `provider`, `auth_type`, `headers`, `azure`, `api_type`, `api_version`, `extra_params`, `passthrough_params`. Their behaviour (`routers/openai.py:588-674`, `utils/headers.py`):

| Field | Behaviour (verified) |
|---|---|
| `enable` (default `true`) | `false`: the connection is skipped entirely |
| `model_ids` | **Non-empty: Open WebUI does not call the upstream `/models` at all.** It synthesises one entry per ID (`openai.py:605-622`). The fake upstream logged **zero** model-list requests. Empty: it fetches `{url}/models` |
| `prefix_id` | ID becomes `f"{prefix_id}.{id}"` and name becomes `f"{prefix_id}.{name}"` (`openai.py:651-654`). **The separator `.` is added by Open WebUI**, so store `prefix_id: "OR"` (not `"OR."`) to get `OR.anthropic/claude-sonnet-5.5`. The prefix is stripped before the request goes upstream (`utils/model_ids.py`; the fake received `model: "fake/alpha"` for `OR.fake/alpha`) |
| display name | With `model_ids`, the name is the ID, so the picker shows `OR.anthropic/claude-sonnet-5.5`, not OpenRouter's pretty name (testbed `/api/models`: `"name": "OR.fake/alpha"`) |
| `tags` | A list of `{"name": ...}` objects, copied onto each model (`"tags": [{"name": "cloud"}]` seen on `/api/models`) |
| `connection_type` | Default `"external"`. **This is what selects `TASK_MODEL_EXTERNAL` for background tasks** (§4). Keep it `"external"` |
| `headers` | A dict merged **last** into every upstream request (`utils/headers.py:77-79`). The fake received `X-OWH-Probe: 1` on chat and task requests. Supports `{{CHAT_ID}}`-style templates |
| `auth_type` | Absent or `"bearer"` sends `Authorization: Bearer <key>` (`utils/headers.py:56-75`). Confirmed: the fake saw `Bearer sk-or-v1-…` |

**R9 (attribution headers): contradicts the spec.** For any URL containing `openrouter.ai`, Open WebUI **always** adds `HTTP-Referer: https://openwebui.com/` and `X-Title: Open WebUI` (`utils/headers.py:36-49`, a hard-coded upstream identifier). Testbed: a connection URL `http://127.0.0.1:18091/openrouter.ai/v1` sent both headers on `GET /models` and on `POST /chat/completions`. A per-connection `headers` entry overrides them, because it is merged last: `{"HTTP-Referer": "", "X-Title": "OWH"}` arrived as exactly those values. They identify the app, not the user. Spec R9 is corrected in Amendments v2 and ADR-0012.

### 2.4 How `/api/models` merges the backends
`GET /api/models` (`main.py:876`) merges the Ollama list (`connection_type: "local"`, `owned_by: "ollama"`) with the OpenAI-side list (`owned_by: "openai"`, `connection_type: "external"`, `urlIdx`). After the testbed apply it listed:
`OR.fake/alpha, OR.fake/beta, nomic-embed-text:latest, gemma2:9b, qwen3:8b, qwen3:1.7b, qwen3:4b-instruct`.
A chat through `POST /api/chat/completions` with `model: "OR.fake/alpha"` reached the fake upstream as `POST /v1/chat/completions`, `model: "fake/alpha"`, HTTP 200.

### 2.5 R1: the dead `api.openai.com` connection
The pristine state (`api.openai.com`, key `""`, no `api_configs` entry) uses the "legacy" path, which fetches `https://api.openai.com/v1/models` with no auth on **every** model-list refresh (`openai.py:599-600`). The 401 body has no `data`, so the merge drops it silently: no log error, and `/api/models` took **0.19–0.26 s** (3 runs, including Ollama). It is harmless for speed, but it is an outbound request to OpenAI on every refresh. Replacing it at index 0 (R1) removes that request. R1 is confirmed as specified.

**Consequence for Phase 04:**
- Read with `GET /openai/config`.
- Write with `POST /openai/config/update`, always sending **all four fields including `ENABLE_OPENAI_API: true`**.
- Key `OPENAI_API_CONFIGS` by string index.
- Use `prefix_id: "OR"`, `model_ids: <allowlist>`, `connection_type: "external"` and `enable: true`. Optionally add `tags: [{"name": "OpenRouter"}]`.
- Do not use `/openai/verify` to validate the key (§6).
- `status` needs the admin token for `/openai/config`, because that endpoint returns keys.

## 3. Persistence (task 3, R2, ADR-0004)
- **Storage:** `config` table, one row per key: `key TEXT PK, value JSON, updated_at BIGINT` (`models/config.py:104-118`). Testbed rows after the apply (read through a `mode=ro` SQLite URI):
  ```
  openai.api_base_urls  ["http://127.0.0.1:18091/v1"]
  openai.api_configs    {"0":{"enable":true,"prefix_id":"OR","model_ids":["fake/alpha","fake/beta"],"tags":[{"name":"cloud"}],"connection_type":"external","headers":{"X-OWH-Probe":"1"}}}
  openai.api_keys       ["<TESTKEY>"]
  openai.enable         true
  ```
- **`updated_at` changes on every write**, even for an unchanged value: all four `openai.*` rows got the new timestamp. A byte-for-byte "restore" can only compare `key` + `value`, not `updated_at`.
- **Seeding:** env/defaults only fill keys that are missing; "Existing DB values take precedence over defaults" (`models/config.py` `seed_defaults`).
- **Recreate test:** `docker rm -f owh-test-owu` kept the volume. The container was then recreated with `-e OPENAI_API_BASE_URLS=http://127.0.0.1:18092/v1 -e OPENAI_API_KEYS=env-key -e TASK_MODEL_EXTERNAL=qwen3:8b`. **The stored config won:** URL `:18091`, `<TESTKEY>`, prefix and `model_ids` were kept, the task model stayed `qwen3:4b-instruct`, and `/api/models` still showed both `OR.` models.
- **When env wins:** only with `ENABLE_PERSISTENT_CONFIG=false` (`config.py:3421`; `Config.get` then returns the env defaults). Testbed: after a recreate with it, `GET /openai/config` returned the env URL `:18092` and `OPENAI_API_CONFIGS={}`. API writes then go to memory only (`Config.upsert` writes `DEFAULTS`). The live container does not set `ENABLE_PERSISTENT_CONFIG` or any `AIOHTTP_*`/`MODELS_CACHE_TTL` variable (`docker inspect`, read-only).
- **After a normal recreate,** the stored connection was back, so `open-webui-upgrade`, which recreates from env diffs, keeps it. R2 is confirmed. Phase 06 re-verifies it against the real upgrade script.

**Consequence for Phase 04:** snapshot and compare the `value` of `openai.enable`, `openai.api_base_urls`, `openai.api_keys`, `openai.api_configs` and `task.model.external`, as returned by the API (equivalently the DB `value` column). The testbed integration test's "rows byte-for-byte" check compares `key, value` only. `status` can warn if `ENABLE_PERSISTENT_CONFIG=false` is ever set.

## 4. Background tasks on a local model (task 4, R3, ADR-0005)
- **Endpoints:**
  - `GET /api/v1/tasks/config` (any verified user) returns 19 fields, among them `TASK_MODEL`, `TASK_MODEL_EXTERNAL` and `TASK_MODEL_PARAMS` (`routers/tasks.py:42-62,105`).
  - `POST /api/v1/tasks/config/update` (admin) takes `TaskConfigForm` (`routers/tasks.py:110-138`), where **every field is required**. A body with only `TASK_MODEL_EXTERNAL` got **HTTP 422** (missing `TASK_MODEL`, `ENABLE_TITLE_GENERATION`, …). The full GET body with `TASK_MODEL_EXTERNAL` changed got 200 and an echo identical to what was sent.
- **Selection rule** (`utils/task.py:17-37`): if the chat model's `connection_type` is `local`, use `TASK_MODEL` when set; otherwise use `TASK_MODEL_EXTERNAL` **if it exists in the model list**, else the chat model itself. The title, follow-up, tags, image-prompt, query, autocomplete and emoji endpoints all go through `get_task_model_generation_config` (`routers/tasks.py:169-579`). Search and retrieval query generation are covered too.
- **Baseline** (`TASK_MODEL_EXTERNAL=""`): title, tags and follow-up for `OR.fake/alpha` **all went to the upstream** (4 upstream requests: the chat plus 3 tasks, whose prompts start `### Task: Generate a concise title…`). This is the paid leak R3 predicted.
- **With `TASK_MODEL_EXTERNAL="qwen3:4b-instruct"`:** direct task calls were answered by `qwen3:4b-instruct` (title 2.97 s including model load, tags 0.36 s, follow-up 0.69 s). The upstream saw **0** requests.
- **End-to-end as the UI does it:** a saved chat (`POST /api/v1/chats/new`), then `POST /api/chat/completions` with `chat_id`, `id`, `stream: true` and `background_tasks: {title_generation, tags_generation, follow_up_generation: true}`. The upstream got **exactly one** request (the chat completion, `model: "fake/alpha"`). Within 2 s the chat had a generated title, 3 tags and 4 follow-ups, all from the local model (logs: `POST /api/v1/tasks/{title,tags,follow_up}/completions 200`).
- **ADR-0005 is Accepted** (2026-11-13 12:06 CST).

**Consequence for Phase 04:** `apply` GETs `/api/v1/tasks/config`, changes only `TASK_MODEL_EXTERNAL`, and POSTs the **whole** object back. It checks first that the model is installed (Ollama `GET /api/tags`, or its presence in `/api/models`), because a missing model silently falls back to the chat model. The snapshot keeps the prior value (`""` on the live instance). Leave `TASK_MODEL` (local chats) untouched.

## 5. Offline and slow upstream (task 5, R5)
`GET /api/models` time on the testbed, 1.2 s after each config change (cache TTL 1 s). There were 5 local models throughout.

| Upstream | `model_ids` **empty** (fetch `/models`) | `model_ids` **set** (allowlist) |
|---|---|---|
| fake, healthy | 0.11 s, 2 `OR.` | 0.10 s, 1 `OR.` |
| closed port `127.0.0.1:1` | 0.14 s, 0 `OR.` | 0.11 s, 1 `OR.` |
| unroutable `10.255.255.1` | **10.99 s**, 0 `OR.` | 0.10 s, 1 `OR.` |
| slow (30 s sleep) | **10.77 s**, 0 `OR.` | 0.10 s, 1 `OR.` |
| `api.openai.com`, empty key | 0.19 s, 0 | 0.11 s, 1 |

- **The cap:** `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST`, which falls back to the legacy name `AIOHTTP_CLIENT_TIMEOUT_OPENAI_MODEL_LIST`, **default 10 s** (`env.py:645-653`). It is applied as `aiohttp.ClientTimeout(total=…)` to model-list and verify requests (`routers/openai.py:75`).
- **Chat while OpenRouter is down** (`model_ids` set, closed port): `POST /api/chat/completions` for `OR.fake/alpha` failed fast, HTTP 500 `{"detail": "Open WebUI: Server Connection Error"}` in 0.07 s. A local `qwen3:1.7b` chat at the same time returned HTTP 200 in 2.80 s. Chat requests use `AIOHTTP_CLIENT_TIMEOUT` (default 300 s, `env.py:598-602`, `utils/session_pool.py:43-47`), so an *unroutable* upstream would make only that OR chat wait up to 300 s. Local chats are unaffected.
- **Recommendation: do not tune the timeout.** With the allowlist applied through `model_ids` (ADR-0003), the model list never contacts OpenRouter, so offline or slow OpenRouter costs **no** list delay. Tuning would need a container env change, which ADR-0004 avoids. R5 is met by construction.

**Consequence for Phase 04:** `model_ids` must never be empty for the OpenRouter connection, so `apply` refuses an empty allowlist. An empty `model_ids` would both list all ~470 models and bring back the 10 s stall when offline.

## 6. OpenRouter API facts (task 6, R6)
Fetched 2026-11-13 12:03 CST.

| Fact | Value | Evidence |
|---|---|---|
| Base URL | `https://openrouter.ai/api/v1` | auth docs (openrouter.ai/docs/api-reference/authentication); used for every probe below |
| Auth | `Authorization: Bearer <key>`, "exactly as issued, with no extra whitespace or quotes" | auth docs |
| Key format | `sk-or-v1-` + 64 lowercase hex = **73 characters** | auth docs; matches the Phase 01 shape check of the existing key |
| Models | `GET /api/v1/models`, public (no key), HTTP 200, `{"data": [...], "total_count": 470, "links": {"next": null}}`: all 470 in one page | `curl` |
| Model fields | `id`, `canonical_slug`, `name` (e.g. `"Anthropic: Claude Sonnet 5.5"`), `created`, `description`, `context_length` (int tokens), `architecture{modality,input_modalities,output_modalities,tokenizer}`, `pricing{…}`, `top_provider{context_length,max_completion_tokens,is_moderated}`, `supported_parameters`, `expiration_date`, `reasoning{…}`, `endpoints` | `models.json` |
| **Pricing units** | **strings, USD per token** (`"prompt": "0.000002"` = $2.00 per M input tokens). $/M = `float(x) * 1e6`. Keys seen: `prompt`, `completion`, `image`, `audio`, `audio_output`, `image_output`, `input_audio_cache`, `input_cache_read`, `input_cache_write`, `input_cache_write_1h`, `internal_reasoning`, `web_search`, `overrides` | `models.json` |
| Special prices | router IDs (`openrouter/auto`, `openrouter/auto-code`, …) have **negative** prices ("variable"); `:free` IDs are `"0"` (13 of them); `:batch` variants exist for many models | `models.json` |
| Key info | `GET /api/v1/key` returns `{"data": {label, limit, limit_reset, limit_remaining, include_byok_in_limit, budgets, effective_budget, usage, usage_daily, usage_weekly, usage_monthly, byok_usage…, is_free_tier, free_model_daily_requests{used,limit,remaining}}}`; `rate_limit` is deprecated | limits docs (openrouter.ai/docs/api-reference/limits) |
| No key | `GET /api/v1/key` → **401** `{"error":{"message":"No cookie auth credentials found","code":401}}` (same for `/api/v1/credits`) | `curl` |
| Invalid key | `GET /api/v1/key` and `POST /api/v1/chat/completions` → **401** `{"error":{"message":"User not found.","code":401}}` | `curl` with an all-zero `sk-or-v1-` key |
| **`/models` ignores the key** | `GET /api/v1/models` with the invalid key → **200** | `curl` |
| Error shape and codes | `{"error": {"code": int, "message": str, "metadata"?: {}}}`, HTTP status = `error.code`. 400 bad params; **401** invalid or disabled key; **402** insufficient credits (account or key limit); 403 moderation/guardrail; 408 timeout; **429** rate limited; 502 model down; 503 no provider meets routing. `Retry-After` on 429/503 and some 402 | errors docs (openrouter.ai/docs/api-reference/errors) |
| Free models | `:free` IDs: 20 req/min; 50/day if under 10 credits ever purchased, else 1000/day; 429 when exceeded | limits docs |
| Attribution headers | docs: `HTTP-Referer` (site URL) and `X-OpenRouter-Title` (site name), both optional; Open WebUI sends `X-Title` (§2.3) | auth docs |

**Only confirmable in Phase 05, with the real dedicated key:**
- the exact `/api/v1/key` body: whether `label` shows the key name, `limit` the dollar cap from owner question 2, and `limit_reset` the monthly reset;
- that a 402 actually appears when the key limit is reached (do not provoke it; read `limit_remaining`);
- that Activity shows Open WebUI chats under this key.

**Consequence for Phase 04:**
- **`set-key` validates with `GET /api/v1/key`.** Neither `/models` nor Open WebUI's `/openai/verify` (which calls `/models`) can tell a valid key from an invalid one.
- Check the format with `^sk-or-v1-[0-9a-f]{64}$`.
- `models` multiplies the per-token strings by 1e6. It shows "variable" for negative prices and "free" for `0`, and parses defensively (prices are strings; missing keys are allowed).
- Map 401 to "key rejected", 402 to "out of credit or key limit reached", and 429 to "rate limited".

### 6a. Confirmed in Phase 05 with the real dedicated key (2026-11-13 13:05 CST)
`GET /api/v1/key` (values shown only for the non-identifying fields):
- **Fields present:** `label`, `is_management_key`, `is_provisioning_key`, `limit`, `limit_reset`, `limit_remaining`, `include_byok_in_limit`, `budgets`, `effective_budget`, `usage`, `usage_daily`, `usage_weekly`, `usage_monthly`, `byok_usage`, `byok_usage_daily`, `byok_usage_weekly`, `byok_usage_monthly`, `is_free_tier`, `expires_at`, `creator_user_id`, `organization_id`, `workspace_id`, `allowed_data_regions`, `free_model_daily_requests`, `rate_limit`. Not documented in §6: `is_management_key`, `expires_at`, `creator_user_id`, `organization_id`, `workspace_id`, `allowed_data_regions`.
- **`label` is not the key's name.** It is OpenRouter's masked key preview (18 characters, `sk-or-v1-` + 3 chars + `...` + the last 3). OWH's scrubber therefore shows it as `sk-or-v1-… (12 chars)...275`. Cosmetic; Phase 06 follow-up.
- **`limit`** is the dollar cap in USD (`50`), `limit_reset` is `"monthly"`, and `limit_remaining` falls with `usage` (`49.99999234` after one chat costing $0.00000766). The cap is Nick's choice; OWH does not manage it (ADR-0018).
- **`expires_at`:** `2027-11-13T18:03:06.508Z`. The key stops working after one year unless it is rotated.
- **Usage accounting:** after one `OR.z-ai/glm-5.3-flash` chat with title, tags and follow-ups enabled, the key's `usage` equalled exactly that chat's cost (`7.66e-06`), and Ollama logged three `POST /api/chat` at the same second. This confirms ADR-0005 against the real OpenRouter.
- **Chat delivery:** with a `chat_id`, `POST /api/chat/completions` returns `null` and the reply arrives over the websocket; it is saved in the chat (`history.messages[*].usage` includes `cost`).
- **Testbed cold start:** a new volume downloads about 1.1 GB of embedding model (`sentence-transformers/all-MiniLM-L6-v2`) before `/health` answers; it took about 150 s, so `owh-testbed.sh` now waits up to 300 s.
- Not done on purpose: provoking a 402 (left to the docs, §6).

## 7. Proposed model shortlist (task 7, owner question 1)
From the live `GET /api/v1/models`, **fetched 2026-11-13 12:03 CST**. Prices are $ per million tokens (input / output). **A proposal only; Nick decides** (owner question 1 stays Open). It is not written to `config/openrouter-models.txt`.

| Role | Exact ID | Context | In $/M | Out $/M | Why |
|---|---|---|---:|---:|---|
| Strong general | `anthropic/claude-sonnet-5.5` | 1,000,000 | 2.00 | 10.00 | Strong all-rounder; good default cloud pick |
| Cheap and fast | `anthropic/claude-haiku-5.5` | 1,000,000 | 0.10 | 0.50 | 20× cheaper than Sonnet; fine for quick questions |
| Long context, multimodal | `google/gemini-4-hydrogen` | 1,048,576 | 1.50 | 7.50 | Takes files, audio, video and images; output up to 943,718 tokens |
| Strong coding | `openai/gpt-6.1-terra` | 1,050,000 | 1.00 | 5.00 | A second vendor, described for "agentic, coding, and writing work" at half Sonnet's price |
| Free (optional) | `google/gemma-4-31b-it:free` | 262,144 | 0 | 0 | No cost. Rate-limited (§6), and free endpoints may log prompts (see owner question 3) |

Notes for Nick's choice:
- Almost every current model has a context of about 1M tokens, so "long context" now mainly means price per long input. The cheapest long-input option is `deepseek/deepseek-v4.1-flash-1017` (1,048,576; $0.038 / $0.50), but it is a dated snapshot.
- The premium option is `anthropic/claude-opus-5.5` (1,000,000; $4.00 / $20.00). Leave it off unless wanted (spend guard S5).
- Avoid `:batch` variants and the `openrouter/auto*` routers (variable price) in an interactive picker.
- Spend guide at the $20/month default (owner question 2): about 2 M Sonnet output tokens, or about 40 M Haiku output tokens.

---

## 8. Hardening measurements (Phase 06, 2026-11-13 13:39–13:49 CST)
Raw transcripts were printed by `make test-testbed` (`tests/integration/test_hardening.py`) and by the read-only sweep. Only counts and file names are given, never key material.

### 8.1 Secret sweep (live system, read-only, 13:39 CST)
The search used the key prefix `sk-or-v1-` and the key's last 16 characters, passed to `grep` through a pipe or an fd so they were never in argv. **Hits on the OWH key** (tail):

| Place | Hits | Note |
|---|---|---|
| `~/.config/owh/openrouter.key` | 1 | expected; 0600, dir 0700 |
| live `webui.db` (read with a throwaway `--network none` container, volume mounted `:ro`, SQLite `immutable=1`) | 1 row (`config`, `openai.api_keys`) | expected; no other table and no other file in the volume; `-wal` 0 |
| `~/.local/state/owh/snapshots/*.json` (2 at the time) | 0 | snapshots hold the prior config, which had no key (ADR-0022) |
| `~/.local/state/owh/owh.log` | 0 | 11 lines carry the 9-character prefix by design |
| `~/.bash_history`, `~/.local/state/open-webui-toggle.log` | 0 | `~/.bash_history` has 1 line with a **different** real key (`ai-provider set-key sk-or-v1-…`, the AI Provider Switch key); out of scope, reported to Nick |
| `docker inspect open-webui`, `docker logs open-webui` (all and since apply, 642 lines), user journal since 12:40 | 0 | |
| repo working trees, every commit of every branch (`git grep` over `rev-list --all`), `gitleaks` | 0 | the 17 repo files that hold the prefix are docs, the scrubber, the gitleaks config and tests with `TESTKEY`/all-zero fakes |
| `~/Documents` (tail, and any `sk-or-v1-<64 hex>`) | 0 / 0 | |
| process list | 0 | |
| upgrade backups (`~/.local/share/open-webui-upgrade/backups/`, 2), manual backups (`~/.local/share/open-webui-backups/`, 3 + `-wal`/`-shm`) | 0 | all predate OWH. Dirs 0700. Files 0600, except two 2026-11-09 manual copies at 0644 inside the 0700 dir |

The live container was **stopped** during the sweep (exited cleanly at 13:37:14 CST after a start at 13:31:45 CST; Nick's doing, before this phase). The stored config survived that restart: the key row was present.

### 8.2 Upgrade survival (R2), testbed
`up` → `apply` (fake key, the real eight-ID allowlist served by the fake OpenRouter) → recreate the container with `make_recipe` and `create_from_recipe` **sourced from `~/.local/bin/open-webui-upgrade`** (stop, rename to `-prev`, create, start, the same image) → compare.
- The recipe carried `network: host`, the bind `owh-test-owu-data:/app/backend/data`, and the env diff `WEBUI_SECRET_KEY, HOST, PORT, OLLAMA_BASE_URL, ENABLE_VERSION_UPDATE_CHECK`. The new container ID was different; `/health` came back after 20 s.
- The 5 OWH rows (`openai.enable`, `openai.api_base_urls`, `openai.api_keys`, `openai.api_configs`, `task.model.external`) were byte-identical. `status --json` was identical for connections, task model, model counts and the enable switch: 8 `OR.` and 5 local models, task model `qwen3:4b-instruct`.
- **The script's post-upgrade checks** (`run_test`) are `/health`, `/api/version`, `/api/config`, Ollama `/api/version`, `PRAGMA integrity_check` and the log grep for tracebacks or migration errors. None of them touches the OpenAI connection, and with `model_ids` set no model-list fetch can log a traceback. **R2 holds; the script needs no change.**

### 8.3 Offline (R5), testbed, real allowlist (8 IDs)
The connection URL was changed through the admin API. Each value is the median of 3 `GET /api/models`, each 1.2 s after the previous one (cache TTL 1 s):

| Upstream | `/api/models` | listed | Phase 03 (`model_ids` set) |
|---|---|---|---|
| fake, healthy | 0.12 s | 8 `OR.` + 5 local | 0.10 s |
| closed port `127.0.0.1:1` | 0.13 s | 8 + 5 | 0.11 s |
| unroutable `10.255.255.1` | 0.12 s | 8 + 5 | 0.10 s |

- **Local chat** on `qwen3:4b-instruct` with OpenRouter unroutable: HTTP 200 in 3.02 s (model load included).
- **`OR.` chat with the port closed:** HTTP 500 `Open WebUI: Server Connection Error` in 0.04 s, so it fails fast.
- R5 is met with the real-size allowlist: an unreachable OpenRouter adds no measurable delay to the picker.

### 8.4 Out of credit or key limit (spend guard), testbed
OWH manages no spend (ADR-0018). The live key's `/api/v1/key` reports `limit` 50 (USD), `limit_reset` `monthly`, and a `limit_remaining` that falls with `usage` (§6a). We did not exhaust it. Instead, the fake OpenRouter answered chat completions with **HTTP 402** in OpenRouter's error shape (`{"error":{"code":402,"message":…}}`):
- Open WebUI passed it through: **HTTP 402 in 0.03 s with the upstream's `message` as `detail`**, which the chat shows as the error. With the real OpenRouter, that is its own insufficient-credits text (errors docs, §6).
- Local models are unaffected. `owh-openrouter set-key` and `status` map a 402 on the key check to "out of credit or the key's spending limit is reached".

### 8.5 Exposure (S6), read-only, 13:45 CST
Host networking, with no `HOST` in the container env, so uvicorn binds `0.0.0.0:8080` while it runs. Interfaces: a Wi-Fi LAN interface, `tailscale0`, Docker bridges. `ufw`: active, `DEFAULT_INPUT_POLICY="DROP"`, no rule for 8080. Open WebUI: 1 user (admin), `ui.enable_signup=false`, `ui.default_user_role="pending"`, `auth.enable_api_keys=false`. Decision: keep as is (ADR-0021, threat model §5).

## Summary of spec impact
| Spec item | Finding | Action |
|---|---|---|
| A3 prefix `OR.` | Open WebUI adds the `.`; store `prefix_id: "OR"` | Amendment v2 (A3 clarified) |
| R1 | Confirmed: dead entry harmless (0.2 s) but makes an outbound request; replace at index 0 | none |
| R2 | Confirmed: DB wins over env, survives recreate; except `ENABLE_PERSISTENT_CONFIG=false` | none (Phase 06 re-checks the real upgrade) |
| R3 / ADR-0005 | Confirmed: `TASK_MODEL_EXTERNAL` = local model keeps every task local | ADR-0005 Accepted |
| R5 | With `model_ids` set, no model-list delay at all; timeout tuning unnecessary | Amendment v2 (R5 refined) |
| R6 | Facts above; key validation must use `/api/v1/key` | ADR-0013 |
| R9 | **Contradicted:** Open WebUI always sends `HTTP-Referer`/`X-Title` to openrouter.ai; overridable via `headers` | Amendment v2 (R9 corrected), ADR-0012 |
