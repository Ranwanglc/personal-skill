#!/usr/bin/env python3
"""List models served by the Mininglamp LLM gateway using the local OpenClaw key.

The gateway URL is fixed; the API key is read from the caller's own OpenClaw
config (never hardcoded). Read-only: only does GET /v1/models.
"""
import argparse
import json
import os
import sys
import urllib.request
from collections import defaultdict

GATEWAY_HOST = "llm-gateway.mlamp.cn"
MODELS_URL = "https://llm-gateway.mlamp.cn/v1/models"


def find_config(explicit=None):
    if explicit:
        return os.path.expanduser(explicit)
    candidates = []
    home = os.environ.get("OPENCLAW_HOME")
    if home:
        candidates.append(os.path.join(os.path.expanduser(home), "openclaw.json"))
        candidates.append(os.path.join(os.path.expanduser(home), ".openclaw", "openclaw.json"))
    candidates.append(os.path.expanduser("~/.openclaw/openclaw.json"))
    for c in candidates:
        if os.path.isfile(c):
            return c
    raise SystemExit(
        "ERROR: could not find openclaw.json. Tried:\n  " + "\n  ".join(candidates)
        + "\nPass --config /path/to/openclaw.json"
    )


def find_key(config_path):
    with open(config_path) as f:
        cfg = json.load(f)
    providers = (cfg.get("models") or {}).get("providers") or {}
    for name, p in providers.items():
        if not isinstance(p, dict):
            continue
        base = str(p.get("baseUrl") or p.get("base_url") or "")
        if GATEWAY_HOST in base:
            key = p.get("apiKey") or p.get("api_key")
            if key:
                return key, name
    raise SystemExit(
        f"ERROR: no provider in {config_path} has baseUrl pointing at {GATEWAY_HOST}.\n"
        "Add a provider with that baseUrl and your apiKey, then retry."
    )


def fetch_models(key):
    req = urllib.request.Request(MODELS_URL, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser(description="List models on the Mininglamp LLM gateway.")
    ap.add_argument("--config", help="path to openclaw.json (default: auto-discover)")
    ap.add_argument("--raw", action="store_true", help="dump raw JSON response")
    ap.add_argument("--grep", help="only show model ids containing this substring (case-insensitive)")
    args = ap.parse_args()

    config_path = find_config(args.config)
    key, provider = find_key(config_path)
    print(f"# config: {config_path}  (key from provider '{provider}')", file=sys.stderr)

    data = fetch_models(key)

    if args.raw:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    ids = sorted(m.get("id", "") for m in data.get("data", []) if m.get("id"))
    if args.grep:
        needle = args.grep.lower()
        ids = [i for i in ids if needle in i.lower()]

    print(f"TOTAL: {len(ids)}")
    groups = defaultdict(list)
    for i in ids:
        prefix = i.split("/")[0] if "/" in i else "(no-prefix)"
        groups[prefix].append(i)
    for prefix in sorted(groups):
        print()
        print(f"## {prefix} ({len(groups[prefix])})")
        for i in groups[prefix]:
            print(f"  {i}")


if __name__ == "__main__":
    main()
