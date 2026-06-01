# octo-speech Prompt 修改全历程

## 一、Ares 的 Prompt 优化（2026-05-29，3 个 commit）

基于 qwen3-omni 的 badcase 评估报告（30 条测试用例），对初始版 Go 代码做了 3 轮优化。

### 1. System prompt 层面（8486b94 + 261f010）

- **NO_SPEECH 判定放宽**：从"无清晰人类语音"改为"完全无人声"，降低误判率
- **数字格式强化**：从简单一行规则扩展为带多个示例的强制规则（特别加了"一二三四五六七→1234567"逐字念场景）
- **@提及识别**：新增强制规则，要求"艾特/at"转为@符号，移入 mentionSection 跟随 skipMention 开关
- **NO_SPEECH 措辞统一**：全部 task 常量对齐为"完全无人声"

### 2. User prompt（task）层面（8486b94 + 40010d2）

- taskEdit/taskEditOnly 加前缀"⚠️ 重要：你的输出必须是【完整文本】"，解决模型只输出修改片段的问题
- taskEdit 去掉"= input_buffer全部内容 + 新转写内容"的等式描述，因为删除/替换操作的结果可能比原文短

### 3. YAML 覆盖层（prompt_qwen3_omni.yaml）

- editInputBuffer 模板简化
- taskEditOnly 加"内部执行（不要输出这些步骤）"引导
- taskEdit 加编辑/追加示例

**得：** badcase 修复率 100%（NO_SPEECH 误判、数字格式、@提及）。task 指令更清晰，完整文本输出的遵循率提升。

**失：** 无明显负面影响。但 edit_only 模式的 system prompt 仍然是完整版（包含大量转写润色规则），导致角色混淆问题未根治。

---

## 二、Danni 的 Prompt 架构重构（2026-06-01）

### 4. editSection + EDIT_SECTION 机制（修复 + 从主仓库同步）

- 主仓库已有的 `editSection` 常量（编辑身份声明"你现在是文本编辑器"+ 反面示例）和 `BuildSystemMessage(mode)` 的条件注入逻辑，同步到 qwen 部署仓库
- 这是 Ares 的 P0 建议的落地，之前主仓库有但 qwen 仓库缺失

### 5. 按模式拆分三套 system prompt（Boss 方案）

- `system`（smart/edit 默认）→ 保持完整版不变
- `system_append_only`（语音输入）→ 角色=语音转写器，去掉编辑相关内容，保留全部转写规则
- `system_edit_only`（语音编辑）→ 角色=语音指令编辑器，编辑身份 bake in，保留语音理解基础规则，去掉润色规则
- Go 代码 `BuildSystemMessage` 根据 mode 选模板，YAML 可覆盖

**得：**
- edit_only 成功率从 29%（拆分前）→ 89%（拆分后），最大收益
- edit_only system prompt 从 8354 字符缩减到 ~2000 字符，token 消耗和响应速度优化
- 角色不再混淆，模型不会在编辑模式下看到转写润色规则而"走捷径"做转写
- append_only 与全量版差异仅 3.7%，转写能力无损

**失：**
- 过程中因两个仓库代码不同步，重建镜像时引入了 EDIT_SECTION 回归（已修复）
- edit_only 仍有约 11% 的偶发失败（模型快速返回转写指令），模型层面限制

### 6. edit_only 加"常见错误模式"防护规则

- 错误1：转写指令直接输出（带示例）
- 错误2：转写指令拼接在句首（带示例）
- 输出自检提醒

### 7. append_only 补全自查项

- 加回"数字检查"和"@提及检查"两条输出前自查

**得：** 防护更完整，edit_only 的鲁棒性进一步提升。
**失：** 无。这两条是从全量版摘取的，不引入新复杂度。

---

## 整体评价

Ares 的优化解决了具体的 badcase（NO_SPEECH、数字、@提及、完整文本输出），属于"修补漏洞"。Danni 的架构拆分解决了根本的角色混淆问题，属于"结构性改进"。两者互补，叠加效果显著。最终 edit_only 的表现甚至好于老 prompt 的 qwen3.5-omni-plus。
