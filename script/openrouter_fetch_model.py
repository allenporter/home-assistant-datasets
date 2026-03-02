#!/usr/bin/env python3
"""
Fetch a single OpenRouter model record from the public "author-models" endpoint.

Given an OpenRouter model URL like:
  https://openrouter.ai/deepseek/deepseek-v3.2

This script will:
  - derive the model slug (e.g. "deepseek/deepseek-v3.2")
  - derive the authorSlug (e.g. "deepseek")
  - call:
      https://openrouter.ai/api/frontend/author-models?authorSlug=<authorSlug>
  - find the entry in data.models[] whose slug matches the model slug
  - write a `models/<model_id>.yaml` file (silent on success)

Notes:
  - `model_id` is the part after the final "/" in the slug (e.g. "deepseek-v3.2")
  - `config_entry_options.chat_model` is set to the full OpenRouter slug
  - costs are derived from `endpoint.pricing.prompt` and `endpoint.pricing.completion`
    (OpenRouter reports $/token; the YAML uses $/1M tokens)
  - the YAML description uses the friendly model name (not the long model description)
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


OPENROUTER_AUTHOR_MODELS_URL = "https://openrouter.ai/api/frontend/author-models"


# type: ignore[name-defined]
def _die(message: str, *, exit_code: int = 2) -> "NoReturn":
    print(message, file=sys.stderr)
    raise SystemExit(exit_code)


def _parse_slug_from_input(value: str) -> str:
    """
    Accept either:
      - a full OpenRouter URL: https://openrouter.ai/<author>/<model>
      - a raw slug: <author>/<model>
    """
    value = value.strip()
    if not value:
        _die("Empty input.")

    if "://" not in value:
        # Looks like a slug.
        if "/" not in value:
            _die(f"Expected '<author>/<model>' slug, got: {value!r}")
        return value.strip("/")

    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        _die(f"Unsupported URL scheme: {parsed.scheme!r}")
    if parsed.netloc not in {"openrouter.ai", "www.openrouter.ai"}:
        _die(f"Expected an openrouter.ai URL, got host: {parsed.netloc!r}")

    # Typical model pages look like /<author>/<model> (sometimes with extra segments).
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        _die(
            f"Could not derive '<author>/<model>' from URL path: {parsed.path!r}")
    return f"{parts[0]}/{parts[1]}"


def _author_slug_from_model_slug(model_slug: str) -> str:
    author, _, _ = model_slug.partition("/")
    if not author:
        _die(f"Invalid model slug (missing author): {model_slug!r}")
    return author


def _model_id_from_model_slug(model_slug: str) -> str:
    model_id = model_slug.rsplit("/", 1)[-1].strip()
    if not model_id:
        _die(f"Invalid model slug (missing model id): {model_slug!r}")
    return model_id


def _http_get_json(url: str) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "home-assistant-datasets/openrouter_fetch_model.py",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        # Include a bit of body when available to help debugging.
        body = getattr(e, "read", lambda: b"")()
        snippet = body[:500].decode("utf-8", errors="replace") if body else ""
        _die(f"HTTP {e.code} fetching {url}\n{snippet}".rstrip())
    except urllib.error.URLError as e:
        _die(f"Network error fetching {url}: {e}")

    try:
        return json.loads(body.decode("utf-8"))
    except Exception as e:  # noqa: BLE001 - show decode issues
        _die(f"Failed to parse JSON response from {url}: {e}")


def _extract_cost_per_million_tokens(endpoint: dict[str, Any]) -> tuple[Decimal | None, Decimal | None]:
    """
    OpenRouter typically provides pricing as $/token strings:
      endpoint.pricing.prompt, endpoint.pricing.completion
    Convert to $/1M tokens as Decimals.
    """
    pricing = endpoint.get("pricing")
    if not isinstance(pricing, dict):
        return None, None

    prompt = pricing.get("prompt")
    completion = pricing.get("completion")

    def to_per_million(value: Any) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            raw = Decimal(str(value))
        elif isinstance(value, str):
            try:
                raw = Decimal(value)
            except InvalidOperation:
                return None
        else:
            return None
        return raw * Decimal("1000000")

    return to_per_million(prompt), to_per_million(completion)


def _format_decimal_for_yaml(value: Decimal) -> str:
    # Keep YAML readable (strip trailing zeros)
    s = format(value.normalize(), "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def _build_model_yaml(model_id: str, model_slug: str, model_entry: dict[str, Any]) -> str:
    friendly_name = str(model_entry.get("short_name") or model_entry.get(
        "name") or model_slug).strip() or model_slug

    description = f"OpenRouter integration using {friendly_name}"

    endpoint = model_entry.get("endpoint")
    if not isinstance(endpoint, dict):
        endpoint = {}

    rpm = endpoint.get("limit_rpm")
    if not isinstance(rpm, int) or rpm <= 0:
        rpm = 20

    in_cost, out_cost = _extract_cost_per_million_tokens(endpoint)

    # Minimal schema consistent with existing `models/*.yaml` files in this repo.
    # We intentionally do not print anything to stdout on success.
    lines: list[str] = [
        "---",
        f"model_id: {model_id}",
        "domain: open_router",
        f"description: {description}",
        "categories:",
        "  - openrouter",
        "  - cloud",
        "urls:",
        f"  - https://openrouter.ai/{model_slug}",
        "config_entry_data:",
        "  api_key: !secret openrouter_api_key",
        "config_entry_options:",
        f"  chat_model: {model_slug}",
        "  llm_hass_api: assist",
        f"rpm: {rpm}",
    ]

    if in_cost is not None or out_cost is not None:
        lines.append("cost:")
        if in_cost is not None:
            lines.append(
                f"  input_tokens: {_format_decimal_for_yaml(in_cost)}")
        if out_cost is not None:
            lines.append(
                f"  output_tokens: {_format_decimal_for_yaml(out_cost)}")

    lines.append("")  # trailing newline
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch an OpenRouter model record from the author-models endpoint, "
            "then write a Home Assistant Datasets model YAML into ./models/."
        )
    )
    parser.add_argument(
        "openrouter_model_url_or_slug",
        help="Example: https://openrouter.ai/deepseek/deepseek-v3.2 OR deepseek/deepseek-v3.2",
    )
    args = parser.parse_args(argv)

    model_slug = _parse_slug_from_input(args.openrouter_model_url_or_slug)
    author_slug = _author_slug_from_model_slug(model_slug)
    model_id = _model_id_from_model_slug(model_slug)

    url = f"{OPENROUTER_AUTHOR_MODELS_URL}?{urllib.parse.urlencode({'authorSlug': author_slug})}"
    payload = _http_get_json(url)

    data = payload.get("data") if isinstance(payload, dict) else None
    models = data.get("models") if isinstance(data, dict) else None
    if not isinstance(models, list):
        _die(
            f"Unexpected response shape from {url}: expected data.models[] list")

    for entry in models:
        if not isinstance(entry, dict):
            continue
        # Per requirement: match the exact slug from the model URL
        if entry.get("slug") == model_slug:
            repo_root = Path(__file__).resolve().parents[1]
            models_dir = repo_root / "models"
            models_dir.mkdir(parents=True, exist_ok=True)

            out_path = models_dir / f"{model_id}.yaml"
            yaml_text = _build_model_yaml(model_id, model_slug, entry)
            out_path.write_text(yaml_text, encoding="utf-8")
            return 0

    _die(
        f"Model not found for slug {model_slug!r} under authorSlug={author_slug!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
