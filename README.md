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

## Installation

```
# In OpenClaw, install a skill from this repo:
/skill install https://github.com/Ranwanglc/personal-skill/tree/main/speech-prompt-engineering
```
