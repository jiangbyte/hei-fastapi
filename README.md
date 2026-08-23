# HEI FastAPI

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116%2B-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2%20Async-D71F00?logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supported-4169E1?logo=postgresql&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-Supported-4479A1?logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Supported-DC382D?logo=redis&logoColor=white)
![License](https://img.shields.io/badge/License-Apache_2.0-blue)
![Version](https://img.shields.io/badge/version-1.0.0--beta-orange)

**HEI FastAPI** 是一套面向中后台场景的 FastAPI 异步工程化脚手架：单个应用同时提供 **Admin** 与 **Portal** 双端 API，统一认证、权限、运维与消息能力，并与 [hei-boot](https://github.com/jiangbyte/hei-boot)、[hei-gin](https://github.com/jiangbyte/hei-gin) 等姊妹后端保持契约一致。

> 当前版本：`1.0.0-beta` · 协议：[Apache License 2.0](LICENSE)

## 目录

- [功能特性](#功能特性)
- [前端姊妹项目](#前端姊妹项目)
- [技术栈](#技术栈)
- [工程结构](#工程结构)
- [快速开始](#快速开始)
- [默认账号](#默认账号)
- [姊妹项目](#姊妹项目)
- [License](#license)

## 功能特性

API 前缀统一为 `/api/v1/admin/*` 与 `/api/v1/portal/*`，常见中后台能力按模块划分如下：

| 模块 | 说明 |
| --- | --- |
| 双端账号体系 | ADMIN / PORTAL 独立会话（HttpOnly Cookie / Authorization 双通道）；密码 RSA 传输、验证码登录、失败锁定与限流；可配置三方 OAuth 登录 |
| RBAC 权限 | 账号 / 角色 / 部门 / 用户组 / 岗位；菜单、按钮与 API 资源授权；在线会话踢出 |
| 系统管理 | 字典、动态配置（敏感项 Fernet 加密）、Banner、公告 / 通知、意见反馈、弱口令库 |
| 对象存储 | S3 兼容存储（MinIO / RustFS / 阿里云 OSS / 腾讯云 COS 等），直链或预签名访问 |
| 运维能力 | 操作审计与告警、登录日志、运营工作台概览、内置任务调度（`sys_job`；种子任务默认禁用，需在管理端启用） |
| 代码生成 | 单表 / 树表 / 主子表方案，预览与 ZIP 下载（含菜单权限 SQL；前端产物目录可配置） |
| 实名认证 | 工单提交与审核、敏感字段加密存储（对齐 hei-boot） |
| 业务扩展 | `app/modules/biz` 示例模块，可按同样模式横向扩展 |

## 前端姊妹项目

| 项目 | 说明 |
| --- | --- |
| [**hei-admin**](https://github.com/jiangbyte/hei-admin) | Vue 3 管理端，对接 `/api/v1/admin/*` |
| [**hei-portal**](https://github.com/jiangbyte/hei-portal) | React 门户，对接 `/api/v1/portal/*` |
| [**hei-admin-uniapp**](https://github.com/jiangbyte/hei-admin-uniapp) | uni-app 管理端移动端 |

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 后端 | Python 3.11+ · FastAPI · uvicorn / gunicorn · Pydantic Settings |
| 持久化 | PostgreSQL / MySQL · SQLAlchemy 2（async）· Alembic · asyncpg / aiomysql |
| 缓存 / 会话 | Redis |
| 文档 | OpenAPI（`/docs`、`/redoc`，默认关闭，见 `.env.example`） |
| 其他 | boto3 / oss2 · croniter · cryptography · OpenTelemetry（可选） |

## 工程结构

```text
hei-fastapi/
├── app/                      # FastAPI 应用
│   ├── core/                 # 配置、安全、存储、中间件等
│   └── modules/              # 业务模块（auth / iam / sys / profile / workspace / biz）
├── scripts/hei_fastapi.sql   # MySQL 全量建表、种子数据与表/列 COMMENT
├── migrations/               # Alembic 增量表结构
└── tests/                    # 单元 / API 测试
```

`scripts/` 与 `migrations/` 目录：

| 文件 / 目录 | 用途 |
| --- | --- |
| `scripts/hei_fastapi.sql` | MySQL 全量建表、种子数据（`sys_job.handler` 为 FastAPI 原生 key） |
| `migrations/` | Alembic 增量表结构（PG / MySQL 可移植建表，见 [`migrations/README.md`](migrations/README.md)） |

## 快速开始

### 环境要求

- Python **3.11+**
- MySQL 8+（演示种子）、Redis
- PostgreSQL 亦可（通过 Alembic 建表，见 `migrations/README.md`）

### 1. 初始化数据库

**MySQL 8+（本地演示，含种子，推荐）：**

```bash
mysql -u root -p -e "CREATE DATABASE hei_fastapi DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p hei_fastapi < scripts/hei_fastapi.sql
```

与 `hei_boot` 表结构对齐；`sys_job.handler` 使用 FastAPI 栈标识（如 `sys_job_sample`），非 Boot 的 Java 全限定类名。

**Alembic（可移植建表，适合 PG / 空库增量维护）：**

```bash
cp .env.example .env
# 配置 DB__URL，例如：
# DB__URL=mysql+aiomysql://root:123456@127.0.0.1:3306/hei_fastapi?charset=utf8mb4

pip install -e ".[dev,mysql]"   # 或 ".[dev,postgres]"
alembic upgrade head
```

种子数据需另行导入 `scripts/hei_fastapi.sql` 中的 `INSERT` 段，或从已初始化的 `hei_boot` 库迁移业务数据后修正 `sys_job.handler`。

配置见 [`.env.example`](.env.example)（`DB__URL` / `REDIS__URL` / `APP__CONFIG_CRYPTO_KEY` 等）。`APP__CONFIG_CRYPTO_KEY` 须与种子中 `sys_config` 密文匹配；生产环境请生成新 Fernet 密钥。

> 应用启动（`entrypoint.sh`）不执行迁移；`alembic upgrade head` 仅在维护时手动执行。

### 2. 启动后端

```bash
pip install -e ".[dev,mysql]"
cp .env.example .env
# 按需修改 DB__URL / REDIS__URL 等
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

| 项 | 地址 |
| --- | --- |
| API | http://127.0.0.1:8000 |
| OpenAPI | http://127.0.0.1:8000/docs（需 `SWAGGER__ENABLED=true`） |
| ReDoc | http://127.0.0.1:8000/redoc（需 `SWAGGER__ENABLED=true`） |

> Linux / 容器可用 `./entrypoint.sh`（gunicorn）。Docker 相关见 [`docker/`](docker/) 与根目录 [`Dockerfile`](Dockerfile)。

### 3. 启动前端（可选）

前端为独立仓库，默认将 `/api` 代理到本后端 `http://127.0.0.1:8000`：

```bash
# 管理端 → http://127.0.0.1:5173
git clone https://github.com/jiangbyte/hei-admin.git && cd hei-admin
pnpm install && pnpm dev

# 门户 → http://127.0.0.1:5174
git clone https://github.com/jiangbyte/hei-portal.git && cd hei-portal
pnpm install && pnpm dev
```

详见 [hei-admin](https://github.com/jiangbyte/hei-admin) / [hei-portal](https://github.com/jiangbyte/hei-portal) 各仓库 README。

## 默认账号

| 端 | 前端仓库 | 地址 | 账号 | 密码 | 说明 |
| --- | --- | --- | --- | --- | --- |
| Admin | [hei-admin](https://github.com/jiangbyte/hei-admin) | http://127.0.0.1:5173 | `superadmin` | `123456` | 超级管理员（`*:*:*`） |

> 仅供本地演示。部署后请修改默认密码，并更换配置加密密钥、对象存储凭证等敏感项。更多演示账号与内容种子已写入 `scripts/hei_fastapi.sql`。

## 姊妹项目

| 项目 | 说明 | 协议 |
| --- | --- | --- |
| [**hei-boot**](https://github.com/jiangbyte/hei-boot) | Spring Boot 脚手架 | Apache License 2.0 |
| [**hei-gin**](https://github.com/jiangbyte/hei-gin) | Go / Gin 后端 | Apache License 2.0 |
| [**hei-fastapi**](https://github.com/jiangbyte/hei-fastapi) | FastAPI 后端（本仓库） | Apache License 2.0 |
| [**hei-admin**](https://github.com/jiangbyte/hei-admin) | Vue 3 管理端前端 | Apache License 2.0 |
| [**hei-portal**](https://github.com/jiangbyte/hei-portal) | React 门户前端 | Apache License 2.0 |
| [**hei-admin-uniapp**](https://github.com/jiangbyte/hei-admin-uniapp) | uni-app 管理端移动端 | Apache License 2.0 |

## License

本项目基于 [Apache License 2.0](LICENSE) 开源。完整条款见 [LICENSE](LICENSE)，版权声明见 [NOTICE](NOTICE).
