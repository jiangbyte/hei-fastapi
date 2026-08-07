# HEI FastAPI

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116%2B-009688?logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

HEI FastAPI 是一个面向中后台和通用业务系统的全栈脚手架，包含 FastAPI 异步后端、Vue 3 管理端、React 门户端和 uni-app 管理端。

项目核心目标是提供一套可直接二次开发的基础工程：IAM/RBAC、系统配置、文件存储、消息通知、代码生成、任务调度、数据库迁移和可观测性都已经内置，业务模块通过 `ModuleSpec` 插件式装配，尽量减少对框架主体的侵入。

> 个人开发，有 bug 欢迎提，邮箱 jiangbytebiz@163.com

---

## 功能概览

- 异步后端：FastAPI / SQLAlchemy 2.0 Async / Pydantic v2；自定义中间件纯 ASGI
- 权限体系：账号、角色、部门、用户组、资源菜单、数据范围（`owner_dept_id`）
- 会话安全：Cookie 优先（Web）；原生裸 Authorization token；Admin TOTP / WebAuthn MFA；IM 短时 ticket
- 密钥托管：Fernet / Vault KV；生产可强制 Vault
- 系统能力：字典、配置、文件、Banner、审计 outbox、代码生成
- 消息能力：站内消息、通知、公告、反馈、IM 双通道（WS Binary + TCP）
- 文件存储：Local / MinIO / S3 / OSS
- 前端应用：Vue 3 管理端、React 门户端、uni-app 管理端（原生本地存储会话 token）
- 工程能力：Alembic、Celery（Redis broker）、RedBeat、Docker、Prometheus、OpenTelemetry、DR 演练门禁

---

## 截图

| | |
|---|---|
| ![运营工作台](docs/IMAGES/img.png) | ![通知管理](docs/IMAGES/img_1.png) |
| ![公告管理](docs/IMAGES/img_2.png) | ![反馈管理](docs/IMAGES/img_3.png) |
| ![在线会话](docs/IMAGES/img_4.png) | ![字典管理](docs/IMAGES/img_5.png) |
| ![文件管理](docs/IMAGES/img_6.png) | ![系统配置](docs/IMAGES/img_7.png) |
| ![代码生成](docs/IMAGES/img_8.png) | ![账号管理](docs/IMAGES/img_9.png) |

---

## 技术栈

| 类别 | 技术 |
|---|---|
| 后端 | FastAPI / SQLAlchemy Async / Pydantic v2 / Gunicorn / Uvicorn |
| 数据库 | PostgreSQL（主推）/ SQLite（测试）/ Alembic；可选 MySQL extra |
| 缓存会话 | Redis |
| 任务队列 | Celery / celery-redbeat / Redis（broker + beat） |
| 存储 | Local / MinIO / S3 / OSS |
| 管理端 | Vue 3 / Naive UI / Vite / TypeScript |
| 门户端 | React 19 / Ant Design / Vite / TypeScript |
| 移动端 | uni-app |

---

## 项目结构

```text
app/
  core/          配置、安全、日志、异常、统一响应
  deps/          FastAPI 依赖注入
  middleware/    中间件
  modules/       业务模块，自动发现并装配
  platform/      DB、Redis、Storage、Celery、模块加载等基础设施
  worker/        Celery 入口
migrations/      Alembic 迁移
scripts/         开发、迁移、seed 辅助脚本
tests/           测试
web/
  admin/         Vue 管理端
  portal/        React 门户端
  admin-uniapp/  uni-app 管理端
```

---

## 快速开始

### 后端

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,postgres]"

cp .env.example .env
# 编辑 .env：DB__URL、REDIS__URL、CELERY__BROKER_URL、APP__CONFIG_CRYPTO_KEY

python scripts/db/migrate.py
python scripts/db/load_bootstrap_sql.py   # 可选：字典 / 配置 / 存储配置基线
python scripts/seed/seed_super_admin.py
./entrypoint.sh
```

默认地址：`http://127.0.0.1:8000`

接口文档：`http://127.0.0.1:8000/docs`

`./entrypoint.sh` 默认按 `all` 模式启动 API、Celery worker 和 beat。也可以显式传参切换：`./entrypoint.sh api|worker|beat|migrate|seed`。

### 管理端

```bash
cd web/admin
pnpm install
pnpm dev
```

### 门户端

```bash
cd web/portal
pnpm install
pnpm dev
```

### uni-app

```bash
cd web/admin-uniapp
pnpm install
pnpm dev:h5
```

---

## 配置边界

`.env` 只放部署和基础设施配置，例如应用监听、数据库、Redis、Celery、CORS、加密 key。

运行态业务配置放在数据库中：

- `sys_config`：上传限制、邮件配置、模块运行参数等普通配置
- `sys_storage_config`：存储 provider、endpoint、bucket、access key、secret key 等连接配置

存储配置由管理后台维护并设置默认配置。上传接口可以只传 `storage_provider`，后端会解析到对应配置；需要精确指定时也支持 `storage_config_id`。

多实例部署依赖 Redis 广播配置变更。管理后台保存 `sys_config` 或 `sys_storage_config` 后，当前进程会立即重载配置，其它 API/worker 会通过 Redis 订阅事件刷新本地缓存。

---

## 模块扩展（低侵入）

后端通过扫描 `**/module.py` 的 `ModuleSpec` 自动装配。**新增业务模块不要改** `app/factory.py`、`app/lifespan.py`，也不要为新菜单去改 `web/admin/src/router/routes.static.ts`（Admin 默认 `VITE_ROUTE_LOAD_MODE=dynamic`，菜单以 DB `sys_resource` 为准）。

路由全局挂 `/api`；完整路径写在装饰器上（如 `@router.post("/v1/admin/sys/banners/create")`）。`RouteSpec.tags` 只给 OpenAPI 用。

### 新增模块 checklist

1. **模块包**：在 `app/modules/...` 放 `model` / `schema` / `repository` / `service` / `router` / `module.py`（或用代码生成）；`RouteSpec(tags=("admin",), router="...:router")`，路径带 `/v1/admin|portal/...`
2. **落盘生成物**（可选）：`python scripts/codegen/apply_plan.py --plan-id <id>`  
   - 会写入后端与 Admin 视图/API  
   - 幂等合并 `web/admin/src/api/index.ts`  
   - 产出 `*_menu_permission.sql`
3. **迁移**：`python scripts/db/makemigration.py "..."` / `migrate.py`  
   - Alembic 使用 `include_disabled=True`，**禁用模块的模型也会进入 metadata**，不必为了迁表而打开路由
4. **菜单权限**：执行生成的 menu SQL（按需改 `module_id` / `parent_id`），再给角色授权
5. **Admin**：确保 `component_path` 对应的 vue 文件存在；dynamic 模式下登录后即可看到菜单
6. **模块配置**（可选）：本模块 `BaseSettings` + `ModuleSpec.config_model="pkg:Class"`；env 前缀写在 settings 类上；需要库表覆盖时设 `config_from_db=True`（键名 `{module.name}.{field}`）

### 启用开关

```bash
HEI_MODULE_PACKAGES=your_company.modules   # 追加外部包扫描根
HEI_DISABLED_MODULES=some.module           # 强制关闭（运行时）
HEI_ENABLED_MODULES=some.module            # 强制打开（覆盖 ModuleSpec.enabled=False）
```

推荐二次开发方式：

- 业务代码放在独立模块内，不改框架启动与路由聚合
- 模块间协作优先使用 `app/platform/interfaces`
- 存储连接统一走 `sys_storage_config`，不要在业务模块里硬编码 provider 密钥

### API JSON 契约（标量字符串化）

HTTP JSON 进出时，**所有标量均为字符串**（含 `ApiResponse.code`、分页 `current/size/total/pages`、业务 `bool/int/float`）。允许 `string` / `object` / `list` / `null`。服务端内部与数据库仍使用真实类型；Admin/Portal 只认字符串契约，不做 number/bool 历史兼容。

---

## Docker

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

多机多节点：面向 Swarm/外部编排，基础设施地址通过环境变量注入。

```bash
docker build -t hei-fastapi-backend:latest .
docker build -t hei-fastapi-admin:latest web/admin
docker network create --driver overlay --attachable hei_overlay
docker node update --label-add hei.beat=true <beat-node>
docker compose -f docker-compose.distributed.yml config | docker stack deploy -c - hei-fastapi
```

管理端单独镜像：

```bash
docker build -t hei-fastapi-admin web/admin
docker run -d -e BACKEND_URL="http://host.docker.internal:8000" -p 8081:81 hei-fastapi-admin
```

---

## 常用命令

```bash
python scripts/db/makemigration.py "describe schema change"
python scripts/db/check_migration.py
python scripts/db/migrate.py
python scripts/db/load_bootstrap_sql.py
python scripts/db/export_bootstrap_sql.py

python -m ruff check app tests
python -m pytest
```

```bash
cd web/admin
pnpm build
```

压测基线：

```bash
python scripts/ops/loadtest_http.py --base-url http://127.0.0.1:8000 --path / --requests 1000 --concurrency 50
```

---

## 相关文档

- [docs/iam.md](docs/iam.md)
- [docs/migration.md](docs/migration.md)
- [docs/production.md](docs/production.md)
- [docs/dr-checklist.md](docs/dr-checklist.md)
- [docs/dr-drills/](docs/dr-drills/)
- [migrations/README.md](migrations/README.md)
- [web/admin/README.md](web/admin/README.md)
- [web/portal/README.md](web/portal/README.md)
- [web/admin-uniapp/README.md](web/admin-uniapp/README.md)

---

## License

MIT License。详见 [LICENSE](LICENSE)。
