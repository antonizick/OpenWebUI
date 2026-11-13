# OWH: Architecture

Short and kept in sync by every phase. Details of Open WebUI and OpenRouter behaviour are in `docs/OWH_FINDINGS.md` (Phase 03).

## Current (before OWH)
```
Browser ──> Open WebUI (container `open-webui`, host net, :8080)
              └──> Ollama 127.0.0.1:11434 (local models)
              └──> stored OpenAI connection api.openai.com/v1, empty key (dead leftover)
```

## Target (after Phase 05)
```
Browser ──> Open WebUI (unchanged container, unit, toggle, OCC)
              ├──> Ollama 127.0.0.1:11434          local models, data stays on the laptop
              └──> OpenRouter https://openrouter.ai/api/v1   allowlisted models (`model_ids`), shown as "OR.<id>" (`prefix_id: "OR"`)
                     (connection stored in webui.db; replaces the dead OpenAI entry)
```
Background tasks (titles, tags, follow-ups, search queries) run on a local model (`TASK_MODEL_EXTERNAL`), so only the chat completion goes to OpenRouter (ADR-0005, Accepted in Phase 03). Because the allowlist is applied as `model_ids`, Open WebUI never fetches OpenRouter's model list, so the picker does not wait on OpenRouter when it is offline.

## Real endpoints (Open WebUI 0.13.3, OpenRouter; see `docs/OWH_FINDINGS.md`)
| Purpose | Endpoint |
|---|---|
| Admin sign-in | `POST /api/v1/auths/signin` → Bearer token |
| Read / write connections | `GET /openai/config`, `POST /openai/config/update` (all four fields, `ENABLE_OPENAI_API` always sent) |
| Read / write task model | `GET /api/v1/tasks/config`, `POST /api/v1/tasks/config/update` (full object) |
| Merged model list | `GET /api/models` |
| Local models installed | Ollama `GET http://127.0.0.1:11434/api/tags` |
| Key check | OpenRouter `GET https://openrouter.ai/api/v1/key` (ADR-0013) |
| Price list | OpenRouter `GET https://openrouter.ai/api/v1/models` (public; USD per token as strings) |

Testbed for rehearsals: `scripts/owh-testbed.sh` (container `owh-test-owu`, volume `owh-test-owu-data`, host network, `127.0.0.1:18080`; ADR-0007, ADR-0011).

## What `owh-openrouter` touches
| Thing | Where | Notes |
|---|---|---|
| Dedicated key | `~/.config/owh/openrouter.key` (dir 0700, file 0600) | outside the repo |
| Allowlist | `config/openrouter-models.txt` | in the repo, one model ID per line |
| Pre-apply snapshots | `~/.local/state/owh/snapshots/*.json` (0600 in 0700; contain prior keys) | one per writing `apply`, tagged with the Open WebUI URL; `remove` uses the earliest one for that URL (ADR-0015) |
| Action log | `~/.local/state/owh/owh.log` (0600) | one line per run, no secrets (ADR-0016) |
| Open WebUI config | `webui.db` config table, via the admin API only | never edited directly |
| Launcher | `~/.local/bin/owh-openrouter` (`make install`) | an OS modification, in OSMods |

Nothing in the container, its systemd unit, `Super+Alt+O`, OCC or `open-webui-upgrade` changes. The live Open WebUI is changed only in Phase 05; earlier phases use the throwaway testbed.

## Code map (`src/owh_openrouter/`)
| Module | Role |
|---|---|
| `cli.py` | argparse and the five commands; prompts (`getpass`, `--password-stdin`); prints and logs only through `scrub()`; maps errors to exit codes 0–5 |
| `plan.py` | pure functions: R1 placement (`update`/`replace`/`append`), desired state for `apply` and `remove`, task-model choice, redacted `view()` and `diff()` |
| `webui.py` | Open WebUI 0.13.3 client: sign-in, `/openai/config[/update]` (always all four fields), `/api/v1/tasks/config[/update]` (whole object), `/api/models`, `/api/version` |
| `openrouter.py` | `GET /key` (401/402/429 mapped) and public `GET /models`; `per_million()` price formatting |
| `net.py` | JSON over urllib: timeouts, no redirects, no proxy for loopback, scrubbed `HttpError`/`Unreachable`, URL checks (loopback Open WebUI, https OpenRouter) |
| `snapshot.py` | 0600 snapshots in a 0700 dir, filtered by Open WebUI URL |
| `secrets.py` | key format check and cleaning, `redact()`, `register()`/`scrub()`, atomic 0600 key file |
| `paths.py`, `allowlist.py`, `errors.py` | XDG dirs and permission checks; allowlist parsing; exit-code exceptions |

```
apply:  allowlist + key file ──> OpenRouter /key, /models (validate)
        ──> Open WebUI signin, GET config/tasks/models ──> plan_apply ──> diff
        ──> (no change: stop) ──> snapshot ──> POST config, POST tasks ──> re-read and compare
remove: earliest snapshot for this URL ──> signin, GET ──> plan_remove ──> POST ──> re-read
```

Tests live in `tests/` (`make check`, coverage gate 90 %). `tests/fakes/server.py` holds the fake Open WebUI and the fake OpenRouter (127.0.0.1, in-memory state, request log, failure injection), aligned with `docs/OWH_FINDINGS.md`. `tests/integration/test_testbed.py` (`make test-testbed`, `OWH_TESTBED=1`) runs apply → no-op apply → remove on the real v0.13.3 testbed with a fake OpenRouter on the host and compares the `config` table's `key, value` rows.
