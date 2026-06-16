---
name: gateway-model-list
description: "List the models available on the Mininglamp LLM gateway (llm-gateway.mlamp.cn) using YOUR OWN locally-configured OpenClaw API key. Use when asked what models the gateway/网关 offers, or to pick/compare models."
---

# Gateway Model List

Query the Mininglamp LLM gateway and print every model it currently serves,
grouped by provider prefix. Useful for "网关有哪些模型 / what models are
available / 帮我挑个模型" questions.

## Important: the key

- The gateway base URL is **fixed and public**: `https://llm-gateway.mlamp.cn`
- The models endpoint is **`https://llm-gateway.mlamp.cn/v1/models`**
- The API key is **NOT** stored in this skill. Each lobster/agent must use
  **its own** key that already lives in its local OpenClaw config. Do not ask
  the user for a key, and never hardcode one here.

### Where your key lives

It is the `apiKey` of whichever provider points at this gateway, inside your
OpenClaw config. Default config path: `$OPENCLAW_HOME/openclaw.json`
(falls back to `~/.openclaw/openclaw.json`).

Typical shape:

```json
{
  "models": {
    "providers": {
      "anthropic":    { "baseUrl": "https://llm-gateway.mlamp.cn/", "apiKey": "sk-..." },
      "gemini-image": { "baseUrl": "https://llm-gateway.mlamp.cn/", "apiKey": "sk-..." }
    }
  }
}
```

The helper script auto-discovers the key by scanning every provider whose
`baseUrl` contains `llm-gateway.mlamp.cn` and grabbing its `apiKey`. If several
providers share the gateway, any of their keys works.

## Workflow

### 1. Run the helper (recommended)

```bash
python3 scripts/list_models.py
```

It will:
1. Locate your OpenClaw config (`$OPENCLAW_HOME/openclaw.json` or `~/.openclaw/openclaw.json`).
2. Find the gateway key from a provider whose `baseUrl` matches the gateway host.
3. `GET https://llm-gateway.mlamp.cn/v1/models` with `Authorization: Bearer <key>`.
4. Print the total count + models grouped by provider prefix (e.g. `vertexai/`, `ali/`, no-prefix).

Optional flags:
- `--config /path/to/openclaw.json`  use a specific config file
- `--raw`                            dump the raw JSON response instead of the grouped view
- `--grep <substr>`                  only show model ids containing `<substr>` (case-insensitive)

### 2. Manual fallback (no Python / different setup)

Pull your key from config, then curl directly. Never print the key into the chat.

```bash
KEY=$(python3 -c "import json,os;p=os.path.expanduser(os.environ.get('OPENCLAW_HOME','~/.openclaw')+'/openclaw.json');d=json.load(open(p));pr=d['models']['providers'];print(next(v['apiKey'] for v in pr.values() if 'llm-gateway.mlamp.cn' in str(v.get('baseUrl',''))))")
curl -s -H "Authorization: Bearer $KEY" https://llm-gateway.mlamp.cn/v1/models \
  | python3 -m json.tool
```

## Output

A grouped list like:

```
TOTAL: 191

## (no-prefix) (155)
  claude-opus-4-8
  gpt-5.5
  gemini-3.1-pro
  ...
## vertexai (9)
  vertexai/claude-opus-4-8
  ...
## ali (11)
  ...
```

## Safety

- Treat the key as a secret: never echo it to chat, logs, or commit it anywhere.
- This skill only does a read-only `GET /v1/models`. It does not spend tokens or
  change any config.
- If no gateway provider/key is found in config, tell the user their OpenClaw
  config has no provider pointing at `llm-gateway.mlamp.cn` — they need to add one.
