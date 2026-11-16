"""Add, update or remove the "Local Image (RealVisXL)" model in Open WebUI's model picker.

Runs inside the container with PYTHONPATH=/app/backend, through Open WebUI's own
`Models` API so the version history and access rows are written as the UI would.

Usage: python3 create_local_image_model.py [--remove]
"""

import asyncio
import sqlite3
import sys

from open_webui.models.models import ModelForm, Models

MODEL_ID = "local-image-realvisxl"

SYSTEM = (
    "You make pictures on this computer with a local image generator. For every request, "
    "call the generate_image tool once with a detailed English prompt: subject, setting, "
    "lighting, camera or art style, and composition (photorealistic unless the user asks for "
    "another style). Never answer with only text when the user wants a picture. After the "
    "image is made, reply with one short sentence. When the user asks for a change, call "
    "generate_image again with a complete, updated prompt. The generator cannot edit an "
    "uploaded photo and is poor at readable lettering; say so if asked."
)

FORM = ModelForm(
    id=MODEL_ID,
    base_model_id="qwen3:4b-instruct",
    name="Local Image (RealVisXL)",
    meta={
        "description": "Free, private picture maker on this laptop: qwen3:4b-instruct writes "
        "the prompt, RealVisXL 5 Lightning (P11's ComfyUI) draws it. First picture ~25-50 s, "
        "then ~10 s.",
        "capabilities": {
            "vision": False,
            "file_upload": False,
            "web_search": False,
            "image_generation": True,
            "code_interpreter": False,
            "terminal": False,
            "citations": False,
            "status_updates": True,
            "memory": False,
            "builtin_tools": True,
        },
        "defaultFeatureIds": ["image_generation"],
        "tags": [{"name": "local"}, {"name": "image"}],
    },
    # Ollama's default 4,096-token context is too small: the system prompt plus Open WebUI's
    # built-in tool definitions come to ~6,000 tokens (2026-11-16, "request exceeds the
    # available context size"). 8,192 leaves room for a chat and still shares the GPU with SDXL.
    params={"system": SYSTEM, "num_ctx": 8192},
    commit_message="OWH: local image model (ComfyUI RealVisXL), num_ctx 8192",
)


def admin_id() -> str:
    db = sqlite3.connect("file:/app/backend/data/webui.db?mode=ro", uri=True)
    sql = "select id from user where role = 'admin' order by created_at limit 1"
    row = db.execute(sql).fetchone()
    if not row:
        sys.exit("no admin user found")
    return row[0]


async def main() -> None:
    existing = await Models.get_model_by_id(MODEL_ID)
    if "--remove" in sys.argv:
        removed = existing and await Models.delete_model_by_id(MODEL_ID)
        print("removed" if removed else "not present")
        return
    if existing:
        same_params = existing.params.model_dump() == FORM.params.model_dump()
        if same_params and existing.meta.description == FORM.meta.description:
            print(f"{MODEL_ID} is up to date")
        else:
            await Models.update_model_by_id(MODEL_ID, FORM, user_id=admin_id())
            print(f"updated {MODEL_ID}")
        return
    model = await Models.insert_new_model(FORM, admin_id())
    print(f"created {model.id} ({model.name})")


if __name__ == "__main__":
    asyncio.run(main())
