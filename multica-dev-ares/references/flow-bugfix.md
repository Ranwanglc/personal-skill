# 流程 C：BUG FIX（缺陷修复）—— 根因先行（拆成独立工单）

> 加载条件：PM 判定任务类型为 BUG FIX 时加载本文件。先读主 SKILL.md 的铁律 + 共同约定，写工单时读 `references/issue-template.md`。

## 步骤

1. [octo] 报 bug → PM 建 **bug issue**（现象、复现步骤、期望 vs 实际、环境）。
2. [multica] **独立的「根因定位」issue**：开发 agent 接单 → **只定位根因，不写修复**（源码「接了」≠功能能用；定不下来加埋点/日志抓铁证，参考标题 bug = APIClient 缺 patch verb 案例）→ 把根因结论写进 issue。**状态由 multica webhook 自动回报**（根因结论随回报带回 octo）。
3. [octo] **PM/老板确认根因**后，才进入开发；根因不认可就打回重定位。
4. [octo→multica] 根因认可 → PM 建 **修复开发 issue**（写清根因 + 修法方向 + 影响面 + GitHub/GitLab issue + push fork + 开 draft PR）。
5. [multica] 开发 agent 修复 → push fork → 开 **draft PR**（`gh pr create --draft`，锁死不可合）。**状态由 multica webhook 自动回报**（含 draft PR 链接）。
6. [multica] Reviewer 验「真修根因没」：在 draft PR 上 `gh pr review`，false-fix 判定必拉 head 分支 grep 具体 blocker；信 diff 不信 commit message。
7. [multica] **开发团队-dev 本地 docker 部署到测试环境**（部署归 dev 小队）。
8. [multica] 测试 agent：**先复现原 bug**（确认能复现）→ 在已部署环境应用修复 → 验证 bug 消失 → 跑回归 + 黑盒（确认没引新 bug）。
9. [octo] PM 回写根因+修复结论，@老板验收。**全绿 + 老板确认后，`gh pr ready <PR>` 将 draft 转正式 PR**；紧急 bug 可走加急 merge（老板拍板）。

## 要点
- **根因优先**：定位根因是**独立工单**，结论回 octo 等 PM 确认后再开发，不在同一工单里边定位边改。
- 测试 **先复现原 bug 再验修复** + 跑回归/黑盒确认没引新 bug。
- Review **验真修根因没**（防 false-fix）。
- **PR 后置铁律**：修复 push fork 后只开 **draft PR**，review+测试全绿且老板确认后才 `gh pr ready` 转正式 PR。
- 顺序：根因 → 确认 → 开发 → **draft PR** → review → **部署 → 测试** →（全绿+老板确认）转正式 PR。
- **状态回报靠 multica 自身 webhook**（根因定位单的根因结论随回报带回）；巡检员用 multica-cli 定时查、专治卡死。
