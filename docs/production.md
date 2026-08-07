# 生产部署与压测验收

## 部署形态

前端：Vue 3 管理端、React 门户端（Vite）；Celery broker / RedBeat 仅使用 Redis。

单机单 Docker：一个项目容器内运行 API、worker、beat，PostgreSQL、Redis 由外部基础设施提供。

```bash
docker compose run --rm hei migrate
docker compose up -d --build
```

等价 Docker 命令：

```bash
docker build -t hei-fastapi-backend .
docker run --rm --env-file .env hei-fastapi-backend migrate
docker run -d --name hei-fastapi-single --env-file .env -p 8000:8000 hei-fastapi-backend all
```

单机多 Docker 多实例：复制同一个项目镜像的 `api` / `worker` 角色，基础设施仍由外部提供。

```bash
docker compose -f docker-compose.multi.yml up -d --build --scale api=2 --scale worker=2
docker compose -f docker-compose.multi.yml --profile seed run --rm seed
```

多机多节点：面向 Docker Swarm 或等价编排环境，应用节点接入外部 PostgreSQL、Redis，API/worker 按副本数横向扩展，beat 固定单副本。

```bash
docker build -t hei-fastapi-backend:latest .
docker build -t hei-fastapi-admin:latest web/admin
docker network create --driver overlay --attachable hei_overlay
docker node update --label-add hei.beat=true <beat-node>
docker compose -f docker-compose.distributed.yml config | docker stack deploy -c - hei-fastapi
```

分布式部署前必须提供外部基础设施地址：

```bash
export APP__CONFIG_CRYPTO_KEY="..."
export DB__URL="postgresql+asyncpg://user:password@postgres.example:5432/hei_fastapi"
export REDIS__URL="redis://redis.example:6379/0"
export CELERY__BROKER_URL="redis://redis.example:6379/1"
```

API 和 worker 可以横向扩容；beat 只运行一个实例。Celery 定时任务使用 RedBeat，仍建议在编排层保证 beat 单副本，避免 Redis 锁异常时重复调度。

单机多 Docker 模板通过 `api` 和 `worker` 服务的 `--scale` 参数复制实例，并通过 `gateway` 暴露 `8000` 端口，适合在单机 Docker 环境模拟 API 横向扩展、配置同步和 IM 跨实例投递。IM 网关端口由 Redis 分布式锁保证同一主机上仅一个 worker 绑定 `18080/18081`；生产建议 `APP__WORKERS=1` 并水平扩展 api 副本。

## 配置一致性

运行态业务配置由数据库管理：

- `sys_config`：邮件、上传限制等配置
- `sys_storage_config`：Local / MinIO / S3 / OSS provider 连接配置

后台保存配置后，当前进程会立即重载配置，并通过 Redis `hei:config:changed` 频道通知其它 API/worker 进程清理本地缓存。多实例部署时 Redis 是配置一致性的必需依赖；Redis 不可用时，修改只保证当前进程生效，日志和 ready 检查会暴露同步异常。

## 连接池预算

数据库最大潜在连接数按下面估算：

```text
api_replicas * api_workers * (DB__POOL_SIZE + DB__MAX_OVERFLOW)
+ worker_replicas * worker_concurrency * task_db_connection_budget
```

生产配置必须小于数据库 `max_connections`，并预留迁移、运维、监控连接。Redis 连接数同样要按 API worker、Celery worker、WebSocket 连接和 Pub/Sub 订阅估算。

## 真实客户端 IP

默认不信任 `X-Forwarded-For`。如果应用部署在反向代理或网关后面，需要配置可信代理：

```bash
APP__TRUSTED_PROXY_IPS='["10.0.0.0/24","127.0.0.1"]'
```

只有请求来源 IP 命中可信代理时，后端才会读取 `X-Real-IP` 或 `X-Forwarded-For`。限流、审计和会话 IP 绑定共用同一解析逻辑。

## 会话与 Cookie

- 登录同时返回 JSON `token`（兼容原生/旧客户端）并设置 HttpOnly Cookie `hei_session`。
- Web Admin/Portal：**不再把 token 写入 localStorage**；API 依赖 Cookie（`withCredentials`）；IM 仅用一次性 `imt_` ticket。
- API 鉴权：Cookie 优先；原生客户端可传**裸**会话 token 于 `Authorization`（或 `AUTH__TOKEN_NAME`）。不支持 `Bearer` 方案。
- 生产建议：`AUTH__SESSION_COOKIE_SECURE=true`、`AUTH__SESSION_IDLE_TIMEOUT_SECONDS=1800`。
- 跨站（不同域）部署需 `SameSite=None` + Secure，并保证 CORS `allow_credentials` 与显式 Origin。
- **Admin MFA（TOTP + WebAuthn/Passkey）**：账号可自助开通；`AUTH__MFA_REQUIRED=true` 时未开通无法完成登录；Portal 不走 MFA。
- **密钥托管**：`SECRETS__BACKEND=fernet|vault`；Vault 模式从 KV v2 读取 Fernet 主密钥，不可达则 fail-closed。非 debug 可用 `SECRETS__ALLOW_FERNET_IN_PROD=false` / `SECRETS__REQUIRE_VAULT=true` 强制 Vault。
- **admin-uniapp（原生）**：无 Cookie 会话；本地存储裸会话 token，请求头 `Authorization: <token>`（禁止 `Bearer`）；H5 有 XSS 面，敏感环境优先 Web Admin。

## 审计耐久性

操作审计先入内存队列；队列满时写入 `sys_operation_audit_outbox`（失败再落 Redis spill）。Worker `await emit` 持久化到 `sys_operation_audit_log`。部署后执行迁移 `b2c3d4e5f6a7_audit_outbox`。

## TLS / HSTS

`docker/nginx/api-gateway.conf` 默认仅 HTTP `:8000`，TLS 建议在边缘负载均衡终止。前端 nginx 通过 `HSTS_HEADER` 注入 HSTS；multi/distributed 的 admin/portal 服务应设置该环境变量。

## 中间件性能

自定义中间件（Trace / AuthContext / AccessLog / SecurityHeaders / AuthWhitelist / RateLimit / OperationAudit）均为**纯 ASGI**，避免 `BaseHTTPMiddleware` 嵌套带来的任务包装开销。发布前可用 `scripts/ops/loadtest_http.py` 建立 p95 基线。

## 灾备与备份（DR）

发布前勾选清单见 [dr-checklist.md](./dr-checklist.md)。CI 运行 `python scripts/ops/check_dr_docs.py` 校验文档锚点（不替代真实演练）。

最低要求（生产上线前勾选）：

1. **PostgreSQL**：开启持续归档 / PITR（或云厂商自动备份）；每日全量 + WAL；保留 ≥ 7 天。
2. **Redis**：RDB/AOF 至少一种；会话与 IM 绑锁可接受短暂丢失，但需监控重启后会话重建。
3. **对象存储**：Local 根目录纳入卷备份；S3/OSS 开启版本控制与跨区域复制（按合规要求）。
4. **RTO / RPO 目标（建议内网中台）**：RPO ≤ 15min，RTO ≤ 2h；每季度做一次恢复演练并记录。
5. **演练步骤**：停写 → 从备份恢复到隔离实例 → 跑 `alembic upgrade head` 校验 → `ready` 探针与登录冒烟 → 切流。

Compose 默认 `AUTH__SESSION_IDLE_TIMEOUT_SECONDS=1800`。HTTPS 终结后设 `AUTH__SESSION_COOKIE_SECURE=true`。

## 压测验收

先用轻量脚本建立基线：

```bash
python scripts/ops/loadtest_http.py \
  --base-url http://127.0.0.1:8000 \
  --path /,/api/v1/internal/health/live \
  --requests 5000 \
  --concurrency 100
```

验收至少记录：

- QPS、错误率、p95、p99
- API CPU、内存、worker 数、容器副本数
- DB 活跃连接、慢 SQL、锁等待
- Redis QPS、连接数、慢命令
- Celery 队列积压和任务耗时

业务压测需要补充登录、分页列表、配置保存、文件上传、WebSocket 消息和审计写入场景。发现列表接口慢或 SQL 数量随行数线性增长时，优先排查 N+1、缺索引和分页查询计划。
