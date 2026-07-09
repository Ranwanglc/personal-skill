---
name: "multica-dev-ares"
description: "octo+multica dev team (Ares 版): user gives PM; PM forms team, dispatches FEAT/IMPROVEMENT/BUGFIX/RESEARCH/DESIGN as multica issues; multica's own webhook returns status; patrol uses multica-cli to catch STUCK issues."
---

# multica-dev-ares

把 **octo（对话/协调/沉淀层）+ multica（无状态执行层）** 的多角色研发团队抽象成一个可复用开发 skill。用户给定 PM，PM 自动组队、确认、然后按任务类型把开发工作拆成自包含 multica issue 派发执行。**状态回报由 multica 自身的出站 webhook 完成**（issue 到终态时 multica 主动回报），skill 不再在每个工单末尾塞手动回写指令。**巡检的核心 = 用 `multica-cli` 直接查、揪出卡死（stuck）的 issue 并救活**（同机可查），配 cron 定时兜底。

触发词：multica 开发团队、多角色研发、octo+multica、派单开发、FEAT/IMPROVEMENT/BUGFIX 流程、调研分析/方案设计（RESEARCH/DESIGN）、组研发团队。

**本 skill 是编排 skill**，复用 OpenClaw 已有工具（`octo_management` / `message` / Multica issue CLI `multica`（在 `/usr/local/bin/multica`）/ `cron` / `exec`），不造底层能力。设计骨架借鉴 `collab-research`（PM 选人→读成员→提议分工→用户批准→派发→巡检闭环），但执行体换成 multica issue 而非 octo 子区 worker。

> Ares 版与原 `multica-dev-team` 的关键区别：
> 1. **删掉「每个 issue 收尾手动回写（curl webhook / octo_hook.py）」整套机制**——multica 自己有出站 webhook 回报状态。
> 2. **巡检员改用 `multica-cli` 直接查 issue 状态**（multica 与本 agent 同机），核心目标是**发现并处理卡死的 issue**，不再靠「读 octo 状态板看回写有没有到」那套绕路。
> 3. **删除 `scripts/octo_hook.py`**（其唯一存在理由是替代 webhook，已无必要）。

---

## 渐进式加载（先读本文件，细节按需加载）

| 何时加载 | 加载文件 |
|---|---|
| 派任何 multica issue 前（写工单时） | `references/issue-template.md`（自包含工单模板；无手动回写节） |
| 判定任务类型为 FEAT | `references/flow-feat.md` |
| 判定任务类型为 IMPROVEMENT | `references/flow-improvement.md` |
| 判定任务类型为 BUG FIX | `references/flow-bugfix.md` |
| 判定任务类型为 RESEARCH（调研分析） | `references/flow-research.md` |
| 判定任务类型为 DESIGN（方案设计） | `references/flow-design.md` |

本 SKILL.md 只保留：分层原则 + 铁律 + Phase0/1 组队 + 三流程共同约定与对比 + 巡检闭环 + 汇总 + 工具映射。流程细节与工单模板在上述 reference 文件里，用到再读。

---

## 0. 核心分层原则（先内化）

| 层 | 平台 | 特性 | 谁在这层 |
|---|---|---|---|
| 对话/协调/沉淀层 | **octo** | 有状态、人格连续、跨对话记忆、@人、要拍板 | PM / 产品专员 / 设计师 / 巡检员 |
| 执行层 | **multica** | 无状态、自包含工单、产物可追踪、可 rerun、出 PR | 前端 / 后端 / 部署 / Reviewer / 测试 |

判据：角色价值在「持续对话/拍板」还是「一次性产出 artifact」。前者→octo，后者→multica。

**两套身份不能混**：octo 角色是常驻对话 agent；multica 执行体是无状态工单 agent（走 multica issue 派单）。「分配 octo 角色」和「派 multica issue」是两个不同动作。

**当前聊天 surface（current surface）—— 全程按它走**：开发可能发生在**父群**或**子区(thread)**，两者状态板存储不同，必须先判定当前聊天是哪一种，全程一致：

| 当前聊天 | 状态板 | 读/写工具 |
|---|---|---|
| **父群** | `group.md` | `group-md-read` / `group-md-update` |
| **子区(thread, type5)** | `thread.md` | `thread-md-read` / `thread-md-update` |

**状态回报 = multica 自身 webhook（现行方案）**：multica issue 到终态（done/blocked/in_review 等）时，由 **multica 平台自己的出站 webhook** 把状态回报出来，落到当前 octo surface。skill **不再**要求执行 agent 在工单 prompt 末尾手动 `curl` 或调脚本回写。PM/巡检员据此推进下一环，并把状态登记进当前 surface 状态板。

**当前已建 multica 资源**（真实状态，skill 默认对接，可被用户覆盖）：

| squad | id | 成员 | 职责 |
|---|---|---|---|
| **开发团队-dev** | `7d5e63f4-8ddd-4296-937f-2c51d653f2bb` | leader `dev-work01` + developer `dev-work02`/`dev-work03` | 前端/后端/脚本开发 **+ 本地 docker 部署验证**（部署归 dev 小队，无独立部署 agent） |
| **审核小队-review** | `772b69d6-a1f3-4f9c-88ee-04df2fdeb4b6` | leader `review-lead01` + reviewer `dev-review01-gpt`/`dev-review02-glm`（双引擎独立评审） | 方案评审 + 代码评审两道独立关口 |
| **测试小队-test** | `a399e803-d9ba-465d-86f0-ca960686a1e9` | leader `test-lead01` + tester `dev-test01` | 构建/单测/集成/回归验证，给 PASS/FAIL 裁决 |

⚠️ **部署无独立 agent**：打包部署（本地 docker）是**开发团队-dev 的职责之一**（dev 小队 instructions 第6步「本地部署验证」）。派部署工作时 assignee 用 dev 小队，不要找 `<deploy-agent>`。

---

## 1. 铁律（全程强制）

1. **状态回报靠 multica 自身出站 webhook**：multica issue 到终态时由 multica 平台主动回报状态到当前 octo surface。skill **不在** issue prompt 里塞任何手动回写（不 `curl webhook`、不调 `octo_hook.py`）。执行 agent 只管干活 + 按流程推进 issue 状态机，回报交给 multica。
2. **巡检核心 = 每 30 分钟用 multica-cli 全量筛查当前工作区所有在途 issue（不是盯单个）**（老板 2026-07-09 固化）：mulica 与本 agent 同机，巡检员用 `multica issue list --output json` / `issue runs <id>` 直查真实状态。判据：**最新执行日志(run) 超 20 分钟没动 且 非执行中状态 → 可能需要踢一下**（STALE_MIN=20）。处理手法见 Phase 3。⚠必须是当前工作区的**全量筛查**，绝不能窄化成只盯一个 issue 的 watcher。
3. **状态板存当前聊天 surface**（持久）：PM 把每个 issue 的登记行（issue_id / 类型 / assignee / 关联PR / status / 派单时刻）写进当前 surface 状态板（父群 `group.md` / 子区 `thread.md`），session reset 不丢。
4. **PM 必须是群 bot 管理员**（要写当前聊天状态板 group.md/thread.md）；开 skill 前自检，失败显式报错不静默。
5. **角色分配靠 PM 对成员的了解推断**：`group-members` 无 skill 字段，PM 按已知能力推断分配，**必须标注「基于推断，可能不准，请校正」**。不在状态板维护成员能力登记表。
6. **分配后先问用户合不合理，用户可改，再继续**（never jump the gun）——批准前绝不派任何 multica issue。
7. **PM 不能把任务派给自己**（@不了自己→死锁）；**巡检员不能是 PM 本人**。**产品专员 + 设计师统一由 PM 兼任**（老板 2026-07-09 特别指认，不单拉人）。
7b. **老板/用户告知巡检员是谁后，PM 必须立即 @巡检员告诉他巡检任务**（老板 2026-07-09 固化）：讲清「全量扫当前工作区在途 issue + every 30min + 最新 run idle≥20min 且非执行中就踢 + 救活手法 + 回报去向」。**巡检员已有相符的全量巡检定时器就复用，不重建**。
8. **每个 multica issue 必须自包含**：背景 + 约束 + 验收标准 + 关联仓库/分支。执行 agent 不靠脑补。**代码开发类 issue 额外必须含**：① 对应的 GitHub/GitLab issue 链接；② 明确「开发完成后 push 到执行 agent 自己的 fork 仓库」；③ 明确「开发完成后开 **draft PR**（草稿 PR，锁死不可合、不触发正式合并），承载 review；不在写完代码那一刻提正式 PR」。详见 `references/issue-template.md`。
9. **PR 后置 + draft 过渡（顺序铁律核心）** ⭐：正式 PR 是「成品才提」的对外产出物，必须**测试全绿 + 老板/PM 确认后**才提。代码写完只开 **draft PR** 承载逐行 review（保留 `gh pr review` 能力又不污染上游、不被误合）；review → 部署 → 测试全过 → 老板确认 → `gh pr ready <PR>` 把 draft 转正式 PR，此刻才进 merge 候选。**绝不在开发那一刻就提正式 PR**。
10. **失败不自动级联**：上游 issue 失败时下游别自动判死，挂起并报人等决策（开发链尤其重要，如前端依赖后端契约）。
11. **merge 永远等老板拍板**，PM 绝不自动 merge；**draft 转正式（`gh pr ready`）同样等测试全绿 + 老板确认**。
12. **对外产出物绝不暴露 AI 身份**：禁 Co-Authored-By、禁 "Generated by AI/Claude"，全英文，以人类开发者身份写。
13. PM 是**当前聊天状态板**（父群 `group.md` / 子区 `thread.md`）唯一 writer，状态板格式稳定。
14. **代码注释精简**：只写「为什么/关键约束」，不复述代码、不写评审过程/历史八卦；派 dev issue 时把这条写进工单约束。

---

## 2. Phase 0 — 前置自检（阻塞）

开任何东西前：
0. **判定当前聊天 surface**（父群 or 子区，见开头「当前聊天 surface」表）——后续状态板读写、巡检催办全按它走。
1. **用户已指定 PM**。
2. **PM 自检 bot-admin**：写**当前聊天状态板**（`group-md-update` 或 `thread-md-update`）需管理员权限，失败显式报错（否则状态管理全程死掉却看似在跑）。
3. **multica CLI 可用**：`multica issue list --output json` 探活（CLI 在 `/usr/local/bin/multica`，也可 `~/bin/multica`）；确认三个 squad（开发团队-dev / 审核小队-review / 测试小队-test）存在（部署归 dev 小队，无独立部署 agent）。
4. **确认 multica 出站 webhook 已配置**（状态回报通道）：确认 multica 侧 webhook 会把 issue 终态回报到当前 octo surface。若未配/不确定，回报靠巡检 CLI 兜底，但应显式告知用户「回报只走巡检查询」。

---

## 3. Phase 1 — 组队：读成员 → 按了解分配 octo 角色 → 用户确认

1. PM 读群/子区成员：`octo_management group-members`（父群，`robot=1`，**不按 owner 过滤**——别人的 agent 也能入队）。
2. PM **按任务类型决定需要哪些 octo 角色**：
   - **巡检员：必须有**（任何任务都要；核心职责 = 处理停滞 issue）。**巡检员不能是 PM 本人**；由用户/老板指定。
   - **产品专员 + 设计师：统一由 PM 兼任**（老板 2026-07-09 特别指认）——不单独拉人当产品/设计，需要产品需求/PRD/设计时 PM 自己上。
3. 巡检员由用户/老板指定；其余角色（产品/设计）已固定由 PM 兼任，无需推断分配。
4. **PM 被告知巡检员是谁后，必须立即 @巡检员告诉他巡检任务**（老板 2026-07-09 固化）：把「巡什么（当前工作区全量在途 issue）+ 规则（every 30min 全量扫、最新 run idle≥20min 且非执行中就踢）+ 救活手法 + 回报去向」讲清楚。**如果巡检员已有相符的定时器（相同全量巡检 cron）就复用，不重建**；没有才新建。
5. 涉交互/UI 时需不需要额外确认由 PM 自行判断（产品/设计都是 PM），拆单前向用户确认需求。
6. PM 把提议（需要哪些角色 + 巡检员是谁 + 哪些 multica squad 接执行）发到群，**问用户：这么分配是否合理？** 用户可修改。
7. **用户批准后才继续**；用户改了就重排再问。批准前不派任何 issue、不建任何 thread。

---

## 4. Phase 2 — 按任务类型执行（共同约定 + 加载对应流程文件）

共同约定（三套流程通用）：
- octo = 讨论 + 派单 + 汇报入口；multica issue = 执行 + 留痕载体。
- PM 负责「需求↔工单」翻译 + 全程协调 + 状态登记**当前聊天状态板**（父群 group.md / 子区 thread.md）。
- multica issue 状态机：`backlog → todo(点火) → in_progress → in_review → done`，旁路 `blocked` / `cancelled`。`todo` + agent assignee = 立即触发跑。
- **状态回报由 multica webhook 自动完成**；PM/巡检员收到回报后更新状态板、推进下一环。回报没到时靠巡检 CLI 主动查（Phase 2.5/3）。
- 每个开发 issue 完成后开 **draft PR** 并关联（不是正式 PR），review/测试 issue 与开发 issue 绑定。
- **部署在测试之前**：没部署到测试环境就没法做真机/黑盒测试，顺序固定为「开发 → draft PR → review → 部署 → 测试 →（全绿+老板确认）转正式 PR」。
- **PR 后置**：开发完只开 draft PR，正式 PR（`gh pr ready`）等测试全绿 + 老板确认。

**PM 先判定任务类型，然后只加载对应那一个流程文件执行**：
- FEAT → `references/flow-feat.md`
- IMPROVEMENT → `references/flow-improvement.md`
- BUG FIX → `references/flow-bugfix.md`
- RESEARCH（调研分析） → `references/flow-research.md`（交付报告，无 PR/部署/测试）
- DESIGN（方案设计） → `references/flow-design.md`（交付方案文档，无 PR/部署/测试）

> **两类新流程（RESEARCH/DESIGN）是「非代码交付」**：交付物是报告/方案 md，随 webhook 回报，**不 push fork / 不开 PR / 不部署 / 不跑测试**（铁律里「PR 后置/draft 转正式/部署在测试之前」对这两类不适用）；但仍走 multica issue + webhook + 巡检。它俩常作为 FEAT 的**前置**：调研→方案→（获批后）拆开发工单。

### 五流程对比速查（判型用，细节看各自文件）
| | FEAT | IMPROVEMENT | BUGFIX | RESEARCH（调研） | DESIGN（方案） |
|---|---|---|---|---|---|
| 交付物 | 代码 | 代码 | 代码 | 调研报告 md | 方案设计 md |
| 产品/设计参与 | 全程 | 看是否涉交互 | 一般不需要 | 一般不需要 | 看需求（涉交互拉产品） |
| 验收核心 | 满足 PRD 验收标准 | 不退化（回归优先） | 根因消除 + 不引新 bug | 结论可信 + 依据可追溯 | 可落地 + 覆盖需求 + 风险标清 |
| Review 重点 | 完整性+正确性 | 破坏现有行为没 | 真修根因没（防 false-fix） | 结论有据/来源可核/无臆造 | 覆盖需求/契约无歧义/能拆单 |
| PR/部署/测试 | 有 | 有 | 有 | **无**（报告随 webhook 回报） | **无**（方案随 webhook 回报） |
| 顺序 | 开发→draft PR→review→**部署→测试**→转正式PR | 同 | 根因→确认→开发→同上 | 调研→出报告→review→老板确认 | 设计→出方案→review→老板拍板（→转 FEAT） |

---

## 5. Phase 2.5 — 挂载巡检 cron（必做，派完首批 issue 后）

> 巡检必须有**主动定时机制**去发现停滞（stalled）的 issue，否则卡死/webhook 漏报永远没人管。参照 `collab-research` 的 arm-patrol-loop。**停滞判定逻辑对齐 Herbin 的 stale-scan 规则**（`multica-squad-ops/scripts/multica_stale_scan.py`，2026-07-09 同步），见下 §5.1。

1. PM/巡检员 `cron add` 一个 **isolated 全量巡检轮**（schedule=every 30min，payload=agentTurn）。⚠是**当前工作区的全量筛查**（扫所有在途 issue），**不是盯单个 issue**。payload **自包含**：accountId=`default`、当前 surface 类型（父群/子区）+ channelId、状态板位置（`group.md`/`thread.md`）、停滞阈值 `STALE_MIN=20`（最新 run 过 20 分钟没动且非执行中）、豁免白名单、催办/救活文案、skill 绝对路径。
2. 每轮固定动作：
   - **单飞锁**（防并发：未过期锁→no-op 退出，过期→接管）。
   - **用 `multica-cli` 全量扫当前在途 issue**，按 §5.1 stale-scan 规则算每个的 idle_minutes，揪出 stalled（最新 run idle ≥ STALE_MIN(20) 且无在途 run）。
   - **救活手法**：见 Phase 3（rerun / comment 催 / 报人）。
   - 读/更新**当前 surface 状态板**（`group-md-read`/`thread-md-read`/`-update`），在当前 surface 催办；上游失败→@用户报人。
   - **心跳（强制）**：即使 stale_count==0 也发一条心跳（`✅ 巡检（scanned_at ...）无停滞。active N 个`），让「静默失败」能和「干净结果」区分开。
   - 清锁。
3. 配 **12h 一次性兜底删除**（`at` + `deleteAfterRun`）防僵尸；jobId 记进当前 surface 状态板。
4. 一条链路全 done → 末轮自删 cron + 发汇总。
5. **暂停/恢复**：老板说「暂停巡检」→ `cron` 把该 job disable（paused，不删）；说「恢复」→ 重新 enable。paused 期间不扫描、不报停滞，任务保留。

### 5.1 stale-scan 停滞判定（全量筛查，逐条照做）

巡检**每 30 分钟用 multica-cli 全量扫当前工作区所有「在途」issue**（不是盯单个），判定 stalled 用下面 6 条（阈值 `STALE_MIN=20` 分钟）：

1. **只巡在途**：`status ∈ {todo, in_progress, in_review, blocked}`；`done`/`cancelled` 直接跳过。
2. **有在途 run 就不算停滞**：对每个在途 issue 拉 `multica issue runs <ID> --output json`（runs 最新在前）。只要最新 run 处于执行中状态 `{running, queued, dispatched, pending, in_progress}` → 还在干活，跳过。
3. **last_activity 取最新 run 时间**：否则「最后活跃时间」= 最新执行日志(run) 的 `created_at / started_at / dispatched_at / completed_at` 时间戳，并上 issue 自身 `updated_at`，取 `max()`。用 max（而非只看 run 时间）是为了避免「有人评论了但没触发新 run」误报。
4. **idle 判定（老板固化）**：`idle_minutes = now - last_activity`；**最新执行日志 idle ≥ STALE_MIN(20) 分钟 且非执行中状态** → 判 stalled（可能需要踢一下）。结果按 idle 降序排。
5. **零 run 边界**：在途但零 run（一直没被 pick up）的 issue 也可能 stalled——只要 `updated_at` 已过 20min 同样纳入。
6. **心跳**：即使 `stale_count==0` 也输出一条心跳（见 Phase 2.5 步骤 2）。

**豁免白名单（不催）**：某些在途 issue 是「等老板治理/已知挂起」的，即便 idle 超阈值也**不催办**，只在心跳里注明「N 个在等老板治理已豁免（不催）」。白名单 issue-id 列进当前 surface 状态板，由 PM/老板维护。

---

## 6. Phase 3 — 巡检员闭环（核心：处理卡死的 issue）

**巡检的核心目标 = 发现并救活卡死（stuck）的 issue。** 双层：

- **主通道 = multica webhook 自动回报（事件驱动）**：issue 到终态时 multica 自己回报到当前 octo surface → PM/巡检员更新状态板、推进下一环（review→部署→测试，或根因→确认→开发）。正常流转不需要巡检介入。
- **兜底通道 = cron 定时用 multica-cli 主动查（Phase 2.5）**：专抓**停滞（stalled）**——按 §5.1 stale-scan 规则：最新 run idle≥STALE_MIN(20) 分钟 且 非执行中。这是巡检的主战场。

### 停滞判定 + 救活手法（对齐 stale-scan，见 §5.1）

| 停滞症状 | 用 CLI 怎么确认 | 救活手法 |
|---|---|---|
| 在途但零在途 run 且 idle≥20min（`todo` 点火没跑 / 无人 pick up） | `runs <id>` 无在途状态 run + last_activity 已过 20min | `issue rerun <id>` 重新点火；仍不动→报人查 assignee/agent 是否存活 |
| `in_progress`/`in_review` 最新 run idle≥20min且非执行中 | `runs <id>` 最新 run 已终态 + last_activity(runs∥updated_at max) 超 20min | `issue comment add <id>` 追问进度 + `issue rerun <id>`；连续两轮没动→报人 |
| `in_review` 挂着但 review run 已 completed（收尾漏流转） | `runs <id>` review run=completed 但 status 未进 done | 以 CLI 为准推进下一环（补上漏掉的流转）+ `comment add` 催收尾 |
| webhook 回报未到但 CLI 已 done/in_review | CLI 状态与状态板不一致 | 以 CLI 为准更新状态板 + 推进下一环 |
| 标了 `blocked` | `issue get <id>` 看 blocked 原因 | 不自动判死；在当前 surface @用户报明 blocked 原因 + 受影响下游，等决策 |
| 豁免白名单（等老板治理/已知挂起） | 在状态板白名单里 | **不催**，只在心跳注明已豁免（见 §5.1） |
| `cancelled` / 异常终态 | `issue get <id>` | 报人 + 挂起依赖它的下游 |

- **巡检员职责**：**每 30 分钟用 multica-cli 全量筛查当前工作区所有在途 issue**（不是盯单个），专治停滞（最新 run idle≥20min 且非执行中）；正常流转交给 webhook。
- **失败处理**：上游 issue 标 blocked/失败 → 下游依赖它的 issue **不自动判死**，PM 挂起下游 + 在**当前 surface** @用户说明失败上游和受影响下游范围，**等用户决策**，绝不自动级联失败。

---

## 7. Phase 4 — 完成与汇总

- 一条链路全 done（**当前 surface 状态板**为准，以 multica-cli 实查校验）→ PM 在**当前聊天**发最终汇总（各 issue 结论 + PR 链接），@老板验收。
- **merge 等老板拍板**，PM 绝不自动 merge。
- 未完成/挂起/失败的 issue 在汇总里明确点名，归因到上游原因，交人决策。

---

## 8. 工具映射

| 用途 | 工具 |
|---|---|
| 读群成员 | `octo_management group-members`（父群，robot=1，不按 owner 过滤） |
| 状态板登记/更新 | **当前 surface**：父群→`octo_management group-md-update`；子区→`octo_management thread-md-update`（PM 唯一 writer） |
| 建/派 multica issue | `multica issue create --description-file ... --assignee <squad\|agent> --status todo` |
| 查 issue / 状态（巡检核心） | `multica issue list --output json` / `issue get <id>` / `issue runs <id>` / `issue status <id> <state>` |
| 救活停滞 / 重跑 / 中断 | `multica issue rerun <id>` / `issue cancel-task <id>` |
| issue 对话/催进度/补上下文 | `multica issue comment add <id> --content "..."` |
| 挂载巡检 cron | `cron add`（every 30min isolated agentTurn 全量扫，最新 run idle≥20min 且非执行中就踢，STALE_MIN=20）+ 12h `at` deleteAfterRun 兜底 |
| @成员 | `octo_management group-members` 取 uid → `@[<uid>:<displayName>]`（方括号必需，单冒号，真 32-hex uid） |
| 群播报/派单/催办 | `message send`（父群或对应子区） |
| 状态回报（回程） | **multica 自身出站 webhook**（skill 不手动回写）；回报没到靠巡检 CLI 补 |

---

## 9. 落地建议（分阶段）

1. **地基先验**：先用现有三个 squad（开发团队-dev / 审核小队-review / 测试小队-test，部署归 dev 小队）跑通一条最短 BUGFIX 链路（octo 报 bug→根因定位工单→multica webhook 回报根因→PM 确认→修复开发→review→dev 小队本地部署→测试），确认 multica webhook 回报真通 + 巡检 CLI 能揪出卡死 issue。
2. **再上 FEAT 全链路**：产品/设计 octo 角色就位后跑完整流程（开发→review→部署→测试）。
3. **角色就位前置**：octo 角色（PM/产品/设计/巡检）的方法论能力由各 agent 自行准备，本 skill 不规定其安装方式。

---

## 附：octo 角色 instructions 要点（建团队 agent 时用）

- **PM**：octo 群里的讨论收敛成自包含 multica 工单（背景/约束/验收/关联仓库分支/GitHub-GitLab issue/push fork/开 draft PR 承载 review），派给对应 squad/agent，状态登记状态板并 @派单人。只调度不写代码。发号拍板钉死不横跳。绝不替老板拍板、绝不自动 merge、绝不在开发那刻提正式 PR（只开 draft）；测试全绿+老板确认后才 `gh pr ready` 转正式 PR。BUGFIX 先派根因定位独立工单，根因回来等老板/自己确认再派修复。
- **产品专员**：需求分析 + PRD（含验收标准），先澄清再动笔，不臆测扩展，先方案后实施等 approval。
- **设计师**：基于产品需求出 UI/视觉设计与原型，迭代听反馈，产出设计系统避免通用 AI 审美。
- **巡检员**：核心 = 处理停滞 issue。**每 30 分钟用 multica-cli 全量扫当前工作区所有在途 issue（不是盯单个）**，判定对齐 stale-scan 规则（只巡 {todo,in_progress,in_review,blocked}；最新 run 执行中不算停滞；last_activity=runs∥updated_at 取 max；**最新 run idle≥20min 且非执行中 判 stalled**；零 run 边界也纳入；无停滞也发心跳）。救活手法 = rerun + comment 催 + 报人（见 Phase 3 表）。豁免白名单（等老板治理）不催。失败不自动级联、挂起报人等决策。巡检员不能是 PM 本人。被指定后 PM 会 @ 他交代巡检任务，已有相符定时器则复用。
