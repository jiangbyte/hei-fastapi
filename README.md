# HEI FastAPI

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116%2B-009688?logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

面向中后台与通用业务的全栈脚手架：FastAPI 异步后端 + Vue 3 管理端 + React 门户 + uni-app 管理端。

账户体系为 **ADMIN** / **PORTAL**。业务模块通过 `ModuleSpec` 插件式装配；内置 IAM/RBAC、系统配置、文件存储、消息、代码生成、SnailJob 定时任务、Alembic 迁移与可选可观测性。

> 个人开发，有 bug 欢迎提：jiangbytebiz@163.com


## 生产状态

以下姊妹项目均已在本公司项目中投产：

| 项目 | 说明 | 协议 |
| :--- | :--- | :--- |
| [**hei-boot**](https://github.com/jiangbyte/hei-boot) | Spring Boot 工程化脚手架 | Apache License 2.0 |
| [**hei-gin**](https://github.com/jiangbyte/hei-gin) | Go 轻量级后端框架 | MIT |
| [**hei-fastapi**](https://github.com/jiangbyte/hei-fastapi) | FastAPI 原型项目（早期阶段，仅供参考） | MIT |

**统一说明：**

- 以上均为个人维护的开源框架，起源是给自己攒一套通用、灵活、多账户体系的开发框架，不做强绑定，图个省事。在公司项目中直接用了，**非公司内部框架产物**。
- 公司内部基于各框架有定制化修改，内部版本与公共仓库**存在差异**，公共仓库更新相对较慢（看鄙人是否有时间了，当然也在用 AI 积极迁移中......）。
- **本项目不涉及任何公司机密信息，无版权争议！！**

---

## 仓库结构

```text
app/
  core/              配置、安全、schema、统一响应
  deps/              依赖注入
  middleware/        ASGI 中间件（鉴权、审计、限流、安全头、追踪）
  modules/           业务模块（auth / iam / sys / message / user / dashboard / internal / biz）
  platform/          平台能力（db / cache / storage / module / tasks / observability / secrets）
  worker/            SnailJob Python 执行器入口
migrations/          Alembic 迁移（只管表结构）
scripts/db/          迁移与业务数据导入导出
script/docker/       本地 SnailJob Server 编排
tests/               后端测试
web/
  admin/             Vue 3 管理端（Naive UI）
  portal/            React 19 门户（Ant Design）
  admin-uniapp/      uni-app 管理端（H5 / 小程序）
docker-compose.yml   后端 + 可选 admin / portal profile
entrypoint.sh        all | api | worker | migrate
dev.sh               启动本机已有的 postgres / redis / minio / rustfs 容器
shutdown.sh          停止本机 entrypoint 拉起的 gunicorn / worker
```

---

## 技术栈

| 类别 | 技术 |
|---|---|
| 后端 | FastAPI / SQLAlchemy 2 Async / Pydantic v2 / Gunicorn + Uvicorn |
| 数据 | PostgreSQL（推荐）/ Redis；可选 MySQL、SQLite extras |
| 任务 | SnailJob（外部 Server + `snail-job-python` 执行器） |
| 存储 | Local / MinIO / RustFS / 阿里云 OSS / 腾讯云 COS（`sys_config` 维护） |
| 密钥 | Fernet（`APP__CONFIG_CRYPTO_KEY`）或 Vault KV v2 |
| 可观测性 | structlog；可选 Prometheus `/metrics`、OpenTelemetry / OTLP |
| 管理端 | Vue 3 / Naive UI / Vite / TypeScript / Pinia / UnoCSS |
| 门户端 | React 19 / Ant Design 6 / Vite / TypeScript / Zustand / UnoCSS |
| 移动端 | uni-app 3 / Vue 3 / Pinia / uview-pro |

---

## 功能概览

- **权限**：账号、角色、部门、用户组、岗位、资源菜单、客户端模块/资源、数据范围
- **会话**：Web 使用 HttpOnly Cookie；uni-app 使用本地 Authorization token；在线会话可强制下线
- **系统**：字典、配置（`sys_config`）、文件、Banner、弱口令、密码策略、操作审计 / 登录日志、代码生成
- **消息**：通知、公告、反馈；邮件 / 短信 / 推送走运行态配置
- **前端**：Admin 动态菜单与 Dashboard；Portal 登录/注册、公告、反馈、个人中心、账号注销；uni-app 管理端能力
- **运维**：存活/就绪探针；配置变更当前进程立即重载，其它实例经 Redis 订阅刷新

API 全局前缀 `/api`，完整路径写在路由装饰器上（如 `/v1/admin/...`、`/v1/portal/...`）。

HTTP JSON：**标量均为字符串**（含 `code`、分页字段、业务 bool/int）。

健康检查：

| 路径 | 说明 |
|---|---|
| `GET /` | 进程存活（`{"status":"ok"}`） |
| `GET /api/v1/internal/health/live` | 存活探针 |
| `GET /api/v1/internal/health/ready` | 就绪探针（DB / Redis / 配置同步 / 存储等） |

Swagger 默认关闭。本地需要文档时在 `.env` 设 `SWAGGER__ENABLED=true`，然后访问 `http://127.0.0.1:8000/docs`。

---

## 快速开始

### 1. 基础设施

准备 PostgreSQL 与 Redis（可用 `./dev.sh` 启动本机已有的 `dev-postgres` / `dev-redis` / `dev-minio` / `dev-rustfs` 容器）。

### 2. 后端

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev,postgres]"

cp .env.example .env
# 配置 DB__URL、REDIS__URL、SNAIL_JOB__*
# 生产还需 APP__CONFIG_CRYPTO_KEY（Fernet，同时用于配置加解密、存储 AK/SK、文件 URL 签名）
# 本地看 Swagger：SWAGGER__ENABLED=true

python scripts/db/migrate.py
python scripts/db/import_data.py   # 导入 scripts/db/seed/data.sql（含 superadmin 等业务数据）
./entrypoint.sh
```

- API：`http://127.0.0.1:8000`
- 文档：先开 `SWAGGER__ENABLED=true`，再访问 `http://127.0.0.1:8000/docs`
- 其它角色：`./entrypoint.sh api|worker|migrate`
- 停止本机进程：`./shutdown.sh`

种子账号：导入 `data.sql` 后管理端账号为 `superadmin`（口令以导出当时为准）。

### SnailJob 执行器（外部 Server）

本仓库跑 **Python 执行器**（`./entrypoint.sh worker` 或 `all`）；调度中心为独立 SnailJob Server。与 hei-boot 共用同一 Server 时靠 **独立 namespace + group** 隔离：

| 项 | 默认值 |
|---|---|
| namespace name | `hei-fastapi` |
| namespace unique_id | `a8c3e5f17b924d6e9f0a1b2c3d4e5f60` |
| group | `hei_fastapi_admin` |
| token | `SJ_heiFastapiAdminToken1234567890ab` |

（hei-boot 使用 Default / `hei_boot_admin`，互不冲突。）

#### 本地 Server

```bash
# 1) Postgres 上建库 snail_job（角色示例 admin/123456）
# 2) 迁移 schema + 本仓种子（greenfield）
./script/docker/snailjob-flyway.sh

# 若 snail_job 已由 hei-boot Flyway 迁过，勿重跑 flyway；只补本仓种子：
# ./script/docker/seed_fastapi_only.sh

# 3) 启动 Server（控制台 9189，RPC 17888）
docker compose -f script/docker/docker-compose.snailjob.yml up -d
```

控制台：`http://127.0.0.1:9189/snail-job`（种子后 admin / 123456）。切换到 namespace `hei-fastapi`，可见组 `hei_fastapi_admin` 与下列任务。

| 执行器名 | Cron（种子） | 说明 |
|---|---|---|
| `accountPurgeCancelledAccounts` | `0 0 3 * * ?` | 清理过期注销账户（args 可传保留天数，默认 `15`） |
| `bannerFlushInteractions` | `0 */5 * * * ?` | Banner 交互增量刷库 |
| `bannerStatusJob` | `0 */5 * * * ?` | 按 start_at/end_at 同步 ENABLED/DISABLED |
| `auditAnalysisCycle` | `0 */5 * * * ?` | 审计告警分析（受 `AUDIT_ALERT` 开关影响） |
| `sysFileCleanupLocalOrphans` | `0 0 * * * ?` | 清理本地存储孤儿文件 |

`SNAIL_JOB__ENABLED=false` 时 `all` 只起 API、不起 worker。Docker 中请把 `SNAIL_JOB__HOST_IP` 设为 Server 可达地址，并发布客户端端口 `17889`。

启动 worker 后控制台应看到 `py-xxxxxxx` 客户端上线。更多说明见 [script/docker/README.md](script/docker/README.md)。

### 3. 管理端

```bash
cd web/admin && pnpm install && pnpm dev
```

`http://127.0.0.1:5173` · [说明](web/admin/README.md)

### 4. 门户端

```bash
cd web/portal && pnpm install && pnpm dev
```

`http://127.0.0.1:5174` · [说明](web/portal/README.md)

### 5. uni-app 管理端

```bash
cd web/admin-uniapp && pnpm install && pnpm dev:h5
```

`.env` 中 `VITE_PORT=5174`，与门户默认端口相同；同时开发时请改其一。后端 CORS 默认包含 `5173` / `5174` / `5163`。

[说明](web/admin-uniapp/README.md)

---

## 配置

| 位置 | 内容 |
|---|---|
| `.env` | 监听、DB、Redis、SnailJob、CORS、加密 key、Swagger、密钥后端、可观测性 |
| `sys_config` | 运行态业务配置：`AUTH_*` / `PASSWORD_*` / `MAIL_*` / `SMS_*` / `PUSH_*` / `AUDIT_ALERT_*` / `STORAGE_*` / `COPYRIGHT_*` |

配置变更后当前进程立即重载，其它实例经 Redis 订阅刷新。

常用环境变量：

```bash
SWAGGER__ENABLED=true                 # 打开 /docs /redoc /openapi.json
SECRETS__BACKEND=fernet               # 或 vault
OBSERVABILITY__ENABLED=true           # 总开关
OBSERVABILITY__METRICS_ENABLED=true   # Prometheus /metrics
OBSERVABILITY__TRACING_ENABLED=true
OBSERVABILITY__OTLP_ENABLED=true
OBSERVABILITY__OTLP_ENDPOINT=http://127.0.0.1:4318
```

模块开关：

```bash
HEI_MODULE_PACKAGES=your_company.modules
HEI_DISABLED_MODULES=biz.cg_test_activity
HEI_ENABLED_MODULES=some.module
```

禁用模块的模型仍参与 Alembic metadata，可正常迁表。`app/modules/biz/cg_test_*` 为代码生成示例模块，可用 `HEI_DISABLED_MODULES` 关掉路由。

---

## 新增业务模块

1. 在 `app/modules/...` 增加 `model` / `schema` / `repository` / `service` / `router` / `module.py`
2. 配置 `ModuleSpec` 与 `RouteSpec`，路径含 `/v1/admin|portal/...`
3. `python scripts/db/makemigration.py "..."` → `python scripts/db/migrate.py`
4. Admin 使用动态路由时，在 DB 写入资源并授权即可

也可用管理端 **代码生成** 产出上述文件并写回工作区。业务代码放在模块内，避免改动 `app/factory.py`、`app/lifespan.py`。

---

## Docker

`docker-compose.yml` 要求 `.env` 中已设置 `APP__CONFIG_CRYPTO_KEY`、`DB__URL`、`REDIS__URL`。

```bash
docker compose run --rm hei migrate
docker compose up -d --build

# 同时启动前端
docker compose --profile admin --profile portal up -d --build
```

| 服务 | 默认端口 |
|---|---|
| 后端 | `8000`（`BACKEND_PORT`） |
| SnailJob 客户端 | `17889`（`SNAIL_JOB_CLIENT_PORT`） |
| Admin | `8081`（`ADMIN_PORT`） |
| Portal | `8082`（`PORTAL_PORT`） |

健康检查打 `http://127.0.0.1:8000/api/v1/internal/health/live`。

```bash
docker build -t hei-fastapi-admin web/admin
docker run -d -e BACKEND_URL="http://host.docker.internal:8000" -p 8081:81 hei-fastapi-admin

docker build -t hei-fastapi-portal web/portal
docker run -d -e BACKEND_URL="http://host.docker.internal:8000" -p 8082:80 hei-fastapi-portal
```

---

## 常用命令

```bash
python scripts/db/makemigration.py "describe schema change"
python scripts/db/check_migration.py
python scripts/db/migrate.py
python scripts/db/export_data.py
python scripts/db/import_data.py

python -m ruff check app tests
python -m pytest

# 在对应 web/* 目录
pnpm dev && pnpm build && pnpm lint
```

- [scripts/README.md](scripts/README.md)
- [migrations/README.md](migrations/README.md)
- [script/docker/README.md](script/docker/README.md)
- [web/admin/README.md](web/admin/README.md)
- [web/portal/README.md](web/portal/README.md)
- [web/admin-uniapp/README.md](web/admin-uniapp/README.md)

---

## License

MIT · [LICENSE](LICENSE)
