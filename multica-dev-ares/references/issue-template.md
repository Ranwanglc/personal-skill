# multica issue 模板（自包含；状态回报由 multica webhook 自动完成，无手动回写节）

> 加载条件：PM 派任何 multica issue 前（写工单时）读本文件。

## 创建命令

每个 issue 用：
```
~/bin/multica issue create --title "..." --description-file <file> --assignee <squad|agent> --status todo
```
`todo` + agent assignee = 立即点火。

⚠️ 大坑：别用 `--content-stdin`+heredoc+其它 flag 混带（flag 会被悄悄吞进 stdin，命令仍 exit 0）。用 `--description-file` 或 `--description`。

## description 文件结构

```
## 背景
<这个工单要解决什么，关联哪个 octo 讨论/PRD/设计稿/bug>

## 约束
<技术约束、跨端契约口径（老板已拍板的）、不可破坏的现有行为、AI 身份铁律、代码注释精简铁律>

## 验收标准
<明确可验的完成判据>

## 关联
- 代码仓库/分支：<repo@branch>
- GitHub/GitLab issue：<链接>（代码开发类必填）
- 关联 multica issue：<上游/绑定的开发或根因 issue id>

## 代码开发类专属（非代码工单可删）
- 开发完成后 push 到执行 agent 自己的 fork 仓库
- **开 draft PR（草稿 PR）承载 review**：`gh pr create --draft ...`。draft PR 有完整 diff、可 `gh pr review` 逐行审，但 **merge 锁死、不触发正式合并请求**。不在开发那一刻提正式 PR。
- **转正式 PR 不归本工单**：review + 部署 + 测试全绿、老板/PM 确认后，由 PM/指定人 `gh pr ready <PR>` 转正式。本工单只负责出 draft PR。
```

## 状态回报（无需在工单里写）

**本工单不含任何手动回写指令。** multica issue 到终态（done/blocked/in_review 等）时，由 **multica 平台自身的出站 webhook** 自动把状态回报到当前 octo surface。执行 agent 只需：干完活 + 把 issue 推到对应状态（`in_review`/`done`；卡住标 `blocked` 并在 issue 里说明原因）。回报与推进由 multica + 巡检员负责，工单本体聚焦「做什么、验收什么」。

## PM 状态板登记

PM 在 issue 入库时把行登记进**当前聊天状态板**（父群 `group.md` / 子区 `thread.md`）（issue_id / 类型 / assignee / 关联PR / status / 派单时刻 / 卡死判定阈值）；收到 multica webhook 回报或巡检 CLI 查得新状态时更新对应行。
