#!/usr/bin/env bash
# Local image generation for Open WebUI (ADR-0026): P11's installed ComfyUI and RealVisXL,
# started on demand by a user socket on 127.0.0.1:8189 and stopped after 10 idle minutes.
#   owh-local-images.sh install     # units + run script, Open WebUI config, picker model
#   owh-local-images.sh uninstall   # undo all three (P11 and its models are not touched)
#   owh-local-images.sh status
# Take a DB backup first (docs/OWH_USER-GUIDE.md, "Make images locally").
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
cfg="$repo/config/local-images"
units="$HOME/.config/systemd/user"
bin="$HOME/.local/bin/owh-comfyui-run"
container="open-webui"

in_container() { # <script> [args...]: run one of our Python helpers inside Open WebUI
  local script="$1"
  shift
  docker cp "$here/$script" "$container:/tmp/$script"
  docker exec -w /app/backend -e PYTHONPATH=/app/backend \
    -e WEBUI_SECRET_KEY=owh-helper-process-only "$container" python3 "/tmp/$script" "$@" 2>&1 |
    grep -vE '^(WARNING|INFO)|WEBUI_SECRET_KEY' || true
  docker exec "$container" rm -f "/tmp/$script"
}

case "${1:-}" in
  install)
    [[ -x "$HOME/.local/share/p11/engine/venv/bin/python" ]] ||
      { echo "P11's engine is not installed (~/.local/share/p11/engine)" >&2; exit 1; }
    install -Dm755 "$cfg/owh-comfyui-run" "$bin"
    install -Dm644 -t "$units" "$cfg/owh-comfyui.service" "$cfg/owh-comfyui-proxy.socket" \
      "$cfg/owh-comfyui-proxy.service"
    systemctl --user daemon-reload
    systemctl --user enable --now owh-comfyui-proxy.socket
    docker cp "$cfg/comfyui-realvisxl-lightning.json" "$container:/tmp/owh-wf.json"
    in_container apply_image_config.py /tmp/owh-wf.json
    docker exec "$container" rm -f /tmp/owh-wf.json
    in_container create_local_image_model.py
    ;;
  uninstall)
    in_container create_local_image_model.py --remove
    in_container apply_image_config.py --off
    systemctl --user disable --now owh-comfyui-proxy.socket || true
    systemctl --user stop owh-comfyui-proxy.service owh-comfyui.service || true
    rm -f "$units/owh-comfyui.service" "$units/owh-comfyui-proxy.socket" \
      "$units/owh-comfyui-proxy.service" "$bin"
    systemctl --user daemon-reload
    echo "Removed. Generated files stay in ~/.local/share/owh-comfyui/ (delete by hand if wanted)."
    ;;
  status)
    systemctl --user --no-pager status owh-comfyui-proxy.socket owh-comfyui.service | grep -E '●|Active' || true
    nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
    ;;
  *)
    echo "usage: $0 install|uninstall|status" >&2
    exit 2
    ;;
esac
