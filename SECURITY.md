# Security

## The key
- The OpenRouter key is a secret. It is **never** written in the repo, logs, shell history, process arguments or `docker inspect` output. The tool reads it only from a hidden prompt or from its 0600 key file.
- It is stored at `~/.config/owh/openrouter.key` (directory mode 0700, file mode 0600). It is a **new, dedicated** key for Open WebUI, separate from the key Claude Code's provider switch uses (`~/.config/ai-provider/openrouter.key`), and carries its own spending limit set on openrouter.ai.
- Output shows at most the first 9 characters and the length.
- The admin password for Open WebUI is read at a hidden prompt; the session token is kept in memory for one run only.

## Where the key ends up
After `apply`, the key also lives in Open WebUI's `webui.db` (config table), and so in every later backup of the `open-webui` volume (`~/.local/share/open-webui-upgrade/backups/` and any manual backup copy). Never copy those into `~/Documents` (it syncs to Drive). Pre-apply snapshots in `~/.local/state/owh/` are 0600.

`GET /openai/config` returns connection keys in clear text to any Open WebUI admin session, so the tool never prints or logs that response unredacted.

The rehearsal testbed (`scripts/owh-testbed.sh`) keeps its random admin password in `~/.local/state/owh/testbed/admin-password` (dir 0700, file 0600), passes its `WEBUI_SECRET_KEY` through a temporary 0600 env file rather than argv, and deletes both on `down`. Testbed runs use only fake keys.

## Rotating the key
1. Create a new dedicated key on openrouter.ai (with a spending limit).
2. `owh-openrouter set-key`, then `owh-openrouter apply`.
3. Revoke the old key on openrouter.ai.

## Repository safeguards
- A gitleaks pre-commit hook (`scripts/git-hooks/pre-commit`, enabled with `git config core.hooksPath scripts/git-hooks`) blocks commits that contain a key; CI runs gitleaks too. `.gitleaks.toml` adds an OpenRouter rule and allows only the documented fake test-key pattern `sk-or-v1-TESTKEY`.
- `.gitignore` excludes keys, `.env*`, databases and archives. The repo is reachable from the Obsidian vault (which syncs), so treat every file as potentially synced.

## Reporting a problem
Report security issues by email to the repository owner. Do not open a public issue with details.
