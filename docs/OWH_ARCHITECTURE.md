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
              └──> OpenRouter https://openrouter.ai/api/v1   allowlisted models, prefix "OR."
                     (connection stored in webui.db; replaces the dead OpenAI entry)
```
Background tasks (titles, tags, follow-ups, search queries) run on a local model so only the chat completion goes to OpenRouter (ADR-0005, verified in Phase 03).

## What `owh-openrouter` touches
| Thing | Where | Notes |
|---|---|---|
| Dedicated key | `~/.config/owh/openrouter.key` (dir 0700, file 0600) | outside the repo |
| Allowlist | `config/openrouter-models.txt` | in the repo, one model ID per line |
| Pre-apply snapshots | `~/.local/state/owh/` (0600, contain the key) | used by `remove` |
| Open WebUI config | `webui.db` config table, via the admin API only | never edited directly |
| Launcher | `~/.local/bin/owh-openrouter` (`make install`) | an OS modification, in OSMods |

Nothing in the container, its systemd unit, `Super+Alt+O`, OCC or `open-webui-upgrade` changes. The live Open WebUI is changed only in Phase 05; earlier phases use the throwaway testbed.
