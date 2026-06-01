---
name: speech-prompt-engineering
description: "Speech ASR/editing prompt design patterns: mode isolation, badcase-driven optimization, error guardrails, and evaluation methodology for multimodal speech models."
---

# Speech Prompt Engineering

Patterns and lessons from optimizing octo-speech prompts for Qwen3-Omni multimodal model. Applicable to any speech-to-text + voice-editing system backed by LLM.

## Core Principle: Mode Isolation

When a single model serves multiple roles (transcription vs editing), **split system prompts per mode** rather than cramming all roles into one prompt.

**Why:** A combined prompt causes role confusion — the model sees transcription rules while doing editing, takes shortcuts, and produces wrong output (e.g., transcribing the edit command instead of executing it).

**Pattern:**
- `system_append_only` — role = transcriber, contains only transcription rules
- `system_edit_only` — role = text editor, contains only editing rules + error guardrails
- `system` (default/smart) — full version for backward compatibility
- Backend selects prompt based on `mode` parameter at runtime

**Result:** edit_only success rate jumped from 29% → 89% after isolation. Transcription quality unchanged (only 3.7% content difference from full prompt).

## Workflow: Badcase-Driven Optimization

1. **Collect badcases** — categorize failures: NO_SPEECH false positives, number format errors, @mention drops, edit command leaks, incomplete output
2. **Trace root cause** — distinguish prompt-level issues (missing rules, ambiguous wording) from model-level limitations (fast return without full audio processing)
3. **Targeted fix** — add specific rules with concrete examples for each badcase category
4. **Regression test** — verify fixes don't break other categories
5. **Iterate** — repeat with new badcases discovered in testing

## Key Patterns

### 1. Explicit Examples Beat Abstract Rules

Bad:
```
数字应转为阿拉伯数字
```

Good:
```
## 数字格式（强制）
- "二零二五年" → "2025年"
- "三千五百" → "3500"
- "一二三四五六七"（逐字念）→ "1234567"
- 例外：成语保留汉字（"三心二意"、"一模一样"）
```

### 2. Negative Examples for Error Prevention

In edit_only mode, explicitly show the model what NOT to do:

```
## ⚠️ 常见错误模式（必须避免）

错误1：将编辑指令转写后直接输出
- 语音说"删除Danni" → ❌ "删除Danni" → ✅ (执行删除后的结果)
- 自检：如果输出以"删除""替换""修改"等动词开头，说明你错误地转写了指令

错误2：将编辑指令转写后拼接在文本开头
- 语音说"删除所有英文" → ❌ "删除所有英文。世界" → ✅ "世界"
```

### 3. Output Self-Check Checklist

Add a pre-output checklist at the end of system prompt. Each item targets a known failure mode:

```
输出前自查：
1. 书面化检查：填充词是否已去除？
2. 逐字忠实检查：实义词、语序、用词是否与音频一致？
3. 模式检查：当前模式的规则是否已遵循？
4. 数字检查：数字是否已转为阿拉伯数字？（成语除外）
5. @提及检查：音频中的"艾特/at"是否已转为 @ 符号？
```

### 4. Role Identity Anchoring

Start system prompt with a clear, unambiguous role declaration:

- Transcription mode: `你是一个语音转写器，将用户的语音转为文字。`
- Edit mode: `你是一个语音指令编辑器。你不是语音转写工具。音频中的语音 = 编辑指令，不是要转写的内容。`

The **negation** ("你不是...") in edit mode is critical — it blocks the model's default transcription instinct.

### 5. YAML Override Layer

Use a layered config: Go/code defaults + YAML override file.

- Code contains stable base prompts as constants
- YAML overrides allow hot-swapping prompts without recompilation
- Runtime: `activePrompt = yaml[key] ?? codeDefault[key]`

Benefits: fast iteration during testing, rollback by removing YAML key, per-deployment customization.

### 6. Conditional Prompt Injection

Use template markers (e.g., `{{EDIT_SECTION}}`, `{{MENTION_SECTION}}`) that get replaced at runtime based on context:

- `{{EDIT_SECTION}}` → injected only in edit modes, empty in append mode
- `{{MENTION_SECTION}}` → injected only in group chats (skipMention=false)

Keeps prompts DRY while maintaining mode-specific behavior.

## Anti-Patterns

### ❌ One prompt, multiple roles
Cramming transcription + editing rules into a single system prompt. The model sees conflicting instructions and takes shortcuts.

### ❌ Relying on task (user message) alone for mode switching
Task-level instructions ("now do editing") are weaker than system prompt role anchoring. The model's "personality" is set by system prompt.

### ❌ Over-trusting pilot results
Pilot (10 QA on 1 conversation) showed Judge=0.80, full evaluation (1986 QA, 10 conversations) showed 0.315. Small-sample tests overfit to specific patterns. Always validate on diverse, larger datasets before declaring victory.

### ❌ Assuming bigger graph/context = better output
More extracted entities doesn't mean better retrieval. Signal-to-noise ratio matters — 126% graph inflation led to 25% quality drop.

### ❌ Ignoring fast-return as a signal
When model returns in ~1000ms for an audio editing task, it likely skipped audio understanding entirely. This is a model-level limitation that prompt engineering can mitigate (via guardrails) but not fully solve.

## Evaluation Methodology

- **Per-category scoring:** Break down by failure type (NO_SPEECH, number format, @mention, edit execution, completeness)
- **A/B with controlled variables:** Change one thing at a time, measure impact
- **Track token cost alongside quality:** edit_only prompt went from 8354 → ~2000 chars, saving tokens AND improving quality
- **Note response latency:** Fast returns (<1.5s) on complex tasks indicate model shortcuts, not efficiency

## Lessons Learned

1. **Structure > rules.** Splitting prompts by mode (structural change) had 10x more impact than adding rules to a combined prompt (content change).
2. **Negative examples are essential for edit mode.** Models default to transcription; you must explicitly show and forbid the transcription-of-commands pattern.
3. **Self-check lists work.** They add minimal tokens but catch systematic errors the model would otherwise miss.
4. **Two-repo sync is a landmine.** When main repo and deployment repo diverge, rebuilding images can silently regress features. Always diff before rebuild.
5. **Iterative refinement compounds.** Each round of badcase → fix → test → new badcase builds a progressively more robust prompt.
6. **Role negation matters.** "你不是X" is as important as "你是Y" when the model has strong priors toward X behavior.
