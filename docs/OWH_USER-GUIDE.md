# OWH: User Guide

**Version 1.0.0**, 2026-11-13 (Phase 07). Steps were run on the live instance on 2026-11-13 13:05 CST (Phase 05). See also `docs/OWH_FINAL-REPORT.md` and `docs/OWH_THREAT-MODEL.md`.

`owh-openrouter` adds your OpenRouter account to the local Open WebUI as a second backend next to Ollama. You then pick either a local model or an `OR.`-prefixed OpenRouter model in the model picker. It changes only Open WebUI's stored settings, through its admin API. The container, its unit, `Super+Alt+O`, OCC and `open-webui-upgrade` stay as they are.

## Daily use
- Open Open WebUI as usual (`Super+Alt+O`, or `http://127.0.0.1:8080`). The model picker lists the local Ollama models and, next to them, the twelve allowlisted OpenRouter models with an `OR.` prefix (for example `OR.anthropic/claude-sonnet-5.5`). The picker shows raw IDs, not friendly names.
- Pick either kind per chat. Each chat goes to the backend of the model chosen; new chats still default to your local model.
- **Privacy:** an `OR.` chat sends the conversation, attached files, RAG excerpts and web-search results to OpenRouter and the upstream provider, which may log or train (ADR-0019). Use a local model for anything private. Titles, tags and follow-up suggestions are always made by the local task model, so they never go to OpenRouter.
- **Check spend:** `owh-openrouter status` shows the key's limit, usage and remaining credit, and openrouter.ai Activity shows each call. OWH sets no limit itself (ADR-0018); the key's $50/month limit is yours on openrouter.ai.

## Model cheat sheet
Prices and context sizes are the live values from OpenRouter on 2026-11-13 (`owh-openrouter models` shows today's). Strengths and weaknesses come from each vendor's own description on OpenRouter, the model size and the capabilities the model reports. They are **not benchmarks**: try a model on your own task before relying on it.

**Cost key:** 🆓 free · 💲 under $0.50 per million output tokens · 💲💲 $0.50–$5 · 💲💲💲 above $5.

**Output categories** say what a model gives back, not what it can read (that is the Input column): *Text (LLM)* = written answers in a chat · *Code* = it writes and fixes programs well · *Image generation* = it draws pictures (and edits ones you attach) · *Embeddings* = it turns text into number vectors for document search and is not a chat model. The tags come from the vendor descriptions and the capabilities each model reports, not benchmarks. No model on your list outputs audio or video.

### Local models (Ollama): free, private, offline
They run on the laptop's RTX 2070 (8 GB), cost nothing per chat and send nothing off the machine. Pick them for anything private.

| Model (picker name) | Size | Context | Output categories | Good at | Not good at | Cost |
|---|---|---|---|---|---|---|
| `qwen3:8b` (the default "Qwen3 8B (Web)") | 8.2B, 5.2 GB | 41 K | Text (LLM), Code (basic) | Best local all-rounder; tool use and a "thinking" mode for harder questions; web search | Slower than the small ones; far weaker than the cloud models on hard coding, long documents and facts; no image input | 🆓 |
| `qwen3:4b-instruct` | 4.0B, 2.5 GB | 262 K | Text (LLM) | Fast; very long context for its size; tool use. Also the task model that writes titles, tags and follow-ups | Shallower reasoning than the 8B; no image input | 🆓 |
| `qwen3:1.7b` | 2.0B, 1.4 GB | 41 K | Text (LLM) | Very fast, tiny; fine for quick rewrites, simple Q&A, testing | Makes more mistakes and loses track of long chats; weak at code and facts | 🆓 |
| `gemma2:9b` | 9.2B, 5.4 GB | 8 K | Text (LLM) | Natural, readable writing and summaries; solid general chat | Short memory (8 K context, so long chats and big documents get cut); no tool use or thinking mode; older than the Qwen3 family | 🆓 |
| `nomic-embed-text` | 137M, 274 MB | 2 K | Embeddings (vectors, not chat) | Turns text into vectors for document search (RAG) | **Not a chat model**: it does not appear in the picker and cannot answer questions | 🆓 |
| `Local Image (RealVisXL)` (added 2026-11-16) | qwen3:4b-instruct + RealVisXL 5 Lightning (SDXL, 6.9 GB) | 262 K | **Image generation** | Free, private photoreal pictures; about 10 s each once warm. See "Make images locally" | First picture after a pause takes 25–45 s; cannot edit an uploaded photo; poor at readable lettering; less good than the cloud models at following long, exact instructions | 🆓 |

### OpenRouter models (`OR.` prefix): cloud, paid per use unless marked free
Your chat goes to OpenRouter and the model's provider. The first eight (text models) all accept tool calls and have a reasoning mode. The last four (**image makers**, added 2026-11-14) draw pictures; see "Make images" below.

| Model (picker ID) | Context | Input | Cost in / out per M tokens | Output categories | Good at | Not good at | Cost |
|---|---|---|---|---|---|---|---|
| `OR.anthropic/claude-sonnet-5.5` | 1 M | text, images, files | $2.00 / $10.00 | Text (LLM), Code | Best all-round pick: building features, fixing bugs, careful writing, well-scoped everyday work | The priciest of the eight (about 20× Haiku); overkill for quick questions | 💲💲💲 |
| `OR.anthropic/claude-haiku-5.5` | 1 M | text, images, files | $0.10 / $0.50 | Text (LLM), Code | Fast and cheap for high-volume work: summaries, quick coding help, browser-style tasks | Less depth than Sonnet on hard, multi-step problems | 💲💲 |
| `OR.google/gemini-4-hydrogen` | 1 M | text, images, files, **audio, video** | $1.50 / $7.50 | Text (LLM), Code | The only one here that takes audio and video; huge inputs; agent workflows and coding at lower cost and latency than Google's larger models | Mid-priced for what it is; a "workhorse" tier, not Google's top model | 💲💲💲 |
| `OR.openai/gpt-6.1-terra` | 1 M | text, images, files | $1.00 / $5.00 | Text (LLM), Code | A second vendor's view; everyday agent, coding and writing work; understanding screenshots | Mid-tier (OpenAI's larger GPT-6.1 Sol is not on the list); replies capped at 128 K tokens | 💲💲 |
| `OR.deepseek/deepseek-v4.1-flash-1017` | 1 M | text, images | $0.038 / $0.50 | Text (LLM) | Cheapest long-input option; sparse mixture-of-experts built for cost | A dated snapshot (17 Oct 2026) that will not improve; a Chinese provider, so mind what you send | 💲💲 |
| `OR.xiaomi/mimo-v2.6-pro` | 1 M | text, images, video, audio | $0.435 / $0.87 | Text (LLM) | Xiaomi's flagship (over 1 T parameters) aimed at demanding tasks, with multimodal input, at a low price | Newest and least proven of the set; a Chinese provider | 💲💲 |
| `OR.z-ai/glm-5.3-flash` | 1 M | text, images, video | $0.04 / $0.078 | Text (LLM), Code | Cheapest paid model by far; efficient coding and long agent tasks; good for trying things out | A "flash" tier: expect less depth than Sonnet; a Chinese provider | 💲 |
| `OR.google/gemma-4-31b-it:free` | 262 K | text, images, video | **free** | Text (LLM) | Costs nothing; 31B model with a thinking mode and image input | **Rate-limited**; free endpoints may log prompts; replies capped at 32 K tokens; only about a quarter of the context of the others | 🆓 |
| `OR.google/gemini-3.1-flash-lite-image` ("Nano Banana 2 Lite") | 66 K | text, images | text $0.25 / $1.50; **images $30 / M image tokens, about 3.4¢ per picture (measured)** | **Image generation**, Text (LLM) | Cheapest and fastest image maker; quick drafts and ideas; editing an image you upload | Lower polish than the others; small context (66 K), so not for long chats | 💲💲💲 |
| `OR.google/gemini-3.1-flash-image` ("Nano Banana 2") | 131 K | text, images | text $0.50 / $3.00; **images $60 / M image tokens, about 7¢ per picture (estimate)** | **Image generation**, Text (LLM) | Google's best image quality at "Flash" speed; generating and editing pictures | About twice the price of Lite per picture | 💲💲💲 |
| `OR.openai/gpt-5-image-mini` | 400 K | text, images, files | text $2.50 / $2.00; **images $8 / M image tokens (picture cost not measured)** | **Image generation**, Text (LLM) | OpenAI's image maker with good instruction following, including text inside pictures; the cheapest per image token | Newer and less tested here; the picture cost per image is not measured yet | 💲💲💲 |
| `OR.openai/gpt-5-image` | 400 K | text, images, files | text $10 / $10; **images $40 / M image tokens (picture cost not measured)** | **Image generation**, Text (LLM) | The best of OpenAI's image models for careful instructions and detail | The most expensive way to make a picture; overkill for sketches | 💲💲💲 |

**Roughly what one chat costs** (about 2,000 words in, 700 out; 2 K tokens in, 1 K out): Sonnet 1.4¢, Gemini 1.1¢, GPT Terra 0.7¢, MiMo 0.17¢, Haiku 0.07¢, DeepSeek 0.06¢, GLM 0.016¢, Gemma free. Long conversations cost more because the whole history is sent each turn.

**Which one?**
| I want to… | Use |
|---|---|
| Keep it private, offline or free | `qwen3:8b` (or `qwen3:4b-instruct` for speed) |
| A quick answer, cheaply | `OR.anthropic/claude-haiku-5.5` or `OR.z-ai/glm-5.3-flash` |
| My best answer on code or writing | `OR.anthropic/claude-sonnet-5.5` |
| A second opinion | `OR.openai/gpt-6.1-terra` |
| Work with audio, video or a huge file | `OR.google/gemini-4-hydrogen` |
| Try a cloud model for nothing | `OR.google/gemma-4-31b-it:free` |
| Make a picture, free and private | `Local Image (RealVisXL)` |
| Make a picture with exact instructions, text in it, or by editing a photo | `OR.google/gemini-3.1-flash-lite-image` (cheapest), then the other three |

Every `OR.` model, free or paid, sends your chat off the laptop (ADR-0019). Local models are the only ones that stay private.

## Make images
Four of the `OR.` models draw pictures. You ask in plain words; there is no separate image button. This is **not free**: every picture is billed by OpenRouter, and none of this is private (the prompt goes to OpenRouter and Google or OpenAI).

**One-time step (after the allowlist change on 2026-11-14):** the four models are in `config/openrouter-models.txt`, but Open WebUI only learns of them when you run, in a real terminal window:
```
owh-openrouter apply --dry-run     # shows the four new model IDs being added
owh-openrouter apply               # asks for the admin e-mail and password (hidden)
```
Then refresh the browser tab. `owh-openrouter status` should now show 12 OpenRouter models.

**Second one-time step: turn off Built-in Tools for each image model.** Open WebUI adds helper tools (for example `get_current_timestamp`) to every chat, and the image models do not support tools. Without this step OpenRouter refuses the request with *"No endpoints found that support tool use. Try disabling \"get_current_timestamp\""* (found on 2026-11-14; nothing is billed for that error). For each of the four image models:
1. Click your name (bottom left) → **Admin Panel** → **Settings** → **Models**.
2. Click the model (for example `OR.google/gemini-3.1-flash-lite-image`) to edit it.
3. Under **Capabilities**, untick **Builtin Tools** (also leave Web Search, Code Interpreter and any tools off). Save.
4. Start a **new chat** with that model; an old chat keeps its old settings.

**To make a picture**
1. Start a **new chat** and choose `OR.google/gemini-3.1-flash-lite-image` in the model picker (cheapest; try this first).
2. Type what you want, as you would to a person: *"Draw a lighthouse on a cliff at sunset, watercolour style, wide format."*
3. The picture appears in the reply. Tell the model what to change ("make the sky stormier", "add a small boat") and it draws a new version. You can also attach a photo with the paperclip and ask for an edit ("put a hat on the dog").
4. Save it with right-click, "Save image as".

**Tips**
- Be specific about subject, style (photo, watercolour, flat icon, pixel art), mood, colours and shape (square, wide, tall).
- For writing inside a picture (a sign, a logo) try `OR.openai/gpt-5-image-mini`; it is the strongest here at following exact instructions. The Gemini models are the cheaper way to draw ideas.
- Keep image chats short. Every turn resends the whole chat, and the earlier pictures count as input.
- Use a fresh chat for each new picture idea, and check the cost on openrouter.ai Activity after your first few.

**Cost.** One 1,024-pixel picture on the Lite model cost **$0.0336** (measured on 2026-11-14: 1,120 image tokens at $30 per million). The full Nano Banana 2 is twice the per-token price (about 7¢ a picture, an estimate), and the two OpenAI models are priced per image token as in the table (not measured). Ten pictures on Lite are about 34¢.

**If you get "No endpoints found that support tool use"**, the second one-time step above has not been done for that model (or the chat is an old one). Do not turn off tools in the chat's `+` menu only: use the model's Capabilities.

**If no picture shows up.** Open WebUI 0.13.3 was not tested with image replies. OpenRouter returns the picture in a separate `images` field of the reply (checked directly on 2026-11-14), and your Open WebUI may or may not draw it. If the reply is blank or only text, you were still billed: tell Claude Code, and the next step is Open WebUI's built-in Image Generation settings (Admin Settings, Images) or a small addition to display the picture. Do not keep retrying, since each try costs money.

**Undo.** Delete the four image lines at the bottom of `config/openrouter-models.txt` and run `owh-openrouter apply`. That removes them from the picker.

## Make images locally (free, private)
Set up 2026-11-16 15:18 CST (ADR-0026). Pictures are drawn on the laptop's GPU by **RealVisXL 5 Lightning**, a photoreal SDXL model that Project1111 (P11) had already downloaded. It runs on P11's installed ComfyUI engine. Nothing leaves the machine and nothing is billed. Ollama itself cannot draw pictures on this setup (0.40.7 has no image endpoint, and Open WebUI cannot call Ollama's experimental image models), so Open WebUI talks to ComfyUI directly.

**To make a picture**
1. Start a **new chat** and choose **`Local Image (RealVisXL)`** in the model picker.
2. Describe what you want: *"A cozy cabin by a mountain lake at sunrise."* The small local model (`qwen3:4b-instruct`) turns that into a detailed image prompt and calls the image generator.
3. The picture appears in the reply (1024×1024). Ask for changes ("make it winter", "from further away") and it draws a new version from scratch, not an edit of the last one.
4. Save it with right-click, "Save image as". Pictures are also kept under `~/.local/share/owh-comfyui/out/`.

**Speed.** The image engine starts on demand: the first picture after a pause takes about **25–45 s** (ComfyUI starts in ~20 s, then loads the 6.9 GB model). After that it takes about **10–12 s** (measured 2026-11-16: 11.7 s with `qwen3:4b-instruct` loaded at the same time). After 10 minutes with no picture requests, the engine stops and gives the GPU memory back to Ollama.

**Other local models.** Image generation is now switched on in Admin Settings → Images, so the **Image** toggle in the chat box's integrations menu works with other local models too. `qwen3:8b` already had Image among its default features, so in a `qwen3:8b` chat you can just say "draw …" and it calls the same generator; it does not draw unless asked. `Local Image (RealVisXL)` is the dependable choice, because its instructions always call the generator.

**Limits.** It cannot edit a photo you attach (use an `OR.` image model for that). Writing inside pictures (signs, logos) comes out garbled. It is best at photos; ask for "illustration", "watercolour" or "3D render" for other styles. Exact, many-part instructions are followed less faithfully than by the cloud models.

**P11 Studio and this share the GPU.** Both use P11's GPU lock (`~/.cache/p11/gpu.lock`), so they never load SDXL at the same time. If P11 Studio is generating, a picture request here fails after 20 s (the reply says image generation failed): try again when P11 is idle. While this engine is warm (up to 10 minutes after the last picture), P11 Studio waits for the GPU. `systemctl --user stop owh-comfyui` frees it at once.

**How it is wired** (all under `config/local-images/` and `scripts/local-images/` in this repo):
- `owh-comfyui-proxy.socket` (user unit, enabled) listens on `127.0.0.1:8189`. The first connection starts `owh-comfyui-proxy.service` (`systemd-socket-proxyd --exit-idle-time=10min`), which pulls in `owh-comfyui.service`. That runs `~/.local/bin/owh-comfyui-run`: P11's ComfyUI v0.43.0 from `~/.local/share/p11/engine/` on `127.0.0.1:8190`, offline, no custom nodes, with its own output, input, temp and user folders under `~/.local/share/owh-comfyui/`. P11's engine and models are only read, never changed.
- Open WebUI Admin Settings → Images: engine ComfyUI, URL `http://127.0.0.1:8189`, model `RealVisXL_V5.0_Lightning_fp16.safetensors`, 1024×1024, 5 steps, the workflow `config/local-images/comfyui-realvisxl-lightning.json` (dpmpp_sde/karras, CFG 1.5, SDXL fp16-fix VAE: P11's tuned defaults), with "image prompt generation" on.
- The workspace model `local-image-realvisxl`: base `qwen3:4b-instruct`, Builtin Tools on, Image on by default, and a system prompt that always calls `generate_image`.

**Install, check, undo**
```
scripts/local-images/owh-local-images.sh install     # idempotent; take a DB backup first (below)
scripts/local-images/owh-local-images.sh status      # is the engine running, GPU memory
scripts/local-images/owh-local-images.sh uninstall   # removes the units, turns Images off, deletes the picker model
```
The DB backup taken before the live change is `~/.local/share/open-webui-backups/webui.db.20261116-1512.pre-local-images.bak` (made with the backup command in "What was run on the live instance" below). `uninstall` leaves P11, its models and the pictures already made in place.

**If no picture appears:** run `owh-local-images.sh status`. Check `journalctl --user -u owh-comfyui -n 50` for the engine log (an exit code of 75 means P11 held the GPU), and `docker logs open-webui 2>&1 | grep -i comfy` for Open WebUI's side.

## Add or remove a model
1. Edit `config/openrouter-models.txt` in the main checkout (one OpenRouter ID per line, `#` comments allowed). Find IDs and prices with `owh-openrouter models --search TEXT`.
2. `owh-openrouter models` (unknown IDs are flagged, exit 1), then `owh-openrouter apply --dry-run`, then `owh-openrouter apply`, all in a terminal window. Refresh the browser tab; no restart is needed.
3. Never empty the allowlist: `apply` refuses, because Open WebUI would then list every OpenRouter model and wait up to 10 s on OpenRouter whenever it is offline.

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
The key is read at a hidden prompt. The command trims whitespace and rejects control characters (stray arrow keys) or anything that is not `sk-or-v1-` + 64 hex characters. It checks the key live with OpenRouter (`GET /api/v1/key`). Only then does it write `~/.config/owh/openrouter.key` (directory 0700, file 0600, atomic). It prints the first 9 characters, the length, and the key's limit, usage and `expires_at`, and warns when the key expires within 30 days (ADR-0023).
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
- the OpenRouter key's limit, usage and expiry, with a warning from 30 days before `expires_at` (ADR-0023);
- the number of snapshots.

## 6. Undo: `remove`
```
owh-openrouter remove                    # restore from the earliest snapshot of this Open WebUI
owh-openrouter remove --snapshot FILE    # or a specific one (one step back)
owh-openrouter remove --delete-key       # also delete ~/.config/owh/openrouter.key (asks first; --yes skips the question)
```
`remove` restores only what OWH changed: its connection slot, the OpenAI on/off switch and the cloud task model. Connections you added later stay. The snapshot is kept. A second `remove` does nothing. If you delete the key file, also revoke the key on openrouter.ai.

## 7. Rotate the key
Do this before `expires_at` (the live key expires 2027-11-13; `status` warns from 30 days before).
1. Create a new key on openrouter.ai (set its limit there if you want one).
2. In a terminal window: `owh-openrouter set-key` (confirm the replacement), then `owh-openrouter apply`. `apply` saves a new snapshot that holds the **old** key.
3. Check one `OR.` chat, then revoke the old key on openrouter.ai.
4. Delete the snapshots newer than the earliest one in `~/.local/state/owh/snapshots/` (keep the earliest: it is the undo point for `remove`, ADR-0022).

## 8. When OpenRouter is down or out of credit
- **OpenRouter unreachable:** the model list is unaffected (the allowlist means Open WebUI never asks OpenRouter for it); local models work as usual. An `OR.` chat fails at once with "Open WebUI: Server Connection Error" when the connection is refused; an unreachable network can make that one chat wait up to 300 s. Measured in `docs/OWH_FINDINGS.md` §8.3.
- **Key limit reached or credit used up:** OpenRouter answers chats with HTTP 402, and Open WebUI shows the error in the chat (§8.4 of the findings has the exact text). Local models keep working. Raise the limit or add credit on openrouter.ai; `owh-openrouter status` shows `limit_remaining`, and `set-key`/`status` report "out of credit or the key's spending limit is reached" for a 402 on the key check.

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

## Troubleshooting
| Symptom | Cause and fix |
|---|---|
| A command exits 3 with "no terminal" | `set-key`, `apply`, `status` and `remove` need a hidden prompt. Run them in a real terminal window, not through the Claude Code `!` prefix (ADR-0020). |
| No `OR.` models in the picker | Run `owh-openrouter status`. If connection 0 is missing or off, run `apply`. Refresh the tab. If you restored the pre-OWH backup, the connection is gone by design. |
| An `OR.` chat fails at once with "Server Connection Error" | OpenRouter is unreachable or the connection is refused. Local models are unaffected (findings §8.3). |
| An `OR.` chat shows HTTP 402 | The key's limit or the account credit is used up. Raise the limit or add credit on openrouter.ai (findings §8.4). |
| `set-key` says "key rejected" (401) | The key is wrong, revoked or expired. Create a new one (§7). |
| `status` warns about expiry | Rotate the key (§7); the live one expires 2027-11-13. |
| `apply` exits 5 | A partial change. Run `owh-openrouter remove`, then `apply` again. |
| The launcher fails after the repo moved | `make install` hard-codes the directory it ran from. Run it again from the main checkout. |
| The setup vanished after an Open WebUI upgrade | It should not: it is stored in the volume and survives `open-webui-upgrade` (findings §8.2). Run `status`, then `apply`. |

## Full undo
Do as much as you want, in this order:
1. `owh-openrouter remove`: restores the connection slot, the OpenAI on/off switch and the cloud task model (surgical, ADR-0015).
2. `owh-openrouter remove --delete-key`: also deletes `~/.config/owh/openrouter.key`. Then revoke the key on openrouter.ai.
3. `make uninstall` (from the main checkout): removes `~/.local/bin/owh-openrouter`.
4. Last resort: restore the pre-OWH database backup (see "Full restore" below). This discards chats made since 2026-11-13 12:58 CST.

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
| Snapshots | `~/.local/state/owh/snapshots/*.json` (0600; the prior connection config, so the prior key if there was one; the live one holds none, ADR-0022) |
| Action log | `~/.local/state/owh/owh.log` (one line per run, no secrets) |
| Allowlist | `config/openrouter-models.txt` in the repo |
