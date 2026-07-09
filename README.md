# personal-skill

Personal AI agent skills collection.

## Skills

### speech-prompt-engineering

Speech ASR/editing prompt design patterns: mode isolation, badcase-driven optimization, error guardrails, and evaluation methodology for multimodal speech models.

Lessons learned from optimizing octo-speech prompts for Qwen3-Omni.

### gateway-model-list

List the models served by the Mininglamp LLM gateway (`llm-gateway.mlamp.cn`).
The gateway URL is baked in; each agent uses **its own** locally-configured
OpenClaw API key (auto-discovered from config, never hardcoded). Read-only
`GET /v1/models`.

### litscout-dblp-to-repo

DBLP-driven top-venue paper discovery: curate, enrich abstracts (CrossRef/arXiv/S2/OpenAlex), fetch open-access PDFs, and push a `papers.json` + README catalog into a GitHub repo folder.

Reconstructed from the agent-memory literature-discovery flow (DBLP → 19 top-venue papers → catalog + PDFs).

### multica-dev-ares

octo + multica multi-role dev-team orchestration skill (Ares variant). The user
names a PM; the PM forms the team, gets approval, then dispatches
FEAT / IMPROVEMENT / BUGFIX work as self-contained multica issues.

Status is returned by **multica's own outbound webhook** (no per-issue manual
write-back). The patrol role's core job is to **catch and revive STUCK issues**
using `multica-cli` directly (same-host queries), with a cron fallback.

Enforces PR-postponement (draft PR first, promote only after tests green + owner
sign-off), no auto-merge, no cascading failure, and human-authored output.

## Installation

```
# In OpenClaw, install a skill from this repo:
/skill install https://github.com/Ranwanglc/personal-skill/tree/main/speech-prompt-engineering
/skill install https://github.com/Ranwanglc/personal-skill/tree/main/litscout-dblp-to-repo
/skill install https://github.com/Ranwanglc/personal-skill/tree/main/multica-dev-ares
```
