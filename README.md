> 本项目是我前段时间在公司内部为负责的小型项目独立开发的框架，目前已在实际生产中投入使用。由于框架完全由我个人设计实现，现将其从内部分支中剥离，参考优秀框架，并添加了更多功能，最终以独立仓库的形式开源，不断在优化中，欢迎大家提意见、提issue、提PR。

# Hei FastAPI

<img width="120" src="https://jiangbyte.github.io/hei-docs/logo.svg">

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.13+-orange.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-brightgreen.svg)

## 简介

**Hei FastAPI** 是 HEI 快速开发框架的 Python 单体应用版本，基于 FastAPI + SQLAlchemy 2.0 构建。提供开箱即用的快速开发解决方案，包含完善的权限管理（RBAC）、数据权限、认证授权等功能模块。框架采用前后端分离架构，支持快速搭建管理系统和 API 服务。

**在线文档**: [https://jiangbyte.github.io/hei-docs/hei-fastapi/](https://jiangbyte.github.io/hei-docs/hei-fastapi/)

## 技术栈

| 类型 | 技术 |
| --- | --- |
| 核心框架 | Python 3.13+ / FastAPI 0.115+ / Uvicorn |
| 数据验证 | Pydantic v2 + Pydantic-Settings |
| ORM | SQLAlchemy 2.0 (Mapped + mapped_column) |
| 数据库 | MySQL 8.0+ (PyMySQL) |
| 缓存 | Redis 6.0+ (redis-py) |
| 认证授权 | JWT / SM2 国密加密 / bcrypt 密码哈希 |
| Excel处理 | OpenPyXL |
| 分布式ID | Snowflake ID 算法 |

## 核心特性

- **双端认证体系** — B端（后台管理）和 C端（客户端）独立的 JWT 认证与权限装饰器
- **SM2 国密加密** — 登录密码传输使用国密 SM2 C1C3C2 模式加密
- **bcrypt 密码哈希** — 存储密码使用 bcrypt 加盐哈希
- **RBAC 权限控制** — 用户→角色→权限 + 用户→组→角色→权限 + 用户直授权限，三层模型
- **数据权限** — 支持全部/本级及以下/本级/仅本人/自定义 五种数据权限粒度，按最严策略合并
- **权限自动发现** — 启动时自动扫描 `@HeiCheckPermission` 装饰器，缓存权限到 Redis
- **统一响应格式** — `{code, message, data, success}` 标准结构
- **全局异常处理** — 统一捕获 BusinessException 返回业务错误码
- **验证码** — 内置图形验证码生成与校验
- **代码生成器** — 通过数据库表自动生成完整 CRUD 模块（8 个文件）
- **雪花ID** — 分布式 Snowflake ID 生成器
- **Excel 导入导出** — 通用模板下载、数据导出、数据导入

## 项目结构

```
hei-fastapi
├── config/
│   └── settings.py              # Pydantic 配置（支持 env 覆盖）
├── core/
│   ├── app/
│   │   ├── setup.py             # FastAPI 应用工厂
│   │   ├── router.py            # 路由注册
│   │   ├── lifespan.py          # 生命周期（DB/Redis/SM2/JWT/权限初始化）
│   │   └── health.py            # 健康检查 GET /
│   ├── auth/
│   │   ├── auth/
│   │   │   ├── hei_auth_tool.py           # B端 JWT 认证工具
│   │   │   └── hei_client_auth_tool.py    # C端 JWT 认证工具
│   │   ├── decorator/
│   │   │   ├── hei_check_login.py         # @HeiCheckLogin
│   │   │   ├── hei_check_permission.py    # @HeiCheckPermission("module:action")
│   │   │   ├── hei_check_role.py          # @HeiCheckRole("admin")
│   │   │   ├── hei_client_check_login.py  # C端登录检查
│   │   │   └── hei_client_check_permission.py  # C端权限检查
│   │   ├── permission/
│   │   │   ├── hei_permission_interface.py          # 权限查询接口
│   │   │   ├── hei_permission_interface_manager.py  # 接口管理器
│   │   │   └── hei_permission_tool.py               # 权限查询门面
│   │   └── permission_scan.py            # 权限自动扫描
│   ├── db/
│   │   ├── mysql.py             # MySQL 同步引擎 + sessionmaker
│   │   ├── base_dao.py          # BaseDAO 通用 CRUD
│   │   └── redis.py             # Redis 异步客户端
│   ├── middleware/
│   │   ├── auth.py              # JWT 认证中间件（按路径分流 B/C/Public）
│   │   ├── cors.py              # CORS 中间件
│   │   └── exception.py         # 全局异常处理
│   ├── result/
│   │   └── result.py            # success() / failure() / page_data() 响应工具
│   ├── exception/
│   │   └── business_exception.py # BusinessException
│   ├── enums/
│   │   ├── data_scope_enum.py   # 数据范围枚举 + 最严策略合并
│   │   └── ...                  # 其他枚举
│   ├── pojo/                    # 公共数据对象（IdParam, IdsParam, PageBounds）
│   └── utils/
│       ├── sm2_crypto_util.py   # SM2 国密加解密
│       ├── excel_utils.py       # Excel 导出导入
│       ├── ip_utils.py          # 客户端 IP 提取
│       ├── snowflake_utils.py   # 雪花 ID 生成
│       └── model_utils.py       # 模型工具（系统字段剥离、更新、模板）
├── modules/
│   ├── auth/
│   │   ├── captcha/             # 图形验证码生成校验
│   │   └── username/            # 用户名密码登录/注册/登出
│   ├── sys/
│   │   ├── banner/              # Banner 管理
│   │   ├── dict/                # 字典管理（树形结构）
│   │   ├── group/               # 用户组管理
│   │   ├── notice/              # 通知管理
│   │   ├── org/                 # 组织管理
│   │   ├── permission/          # 权限管理
│   │   ├── position/            # 职位管理
│   │   ├── resource/            # 资源管理
│   │   ├── role/                # 角色管理（含权限/资源分配）
│   │   └── user/                # 用户管理（含角色/组分配）
│   ├── client/
│   │   └── user/                # C端用户管理
│   └── dev/                     # 代码生成器
│       ├── gen_basic_service.py # 表信息读取 + 代码生成
│       ├── gen_config_service.py# 字段配置
│       └── templates/           # Jinja2 模板
├── scripts/
│   └── sqls/
│       └── hei_ddl.sql          # 数据库建表 DDL
├── .env                         # 环境配置
├── main.py                      # 应用入口
├── pyproject.toml               # 项目配置
└── requirements.txt             # 依赖列表
```

### 模块结构约定

每个业务模块遵循垂直切片布局：

```
modules/<domain>/
├── models.py        # SQLAlchemy ORM 模型（Mapped + mapped_column）
├── params.py        # Pydantic v2 请求/响应模型（VO, PageParam, ExportParam, ImportParam）
├── dao.py           # 数据访问层（继承 BaseDAO）
├── service.py       # 业务逻辑层
└── api/v1/api.py    # FastAPI 路由定义
```

## 快速开始

### 环境要求

- Python 3.13+
- MySQL 8.0+
- Redis 6.0+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 初始化数据库

```bash
# 创建数据库并执行 DDL
mysql -u root -p < scripts/sqls/hei_ddl.sql
```

### 配置

编辑 `.env` 文件：

```env
DB__HOST=localhost
DB__PORT=3306
DB__USER=root
DB__PASSWORD=123456
DB__DATABASE=hei_data

REDIS__HOST=localhost
REDIS__PORT=6379
REDIS__PASSWORD=123456

SM2__PRIVATE_KEY=your-sm2-private-key
SM2__PUBLIC_KEY=your-sm2-public-key

JWT__SECRET_KEY=your-jwt-secret-key
```

### 启动服务

```bash
python main.py
```

服务启动后访问：

- API 文档：<http://localhost:8081/docs>
- 健康检查：<http://localhost:8081/>

## 认证体系

框架提供三套路径规则：

| 路径模式 | 认证方式 | 说明 |
|---------|---------|------|
| `/api/v1/b/*` | HeiAuthTool + @HeiCheckPermission | B端后台管理 |
| `/api/v1/c/*` | HeiClientAuthTool + @HeiClientCheckPermission | C端客户端 |
| `/api/v1/public/b/*`, `/api/v1/public/c/*` | 无 | 公开接口 |

认证中间件按路径前缀自动分流，CORS 预检请求（OPTIONS）和静态路径跳过认证。

## API 规范

### 统一响应格式

```json
{
  "code": 200,
  "message": "请求成功",
  "data": {},
  "success": true
}
```

### 分页响应

```json
{
  "code": 200,
  "message": "请求成功",
  "data": {
    "records": [],
    "total": 100,
    "page": 1,
    "size": 20,
    "pages": 5
  },
  "success": true
}
```

### 权限装饰器

```python
from core.auth.decorator import HeiCheckPermission

@router.get("/api/v1/sys/banner/page")
@HeiCheckPermission("sys:banner:page")
async def page(request: Request, db: Session = Depends(get_db)):
    service = BannerService(db)
    return success(service.page(BannerPageParam()))
```

装饰器必须位于 `@router.*` 下方（紧贴函数）。

## 权限数据链路

```
User ──→ RelUserRole ──→ Role ──→ RelRolePermission ──→ Permission
User ──→ RelUserPermission ──→ Permission (直授)
```

数据范围存储在关系表中（`rel_role_permission.scope`、`rel_user_role.scope` 等），多角色多路径下按最严策略合并（本人 < 自定义 < 本级及以下 < 本级 < 全部）。

## 相关项目

- **[Hei Boot](https://github.com/jiangbyte/hei-boot)** — Java Spring Boot 单体版本
- **[Hei Cloud](https://github.com/jiangbyte/hei-cloud)** — Java 微服务版本
- **[Hei Admin Vue](https://github.com/jiangbyte/hei-admin-vue)** — Vue3 前端管理后台

## 致谢

本项目参考了以下优秀开源项目：

- **[Snowy](https://github.com/xiaonuobase/Snowy)** — 国密前后端分离快速开发平台

## 开源协议

本项目采用 [MIT License](LICENSE) 开源协议
