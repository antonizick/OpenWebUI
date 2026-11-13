# OWH: User Guide (draft)

**Status:** steps as run on the live instance, 2026-11-13 13:05 CST (Phase 05). Phase 07 finalises the guide.

`owh-openrouter` adds your OpenRouter account to the local Open WebUI as a second backend next to Ollama. You then pick either a local model or an `OR.`-prefixed OpenRouter model in the model picker. It changes only Open WebUI's stored settings, through its admin API. The container, its unit, `Super+Alt+O`, OCC and `open-webui-upgrade` stay as they are.

## 1. Install
```
cd /home/nick/Work/OpenWebUI
make install                 # writes ~/.local/bin/owh-openrouter (runs the repo in place, ADR-0010)
owh-openrouter --help
```
Without installing: `uv run --project /home/nick/Work/OpenWebUI owh-openrouter …`.

Run `make install` from the **main checkout**: the launcher hard-codes the directory it was installed from.

**Use a real terminal window.** `set-key`, `apply`, `status` and `remove` read the key or the admin password at a hidden prompt. Without a terminal (for example through Claude Code's `!` prefix) they refuse with exit 3 rather than read a secret that could be echoed. In scripts, use `--from-file` or `--password-stdin`.

## 2. Store the key: `set-key`
Create a **new, dedicated** key on openrouter.ai for Open WebUI. Do not reuse the Claude Code provider key. Any spending limit is yours to set there; OWH does not manage spend (ADR-0018). Keys expire (the live one on 2027-11-13), so rotate before then (§7). Then run:
```
owh-openrouter set-key
```
The key is read at a hidden prompt. The command trims whitespace and rejects control characters (stray arrow keys) or anything that is not `sk-or-v1-` + 64 hex characters. It checks the key live with OpenRouter (`GET /api/v1/key`). Only then does it write `~/.config/owh/openrouter.key` (directory 0700, file 0600, atomic). It prints the first 9 characters, the length, and the key's label, limit and usage.
- A different stored key is replaced only after you confirm, or with `--force`.
- `--from-file PATH` reads the key from a 0600 file instead of the prompt.
- Errors: "key rejected" (401), "out of credit or the key's spending limit is reached" (402), "rate limited" (429).

## 3. Choose models: `models`
The allowlist is `config/openrouter-models.txt`, one OpenRouter model ID per line, with `#` comments allowed.
```
owh-openrouter models                     # table of the allowlisted models: ID, name, context, $/M in and out
owh-openrouter models --search claude     # search all ~470 models; * marks the allowlisted ones
owh-openrouter models --json
```
Prices come live from OpenRouter in dollars per million tokens. `free` means a `:free` model, and `variable` means a router. An ID that OpenRouter does not know is flagged, and the command exits 1. An empty allowlist is refused: Open WebUI would then list every model and wait up to 10 s on OpenRouter whenever it is offline.

## 4. Connect: `apply`
```
owh-openrouter apply --dry-run      # show what would change (keys redacted), write nothing
owh-openrouter apply                # asks for the admin e-mail (or --email) and password (hidden)
```
What `apply` does:
1. It checks the allowlist (all IDs known to OpenRouter) and the stored key (live).
2. It signs in to Open WebUI as an admin.
3. It puts OpenRouter in the slot of the unused `https://api.openai.com/v1` entry (R1). A connection with a key or another URL is never overwritten; OWH then appends and says so. The connection gets `prefix_id: "OR"` and `model_ids` = your allowlist.
4. It sets the task model for cloud chats to a local model (`qwen3:4b-instruct`, else `qwen3:8b`), so titles, tags and follow-ups never go to OpenRouter (ADR-0005). It keeps a local task model you already chose. `--task-model ID` picks one.
5. Before the first write, it saves the exact prior values to `~/.local/state/owh/snapshots/<time>.json` (0600). It then writes and re-reads to verify.

Running `apply` again with nothing changed prints "already up to date; nothing written". No restart of Open WebUI is needed: the change is live at once (refresh the browser tab). After you edit the allowlist, `apply` updates the model list in place.

## 5. Check: `status`
```
owh-openrouter status           # asks for the admin password; shows everything
owh-openrouter status --no-login
owh-openrouter status --json
```
`status` shows:
- the Open WebUI version;
- each connection: URL, on or off, prefix, number of allowlisted models, redacted key, and whether it matches the key file;
- the task model, and whether it is local;
- how many OpenRouter and local models the picker lists;
- the OpenRouter key's limit and usage;
- the number of snapshots.

## 6. Undo: `remove`
```
owh-openrouter remove                    # restore from the earliest snapshot of this Open WebUI
owh-openrouter remove --snapshot FILE    # or a specific one (one step back)
owh-openrouter remove --delete-key       # also delete ~/.config/owh/openrouter.key (asks first; --yes skips the question)
```
`remove` restores only what OWH changed: its connection slot, the OpenAI on/off switch and the cloud task model. Connections you added later stay. The snapshot is kept. A second `remove` does nothing. If you delete the key file, also revoke the key on openrouter.ai.

## 7. Rotate the key
Create a new key on openrouter.ai, then `owh-openrouter set-key` (confirm the replacement) and `owh-openrouter apply`. Then revoke the old key on openrouter.ai.

## What was run on the live instance (2026-11-13 13:05 CST, Phase 05)
1. `set-key` in a terminal window (the `!` attempt refused; see §1). The key is 0600, separate from `~/.config/ai-provider/openrouter.key`, which was untouched.
2. `make install` from the main checkout.
3. Rehearsal on the testbed with the real key: `owh-testbed.sh up`; `owh-openrouter --webui-url http://127.0.0.1:18080 apply --email owh-test@localhost --password-stdin < ~/.local/state/owh/testbed/admin-password`; one chat on `OR.z-ai/glm-5.3-flash` ("OK", $0.0000077); `remove`; `owh-testbed.sh down`.
4. A consistent DB backup through SQLite's backup API (the live DB is in WAL mode, so a plain `docker cp webui.db` misses recent writes):
   ```
   docker exec open-webui python3 -c "import sqlite3; s=sqlite3.connect('file:/app/backend/data/webui.db?mode=ro',uri=True); d=sqlite3.connect('/tmp/owh-pre.bak'); s.backup(d)"
   docker cp open-webui:/tmp/owh-pre.bak ~/.local/share/open-webui-backups/webui.db.<stamp>.pre-owh.bak && docker exec open-webui rm /tmp/owh-pre.bak
   chmod 600 ~/.local/share/open-webui-backups/webui.db.*.pre-owh.bak
   ```
5. `apply --dry-run`, `apply`, `apply` again (no-op), `status`, all in a terminal window.
6. Checked in the browser: both backends answer from the picker.

**Full restore from that backup** (also discards chats made since): `open-webui-stop`, then `docker run --rm -v open-webui:/data -v ~/.local/share/open-webui-backups:/b alpine sh -c 'cp /b/webui.db.<stamp>.pre-owh.bak /data/webui.db && rm -f /data/webui.db-wal /data/webui.db-shm'`, then `open-webui-start`.

## Options for every command
| Option | Meaning |
|---|---|
| `--webui-url URL` | default `http://127.0.0.1:8080`; must be on this machine unless `--allow-remote` |
| `--openrouter-url URL` | default `https://openrouter.ai/api/v1`; https unless it is a loopback URL (tests) |
| `--state-dir`, `--config-dir` | default `~/.local/state/owh`, `~/.config/owh` |
| `--timeout S` | seconds per request (default 15) |
| `--json` | machine-readable output (`models`, `status`) |
| `--email`, `--password-stdin` | admin login for `apply`, `status`, `remove`; `--password-stdin` reads one line from stdin (for scripts) |

Global options go **before** the command: `owh-openrouter --webui-url http://127.0.0.1:18080 apply`.

**Exit codes:**
- 0 ok;
- 1 validation (bad key, unknown model, empty allowlist);
- 2 usage;
- 3 refused (remote URL, open permissions, key already stored, no snapshot);
- 4 failed, nothing changed;
- 5 failed after a partial change (run `owh-openrouter remove`).

## Where things are
| What | Where |
|---|---|
| Key | `~/.config/owh/openrouter.key` (0600), plus Open WebUI's `webui.db` and its backups after `apply` (SECURITY.md) |
| Snapshots | `~/.local/state/owh/snapshots/*.json` (0600, contain the prior keys) |
| Action log | `~/.local/state/owh/owh.log` (one line per run, no secrets) |
| Allowlist | `config/openrouter-models.txt` in the repo |
