# 流程 A：FEAT（新功能）—— 全链路（最长）

> 加载条件：PM 判定任务类型为 FEAT 时加载本文件。先读主 SKILL.md 的铁律 + 共同约定，写工单时读 `references/issue-template.md`。

## 步骤

1. [octo] 老板提需求 → PM + 产品专员澄清。
2. [octo] 产品专员出 PRD（含验收标准）→ 老板 approve。
3. [octo] 设计师出 UI 设计稿/原型（需 UI 时）→ 老板/产品 confirm。
4. [octo→multica] PM 把 PRD 拆成自包含工单：前端 issue（关联设计稿）+ 后端 issue（关联 API 契约）。**契约/前缀口径等跨端决策先在 octo 由老板拍板，写进工单**。开发类工单必须含对应 GitHub/GitLab issue、push 自己 fork、开 draft PR。
5. [multica] 前端/后端 agent 接单 → 执行 → 自测 → push 自己 fork → 开 **draft PR**（`gh pr create --draft`，承载逐行 review，**锁死不可合、不触发正式合并**）→ issue 进 in_review。**状态由 multica webhook 自动回报**（含 draft PR 链接）。
6. [multica] Reviewer 接 review issue（CC+Codex 双引擎）→ 在 draft PR 上逐行 `gh pr review` → 三态结论。CHANGES_REQUESTED→打回 rerun；APPROVED→下一步。
7. [multica] 部署 agent（`<deploy-agent>`）打包部署到测试环境 → 验证部署成功（健康检查 + 服务起来）。
8. [multica] 测试 agent 在已部署的测试环境上：基于 PRD 出测试用例 → 跑用例 + **黑盒测试（真机操作、边界/异常路径、端到端场景）** → 报告。失败→回开发（附复现步骤+截图）；通过→done。
9. [octo] PM 汇总回写群，@老板验收。**全绿 + 老板确认后，才把 draft PR 转正式**（`gh pr ready <PR>`，此刻才进 merge 候选）；**merge 仍等老板批**。

## 要点
- 产品/设计全程参与，验收核心 = 满足 PRD 验收标准。
- 测试 = 用例 + 黑盒全覆盖。
- 顺序铁律：开发 → **draft PR** → review → **部署 → 测试** →（全绿+老板确认）转正式 PR（没部署没法测）。
- **PR 后置铁律**：写完代码只开 **draft PR**（半成品、锁死不可合），review+测试全绿且老板确认后才 `gh pr ready` 转正式 PR。不在开发那一刻就提正式 PR。
- **状态回报靠 multica 自身 webhook**，issue 到终态自动回报；巡检员用 multica-cli 定时查、专治卡死。
