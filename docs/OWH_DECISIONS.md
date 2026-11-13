# OWH: Architecture Decision Log

Lightweight ADRs. Append new decisions at the bottom, and never rewrite history: to reverse a decision, add a new entry that supersedes the old one. Every phase that makes a non-trivial technical choice adds an entry here. Timestamps are `YYYY-MM-DD HH:MM TZ` from `date '+%Y-%m-%d %H:%M %Z'`; a status change (for example `Proposed` → `Accepted`, or `Superseded by ADR-00NN`) is noted in the entry with its own timestamp.

| ID | Timestamp | Decision | Status | Phase |
|---|---|---|---|---|
| ADR-0001 | 2026-11-13 11:20 CST | Project prefix `OWH` | Accepted | 00 |
| ADR-0002 | 2026-11-13 11:20 CST | Dedicated OpenRouter key for Open WebUI | Accepted | 00 |
| ADR-0003 | 2026-11-13 11:20 CST | Curated, prefixed model allowlist | Accepted | 00 |
| ADR-0004 | 2026-11-13 11:20 CST | Configure via Open WebUI admin API (stored config), not env vars | Accepted | 00 |
| ADR-0005 | 2026-11-13 11:20 CST | Background tasks (titles, tags, follow-ups, queries) on a local model | Accepted (2026-11-13 12:06 CST) | 00 (verified 03) |
| ADR-0006 | 2026-11-13 11:20 CST | Python stdlib-only CLI `owh-openrouter`, uv/pytest/ruff for dev | Accepted | 00 |
| ADR-0007 | 2026-11-13 11:20 CST | Rehearse on a throwaway container before touching the live instance | Accepted | 00 |
| ADR-0008 | 2026-11-13 11:20 CST | Owner brainstorming recorded as a planning session in the timeline | Accepted | 00 |
| ADR-0009 | 2026-11-13 11:42 CST | Secret-scan hook: plain `core.hooksPath` script using `gitleaks git --staged`, plus optional pre-commit config | Accepted | 01 |
| ADR-0010 | 2026-11-13 11:48 CST | Install via a launcher script that runs the repo in place, not `uv tool install` | Accepted | 02 |
| ADR-0011 | 2026-11-13 12:06 CST | Testbed on host networking bound to `127.0.0.1:18080` | Accepted | 03 |
| ADR-0012 | 2026-11-13 12:06 CST | Keep Open WebUI's built-in OpenRouter attribution headers; no custom `headers` by default (R9 corrected) | Accepted | 03 |
| ADR-0013 | 2026-11-13 12:06 CST | Validate the key with OpenRouter `GET /api/v1/key`, never via `/models` or Open WebUI `/openai/verify` | Accepted | 03 |
| ADR-0014 | 2026-11-13 12:16 CST | OpenRouter allowlist: eight models (owner question 1) | Accepted | between 03 and 04 |
| ADR-0015 | 2026-11-13 12:35 CST | `remove` restores only OWH's slot; snapshots are scoped to the Open WebUI URL | Accepted | 04 |
| ADR-0016 | 2026-11-13 12:35 CST | CLI secret handling: hidden prompt or stdin/0600 file only, scrub every output line, no redirects | Accepted | 04 |
| ADR-0017 | 2026-11-13 12:35 CST | `apply` keeps hand-made settings: an existing local task model and extra per-connection fields | Accepted | 04 |
| ADR-0018 | 2026-11-13 12:45 CST | No spend management in OWH; any key limit is Nick's, set on openrouter.ai (owner question 2) | Accepted | 05 |
| ADR-0019 | 2026-11-13 12:45 CST | OpenRouter account privacy: training and logging providers allowed (owner question 3) | Accepted | 05 |
| ADR-0020 | 2026-11-13 13:05 CST | Hidden prompts refuse without a terminal; pre-OWH backup through SQLite's backup API | Accepted | 05 |
| ADR-0021 | 2026-11-13 13:45 CST | Port 8080 exposure (S6): keep as is, documented; no binding or firewall change | Accepted | 06 |
| ADR-0022 | 2026-11-13 13:45 CST | Snapshot retention: keep the live pre-apply snapshot, delete testbed snapshots, prune by hand | Accepted | 06 |
| ADR-0023 | 2026-11-13 13:45 CST | `set-key`/`status` warn 30 days before key expiry and stop showing the masked `label` | Accepted | 06 |
---

## ADR-0001: Project prefix `OWH`
**Recorded.** 2026-11-13 11:20 CST (Phase 00)
**Context.** Project documents need a prefix that identifies them out of context.
**Options considered.** `OWH` (OpenWebUI Hybrid), `OWR` (OpenWebUI + OpenRouter).
**Decision.** `OWH`, chosen by Nick; it matches the To Do list name and `OWH_Brainstorming.md`. Unused by other projects (CL, LU2, MM3, OCC, P11, PHX, YTPL2).
**Consequences.** All project documents are `OWH_*`; the vault note is `OWH Implementation Plan.md`.

## ADR-0002: Dedicated OpenRouter key for Open WebUI
**Recorded.** 2026-11-13 11:20 CST (Phase 00)
**Context.** An OpenRouter key already exists for Claude Code's provider switch (`~/.config/ai-provider/openrouter.key`).
**Options considered.** New dedicated key; reuse the ai-provider key.
**Decision.** A new key, created by Nick on openrouter.ai with its own spending limit, stored at `~/.config/owh/openrouter.key` (0600).
**Consequences.** Separate usage in OpenRouter Activity; revoking or rotating it does not affect Claude Code. Account **credit** is still shared by all keys, so a low balance affects both; the per-key limit only caps this key's spend.

## ADR-0003: Curated, prefixed model allowlist
**Recorded.** 2026-11-13 11:20 CST (Phase 00)
**Context.** OpenRouter offers hundreds of models; showing all clutters the picker and makes an expensive pick easy.
**Options considered.** Curated allowlist; all models; free models only.
**Decision.** A short allowlist in a versioned repo file (`config/openrouter-models.txt`), applied through the connection's model filter, with a visible prefix so cloud models are obvious. The exact prefix syntax is verified in Phase 03.
**Consequences.** Adding a model is an edit plus `owh-openrouter apply`. Model IDs are validated against OpenRouter's live list before applying.

## ADR-0004: Configure via Open WebUI admin API (stored config), not env vars
**Recorded.** 2026-11-13 11:20 CST (Phase 00)
**Context.** Open WebUI keeps connection settings as persistent config in `webui.db`; once stored, the DB wins over env vars. The container is recreated by `open-webui-upgrade` from its env diffs.
**Options considered.**

| Option | Pros | Cons |
|---|---|---|
| Scripted admin API | Survives upgrades; key not in `docker inspect`; idempotent, reversible, testable | Needs the admin password per run (hidden prompt) |
| Container env vars | Declarative | Needs a recreate; key visible in `docker inspect`; ignored while DB config exists |
| Manual UI + guide | Simplest | Not reproducible or verifiable by script |

**Decision.** Scripted admin API, chosen by Nick.
**Consequences.** No change to the container, unit, toggle, OCC or `open-webui-upgrade`. The key is stored in `webui.db` and its backups (see spec S3).

## ADR-0005: Background tasks on a local model
**Recorded.** 2026-11-13 11:20 CST (Phase 00)
**Context.** `task.model.external` is empty, so title, tag, follow-up and search-query generation run on the chat model; for an OpenRouter chat that means extra paid calls that send the chat content.
**Options considered.** Local task model; leave as is (chat model); a cheap OpenRouter model.
**Decision (Proposed).** Set the external task model to a local Ollama model (`qwen3:4b-instruct`, else `qwen3:8b`). Phase 03 verifies Open WebUI 0.13.3 accepts this and measures the effect; it then marks this ADR Accepted or supersedes it.
**Consequences.** Only the chat completion goes to OpenRouter; titles use the GPU briefly (Ollama may load a second model; VRAM 8 GB).
**Status change, 2026-11-13 12:06 CST (Phase 03): Accepted.** Verified on the v0.13.3 testbed (`docs/OWH_FINDINGS.md` §4). With `TASK_MODEL_EXTERNAL=""`, a chat on `OR.fake/alpha` sent title, tags and follow-up requests to the upstream (1 chat + 3 task calls). With `TASK_MODEL_EXTERNAL="qwen3:4b-instruct"`, a UI-style chat with background tasks made exactly one upstream request, and the title, tags and follow-ups came from the local model. The rule applies because the OpenRouter connection keeps `connection_type: "external"`. `POST /api/v1/tasks/config/update` needs the full config object, so `apply` changes only this one field of the GET result.

## ADR-0006: Python stdlib-only CLI
**Recorded.** 2026-11-13 11:20 CST (Phase 00)
**Context.** The tool talks JSON to two HTTP APIs and edits config idempotently; existing host tools are bash.
**Options considered.** Bash + curl + jq; Python stdlib; Python with `httpx`.
**Decision.** Python ≥ 3.11, standard library only at runtime (`urllib`, `json`, `getpass`), developed with `uv`, tested with `pytest` against fake servers, linted with `ruff`; `shellcheck` for any shell helpers.
**Consequences.** No runtime dependencies to install; JSON handling and tests are straightforward.

## ADR-0007: Rehearse on a throwaway container first
**Recorded.** 2026-11-13 11:20 CST (Phase 00)
**Context.** The live instance holds Nick's chats and settings.
**Decision.** Phases 03–05 test on a throwaway container (same image tag `v0.13.3`, own volume `owh-test-owu-data`, bound to `127.0.0.1` on a different port, removed afterwards). The live instance is changed only in Phase 05, after a local DB backup.
**Consequences.** Slightly longer path to deploy; no risk to real data before the rehearsal passes.

## ADR-0008: Owner brainstorming recorded as a planning session
**Recorded.** 2026-11-13 11:20 CST (Phase 00)
**Context.** Nick asked (2026-11-13, during planning) that the brainstorming timestamps appear in the timeline as planning, for an accurate record.
**Decision.** A Phase Log entry `Planning: owner brainstorming` with `started 2026-11-13 10:03 CST · finished 2026-11-13 10:59 CST`, the first and last timestamps in `OWH_Brainstorming.md`. The generator already draws `Planning:` entries in the Planning lane; no script change.
**Consequences.** The Planning lane starts at 10:03, before the Phase 00 session (11:02).

## ADR-0009: Secret-scan hook via `core.hooksPath`
**Recorded.** 2026-11-13 11:42 CST (Phase 01)
**Context.** The phase prompt asked for `gitleaks protect --staged`. The installed gitleaks (8.30.1) replaces `protect` with `gitleaks git --staged`.
**Options considered.** Only the pre-commit framework; only a plain hook; both.
**Decision.** A plain `scripts/git-hooks/pre-commit` (enabled with `git config core.hooksPath scripts/git-hooks`) running `gitleaks git --staged --redact --config .gitleaks.toml`, plus an optional `.pre-commit-config.yaml` for the pre-commit framework. The hook fails closed: it refuses to commit if gitleaks is missing. Rule: `sk-or-v1-[0-9a-f]{40,}` (the real key is `sk-or-v1-` + 64 hex characters, checked without printing it); allowlist only `sk-or-v1-TESTKEY...`.
**Consequences.** Works with no extra tooling. `core.hooksPath` is per clone, so each fresh clone must run the one-line setup (documented in CONTRIBUTING); CI gitleaks is the backstop.

## ADR-0010: Install as a launcher script
**Recorded.** 2026-11-13 11:48 CST (Phase 02)
**Context.** `make install` must put `owh-openrouter` on `PATH`. The prompt allowed a launcher or `uv tool install .`.
**Options considered.** (a) `~/.local/bin/owh-openrouter` running `uv run --project <repo> owh-openrouter "$@"`; (b) `uv tool install .`.
**Decision.** (a). Edits to the repo take effect at once with no reinstall, `uninstall` is deleting one file, and there is no second copy of the code in `~/.local/share/uv/tools` to drift. The cost is that the repo must stay at its path and `uv` must be on `PATH`, both true for this single-machine tool.
**Consequences.** One file to document in OSMods in Phase 05; `make install` is not run before then.

## ADR-0011: Testbed on host networking bound to 127.0.0.1
**Recorded.** 2026-11-13 12:06 CST (Phase 03)
**Context.** The Phase 03 prompt asked for a bridge-network testbed with `host.docker.internal`, falling back to `--network host` with `PORT=18080`. Ollama listens on `127.0.0.1:11434` only. From a bridge container, `curl http://host.docker.internal:11434` timed out (exit 28).
**Options considered.** (a) Bridge, and make Ollama listen on the Docker bridge address (a host OS change to `prometheus-ollama.service`); (b) host network with `PORT=18080`, as the prompt's fallback; (c) as (b), plus `HOST=127.0.0.1`.
**Decision.** (c). `start.sh` honours `HOST`, so uvicorn binds `127.0.0.1:18080` only (checked with `ss -ltn`), the same exposure as the prompt's `-p 127.0.0.1:18080:8080`. No host change is needed, and the testbed reaches Ollama and any fake upstream on `127.0.0.1` the same way the live container does.
**Consequences.** The testbed shares the host network namespace, but its name, volume, port and state dir are distinct, and the script refuses the live names. A fake OpenRouter for integration tests listens on `127.0.0.1:<port>` and is reachable by the testbed unchanged.

## ADR-0012: Attribution headers (spec R9 corrected)
**Recorded.** 2026-11-13 12:06 CST (Phase 03)
**Context.** Spec R9 assumed attribution headers are not sent unless configured. Open WebUI 0.13.3 hard-codes `HTTP-Referer: https://openwebui.com/` and `X-Title: Open WebUI` for every request to a URL containing `openrouter.ai` (`utils/headers.py:36-49`; seen on the testbed). Per-connection `headers` are merged last and can override them.
**Options considered.** (a) Leave Open WebUI's defaults; (b) override them with blanks; (c) set OWH's own values.
**Decision.** (a). The headers name the app, not Nick, and the dedicated key already separates usage. Overriding an upstream identifier that Open WebUI's licence asks to keep gains nothing. `apply` sets no `headers` field. Nick can add one later through the connection's `headers` if he wants.
**Consequences.** Requests appear in OpenRouter's app rankings as "Open WebUI". The user guide says so.

## ADR-0013: Key validation via `GET /api/v1/key`
**Recorded.** 2026-11-13 12:06 CST (Phase 03)
**Context.** OpenRouter's `GET /api/v1/models` returned 200 for an invalid key. Open WebUI's `POST /openai/verify` only proxies `{url}/models`, so it would report any key as valid.
**Decision.** `set-key` (and `status`) validate the key with OpenRouter `GET https://openrouter.ai/api/v1/key` and `Authorization: Bearer <key>`. A 200 with a `data` object means valid, and 401 means rejected (`{"error":{"code":401,"message":"User not found."}}`). The format check `^sk-or-v1-[0-9a-f]{64}$` (73 characters) runs first.
**Consequences.** Validation costs nothing (no completion). The label, limit and usage come from the same response, so `status` can show them.

## ADR-0014: OpenRouter allowlist (owner question 1)
**Recorded.** 2026-11-13 12:16 CST (Nick's answer after Phase 03)
**Context.** Phase 03 proposed five models with live prices (`docs/OWH_FINDINGS.md` §7). Nick accepted all five and added three.
**Decision.** The allowlist is these eight IDs. Prices are $/M input / output, fetched 2026-11-13 12:03 CST, all from OpenRouter's live list:

| ID | Role | Context | In | Out |
|---|---|---:|---:|---:|
| `anthropic/claude-sonnet-5.5` | strong general | 1,000,000 | 2.00 | 10.00 |
| `anthropic/claude-haiku-5.5` | cheap, fast | 1,000,000 | 0.10 | 0.50 |
| `google/gemini-4-hydrogen` | long context, multimodal | 1,048,576 | 1.50 | 7.50 |
| `openai/gpt-6.1-terra` | coding | 1,050,000 | 1.00 | 5.00 |
| `google/gemma-4-31b-it:free` | free | 262,144 | 0 | 0 |
| `deepseek/deepseek-v4.1-flash-1017` | very cheap long input (added by Nick) | 1,048,576 | 0.038 | 0.50 |
| `xiaomi/mimo-v2.6-pro` | added by Nick | 1,050,000 | 0.435 | 0.87 |
| `z-ai/glm-5.3-flash` | cheapest output (added by Nick) | 1,048,576 | 0.040 | 0.078 |

**Consequences.** Phase 05 writes these IDs to `config/openrouter-models.txt` and checks them with `owh-openrouter models` (prices are re-fetched then). The free model is rate-limited and its providers may log prompts, depending on owner question 3. `deepseek/deepseek-v4.1-flash-1017` is a dated snapshot and may be retired; `models` flags unknown IDs.

## ADR-0015: Surgical `remove`, snapshots scoped to one Open WebUI
**Recorded.** 2026-11-13 12:35 CST (Phase 04)
**Context.** `remove` must restore the pre-OWH values exactly (S7), but between `apply` and `remove` Nick may add another connection or change the task settings in the UI. Restoring the whole snapshot would silently undo those. Phase 05 also rehearses on the testbed with the same `~/.local/state/owh/`, so "the earliest snapshot" could be one taken of the testbed.
**Options considered.** (a) Write the whole snapshot back. (b) Restore only what OWH changed: its connection slot, `ENABLE_OPENAI_API` and `TASK_MODEL_EXTERNAL`. Separately: a state dir per instance, or a `webui_url` field in each snapshot.
**Decision.** (b). Each snapshot records `webui_url`, the OpenRouter `url`, the `slot` and the `mode` (`replace`, `append` or `update`) plus the full prior OpenAI and task configs. `remove` finds the OpenRouter connection by URL (wherever it is now), puts back the snapshot's entry for a `replace`/`update` slot or deletes it (re-indexing `OPENAI_API_CONFIGS`) for `append`, restores `ENABLE_OPENAI_API` and `TASK_MODEL_EXTERNAL`, and leaves everything else as it is now. By default it uses the earliest snapshot **of the same Open WebUI URL**; `--snapshot FILE` picks another (a one-step rollback), and a snapshot of a different URL is refused (exit 3). Snapshots are kept.
**Consequences.** If nothing else changed, the result equals the snapshot. On the testbed all 403 `config` rows matched byte-for-byte (`key`, `value`) after apply → no-op apply → remove. Connections Nick adds after OWH survive `remove`. A second `remove` is a no-op.

## ADR-0016: Secret handling in the CLI
**Recorded.** 2026-11-13 12:35 CST (Phase 04)
**Context.** Spec S1–S2: the key, the admin password and the session token must never reach argv, env, logs, exceptions or output. Tests and the Phase 05 rehearsal need a non-interactive way in.
**Decision.**
- Secrets come in only through `getpass`, `--password-stdin` (one line on stdin, as `docker login` does), or a 0600 file (`set-key --from-file`, and the key file itself). No env variables and no argv.
- Every secret seen in a run is registered, and every printed or logged line goes through `scrub()`, which removes the registered values and anything shaped like `sk-or-v1-…` or a JWT. HTTP errors carry only a short, scrubbed message (`detail` or `error.message`) and the URL path, raised `from None` so no chained exception holds a body.
- Redirects are never followed, so an `Authorization` header cannot be forwarded to another host. Loopback URLs bypass proxies. The Open WebUI URL must be loopback unless `--allow-remote` is given, and the OpenRouter URL must be https unless it is loopback (the fakes). `models` fetches the public list without the key.
- The action log `~/.local/state/owh/owh.log` (0600) gets one line per run: timestamp, command, result, the key's first 9 characters and a short detail.
**Consequences.** Scrubbing can over-redact. If the password is a common word, that word shows as `<redacted>` in messages. That is the safe direction. A test runs the whole lifecycle and checks that the key, password and token appear in no output or log line, that the key reaches Open WebUI only in `POST /openai/config/update` and OpenRouter only as the `Authorization` header of `GET /api/v1/key`, and that the password goes only to `POST /api/v1/auths/signin`.

## ADR-0017: `apply` keeps hand-made settings
**Recorded.** 2026-11-13 12:35 CST (Phase 04)
**Context.** `apply` must be idempotent and must not fight Nick's own choices made in the admin UI.
**Decision.**
- The connection entry is merged: OWH sets `enable`, `prefix_id: "OR"`, `connection_type: "external"` and `model_ids`, and keeps any other field already on that entry (for example `tags` added in the UI).
- The external task model is set to `qwen3:4b-instruct`, else `qwen3:8b` (ADR-0005), only if the current value is empty or not a local model. A local model that is already set is kept. `--task-model ID` chooses one explicitly. A model missing from Open WebUI's local list is never set, because Open WebUI would silently fall back to the chat model. Without a candidate, `apply` warns and leaves the value alone.
- Placement follows R1: reuse the slot with the OpenRouter URL, else replace the first `https://api.openai.com/v1` entry with an empty key, else append.
**Consequences.** A re-apply after a UI tweak is still a no-op. Changing the allowlist updates `model_ids` in place and writes a new snapshot (`mode: update`).

## ADR-0018: No spend management in OWH (owner question 2)
**Recorded.** 2026-11-13 12:45 CST (Phase 05)
**Context.** Spec S5 and ADR-0002 assumed the new key would carry a spending limit agreed in this project (proposed default $20/month).
**Options considered.** $10, $20 or $50 per month on the key; no limit from this project.
**Decision.** Nick: "no limit... I have spent limits already attached to the API key. So spending is not something we need to manage at the application layer." OWH sets, checks and enforces no spending limit. Whatever limit the key or account has is Nick's, managed on openrouter.ai.
**Consequences.** `set-key` and `status` still show the key's `limit` field as reported by OpenRouter, for information only. Phase 06's "spend guard" task no longer compares the limit with an agreed value; it only documents what Open WebUI shows when a limit or the credit runs out. The ≤ $0.25 cap on build-time test spend per phase is unchanged. Supersedes the "$20/month" default in spec §3.5 and the "own spending limit" wording in ADR-0002 and S5 (spec Amendments v3).

## ADR-0019: OpenRouter privacy allows training and logging providers (owner question 3)
**Recorded.** 2026-11-13 12:45 CST (Phase 05)
**Context.** OpenRouter's account privacy settings decide whether requests may be routed to providers that log or train on prompts. The setting is account-wide, so it also covers the AI Provider Switch key.
**Options considered.** Block them (proposed default); block them and require ZDR; allow them.
**Decision.** Allow them (Nick's answer). OWH changes no account setting; this records the choice.
**Consequences.** All allowlisted models, including the free ones, stay routable. Chats with `OR.` models may be logged or used for training by the upstream provider, so the docs say so (S4). Local models are unaffected.

## ADR-0020: Hidden prompts refuse without a terminal; consistent DB backup
**Recorded.** 2026-11-13 13:05 CST (Phase 05)
**Context.** The phase prompt had Nick run `set-key` and `apply` through Claude Code's `!` prefix. That runs without a TTY: `getpass` warned "Can not control echo" and then hit EOF, crashing with a traceback (nothing was read or written). Separately, the live `webui.db` is in WAL mode with recent changes still in `webui.db-wal`, so the prompt's `docker cp webui.db` backup would have missed them.
**Decision.**
- `read_secret` turns `getpass.GetPassWarning` into an error and catches `EOFError`; both are a refusal (exit 3) with a hint to use a terminal window, `--from-file` or `--password-stdin`. A secret is never read through getpass's echoing fallback. `set-key` uses the same helper. This extends ADR-0016.
- The pre-OWH backup is taken with SQLite's online backup API inside the container (source opened `mode=ro`), copied out with `docker cp`, chmod 0600, and checked with `PRAGMA integrity_check`.
**Consequences.** Nick runs the commands that prompt in a separate terminal window. The backup includes every committed write. Both are in the user guide, and the Phase 05 prompt is corrected.

## ADR-0021: Port 8080 exposure (S6): keep as is, documented
**Recorded.** 2026-11-13 13:45 CST (Phase 06)
**Context.** Spec S6: Open WebUI uses host networking with no `HOST`, so port 8080 listens on every interface (Wi-Fi, `tailscale0`, Docker bridges) while it runs, and a paid key now sits behind the login. Read-only facts: ufw active, default input DROP, no allow rule for 8080; one Open WebUI user (admin), signup off, API keys off. Tailscale's own firewall rules could not be read without root.
**Options considered.** (A) keep as is and document it; (B) bind to loopback with `-e HOST=127.0.0.1` (one container recreate; survives `open-webui-upgrade`); (C) an explicit `sudo ufw deny 8080/tcp`. Table in `docs/OWH_THREAT-MODEL.md` §5. Recommended: B if Open WebUI is never used from another device, else C.
**Decision.** Nick chose A. Nothing was changed on the live container or the firewall.
**Consequences.** The residual risk (reachability depends on ufw staying on and on the admin password; tailnet path unverified) is recorded in the threat model §7 and the OSMods note. B and C stay one step away if Nick changes his mind.

## ADR-0022: Snapshot retention
**Recorded.** 2026-11-13 13:45 CST (Phase 06)
**Context.** Phase 05 left two snapshots in `~/.local/state/owh/snapshots/`: the testbed rehearsal (`webui_url` `http://127.0.0.1:18080`) and the live pre-apply one (`http://127.0.0.1:8080`). Phase 05 assumed both held the key. The Phase 06 sweep showed neither does: a snapshot holds the *prior* connection config, and before OWH that was `api.openai.com` with an empty key. A snapshot taken by a later `apply` after a key rotation would hold the old key.
**Options considered.** Automatic pruning (keep N); keep everything; keep the live undo point and drop the rest by hand.
**Decision.** Keep the live pre-apply snapshot indefinitely: it is what `remove` restores (the earliest one per Open WebUI URL). The testbed snapshot was deleted (its Open WebUI no longer exists and `remove` filters it out anyway). Tests and future rehearsals use a temporary `--state-dir`. No automatic pruning: deleting an undo point silently is worse than a few 0600 files. After a rotation, the docs say to delete snapshots newer than the earliest one once the new key works, then revoke the old key.
**Consequences.** No code change. SECURITY.md and the user guide describe what a snapshot holds and when to delete one.

## ADR-0023: Key expiry warning; no masked `label`
**Recorded.** 2026-11-13 13:45 CST (Phase 06)
**Context.** The dedicated key has `expires_at` 2027-11-13 (findings §6a). After that, `OR.` chats fail. OpenRouter's `label` is a masked preview of the key itself, which the scrubber turned into `sk-or-v1-… (12 chars)...275`.
**Decision.** `set-key` and `status` show `limit`, `limit_remaining`, `limit_reset`, `usage`, `usage_monthly` (set-key) and `expires_at`. When `expires_at` is 30 days away or less, or already past, they print a warning on stderr. `status --json` carries it as `openrouter_key.warning`. Exit codes do not change. A timestamp without a time zone or one that does not parse gives no warning, rather than a guess. `label` is no longer shown.
**Consequences.** Nick sees the expiry in any `status` run from 2027-10-14 on. Rotation steps are in SECURITY.md.
