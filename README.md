# HEI FastAPI

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116%2B-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2%20Async-D71F00?logo=sqlalchemy&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supported-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Supported-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-Apache%202.0-C85119)
![Version](https://img.shields.io/badge/Version-1.0.0--beta-4B0082?logo=git&logoColor=white)

HEI FastAPI 是一个 FastAPI 异步一体化应用脚手架：**一个后端应用同时提供管理端（Admin）与门户（Portal）两套 API**，配合同仓维护的三个前端工程，覆盖账号认证、组织权限（RBAC）、系统管理、消息反馈与运营工作台等常用能力，开箱即用、可按需裁剪。功能与 [hei-boot](https://github.com/jiangbyte/hei-boot)（Spring Boot）保持 API 契约对齐。

- **后端**：Python 3.11+ · FastAPI · SQLAlchemy 2 Async · Pydantic v2 · PostgreSQL · Redis · Gunicorn + Uvicorn
- **前端**：`web/admin`（Vue 3 / Naive UI）· `web/portal`（React / Ant Design）· `web/admin-uniapp`（uni-app）
- **数据约定**：对外 JSON 字段标量（含 boolean / 数字）统一按字符串收发

## 功能特性

**认证与账号（`app/modules/auth`）**

- 双端登录：ADMIN / PORTAL 两套独立账号体系与会话（Web 使用 HttpOnly Cookie，uni-app 使用 Authorization）
- 账号 / 邮箱 / 手机号多种身份登录，密码登录（RSA 加密传输）与验证码登录（OTP）
- 图形验证码（SVG / PNG）、登录失败锁定与限流防护
- 忘记 / 重置密码、门户注册（ACCOUNT / EMAIL / PHONE 通道）
- 三方登录：GitHub、Gitee、QQ、微信开放平台、微信小程序；管理员可绑定 / 解绑

**组织与权限（`app/modules/iam`）**

- 账号、角色、部门、用户组、岗位管理
- 菜单资源、资源模块、客户端资源多层授权（RBAC），权限码三段式规范
- 在线会话查询与强制下线

**系统管理（`app/modules/sys`）**

- 数据字典、系统配置（`sys_config`，敏感配置加密存储）、Banner、文件存储（Local / MinIO / RustFS / 阿里云 OSS / 腾讯云 COS）
- 弱口令清单、密码策略、操作审计、代码生成
- 任务管理（`sys_job`，CRON / 固定间隔调度 + 执行日志，Redis 锁防多实例重复执行）
- 公告 / 通知、意见反馈（管理端 + 门户双端）

**运营与调度**

- 运营工作台（`app/modules/dashboard`）：账号、会话、审计、文件等核心指标概览与 7 日趋势
- 内置任务调度（`sys_job` 表，CRON / 固定间隔）：注销账号清理、Banner 定时上下架、审计量级告警、本地文件清理

## 技术栈

| 分类 | 选型 |
| :--- | :--- |
| 语言 / 框架 | Python 3.11+、FastAPI 0.116+、Pydantic v2、SQLAlchemy 2 Async（asyncpg / aiosqlite） |
| 数据 | PostgreSQL（推荐），可选 MySQL / SQLite extras；Alembic 迁移管理表结构 |
| 缓存 / 会话 | Redis（会话、验证码、操作审计 Redis Stream）、HttpOnly Cookie + Header 双通道会话 |
| 安全 | RSA 密码加密传输、Fernet（`APP__CONFIG_CRYPTO_KEY`）或 Vault KV v2、登录锁定 / 限流、数据脱敏 |
| 任务 | 内置任务调度（`sys_job` 表，CRON / 固定间隔，Redis 锁防多实例重复执行） |
| 观测 / 运维 | structlog；可选 Prometheus `/metrics`、OpenTelemetry / OTLP；存活 / 就绪探针 |
| 其他 | pip 依赖管理（`requirements*.txt`）、Gunicorn + Uvicorn |

| 前端 | 技术 |
| :--- | :--- |
| `web/admin` | Vue 3.5、Naive UI 2、Pinia、Vue Router、Vite 8、TypeScript |
| `web/portal` | React 19、Ant Design 6、zustand、Vite 8、TypeScript |
| `web/admin-uniapp` | uni-app 3（H5 / 小程序） |

## 架构

后端只有**一个可运行应用** `app`（FastAPI），按请求前缀区分管理端与门户两套接口，双账号体系会话相互隔离；业务能力按模块划分，由 `app/routers.py` 显式装配（对齐 hei-boot "explicit deps, no bundle"）。

| 分层 | 说明 |
| :--- | :--- |
| `app/core` | 平台基础设施：config / security / db / cache / storage / tasks / observability / cloud / email / sms / push / secrets |
| `app/deps` / `middleware` | 依赖注入与 ASGI 中间件（鉴权、审计、限流、安全头、追踪） |
| `app/modules` | 业务模块：auth / iam / sys / profile / dashboard / internal / biz（代码生成样板） |
| `migrations` | Alembic 迁移（只管表结构，业务种子见 `scripts/db/seed`） |
| `web/*` | 独立前端工程（无共享依赖层） |

## 快速开始

### 环境要求

- Python 3.11+ 与 pip（推荐 conda 环境，如 `conda activate normal`）
- PostgreSQL、Redis
- Node.js 22+ 与 pnpm 9+（前端）

### 1. 初始化数据库

表结构由 Alembic 迁移管理，业务种子数据以 `scripts/db/seed/data.sql` 为权威来源（含 `superadmin` 账号、菜单、权限、字典、配置）。

```bash
# 创建数据库
createdb -U postgres -h 127.0.0.1 hei_fastapi

# 迁移表结构（数据库表结构由人工维护，应用启动不执行迁移）
python scripts/db/migrate.py

# 导入业务种子数据
python scripts/db/import_data.py
```

### 2. 启动后端

开发默认配置见 `.env.example`：

- 数据库：`postgresql+asyncpg://postgres:123456@127.0.0.1:5432/hei_fastapi`
- Redis：`redis://127.0.0.1:6379/0`

```bash
# 安装依赖（conda 环境示例：conda activate normal）
pip install -r requirements-dev.txt

cp .env.example .env
# 按需配置 DB__URL / REDIS__URL / HEI_JOB__*；生产还需 APP__CONFIG_CRYPTO_KEY

./entrypoint.sh                          # 启动 API
```

> Windows 本地开发（gunicorn 依赖 `fcntl`，仅 Linux / 容器可用）：
>
> ```bash
> python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
> ```

启动后可访问：

| 地址 | 说明 |
| :--- | :--- |
| http://127.0.0.1:8000 | Admin / Portal API |
| http://127.0.0.1:8000/docs | Swagger 接口文档（需 `SWAGGER__ENABLED=true`） |
| http://127.0.0.1:8000/api/v1/internal/health/live | 存活探针 |
| http://127.0.0.1:8000/api/v1/internal/health/ready | 就绪探针（DB / Redis / 配置同步 / 存储等） |

### 3. 启动前端

```bash
cd web/admin && pnpm install && pnpm dev    # http://127.0.0.1:5173
cd web/portal && pnpm install && pnpm dev   # http://127.0.0.1:5174
```

前端开发模式通过 Vite 将 `/api` 代理到后端 `http://127.0.0.1:8000`。

### 默认账号

| 端 | 地址 | 账号 | 密码 |
| :--- | :--- | :--- | :--- |
| Admin | http://localhost:5173 | `superadmin` | `123456` |
| Portal | http://localhost:5174 | `user` | `123456` |

> 口令以 `data.sql` 导出当时为准。登录需要图形验证码（验证码明文小写 SHA-256 存入 Redis，TTL 5 分钟）。**生产环境首次启动后请立即修改默认密码。**

## 界面预览

### 门户 Portal

<table>
  <tr>
    <td width="50%"><img src="docs/images/portal-login.png" alt="门户登录" /></td>
    <td width="50%"><img src="docs/images/portal-home.png" alt="门户首页" /></td>
  </tr>
  <tr>
    <td align="center">登录</td>
    <td align="center">首页</td>
  </tr>
</table>

### 管理端 Admin · 登录 / 工作台

<table>
  <tr>
    <td width="50%"><img src="docs/images/admin-login.png" alt="管理端登录" /></td>
    <td width="50%"><img src="docs/images/admin-dashboard.png" alt="运营工作台" /></td>
  </tr>
  <tr>
    <td align="center">登录</td>
    <td align="center">运营工作台</td>
  </tr>
</table>

### 管理端 Admin · 组织权限

<table>
  <tr>
    <td width="50%"><img src="docs/images/admin-iam-account.png" alt="账号管理" /></td>
    <td width="50%"><img src="docs/images/admin-iam-role.png" alt="角色管理" /></td>
  </tr>
  <tr>
    <td align="center">账号管理</td>
    <td align="center">角色管理</td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/images/admin-iam-resource.png" alt="资源授权" /></td>
    <td></td>
  </tr>
  <tr>
    <td align="center">资源授权</td>
    <td></td>
  </tr>
</table>

### 管理端 Admin · 系统运维

<table>
  <tr>
    <td width="50%"><img src="docs/images/admin-sys-config.png" alt="系统配置" /></td>
    <td width="50%"><img src="docs/images/admin-sys-dict.png" alt="字典管理" /></td>
  </tr>
  <tr>
    <td align="center">系统配置</td>
    <td align="center">字典管理</td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/images/admin-sys-audit.png" alt="操作审计" /></td>
    <td width="50%"><img src="docs/images/admin-sys-codegen.png" alt="代码生成" /></td>
  </tr>
  <tr>
    <td align="center">操作审计</td>
    <td align="center">代码生成</td>
  </tr>
</table>

## 项目结构

```text
hei-fastapi
├── app                          # 应用包
│   ├── core                     # 平台基础设施（config / security / db / cache / storage / tasks / observability / cloud / email / sms / push / secrets）
│   ├── deps                     # 依赖注入
│   ├── middleware               # ASGI 中间件（鉴权、审计、限流、安全头、追踪）
│   ├── modules                  # 业务模块（auth / iam / sys / profile / dashboard / internal / biz 样板）
│   ├── routers.py               # 显式路由装配（/api 前缀 + OpenAPI tags）
│   └── db_models.py             # ORM 模型注册清单（供 Alembic）
├── migrations                   # Alembic 迁移
├── scripts
│   └── db/                      # 迁移与数据导入导出（seed/data.sql 权威业务种子）
├── tests                        # 后端测试（pytest）
├── web                          # 前端（admin / portal / admin-uniapp）
├── docs                         # 文档与界面截图
├── entrypoint.sh                # 仅启动 API（数据库迁移由人工维护）
└── dev.sh / shutdown.sh         # 本机开发辅助
```

## 主要 API

| 前缀 | 用途 |
| :--- | :--- |
| `/api/v1/admin/**` | 管理端接口 |
| `/api/v1/portal/**` | 门户接口 |
| `/api/v1/files/**` | 公开文件读取（可配置） |
| `/api/v1/internal/**` | 健康探针 / 集群内部接口（勿对公网暴露） |
| `/docs`、`/openapi.json` | Swagger 接口文档（默认关闭） |

常用接口：`/api/v1/{admin|portal}/login`、`/captcha`、`/oauth/**`、`/sys/**`（账号、角色、字典、配置、任务、公告、反馈等）、`/profile/**`、`/dashboard/overview`。

## 配置说明

运行配置分为两层：**环境变量**（`.env`，双下划线分组如 `DB__URL`）与 **`sys_config` 表**（运行态业务配置）。

| 配置项 | 说明 | 默认（dev） |
| :--- | :--- | :--- |
| `DB__URL` | PostgreSQL 连接（asyncpg） | `postgresql+asyncpg://postgres:123456@127.0.0.1:5432/hei_fastapi` |
| `REDIS__URL` | Redis 连接（会话、验证码、审计） | `redis://127.0.0.1:6379/0` |
| `APP__CONFIG_CRYPTO_KEY` | 敏感配置加密密钥（Fernet），无默认值 | 空 |
| `APP__HOST` / `APP__PORT` | 监听地址 / 端口 | `127.0.0.1` / `8000` |
| `SWAGGER__ENABLED` | 是否开启 `/docs` | `false` |
| `HEI_JOB__SCAN_INTERVAL_MS` / `HEI_JOB__POOL_SIZE` | 内置任务调度扫描间隔（毫秒）与最大并发数 | `1000` / `4` |
| `SECRETS__BACKEND` | 密钥后端（`fernet` / `vault`） | `fernet` |
| `OBSERVABILITY__*` | 可观测性总开关与 Prometheus / OTLP 配置 | 关 |

`sys_config` 运行态配置：`AUTH_*` / `PASSWORD_*` / `MAIL_*` / `SMS_*` / `PUSH_*` / `AUDIT_ALERT_*` / `STORAGE_*` / `COPYRIGHT_*`。配置变更后当前进程立即重载，其它实例经 Redis 订阅刷新。

## 生产部署

项目不使用 docker compose 编排：后端与各前端均为独立 Dockerfile，直接 `docker build` / `docker run`（与 hei-boot 的 docker 方式一致）。

### 构建镜像

```bash
# 后端（根目录 Dockerfile；tini + 非 root 用户，内置任务调度器随进程运行）
docker build -t hei-fastapi .

# 前端（nginx 托管静态资源，/api 反向代理到后端，BACKEND_URL 可配）
docker build -t hei-fastapi-admin web/admin
docker build -t hei-fastapi-portal web/portal
```

### 运行后端

> 数据库表结构由人工维护：应用启动不会执行迁移。需要变更 schema 时，在维护机直接运行 `python scripts/db/migrate.py`（或由 DBA 执行迁移 SQL），再启动 / 重启应用。

```bash
# 启动 API（8000 为 HTTP）
docker run -d --name hei \
  -p 8000:8000 \
  -e APP__CONFIG_CRYPTO_KEY="..." \
  -e DB__URL="postgresql+asyncpg://postgres:123456@host.docker.internal:5432/hei_fastapi" \
  -e REDIS__URL="redis://host.docker.internal:6379/0" \
  -v hei_storage:/app/storage \
  hei-fastapi
```

### 运行前端

```bash
docker run -d --name hei-admin -p 8081:81 \
  -e BACKEND_URL="http://host.docker.internal:8000" \
  hei-fastapi-admin

docker run -d --name hei-portal -p 8082:80 \
  -e BACKEND_URL="http://host.docker.internal:8000" \
  hei-fastapi-portal
```

| 服务 | 默认端口 |
| :--- | :--- |
| 后端 | `8000`（`BACKEND_PORT`） |
| Admin | `8081`（`ADMIN_PORT`） |
| Portal | `8082`（`PORTAL_PORT`） |

### 生产必填环境变量

| 变量 | 说明 |
| :--- | :--- |
| `DB__URL` | 主库连接（asyncpg） |
| `REDIS__URL` | Redis 连接（会话与 Redis Stream 审计） |
| `APP__CONFIG_CRYPTO_KEY` | 敏感配置 Fernet 密钥（无默认值，首次上线必须设置） |

可选：`SECRETS__BACKEND=vault`、`OBSERVABILITY__*`、`SWAGGER__ENABLED` 等。

### 上线检查清单

- 轮换 `superadmin` 默认密码与 `APP__CONFIG_CRYPTO_KEY`
- 关闭 Swagger / 文档公网暴露（默认已关闭）
- 仅在可信反向代理后开启 `APP__TRUSTED_PROXY_IPS`

## 二次开发

1. 在 `app/modules/...` 增加 `model` / `schema` / `repository` / `service` / `router`
2. 在 `app/routers.py` 显式挂载新路由（`/api` 前缀 + OpenAPI tags）
3. 在 `app/db_models.py` 追加模型模块导入（供 Alembic 元数据）
4. `python scripts/db/makemigration.py "..."` → `python scripts/db/migrate.py`
5. Admin 使用动态路由时，在 DB 写入资源并授权即可

也可用管理端 **代码生成** 产出上述文件并写回工作区（样板 `app/modules/biz/cg_test_*`）。业务代码放在模块内，避免改动 `app/factory.py`、`app/lifespan.py`。

## 代码贡献

欢迎 Issue 与 PR。提交前请确认：

- Controller 入参与出参符合标量字符串线格式约定（`snake_case`）
- 遵守模块边界：`app/core` / `app/modules` / `web/*`
- 后端通过 ruff 与 pytest；文档随行为同步

```bash
python -m ruff check app tests
python -m pytest

# 在对应 web/* 目录
pnpm dev && pnpm build && pnpm lint
```

## 许可证

本项目使用 [Apache License 2.0](LICENSE) 开源协议。
