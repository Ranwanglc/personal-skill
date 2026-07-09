# 流程 B：IMPROVEMENT（优化/重构）—— 精简链路

> 加载条件：PM 判定任务类型为 IMPROVEMENT 时加载本文件。先读主 SKILL.md 的铁律 + 共同约定，写工单时读 `references/issue-template.md`。

## 步骤

1. [octo] PM 评估范围：纯技术优化（性能/重构/依赖升级）→ 跳过产品/设计，PM 直接出工单；涉交互/体验→拉产品专员确认。
2. [octo→multica] PM 出开发工单（优化目标 + **回归验收标准** + 不可破坏的现有行为 + GitHub/GitLab issue + push fork + 开 draft PR）。
3. [multica] 开发 agent 接单 → 执行 → **必须跑回归测试** → push fork → 开 **draft PR**（`gh pr create --draft`，锁死不可合）。**状态由 multica webhook 自动回报**（含 draft PR 链接）。
4. [multica] Reviewer 在 draft PR 上 `gh pr review`，重点看「有没有破坏现有功能」+ 性能/可维护性。
5. [multica] **开发团队-dev 本地 docker 部署到测试环境** → 验证部署成功。
6. [multica] 测试 agent 在测试环境跑回归用例 + 黑盒回归（重点验「优化没引入退化」）。
7. [octo] PM 回写，@老板验收。**全绿 + 老板确认后，`gh pr ready <PR>` 将 draft 转正式 PR**，merge 等批。

## 要点
- 验收核心 = **不退化**，回归测试权重高于新功能验证。
- 产品/设计是否参与看是否涉交互/体验。
- 测试 = 回归用例 + 黑盒回归。
- **PR 后置铁律**：push fork 后只开 **draft PR**，review+测试全绿且老板确认后才 `gh pr ready` 转正式 PR。
- 顺序铁律：开发 → **draft PR** → review → **部署 → 测试** →（全绿+老板确认）转正式 PR。
- **状态回报靠 multica 自身 webhook**，issue 到终态自动回报；巡检员用 multica-cli 定时查、专治卡死。
