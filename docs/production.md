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

单机多 Docker 模板通过 `api` 和 `worker` 服务的 `--scale` 参数复制实例，并通过 `gateway` 暴露 `8000` 端口，适合在单机 Docker 环境模拟 API 横向扩展、配置同步和 WebSocket 跨实例投递。

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
