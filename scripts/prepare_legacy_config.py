"""Build a v1 configuration from the environment used by pre-v1 forks."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Mapping


DEFAULT_ARXIV_CATEGORIES = ["cs.AI", "cs.CV", "cs.LG", "cs.CL"]


def _value(environ: Mapping[str, str], name: str, default: str) -> str:
    value = environ.get(name, "").strip()
    return value or default


def _boolean(environ: Mapping[str, str], name: str, default: bool) -> bool:
    value = environ.get(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def _integer(environ: Mapping[str, str], name: str, default: int) -> int:
    value = environ.get(name, "").strip()
    return int(value) if value else default


def _arxiv_categories(environ: Mapping[str, str]) -> list[str]:
    query = environ.get("ARXIV_QUERY", "")
    categories = [category.strip() for category in query.split("+") if category.strip()]
    return categories or DEFAULT_ARXIV_CATEGORIES


def build_config(environ: Mapping[str, str]) -> dict:
    """Return a Hydra-compatible config without copying credentials into it."""
    return {
        "zotero": {
            "user_id": "${oc.env:ZOTERO_ID}",
            "api_key": "${oc.env:ZOTERO_KEY}",
            "include_path": None,
            "ignore_path": None,
        },
        "email": {
            "sender": "${oc.env:SENDER}",
            "receiver": "${oc.env:RECEIVER}",
            "smtp_server": _value(environ, "SMTP_SERVER", "smtp.qq.com"),
            "smtp_port": _integer(environ, "SMTP_PORT", 465),
            "sender_password": "${oc.env:SENDER_PASSWORD}",
        },
        "llm": {
            "api": {
                "key": "${oc.env:OPENAI_API_KEY}",
                "base_url": _value(
                    environ, "OPENAI_API_BASE", "https://api.openai.com/v1"
                ),
            },
            "generation_kwargs": {
                "model": _value(environ, "MODEL_NAME", "gpt-4o-mini")
            },
            "language": _value(environ, "LANGUAGE", "English"),
        },
        "source": {"arxiv": {"category": _arxiv_categories(environ)}},
        "executor": {
            "debug": _boolean(environ, "DEBUG", False),
            "send_empty": _boolean(environ, "SEND_EMPTY", False),
            "max_paper_num": _integer(environ, "MAX_PAPER_NUM", 100),
            "source": ["arxiv"],
            "reranker": "local",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(
        json.dumps(build_config(os.environ), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
