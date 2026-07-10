# mano-cua 可视化测试流程（测试环节加载）

**执行归 测试小队-test**（在「部署到测试环境后」跑）。用 `mano-cua` 在桌面 Firefox 上做黑盒/真机 UI 测试并截图裁 PASS/FAIL。

> mano-cua 用法详见 workspace `TOOLS.md`「mano-cua 已装」条。要点：本机 `DISPLAY=:10.0`，云端模式直接可用，同设备一次只能跑一个任务。

## 测试规模

**每个功能 1–3 个用例即可**，只验功能是否生效，不追求覆盖全。老板固化：不做过多样例。

## 标准 7 步流程（填空模板）

每个测试单只需填 4 个空：**端口 / 账号 / 操作步骤 / 验证点**；其余话术固定。

1. **准备**：确认目标容器已起（复用现有或 local-deploy 临时新建的 301x）。开截图取证：`mano-cua config --set save-trajectory true`（一次性设过即可）。
2. **开浏览器 + 网址**：
   ```bash
   DISPLAY=:10.0 mano-cua run "<测试任务描述>" --url "http://localhost:<端口>" --max-steps 15 --minimize
   ```
   首次进某页用 `--url`；**同一浏览器会话内后续复用不带 `--url`**（否则每次新开 tab）。若目标 tab 被别的窗口挡住，任务描述里先让它「点回 Octo 那个 tab 到前台」。
3. **登录**：账号取 `~/projects/test-user.txt`（test1/2/3，邮箱+密码）。
   🔴 **硬约束**：明文密码只本地当次登录用；回报一律脱敏（`12****56` 或「已用文件中密码」），**绝不把明文密码打进发往 Octo 的消息，也不写进 MEMORY/Hindsight**。
4. **操作**：点哪个按钮 / 进哪个会话 / 填哪个表单（工单里写清）。例：「在 Recent 里打开 BotFather」。
5. **验证点**：在哪看到什么算 PASS（工单里写清）。例：「会话头显示 BotFather 且出现 /newbot 欢迎消息」。
6. **截图取证**：从 `~/.mano/trajectory/sess-*/screenshots/final.png` 取最新一张作为证据，cp 到报告目录。history.jsonl 有每步动作可复盘。
7. **收尾**：`mano-cua stop` 停任务 → 关测试用的浏览器 tab（多余 tab 用 Ctrl+W 逐个关）→ 若用了临时容器，按 local-deploy 规则 `docker rm -f` 拆掉。

## 用例文案模板（写进测试 multica issue）

```
【可视化测试用例 N】
- 目标端口：http://localhost:<端口>（<复用现有 / 临时容器 octo-web-test-xxx>）
- 登录账号：test<N>（凭据取 ~/projects/test-user.txt，回报脱敏）
- 操作步骤：<打开浏览器→该网址→登录→点击X→进入Y>
- 验证点（PASS 判据）：<看到 Z 即通过；未出现/报错即 FAIL>
- 证据：final.png 截图
- 收尾：mano-cua stop + 关 tab + 拆临时容器
```

## PASS/FAIL 裁决

tester 依据截图 + 验证点给明确 PASS/FAIL 结论回报，附证据截图路径。真机测试完成后，进「全绿 + 老板确认 → `gh pr ready` 转正式 PR」环节。
