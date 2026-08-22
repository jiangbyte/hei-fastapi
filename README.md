# HEI FastAPI

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116%2B-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2%20Async-D71F00?logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supported-4169E1?logo=postgresql&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-Supported-4479A1?logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Supported-DC382D?logo=redis&logoColor=white)
![Vue](https://img.shields.io/badge/Admin-Vue%203-4FC08D?logo=vuedotjs&logoColor=white)
![React](https://img.shields.io/badge/Portal-React-61DAFB?logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-Apache_2.0-blue)
![Version](https://img.shields.io/badge/version-1.0.0--beta-orange)

**HEI FastAPI** 是一套开箱即用的 FastAPI 异步工程化脚手架：单个后端应用同时提供 **Admin** 与 **Portal** 双端 API，同仓维护 Vue 3 / React / uni-app 前端，覆盖认证授权、组织权限、系统运维、消息通知与运营看板等常见后台能力。与 [hei-boot](https://github.com/jiangbyte/hei-boot) 保持 API 契约与前端对齐。

> 当前版本：`1.0.0-beta` · 协议：[Apache License 2.0](LICENSE)

## 目录

- [界面预览](#界面预览)
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [工程结构](#工程结构)
- [快速开始](#快速开始)
- [默认账号](#默认账号)
- [相关文档](#相关文档)
- [姊妹项目](#姊妹项目)
- [License](#license)

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

### 管理端 · 登录 / 工作台

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

### 管理端 · 组织权限

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
    <td width="50%"><img src="docs/images/admin-iam-dept.png" alt="部门管理" /></td>
    <td width="50%"><img src="docs/images/admin-iam-group.png" alt="用户组管理" /></td>
  </tr>
  <tr>
    <td align="center">部门管理</td>
    <td align="center">用户组管理</td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/images/admin-iam-position.png" alt="岗位管理" /></td>
    <td width="50%"><img src="docs/images/admin-iam-resource.png" alt="资源授权" /></td>
  </tr>
  <tr>
    <td align="center">岗位管理</td>
    <td align="center">资源授权</td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/images/admin-iam-resource-module.png" alt="资源模块" /></td>
    <td width="50%"><img src="docs/images/admin-iam-client-resource.png" alt="客户端资源" /></td>
  </tr>
  <tr>
    <td align="center">资源模块</td>
    <td align="center">客户端资源</td>
  </tr>
</table>

### 管理端 · 系统运维

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
  <tr>
    <td width="50%"><img src="docs/images/admin-sys-session.png" alt="在线会话" /></td>
    <td width="50%"><img src="docs/images/admin-sys-login-log.png" alt="登录日志" /></td>
  </tr>
  <tr>
    <td align="center">在线会话</td>
    <td align="center">登录日志</td>
  </tr>
</table>

### 管理端 · 消息与文件

<table>
  <tr>
    <td width="50%"><img src="docs/images/admin-sys-banner.png" alt="Banner 管理" /></td>
    <td width="50%"><img src="docs/images/admin-message-notice.png" alt="公告通知" /></td>
  </tr>
  <tr>
    <td align="center">Banner 管理</td>
    <td align="center">公告通知</td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/images/admin-message-feedback.png" alt="意见反馈" /></td>
    <td width="50%"><img src="docs/images/admin-sys-file.png" alt="文件管理" /></td>
  </tr>
  <tr>
    <td align="center">意见反馈</td>
    <td align="center">文件管理</td>
  </tr>
</table>

### 管理端 · 业务示例

<table>
  <tr>
    <td width="50%"><img src="docs/images/admin-biz-order.png" alt="订单示例" /></td>
    <td></td>
  </tr>
  <tr>
    <td align="center">订单示例</td>
    <td></td>
  </tr>
</table>

## 功能特性

- **双端账号体系**：ADMIN / PORTAL 独立会话（HttpOnly Cookie / Authorization 双通道）；密码 RSA 传输、验证码登录、失败锁定与限流；可配置三方 OAuth 登录
- **RBAC 权限**：账号 / 角色 / 部门 / 用户组 / 岗位；菜单、按钮与 API 资源授权；在线会话踢出
- **系统管理**：字典、动态配置（敏感项 Fernet 加密）、Banner、公告 / 通知、意见反馈、弱口令库
- **对象存储**：S3 兼容存储（MinIO / RustFS / 阿里云 OSS / 腾讯云 COS 等），直链或预签名访问
- **运维能力**：操作审计与告警、登录日志、运营工作台、内置任务调度（`sys_job`；种子任务默认禁用，需在管理端启用）
- **代码生成**：单表 / 树表 / 主子表方案，预览与 ZIP 下载；前端产物默认输出到姊妹仓库 [hei-admin](https://github.com/jiangbyte/hei-admin)（`CODEGEN_FRONTEND_ROOT` 可配置）

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
hei-fastapi
├── app/                      # FastAPI 应用
│   ├── core/                 # 配置、安全、存储、中间件等
│   └── modules/              # 业务模块（auth / iam / sys / profile / workspace / biz）
├── scripts/db.sql            # 数据库结构 + 种子数据（对齐 hei-boot）
├── migrations/               # Alembic 增量表结构
├── tests/                    # 单元 / API 测试
└── docs/images               # README 截图
```

前端使用姊妹仓库 [hei-admin](https://github.com/jiangbyte/hei-admin)（管理端）与 [hei-portal](https://github.com/jiangbyte/hei-portal)（门户），通过环境变量代理 API，与本仓库 `hei-boot` 用法一致。

## 快速开始

### 环境要求

- Python **3.11+**、pip（推荐 conda / venv）
- **PostgreSQL 或 MySQL**、Redis（通过 `DB__URL` 二选一，不支持 SQLite）
- Node.js **22+**、pnpm **9+**（姊妹前端 hei-admin / hei-portal）

### 1. 初始化数据库

**PostgreSQL（演示全量，含种子）：**

```bash
createdb -U postgres -h 127.0.0.1 hei_fastapi
psql -U postgres -h 127.0.0.1 -d hei_fastapi -f scripts/db.sql
```

**PostgreSQL / MySQL（可移植建表，推荐）：**

```bash
# PostgreSQL
# DB__URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/hei_fastapi
# pip install -e ".[postgres]"

# MySQL（先建空库，字符集建议 utf8mb4）
# DB__URL=mysql+aiomysql://root:password@127.0.0.1:3306/hei_fastapi
# pip install -e ".[mysql]"

alembic upgrade head
```

> `scripts/db.sql` 仅适用于 PostgreSQL 演示全量重建。MySQL 请用 Alembic。已有库的增量变更同样使用 `alembic upgrade head`。应用启动（`entrypoint.sh`）不执行迁移。

### 2. 启动后端

```bash
pip install -r requirements-dev.txt
# 或按方言：pip install -e ".[dev,postgres]" / pip install -e ".[dev,mysql]"
cp .env.example .env
# 按需修改 DB__URL / REDIS__URL / APP__CONFIG_CRYPTO_KEY / STORAGE__* 等
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

| 项 | 地址 |
| --- | --- |
| API | http://127.0.0.1:8000 |
| OpenAPI | http://127.0.0.1:8000/docs（需 `SWAGGER__ENABLED=true`） |

> Linux / 容器可用 `./entrypoint.sh`（gunicorn）。Docker 相关见 [`docker/`](docker/) 与根目录 [`Dockerfile`](Dockerfile)。

### 3. 启动前端（姊妹仓库）

管理端与门户在独立仓库维护，与本后端 API 契约对齐：

```bash
# 管理端 hei-admin → http://127.0.0.1:5173
cd ../hei-admin && pnpm install && pnpm dev

# 门户 hei-portal → http://127.0.0.1:5174
cd ../hei-portal && pnpm install && pnpm dev
```

将 `VITE_API_PROXY` 指向本后端（默认 `http://127.0.0.1:8000`）。

## 默认账号

| 端 | 地址 | 账号 | 密码 |
| --- | --- | --- | --- |
| Admin | http://localhost:5173 | `superadmin` | `123456` |
| Portal | http://localhost:5174 | `user` | `123456` |

> 仅供本地演示。部署到非本机环境后请立即修改默认密码，并更换配置加密密钥、对象存储凭证等敏感项。

## 相关文档

| 文档 | 说明 |
| --- | --- |
| [hei-admin README](https://github.com/jiangbyte/hei-admin) | 管理端前端说明与环境变量 |
| [hei-portal README](https://github.com/jiangbyte/hei-portal) | 门户前端说明与环境变量 |
| [`.env.example`](.env.example) | 后端环境变量样例 |
| [`scripts/db.sql`](scripts/db.sql) | PostgreSQL 演示库结构与种子数据 |
| [`migrations/README.md`](migrations/README.md) | Alembic 增量迁移（PG / MySQL） |
| [`scripts/README.md`](scripts/README.md) | 脚本用法 |

## 姊妹项目

| 项目 | 说明 | 协议 |
| --- | --- | --- |
| [**hei-boot**](https://github.com/jiangbyte/hei-boot) | Spring Boot 工程化脚手架 | Apache License 2.0 |
| [**hei-admin**](https://github.com/jiangbyte/hei-admin) | Vue 3 管理端前端 | Apache License 2.0 |
| [**hei-portal**](https://github.com/jiangbyte/hei-portal) | React 门户前端 | Apache License 2.0 |
| [**hei-gin**](https://github.com/jiangbyte/hei-gin) | Go 轻量级后端框架 | Apache License 2.0 |
| [**hei-fastapi**](https://github.com/jiangbyte/hei-fastapi) | FastAPI 异步脚手架（本仓库） | Apache License 2.0 |

## License

本项目基于 [Apache License 2.0](LICENSE) 开源。完整条款见 [LICENSE](LICENSE)，版权声明见 [NOTICE](NOTICE)。
