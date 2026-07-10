# 本地部署方案（部署环节加载）

部署归 **开发团队-dev**（无独立部署 agent）。核心原则：**复用优先，只构建有改动的，测完即拆**。

## 当前本地底盘（复用基线，别乱动）

一套后端 compose 项目 `octo-deploy`（`/root/projects/octo-deploy/docker-compose.yaml`），全在 `octo-deploy_default` 网络：

| 服务 | 容器名 | 端口 | 说明 |
|---|---|---|---|
| octo-server | octo-deploy-octo-server-1 | 8090 | 后端 API，healthy |
| mysql | octo-deploy-mysql-1 | 3306(内) | 数据库 |
| redis | octo-deploy-redis-1 | 6379(内) | 缓存 |
| minio | octo-deploy-minio-1 | 9000/9001 | 对象存储 |
| wukongim | octo-deploy-wukongim-1 | 5001/5100/5200 | IM 长连 |
| octo-web(默认) | octo-deploy-octo-web-1 | 3000 | 前端 octo-web:local |

另有常驻前端 `octo-web-agentchat`（3003，octo-web:agent-chat-3003，同一套后端）。

> 3000/3003 只是前端镜像不同，**共用同一后端**。后端整套默认复用、**不重启**。

## 部署规则

1. **复用优先**：后端（server/mysql/redis/minio/wukongim）默认复用现跑的 `octo-deploy`，测试单不重启它；常驻 3000/3003 也不动。
2. **只构建有改动的**：本工单改了哪个服务，只 `docker build` 那一个镜像，起一个**临时容器**——独立容器名 + 独立端口，`--network octo-deploy_default` 复用后端。
3. **临时 web 端口段固定 3010–3019**（避开常驻 3000/3003，防撞端口）。命名建议 `octo-web-test<feat> / :301x`。
4. **测完即拆**：测试出 PASS/FAIL 后 `docker rm -f <临时容器>`，删临时镜像 tag；后端与常驻容器一律保留。
5. **本地专用 Dockerfile 不上线**：需 GOPROXY 加速就新建 `Dockerfile.local`（`ENV GOPROXY=https://goproxy.cn,direct`）+ 加进 `.git/info/exclude` 兜底，build 完即用，**绝不 commit/push**。
6. **构建镜像需 LLM 网关 key 时**：无特殊要求默认用固化的默认网关 key（见 MEMORY.md）。
7. **交付「容器清单」**：工单回报里写清——起了哪个临时容器/端口/镜像、复用了哪些、测完是否已拆。

## 临时容器起停示例（前端改动场景）

```bash
# 只重建改动的前端镜像（用本地 Dockerfile，不污染仓库）
cd <repo> && docker build -f Dockerfile.local -t octo-web:test-<feat> .
# 起临时容器，复用后端网络，占用测试端口段
docker run -d --name octo-web-test-<feat> --network octo-deploy_default \
  -p 3011:80 octo-web:test-<feat>
# —— 测试完成后 ——
docker rm -f octo-web-test-<feat>
docker rmi octo-web:test-<feat>
```

改后端服务同理：build 改动服务的镜像 → 起临时容器接同网络 → 测完拆。
