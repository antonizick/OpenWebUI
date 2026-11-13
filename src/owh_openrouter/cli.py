"""Command-line entry point: `owh-openrouter`."""

from __future__ import annotations

import argparse
import sys

from . import __version__, openrouter, webui


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="owh-openrouter",
        description="Add an OpenRouter connection to a local Open WebUI.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--webui-url", default=webui.DEFAULT_URL)
    p.add_argument("--openrouter-url", default=openrouter.DEFAULT_URL)
    p.add_argument("--state-dir", default=None, help="default: ~/.local/state/owh")
    p.add_argument("--config-dir", default=None, help="default: ~/.config/owh")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("set-key", help="store the dedicated OpenRouter key")
    sub.add_parser("models", help="list or check the model allowlist")
    apply_p = sub.add_parser("apply", help="write the connection into Open WebUI")
    apply_p.add_argument("--dry-run", action="store_true")
    sub.add_parser("status", help="show what is configured")
    sub.add_parser("remove", help="restore the pre-apply configuration")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"owh-openrouter {args.command}: not implemented", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
