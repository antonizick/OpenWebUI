"""Point Open WebUI's image generation at the local ComfyUI (runs inside the container).

Usage: python3 apply_image_config.py <workflow.json>   # enable, ComfyUI on 127.0.0.1:8189
       python3 apply_image_config.py --off             # switch image generation off again

Writes the same `config` rows that Admin Settings > Images writes; Open WebUI 0.13.3 reads
them from the database on every request, so no restart is needed.
"""

import json
import sqlite3
import sys
import time

DB = "/app/backend/data/webui.db"

# Open WebUI fills these nodes of the workflow per request (prompt, model, size, steps, seed).
NODES = [
    {"type": "prompt", "node_ids": ["6"], "key": "text"},
    {"type": "model", "node_ids": ["4"], "key": "ckpt_name"},
    {"type": "width", "node_ids": ["5"], "key": "width"},
    {"type": "height", "node_ids": ["5"], "key": "height"},
    {"type": "n", "node_ids": ["5"], "key": "batch_size"},
    {"type": "steps", "node_ids": ["3"], "key": "steps"},
    {"type": "seed", "node_ids": ["3"], "key": "seed"},
]

UPSERT = (
    "insert into config(key, value, updated_at) values (?, ?, ?) on conflict(key) "
    "do update set value = excluded.value, updated_at = excluded.updated_at"
)


def updates_for(arg: str) -> dict:
    if arg == "--off":
        return {"image_generation.enable": False}
    with open(arg, encoding="utf-8") as f:
        workflow = json.dumps(json.load(f), indent=2)
    return {
        "image_generation.enable": True,
        "image_generation.prompt.enable": True,
        "image_generation.engine": "comfyui",
        "image_generation.model": "RealVisXL_V5.0_Lightning_fp16.safetensors",
        "image_generation.size": "1024x1024",
        "image_generation.steps": 5,
        "image_generation.comfyui.base_url": "http://127.0.0.1:8189",
        "image_generation.comfyui.api_key": "",
        "image_generation.comfyui.workflow": workflow,
        "image_generation.comfyui.nodes": NODES,
    }


def main() -> None:
    updates = updates_for(sys.argv[1])
    db = sqlite3.connect(DB, timeout=30)
    now = int(time.time())
    with db:
        for key, value in updates.items():
            db.execute(UPSERT, (key, json.dumps(value), now))
    shown = (
        "image_generation.enable",
        "image_generation.engine",
        "image_generation.comfyui.base_url",
    )
    for key, value in db.execute(
        "select key, substr(value, 1, 60) from config where key in (?, ?, ?)", shown
    ):
        print(f"{key} = {value}")


if __name__ == "__main__":
    main()
