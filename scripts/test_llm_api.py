"""Run a minimal smoke test against the configured OpenAI-compatible LLM API."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import NoReturn
from urllib.parse import urlparse


def fail(message: str) -> NoReturn:
    print(f"LLM API smoke test failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        fail(f"GitHub secret {name} is missing or empty")
    return value


def chat_completions_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        fail("OPENAI_API_BASE must be an absolute HTTP(S) URL")
    if parsed.path.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def error_message(raw_body: bytes, api_key: str) -> str:
    text = raw_body.decode("utf-8", errors="replace").strip()
    try:
        payload = json.loads(text)
        error = payload.get("error", payload)
        if isinstance(error, dict):
            text = str(error.get("message") or error.get("detail") or error)
        else:
            text = str(error)
    except (json.JSONDecodeError, AttributeError):
        pass
    return text.replace(api_key, "***")[:1000] or "empty response body"


def main() -> None:
    api_key = required_env("OPENAI_API_KEY")
    base_url = required_env("OPENAI_API_BASE")
    model = required_env("MODEL_NAME")
    endpoint = chat_completions_url(base_url)

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are an API health check."},
                {"role": "user", "content": "Reply with API_OK only."},
            ],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "zotero-arxiv-daily-api-smoke-test",
        },
    )

    print("Calling the configured OpenAI-compatible chat completions endpoint...")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = response.status
            raw_body = response.read()
    except urllib.error.HTTPError as exc:
        fail(f"HTTP {exc.code}: {error_message(exc.read(), api_key)}")
    except urllib.error.URLError as exc:
        fail(f"connection error: {exc.reason}")
    except TimeoutError:
        fail("request timed out after 60 seconds")

    if not 200 <= status < 300:
        fail(f"unexpected HTTP status {status}")

    try:
        response_payload = json.loads(raw_body)
        content = response_payload["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        fail(f"HTTP {status}, but the response is not Chat Completions compatible: {exc}")

    if not isinstance(content, str) or not content.strip():
        fail(f"HTTP {status}, but the model returned empty content")

    print(f"LLM API smoke test succeeded (HTTP {status}, non-empty model response).")


if __name__ == "__main__":
    main()
