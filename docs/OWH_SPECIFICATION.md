# OWH: OpenWebUI Hybrid (local Ollama + OpenRouter) Specification

> **Amendments override earlier sections.** Section 3 (Amendments) is the binding version; sections 1–2 keep the owner's original request and the verified starting point.

Source: `OWH_Brainstorming.md` (repo root; in the vault as [[OWH_Brainstorming]] via `02 Projects/Work`). To Do list item 10, "OpenWebUI Hybrid".

## 1. Owner's request (verbatim, 2026-11-13 10:59 CST)
> I am running (on my laptop) OpenWebUI locally, Ollama locally, and you..Claude Code. Today OpenWebUI is connected (only) to the local Ollama instance. I would like you to design and build and deploy an OpenWebUI configuration such that my local OpenWebUI can also connect it to my OpenRouter-API so that the local instance of OpenWebUI can use both 'the local Ollama' AND 'my OpenRouter API' depending on what model I select in the OpenWebUI UI.

Restated goal: one Open WebUI instance, one model picker, two backends. Picking a local model routes the chat to Ollama on the laptop. Picking an OpenRouter model routes it to OpenRouter's OpenAI-compatible API, paid from Nick's OpenRouter account.

## 2. Starting point (verified 2026-11-13 11:10 CST, read-only)
| Item | Value |
|---|---|
| Open WebUI | Docker container `open-webui`, image `ghcr.io/open-webui/open-webui:v0.13.3` (pinned), **host network**, port 8080, volume `open-webui` → `/app/backend/data`, restart `no` |
| Lifecycle | user unit `~/.config/systemd/user/open-webui.service` (`docker start -a`, no `[Install]`), toggled by `Super+Alt+O` / `open-webui-toggle`; upgrades only via `~/.local/bin/open-webui-upgrade` (OCC tile), which recreates the container from its env diffs and backs up the volume |
| Ollama | 0.40.7, `prometheus-ollama.service` (user unit, `127.0.0.1:11434`, `PartOf=prometheus.target`). Models: `qwen3:8b`, `qwen3:4b-instruct`, `qwen3:1.7b`, `gemma2:9b`, `nomic-embed-text` |
| Container env (relevant) | `OLLAMA_BASE_URL=http://127.0.0.1:11434`, `DEFAULT_MODELS=qwen3:8b`, `OPENAI_API_BASE_URL=` and `OPENAI_API_KEY=` (empty), web search on (DuckDuckGo) |
| Stored config (`webui.db`, `config` table, key/value rows) | `ollama.enable=true`, `ollama.base_urls=["http://127.0.0.1:11434"]`; **`openai.enable=true` with one dead connection** `openai.api_base_urls=["https://api.openai.com/v1"]`, `openai.api_keys=[""]`, `openai.api_configs={}`; `direct.enable=false`; `task.model.default=""`, `task.model.external=""`; title, tags, follow-up and search-query tasks enabled |
| Users | one admin (`nick@antonizick.com`), signup off |
| Default chat model | Workspace Model **Qwen3 8B (Web)** (`qwen3-8b-web`, wraps `qwen3:8b`) |
| Existing OpenRouter key | `~/.config/ai-provider/openrouter.key` (0600), used by Claude Code's provider switch. Account credit is shared by every key on the account |
| Host | Omarchy (Arch) Linux, kernel 7.2.8, RTX 2070 Max-Q 8 GB, Docker 29.9.2, Python 3.14.8, uv 0.13.0, gh 2.103.2 (logged in as `antonizick`), gitleaks, shellcheck, jq |

Existing documentation: `~/Documents/04 Resources/OSMods/Open WebUI.md` (says "Everything stays local except web-search queries", which this project changes), `AI Provider Switch.md`, `~/Documents/04 Resources/OpenRouter Analysis.md`.

## 3. Amendments (v1, 2026-11-13 11:19 CST)

These amendments supersede conflicting text in the earlier sections. Each amendment that records a decision has an entry in `docs/OWH_DECISIONS.md`.

#### 3.1 Decisions confirmed by the project owner
| ID | Topic | Decision |
|---|---|---|
| A1 | Project prefix | `OWH` ("OpenWebUI Hybrid", the name already used in the To Do list and the brainstorm file). ADR-0001 |
| A2 | API key | A **new, dedicated OpenRouter key** for Open WebUI, created by Nick on openrouter.ai with its own spending limit. Never reuse `~/.config/ai-provider/openrouter.key`. This keeps usage separate in OpenRouter Activity and lets the key be revoked without breaking Claude Code failover. ADR-0002 |
| A3 | Models shown | A **curated allowlist** of OpenRouter models, shown with a visible prefix (default `OR.`, final form verified in Phase 03) so cloud and local models are told apart in the picker. The list is a versioned file in the repo and is changed with one command. ADR-0003 |
| A4 | Configuration method | **Scripted via Open WebUI's admin API**, writing the connection to the stored config in `webui.db`. Not container env vars (would need a recreate, put the key in `docker inspect`, and lose to the stored config anyway) and not a click-through. The script asks for the admin password at a hidden prompt and keeps the session token in memory only. ADR-0004 |

#### 3.2 Technical refinements
- **R1 Replace the dead OpenAI connection.** The stored `https://api.openai.com/v1` entry with an empty key is a leftover default that Open WebUI polls for models on every list refresh. The OpenRouter connection replaces it at the same index, so no extra failing connection is left. The original values are saved in the pre-apply snapshot so `remove` restores them exactly. *Verify in Phase 03.*
- **R2 Upgrade-safe by construction.** Because the connection lives in the volume's DB, not the container env, `open-webui-upgrade` (which recreates the container from env diffs) keeps it with no change to that script, the unit, the toggle or OCC. *Verify in Phase 03 (recreate a throwaway container on the same volume) and again in Phase 06.*
- **R3 Background tasks stay local.** With `task.model.external=""`, Open WebUI runs title, tag, follow-up and search-query generation on the chat's own model, so an OpenRouter chat would make extra paid calls that also send the chat. Default: set the external task model to a local Ollama model (`qwen3:4b-instruct`, else `qwen3:8b`), so only the chat completion itself goes to OpenRouter. *Phase 03 verifies Open WebUI accepts a local model as the external task model; ADR-0005 (Proposed).*
- **R4 Local stays the default.** `DEFAULT_MODELS` and the default Workspace Model (`qwen3-8b-web`) are not changed. A new chat is local unless Nick picks an OpenRouter model.
- **R5 Graceful when offline.** If OpenRouter is unreachable (no network, key revoked, credit exhausted), the local models must still list and work, and the model list must not stall the UI for long. *Phase 03 measures the model-list behaviour with an unreachable endpoint and records the timeout setting that governs it (expected `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST`; do not assume, verify).*
- **R6 API facts are verified, not assumed.** The OpenRouter base URL (expected `https://openrouter.ai/api/v1`), the key-info endpoint (expected `GET /api/v1/key`), the models endpoint and its pricing fields, the key format (expected `sk-or-…`), and Open WebUI 0.13.3's connection endpoints and `api_configs` fields (expected `/openai/config`, `/openai/config/update`, per-connection `enable`, `prefix_id`, `model_ids`, `tags`, `connection_type`) are checked in Phase 03 against the real software and recorded in `docs/OWH_FINDINGS.md`. Later phases use the findings, not this list.
- **R7 Tool shape.** One CLI, `owh-openrouter` (Python ≥ 3.11, standard library only at runtime; `uv` for dev, `pytest`, `ruff`), with `set-key`, `models`, `apply [--dry-run]`, `status`, `remove`. Idempotent: running `apply` twice changes nothing the second time. Installed to `~/.local/bin` by `make install` (an OS modification, documented in OSMods).
- **R8 Rehearse before live.** Every change is first applied to a **throwaway** Open WebUI container (same image tag, own volume, `127.0.0.1` only, a different port) before the real instance. The real instance is touched only in Phase 05, after a local DB backup.
- **R9 Attribution headers.** OpenRouter's optional app-attribution headers are not sent by default (the dedicated key already separates usage). Phase 03 records whether Open WebUI can send per-connection headers, in case Nick wants them later.

#### 3.3 Security and privacy baseline (applies to every phase)
- **S1 The key is never in the repo, logs, shell history, process arguments or `docker inspect`.** It is entered at a hidden prompt, validated (format, then a live key-info call), stored at `~/.config/owh/openrouter.key` (dir 0700, file 0600) and sent to Open WebUI only in an HTTPS-free localhost API body. Output shows at most the first 9 characters and the length. The repo has a gitleaks pre-commit hook and a CI scan. The repo is reachable from the vault through the `02 Projects/Work` symlink, so treat every repo file as potentially synced.
- **S2 Admin credentials are not stored.** The admin password is read at a hidden prompt; the session token is held in memory for one run and never written down.
- **S3 Where the key ends up, stated honestly.** After `apply`, the key also lives in `webui.db` (Open WebUI stores connection keys in its config table), and therefore in every later volume backup: `~/.local/share/open-webui-upgrade/backups/` (0700/0600) and any manual `~/.local/share/open-webui-backups/` copy. Never copy those into `~/Documents` (it syncs to Drive). The pre-apply snapshots in `~/.local/state/owh/` are 0600. Rotating the key = new key + `set-key` + `apply` + revoke the old key on openrouter.ai.
- **S4 Data leaves the laptop only for OpenRouter models, and the docs say so.** A chat with an `OR.` model sends the conversation, any attached files or RAG excerpts, and any web-search results to OpenRouter and the upstream provider. Local models stay local. The Open WebUI OSMods note's "everything stays local" line is corrected in Phase 05. OpenRouter account privacy settings (training/logging providers, ZDR) are Nick's choice (owner question 3).
- **S5 Spend is capped outside the laptop.** The dedicated key carries a spending limit set on openrouter.ai (owner question 2). The allowlist keeps expensive models out of the picker unless Nick adds them; `models` shows each model's price.
- **S6 Network exposure unchanged, noted.** Open WebUI uses host networking, so port 8080 listens on all interfaces while running; login is required and signup is off. With a paid key behind it this matters more; Phase 06 assesses it and recommends (does not silently apply) any change.
- **S7 Reversible.** `owh-openrouter remove` restores the pre-apply connection and task-model values from the snapshot. A full DB backup is taken before the live apply.

#### 3.4 Repository and publication requirement (mandatory)
The project lives in one Git repository, `/home/nick/Work/OpenWebUI`, pushed to a **private** GitHub repo (`antonizick/OpenWebUI`, created in Phase 01). It contains and keeps accurate: README, LICENSE, NOTICE, THIRD_PARTY_NOTICES, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG, .gitignore, .dockerignore, .editorconfig, .github/ (CI, templates, Dependabot), and docs/. Private data never gets committed; `.gitignore` and a pre-commit secret scan enforce this. Making the repo public needs Nick's explicit confirmation; none is planned.

#### 3.5 Owner questions (status as of 2026-11-13 11:19 CST)
1. **Open (needed by Phase 05).** Which OpenRouter models go on the allowlist? Phase 03 proposes a short list from OpenRouter's live models endpoint with real prices (for example a strong model, a cheap fast model, a long-context model, a coding model); Nick confirms or edits it.
2. **Open (needed by Phase 05).** Spending limit for the new key. Proposed default: **$20 per month**, set on openrouter.ai when the key is created.
3. **Open (needed by Phase 05).** OpenRouter account privacy settings: allow providers that may log or train on prompts? Proposed default: turn off training/logging providers in openrouter.ai privacy settings; ZDR-only stays off unless Nick wants it.
4. **Deferred (Phase 07, only if ever published).** Licence. Default: repo stays private, LICENSE states "All rights reserved".

#### 3.6 Amendments v2 (2026-11-13 12:06 CST, Phase 03 findings)
Verified against Open WebUI v0.13.3 and OpenRouter's live API; evidence is in `docs/OWH_FINDINGS.md`, which supersedes the "expected" values in R6.
- **A3 (clarified).** The prefix is stored as `prefix_id: "OR"`. Open WebUI adds the dot, so picker IDs and names read `OR.<openrouter-id>`, for example `OR.anthropic/claude-sonnet-5.5`. With an allowlist (`model_ids`), the picker shows the ID, not OpenRouter's display name.
- **R3 (confirmed).** Setting `TASK_MODEL_EXTERNAL` to a local Ollama model keeps title, tag, follow-up and query generation local for OpenRouter chats. The connection keeps `connection_type: "external"`. ADR-0005 Accepted.
- **R5 (refined).** Because the allowlist is applied through `model_ids`, Open WebUI never fetches OpenRouter's model list. An offline or slow OpenRouter adds **no** delay to the model list (measured at about 0.1 s against about 11 s without `model_ids`). `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST` (default 10 s) is not tuned. The allowlist must never be empty. A chat on an `OR.` model while OpenRouter is down fails with "Server Connection Error"; local chats are unaffected.
- **R6 (resolved).** Base URL `https://openrouter.ai/api/v1`; key `sk-or-v1-` + 64 hex (73 chars); key info `GET /api/v1/key`; prices are per-token USD strings. Key validation uses `/api/v1/key` only (ADR-0013). Open WebUI endpoints: `POST /api/v1/auths/signin`, `GET /openai/config`, `POST /openai/config/update` (always send `ENABLE_OPENAI_API`), `GET`/`POST /api/v1/tasks/config[/update]` (full object).
- **R9 (corrected).** Open WebUI always sends `HTTP-Referer: https://openwebui.com/` and `X-Title: Open WebUI` to openrouter.ai URLs. Per-connection `headers` can override them. OWH keeps the defaults and sets no custom headers (ADR-0012).
