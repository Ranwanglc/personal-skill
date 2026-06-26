---
name: multica-cli
description: Multica CLI 完整命令参考。当需要用 `multica` 命令管理 AI agent、拆解/指派 issue、组建 squad、拉取仓库、安装平台 skill、配置 autopilot、查 runtime/daemon 状态时使用本 skill。覆盖 20 个顶层命令及全部子命令的用途、关键参数、易错点与高频组合。
---

# Multica CLI 使用指南

> 通用调用形式：`multica <命令> <子命令> [flags]`
> 几乎所有 `list` / `get` 都支持 `--output json`，脚本解析优先用 JSON。
> 本文命令树来自 `multica --help` 实测，非记忆编造。

## 何时用本 skill

- 要在 Multica 工作区里**拆任务、派活、跟进度、改状态**（`issue` 系列）。
- 要**管理 AI 队员/小队**、给 agent 绑定 skill 或设环境变量（`agent` / `squad`）。
- 要**拉代码干活**（`repo checkout`）。
- 要**给团队装平台级 skill**（`skill import` + `agent skills add`）。
- 要配**定时/触发自动化**（`autopilot`），或查 **runtime / daemon** 状态。

---

## 全局选项（所有命令通用）

| Flag | 作用 |
|------|------|
| `--profile <name>` | 配置 profile，隔离 config/daemon/workspace |
| `--server-url <url>` | 服务器地址（env `MULTICA_SERVER_URL`） |
| `--workspace-id <id>` | 指定工作区（env `MULTICA_WORKSPACE_ID`） |
| `--debug` | 失败时打印完整错误 |
| `-h/--help`、`-v/--version` | 帮助 / 版本 |

---

## CORE 核心命令

### 1. `agent` — 管理 AI 队员

| 子命令 | 作用 |
|--------|------|
| `list` | 列所有 agent — `multica agent list --output json` |
| `get` | agent 详情（instructions/runtime/model） — `agent get <id> --output json` |
| `create` / `update` | 创建 / 修改 agent |
| `archive` / `restore` | 归档 / 恢复 |
| `avatar` | 上传头像 |
| `tasks` | 列某 agent 的任务 |
| `skills` | skill 绑定：`add`(追加) / `set`(替换全部，谨慎) / `list` |
| `env` | 自定义环境变量（仅 owner/admin，**有审计**）：`get` / `set` |

### 2. `issue` — 任务核心（命令最多）

| 子命令 | 作用 |
|--------|------|
| `list` / `get` / `create` / `update` | 增查改 |
| `status` | 快捷改状态 — `issue status <id> in_progress` |
| `assign` | 指派给 member/agent/squad |
| `children` | 看子任务（按 stage 分组） |
| `search` | 按标题/描述搜索 |
| `label` | 打/去标签 |
| `metadata` | KV 元数据：`list`/`get`/`set`/`delete` |
| `comment` | 评论：`add`/`list`/`delete`/`resolve`/`unresolve` |
| `subscriber` | 订阅者：`add`/`list`/`remove` |
| `pull-requests` | 关联 PR（含 state/CI） |
| `runs` / `run-messages` | 执行历史 / 某次执行消息流 |
| `rerun` | 重新入队成新 task |
| `cancel-task` | 取消运行中的 task（中断 agent） |
| `usage` | issue token 用量 |

`issue create` 关键参数：

```bash
multica issue create --title "标题" --description-file desc.md \
  --priority high --status todo \      # todo=立即开工，backlog=不自动触发
  --assignee-id <uuid> --parent <issue-id> \
  --stage N \                          # 同 stage 并行，跨 stage 串行
  --project <id> --due-date <RFC3339> --attachment <path>
```

- 状态枚举：`todo / in_progress / in_review / done / blocked / backlog / cancelled`
- ⚠️ 评论务必用 `--content-file`（inline `--content` 会被 shell 改写反引号 / `$()`）。
- ⚠️ 长描述用 `--description-file`（heredoc 内联会吞掉后续 flag）。

### 3. `autopilot` — 定时/触发式自动化

`list` / `get` / `create` / `update` / `delete` / `runs` / `trigger`(手动触发一次) /
`trigger-add`(加 schedule 或 webhook) / `trigger-update` / `trigger-delete` / `trigger-rotate-url`

### 4. `project` — 项目

`list` / `get` / `create` / `update` / `delete` / `status`
\+ `resource`（挂资源：`add --type github_repo --url <url>` / `list` / `update` / `remove`）

### 5. `repo` — 仓库

| 子命令 | 用法 |
|--------|------|
| `checkout` | `repo checkout <url> [--ref <branch/sha>]` — 拉到工作目录（建 worktree） |
| `add` / `list` / `remove` | 工作区仓库注册表管理 |

### 6. `skill` — 平台层 Skill

`list` / `get` / `import` / `create` / `update` / `delete` / `search`
\+ `files`（`list` / `upsert` / `delete`）

- `import --url <url>` — **唯一受支持的安装路径**，支持 clawhub.ai / skills.sh / github.com，
  `--on-conflict fail|overwrite|rename|skip`。
- ⚠️ **平台 skill ≠ 本地 `~/.hermes/skills/`**。只有进了工作区 skill 库才能被平台管理、
  并通过 `agent skills add` 绑定到 agent。手动塞本地目录平台看不见、管不了。

### 7. `squad` — 小队

`list` / `get` / `create` / `update` / `delete`
\+ `member`（`add` / `list` / `remove` / `set-role`）
\+ `activity`（记录 squad leader 评估）

### 8. `label` — 标签

`list` / `get` / `create` / `update` / `delete`

### 9. `workspace` — 工作区

`get` / `list` / `switch`(设默认) / `update`(仅 admin/owner)
\+ `member list`

---

## RUNTIME 运行时命令

### 10. `runtime` — Agent 运行时

`list` / `activity`(按小时 task 活动) / `usage`(token) / `update`(触发 CLI 更新) / `delete`
\+ `profile`（`list` / `create` / `update` / `delete` / `set-path` / `unset-path`）

### 11. `daemon` — 本地运行时守护进程

`start` / `stop` / `restart` / `status` / `logs` / `disk-usage`(按 task/workspace 看磁盘)

---

## ADDITIONAL 辅助命令

| 命令 | 作用 |
|------|------|
| `attachment download` | 下载附件到本地 |
| `auth status` / `auth logout` | 认证状态 / 清 token |
| `config show` / `config set` | 查 / 设 CLI 配置 |
| `login` | 认证并配置工作区 |
| `setup cloud` / `setup self-host` | 配置 CLI（云端/自托管）并启 daemon |
| `update` | 升级 CLI |
| `user profile get` / `update` | 查 / 改个人 profile |
| `version` | 版本 |

---

## 高频组合速查

```bash
# 看我和队员
multica agent list --output json

# 拆任务派活（子任务 + 立即开工 + 编排 stage）
multica issue create --title "..." --description-file desc.md \
  --parent <父issue> --stage 1 --assignee-id <队员id> --status todo

# 看任务全貌
multica issue children <父issue> --output json

# 加评论（必须用文件）
multica issue comment add <issue> --content-file reply.md --parent <comment-id>

# 拉代码干活
multica repo checkout <git-url> --ref <branch>

# 装平台 skill 并绑给 agent
multica skill import --url github.com/owner/repo/tree/main/skill --output json
multica agent skills add <agent-id> --skill-ids <skill-id> --output json
```

---

## 易错点速记

1. **评论/长文用文件**：`--content-file` / `--description-file`，别用 inline，shell 会改写反引号、`$()`，heredoc 会吞 flag。
2. **`status` 与 `backlog` 的触发差异**：`todo` 立即开工；`backlog` 不自动触发。
3. **stage 编排**：同 stage 并行、跨 stage 串行。
4. **`agent skills set` 是替换全部**：要追加用 `add`，别误用 `set` 把已有绑定清掉。
5. **平台 skill 与本地 skill 是两套**：要团队可见可管，走 `skill import` + `agent skills add`，别手动塞 `~/.hermes/skills/`。
6. **脚本解析一律加 `--output json`**。
