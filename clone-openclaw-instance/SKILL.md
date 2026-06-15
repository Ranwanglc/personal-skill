---
name: clone-openclaw-instance
description: "Clone a second isolated OpenClaw instance (new agent) from an existing one: copy config, isolate home/port/token/workspace, reset identity+memory, bootstrap."
---

# Clone OpenClaw Instance

Deploy a SECOND, fully-isolated OpenClaw instance on the same host. It reuses the
source instance's config (providers, skills, MCP) but gets a fresh identity, empty
memory, its own port/token/workspace, and self-bootstraps on first run.

Use when the user wants "another agent / second lobster / a clone with same setup
but new identity/memory" alongside the running one.

## Key facts (learned the hard way)

- A second instance is isolated by `OPENCLAW_HOME`. Everything keys off it.
- With `OPENCLAW_HOME=<DIR>`, the config path is **`<DIR>/.openclaw/openclaw.json`**
  (note the nested `.openclaw`), NOT `<DIR>/openclaw.json`.
- Code lives in the npm install dir; user data lives under each home. They are
  physically separate, so cloning never touches the source instance's data.
- **Every command for the new instance MUST be prefixed with `OPENCLAW_HOME=<DIR>`.**
  Omitting it makes the command operate on the DEFAULT instance — this can kill/restart
  the wrong gateway. This is the #1 footgun.
- Two gateways cannot share a port. Pick a free port (e.g. source 18789 -> new 18790).

## Inputs to confirm with the user

1. Target dir `NEW_HOME` (e.g. `/Users/<u>/study-openclaw`).
2. New port (must differ from source; default source 18789 -> 18790).
3. Which channels to drop (usually all messaging channels — user reconfigures their
   own bot accounts so the clone does not steal the source's messages).
4. Identity init style: BOOTSTRAP self-setup (recommended) vs blank templates.

## Workflow

### 1. Inspect source

- Find source home (default `~/.openclaw`; config `~/.openclaw/openclaw.json`).
- Read source config structure (redact secrets). Note: providers, gateway port/auth,
  channels, plugins/extensions, mcp, sub-agents, workspace path.

### 2. Scaffold + copy config

```bash
NEW_HOME=/path/to/new-home
mkdir -p "$NEW_HOME/.openclaw" "$NEW_HOME/workspace/memory"
cp ~/.openclaw/openclaw.json "$NEW_HOME/.openclaw/openclaw.json"
```

### 3. Edit the NEW config (script does it safely)

Run `scripts/clone_config.py`. It: removes chosen channels + their bindings, sets a
new `gateway.port`, generates a fresh `gateway.auth.token`, sets
`agents.defaults.workspace` to `<NEW_HOME>/workspace`, and strips dropped channels'
plugin entries/allow so the clone starts clean.

```bash
python3 scripts/clone_config.py "$NEW_HOME/.openclaw/openclaw.json" \
  --port 18790 --workspace "$NEW_HOME/workspace" --drop-channel octo
```

Verify after: providers preserved, port set, channels emptied, workspace path correct.

### 4. Fresh identity + empty memory

- Do NOT copy `IDENTITY.md`, `MEMORY.md`, `memory/*`, `USER.md`, or `~/self-improving`.
- Generate blank workspace baseline. Easiest: run setup against the new home
  (`OPENCLAW_HOME=$NEW_HOME openclaw setup --non-interactive --accept-risk --workspace "$NEW_HOME/workspace"`)
  which writes clean AGENTS.md/SOUL.md/IDENTITY.md/USER.md templates. Confirm they are
  blank templates (no source personal data) and `memory/` is empty.
- Caution: `setup` may write to `<NEW_HOME>/.openclaw/openclaw.json`. After setup,
  re-copy the edited config from step 3 over that path so your changes win, then remove
  any stray `<NEW_HOME>/openclaw.json`.
- Drop a `BOOTSTRAP.md` in the new workspace (see `assets/BOOTSTRAP.template.md`) so the
  new agent introduces itself, sets its own identity, and deletes the file on first run.

### 5. Validate without disturbing the source

```bash
OPENCLAW_HOME=$NEW_HOME openclaw doctor --non-interactive   # config sanity
# Real start test — ALWAYS inject env into the backgrounded process itself:
env OPENCLAW_HOME=$NEW_HOME nohup openclaw gateway run --port 18790 > /tmp/clone-gw.log 2>&1 &
sleep 8
lsof -nP -iTCP:18790 -sTCP:LISTEN   # new instance ready
lsof -nP -iTCP:18789 -sTCP:LISTEN   # source untouched
```

Look for `[gateway] ready` in the log. If a dropped channel still errors as
"plugin not found", its extension/config residue remains — clean it.

### 6. Hand off

- To run foreground/interactive: `env OPENCLAW_HOME=$NEW_HOME openclaw chat`
  (or `gateway run` to keep it serving).
- The user reconfigures their own channel/bot for the clone (a DIFFERENT bot id than
  the source, so they don't collide).
- For always-on, install a separate LaunchAgent/systemd unit with `OPENCLAW_HOME` set.

## Safety

- Back up the source config first: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak-$(date +%s)`.
- Never run an unprefixed `gateway run/restart` while intending the clone.
- Cloning copies code-shared config only; source identity/memory stay private and untouched.
