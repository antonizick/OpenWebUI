# Security

## The key
- The OpenRouter key is a secret. It is **never** written in the repo, logs, shell history, process arguments or `docker inspect` output. The tool reads it only from a hidden prompt or from its 0600 key file.
- It is stored at `~/.config/owh/openrouter.key` (directory mode 0700, file mode 0600). It is a **new, dedicated** key for Open WebUI, separate from the key Claude Code's provider switch uses (`~/.config/ai-provider/openrouter.key`), Any spending limit is set by Nick on openrouter.ai; OWH does not manage spend (ADR-0018). Account credit is shared with the provider-switch key.
- Output shows at most the first 9 characters and the length.
- The admin password for Open WebUI is read at a hidden prompt (or one line on stdin with `--password-stdin`); the session token is kept in memory for one run only. Neither is ever stored.
- Every line the tool prints or logs passes through a scrubber that removes the key, password and token seen in that run, plus anything shaped like `sk-or-v1-…` or a JWT. HTTP errors carry only a short, scrubbed message (ADR-0016).
- The tool never follows redirects (an `Authorization` header cannot be forwarded to another host). It talks only to a loopback Open WebUI unless `--allow-remote` is given, and sends the key to OpenRouter only over https. The model list is fetched without the key.
- `~/.local/state/owh/owh.log` (0600) gets one line per run: time, command, result, the key's first 9 characters.

## Where the key ends up
After `apply`, the key also lives in Open WebUI's `webui.db` (config table), and so in every later backup of the `open-webui` volume (`~/.local/share/open-webui-upgrade/backups/` and any manual backup copy). Never copy those into `~/Documents` (it syncs to Drive). Pre-apply snapshots in `~/.local/state/owh/snapshots/` (directory 0700, files 0600) hold the prior connection config, including any key it had, and are kept after `remove`. The live pre-apply snapshot holds no key (the prior connection had none). A snapshot taken after a rotation holds the old key: delete those once the new key works, and keep the earliest one, which is the undo point (ADR-0022).

`GET /openai/config` returns connection keys in clear text to any Open WebUI admin session, so the tool never prints or logs that response unredacted.

The rehearsal testbed (`scripts/owh-testbed.sh`) keeps its random admin password in `~/.local/state/owh/testbed/admin-password` (dir 0700, file 0600), passes its `WEBUI_SECRET_KEY` through a temporary 0600 env file rather than argv, and deletes both on `down`. Testbed runs use only fake keys.

## Rotating the key
Keys expire (the live one on 2027-11-13). `set-key` and `status` warn from 30 days before `expires_at` (ADR-0023).
1. Create a new dedicated key on openrouter.ai (set its limit there if you want one).
2. `owh-openrouter set-key`, then `owh-openrouter apply`.
3. Revoke the old key on openrouter.ai, and delete the snapshots newer than the earliest one.

## Network exposure
Open WebUI uses host networking, so while it runs, port 8080 listens on every interface. ufw (default input DROP, no rule for 8080), the login, signup off and API keys off protect it. Nick chose to keep it that way (ADR-0021). Binding to loopback (`-e HOST=127.0.0.1`) or `sudo ufw deny 8080/tcp` are the alternatives. The full threat model is `docs/OWH_THREAT-MODEL.md`.

## Repository safeguards
- A gitleaks pre-commit hook (`scripts/git-hooks/pre-commit`, enabled with `git config core.hooksPath scripts/git-hooks`) blocks commits that contain a key; CI runs gitleaks too. `.gitleaks.toml` adds an OpenRouter rule and allows only the documented fake test-key pattern `sk-or-v1-TESTKEY`.
- `.gitignore` excludes keys, `.env*`, databases and archives. The repo is reachable from the Obsidian vault (which syncs), so treat every file as potentially synced.

## Reporting a problem
Report security issues by email to the repository owner. Do not open a public issue with details.
