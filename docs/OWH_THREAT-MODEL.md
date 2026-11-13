# OWH: Threat Model

**Scope:** the OpenRouter connection that `owh-openrouter` adds to Nick's local Open WebUI v0.13.3 (Docker container `open-webui`, host network, port 8080), next to the local Ollama.
**Written:** 2026-11-13 13:45 CST (Phase 06). The evidence (sweep, measurements) is in `docs/OWH_FINDINGS.md` §8. Decisions: ADR-0016, ADR-0018, ADR-0019, ADR-0021, ADR-0022.

## 1. Assets
| Asset | Why it matters | Where it lives |
|---|---|---|
| **Dedicated OpenRouter key** | Spends money from the OpenRouter account credit, which the AI Provider Switch key shares. Its `limit` is $50/month and it expires 2027-11-13; both are set by Nick on openrouter.ai (ADR-0018). | See §3 |
| **Chats and uploaded files** | Private conversations, documents and RAG excerpts. | `webui.db` and `uploads/` in the `open-webui` volume, plus every backup of it |
| **Open WebUI admin account** | The only account (signup off, default role `pending`). An admin session can read every connection key in clear text (`GET /openai/config`) and can point the connection at any URL. | `user`/`auth` tables; the password is in Nick's head or password manager only |
| **Open WebUI's `WEBUI_SECRET_KEY`** | Signs session JWTs; anyone who has it can mint an admin session. | Container env (`docker inspect`), not managed by OWH |

## 2. Trust boundaries
```
 ┌──────────────────────── Nick's laptop (single user) ─────────────────────────┐
 │  terminal ──owh-openrouter──▶ Open WebUI :8080 (loopback API) ──▶ Ollama 127.0.0.1:11434
 │     │ key file 0600              │ webui.db (key in config row)                 │
 │     │                            │                                              │
 └─────┼────────────────────────────┼──────────────────────────────────────────────┘
       │ https, Authorization       │ https, Authorization (only for OR. chats)
       ▼                            ▼
   openrouter.ai  ──────────────▶ upstream model providers (Anthropic, Google, OpenAI,
   (/key check, public /models)      DeepSeek, Xiaomi, Z.ai…); may log or train (ADR-0019)
```
1. **Laptop ↔ OpenRouter:** TLS. The CLI sends the key only to `GET /api/v1/key` over https and never follows redirects. Open WebUI sends it on every `OR.` chat.
2. **OpenRouter ↔ upstream providers:** out of Nick's control except through OpenRouter account settings (logging and training providers allowed, ADR-0019).
3. **Network ↔ port 8080:** host networking means Open WebUI listens on all interfaces while it runs (§5, S6).
4. **Laptop ↔ Google Drive:** `~/Documents` (the vault, including the repo through the `02 Projects/Work` symlink) syncs, so nothing secret may sit there.

## 3. Where the key is stored (verified 2026-11-13 13:39 CST, findings §8.1)
| Store | Contains the key? | Protection |
|---|---|---|
| `~/.config/owh/openrouter.key` | yes (the source of truth) | file 0600, dir 0700; `secrets.read_key` refuses group/world access |
| `webui.db`, table `config`, row `openai.api_keys` (in the `open-webui` volume) | yes, in clear text (one row; no other table or volume file) | `/var/lib/docker` is root-only (0710); Open WebUI returns it only to admin sessions |
| `~/.local/share/open-webui-upgrade/backups/*.tar.gz` | not yet (both backups predate OWH); **every upgrade from now on** adds a copy | files 0600, dir 0700; pruned to the last 2 versions by `open-webui-upgrade prune` |
| `~/.local/share/open-webui-backups/` (manual) | not in the pre-OWH backup; any later manual copy will | dir 0700; the pre-OWH backup is 0600 (two older 2026-11-09 copies are 0644 inside the 0700 dir) |
| `~/.local/state/owh/snapshots/*.json` | **no**: a snapshot holds the *prior* connection config, which had no OpenRouter key. A snapshot taken after a key rotation would hold the old key | files 0600, dir 0700; retention: ADR-0022 |
| `~/.local/state/owh/owh.log` | no (first 9 characters only, `sk-or-v1-`) | 0600 |
| The repo and its whole history, `~/Documents`, shell history, `docker inspect`, `docker logs`, the user journal, the process list | no | gitleaks hook and CI; hidden prompt or 0600 file only (ADR-0016, ADR-0020) |

## 4. Threats and mitigations
| # | Threat | Mitigation | Residual |
|---|---|---|---|
| T1 | Key committed to git or synced to Drive | gitleaks pre-commit hook and CI with an OpenRouter rule; key lives outside the repo and the vault; sweeps of history and `~/Documents` found 0 | A key pasted into a vault note by hand would sync. Low. |
| T2 | Key in argv, env, shell history or logs | hidden prompt or `--from-file` (0600) only; no env var; every printed or logged line goes through `scrub`; prompts refuse without a TTY rather than echo (ADR-0020) | None found. |
| T3 | Key leaked through an error message | `net.HttpError` carries a scrubbed, 200-character detail; tracebacks are never shown; `GET /openai/config` responses are never printed unredacted (code review, §6) | Low. |
| T4 | Key sent to the wrong host | no redirects; OpenRouter URL must be https unless loopback; Open WebUI URL must be loopback unless `--allow-remote`; the model list is fetched without the key | An admin could repoint the connection in the UI; that needs the admin password. |
| T5 | Someone on the network reaches Open WebUI and spends on `OR.` models, or reads chats | login required, signup off, API keys off, one admin; ufw active with default input DROP and no rule for 8080 | Port 8080 listens on all interfaces under host networking; protection relies on ufw staying on and on the password. Tailscale's own rules were not inspectable without root. Accepted by Nick (ADR-0021). Medium-low. |
| T6 | Stolen `WEBUI_SECRET_KEY` (from `docker inspect` or an upgrade recipe) lets someone forge an admin session | only local users can run `docker inspect` (docker group); out of OWH's scope | Unchanged by OWH. Low on a single-user laptop. |
| T7 | Backups of the volume spread the key | upgrade backups and manual backups are 0600/0700 and live outside `~/Documents`; docs say never to copy them into the vault | Every upgrade adds a copy until pruned. After a rotation, old backups hold a revoked key, which is harmless. |
| T8 | Unexpected spend: expensive models, runaway background tasks, a leaked key | allowlist of eight priced models; titles, tags and follow-ups on local `qwen3:4b-instruct` (ADR-0005, verified: key usage = the chat alone); the key's own $50/month limit on openrouter.ai (Nick's, ADR-0018) | A long chat on Sonnet 5.5 still costs money; that is the feature. |
| T9 | Chat content leaves the laptop | only for `OR.` models; docs say so (S4); local models stay local; the OpenRouter privacy setting allows logging/training providers (ADR-0019) | Accepted by Nick. |
| T10 | OpenRouter down or slow stalls Open WebUI | `model_ids` allowlist, so the model list never contacts OpenRouter: 0.12–0.13 s with the upstream closed or unroutable, same as healthy (findings §8.3) | An `OR.` chat with an unroutable upstream can wait up to `AIOHTTP_CLIENT_TIMEOUT` (300 s); local chats are unaffected. |
| T11 | An upgrade loses or resets the connection | stored config wins over env; recreate with `open-webui-upgrade`'s own recipe functions kept every OWH row (findings §8.2) | Only `ENABLE_PERSISTENT_CONFIG=false` would change this; nothing sets it. |
| T12 | The key expires (2027-11-13) and `OR.` chats start failing | `set-key` and `status` warn from 30 days before `expires_at` (Phase 06); rotation steps in SECURITY.md | Nick has to run `status` (or see the failure) to notice. |
| T13 | A bad `apply` breaks the live config | dry run, snapshot before the first write, verify after, `remove` restores only OWH's slot (ADR-0015); a full pre-OWH DB backup | Low. |

## 5. S6: port 8080 under host networking
**Facts (2026-11-13 13:45 CST, read-only):** the container sets no `HOST`, so uvicorn binds `0.0.0.0:8080` while it runs. Interfaces: `wlo1` 192.168.40.31/24, `tailscale0` 100.103.35.26, Docker bridges. `ufw` is active with `DEFAULT_INPUT_POLICY="DROP"` and no allow rule for 8080 (allow rules exist only for 53317 and Docker DNS, plus `clbr0` for another project). Open WebUI: one user (admin), `ui.enable_signup=false`, default role `pending`, `auth.enable_api_keys=false`. Whether `tailscaled`'s own `ts-input` rules accept tailnet traffic before ufw sees it could not be checked without root.

| Option | Pros | Cons |
|---|---|---|
| **A. Keep as is, documented** | No change to the live container or firewall; ufw's default DROP already blocks the LAN; login, signup off and no API keys guard the app | Relies on ufw staying enabled; tailnet reachability unverified; a weak admin password would be the only barrier if ufw were off |
| B. Bind to loopback (`-e HOST=127.0.0.1`, one recreate) | Nothing off the laptop can connect, Tailscale included; survives `open-webui-upgrade` (its recipe keeps the env diff) | Needs a container recreate; ends any use from another device; a container env change that ADR-0004 otherwise avoids |
| C. Explicit `sudo ufw deny 8080/tcp` | No container change; documents intent in the firewall; covers `tailscale0` if ufw sees that traffic | Still depends on ufw being on; may not beat Tailscale's own accept rules; a root change Nick has to make |

**Recommendation offered:** B if Open WebUI is never used from another device, else C. **Nick's decision (recorded 2026-11-13 13:45 CST): A, keep as is, documented** (ADR-0021). Nothing was changed. If Nick ever wants it, B is one recreate: add `-e HOST=127.0.0.1` and keep everything else, and C is one root command.

## 6. Code review for secret leaks (Phase 06)
- Output: the only `print` calls are `say` and `warn`, which pass through `scrub` (registered secrets, anything shaped like `sk-or-v1-…`, and JWTs). There is no `logging` module use. The action log line is scrubbed as well.
- Requests: request bodies are never printed. `HttpError` holds a scrubbed body excerpt only. `Unreachable` holds a scrubbed reason and the URL's origin, not its path or query.
- Prompts: `getpass` only, refusing without a TTY. `--password-stdin` and `--from-file` (0600 enforced) are the alternatives.
- argparse never sees a secret (there is no key or password option), so a usage error cannot echo one.
- `status` no longer shows `label` (OpenRouter's masked preview of the key itself; findings §6a).
- **Nothing found that leaks.** Tests in `tests/test_commands.py` and `tests/test_secrets.py` assert that the key and password never appear in output or the log.

## 7. Residual risks Nick accepts
- Port 8080 on all interfaces, protected by ufw and the login (ADR-0021).
- The key in clear text in `webui.db` and in every later volume backup (inherent to Open WebUI; S3).
- Chats with `OR.` models go to OpenRouter and to providers that may log or train (ADR-0019).
- Spend is bounded only by the key's limit on openrouter.ai, which Nick owns (ADR-0018).

## 8. Found outside OWH's scope (reported, not changed)
- `~/.bash_history` holds one line `ai-provider set-key sk-or-v1-…` with the **AI Provider Switch** key (a different key; the OWH key is not in it). Suggested fix for Nick: remove that line (`history -d` or edit the file), then consider rotating that key.
