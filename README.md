> 本项目是我前段时间在公司内部为负责的小型项目独立开发的框架，目前已在实际生产中投入使用。由于框架完全由我个人设计实现，现将其从内部分支中剥离，参考优秀框架，并添加了更多功能，最终以独立仓库的形式开源，不断在优化中，欢迎大家提意见、提issue、提PR。

# Hei FastAPI

<img width="120" src="https://jiangbyte.github.io/hei-docs/logo.svg">

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10+-orange.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-brightgreen.svg)

## 简介

**Hei FastAPI** 是 HEI 快速开发框架的 Python 单体应用版本，基于 FastAPI + SQLAlchemy 2.0 构建。提供开箱即用的快速开发解决方案，包含完善的权限管理（RBAC）、数据权限、认证授权、文件存储、操作日志等功能模块。框架采用前后端分离架构，支持快速搭建后台管理系统和 API 服务。

**在线文档**: [https://jiangbyte.github.io/hei-docs/hei-fastapi/](https://jiangbyte.github.io/hei-docs/hei-fastapi/)

## 技术栈

| 类型 | 技术 |
| --- | --- |
| 核心框架 | Python 3.10+ / FastAPI 0.136+ / Uvicorn |
| 数据验证 | Pydantic v2 + Pydantic-Settings |
| ORM | SQLAlchemy 2.0 (Mapped + mapped_column) |
| 数据库 | MySQL 8.0+ (PyMySQL) |
| 缓存 | Redis 6.0+ (redis-py) |
| 认证授权 | JWT / SM2 国密加密 / bcrypt 密码哈希 |
| 文件存储 | 本地存储 / MinIO / S3 兼容对象存储 |
| Excel处理 | OpenPyXL |
| 分布式ID | Snowflake ID 算法 |

## 核心特性

- **双端认证体系** — B端（后台管理）和 C端（客户端）独立的两套 JWT 认证、权限装饰器
- **SM2 国密加密** — 登录密码传输使用国密 SM2 C1C3C2 模式加密
- **bcrypt 密码哈希** — 存储密码使用 bcrypt 加盐哈希
- **RBAC 权限控制** — 用户→角色→权限 + 用户直授权限，双层模型
- **数据权限** — 支持全部/本级及以下/本级/仅本人/自定义五种粒度，按最严策略合并
- **权限自动发现** — 启动时自动扫描 `@HeiCheckPermission` 装饰器并缓存到 Redis
- **文件存储抽象** — 统一接口，支持本地文件、MinIO、S3 兼容对象存储，一键切换
- **操作日志** — `@SysLog` 装饰器自动记录用户操作，支持请求参数和返回结果
- **防重复提交** — `@NoRepeat` 装饰器防止接口重复调用
- **链路追踪** — 基于 ContextVar 的 trace_id 全链路追踪
- **统一验证码** — B端/C端独立的图形验证码服务
- **统一响应格式** — `{code, message, data, success}` 标准结构
- **全局异常处理** — 统一捕获 BusinessException 返回业务错误码
- **Excel 导入导出** — 通用模板下载、数据导出、数据导入
- **雪花ID** — 分布式 Snowflake ID 生成器

## 项目结构

```
hei-fastapi
├── config/
│   └── settings.py              # Pydantic 配置（支持 .env 覆盖）
├── core/                        # 框架核心
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
│   │   │   ├── hei_client_check_login.py  # C端 @HeiClientCheckLogin
│   │   │   ├── hei_client_check_permission.py  # C端 @HeiClientCheckPermission
│   │   │   ├── hei_client_check_role.py   # C端 @HeiClientCheckRole
│   │   │   └── norepeat.py               # @NoRepeat 防重复提交
│   │   ├── permission/
│   │   │   ├── hei_permission_interface.py           # 权限查询接口
│   │   │   ├── hei_permission_interface_manager.py   # 接口管理器
│   │   │   ├── hei_permission_matcher.py             # 权限匹配器
│   │   │   └── hei_permission_tool.py                # 权限查询门面
│   │   ├── permission_scan.py            # 权限自动扫描
│   │   └── pojo/
│   │       ├── login_user_info.py        # B端登录用户信息
│   │       └── login_client_user_info.py # C端登录用户信息
│   ├── captcha/
│   │   └── captcha.py          # 统一图形验证码服务（B/C 双实例）
│   ├── constants/
│   │   ├── base_fields.py      # 基础模型字段常量
│   │   └── cache_keys.py       # Redis 缓存键常量
│   ├── db/
│   │   ├── mysql.py            # MySQL 同步引擎 + sessionmaker
│   │   ├── base_dao.py         # BaseDAO 通用 CRUD
│   │   ├── base_service.py     # BaseService 通用业务逻辑
│   │   ├── query_wrapper.py    # QueryWrapper 链式查询构建器
│   │   ├── meta_object_handler.py  # 系统字段自动填充
│   │   └── redis.py            # Redis 异步客户端
│   ├── enums/
│   │   ├── data_scope_enum.py  # 数据范围枚举 + 最严策略合并
│   │   ├── permission_enum.py  # 权限类型枚举
│   │   ├── resource_enum.py    # 资源类型枚举
│   │   ├── status_enum.py      # 通用状态枚举
│   │   ├── login_type_enum.py  # 登录类型枚举
│   │   ├── check_mode_enum.py  # 校验模式枚举
│   │   └── ...                 # 其他枚举
│   ├── exception/
│   │   └── business_exception.py # BusinessException
│   ├── log/
│   │   ├── decorator.py        # @SysLog 操作日志装饰器
│   │   └── utils.py            # 日志工具（User-Agent 解析、参数序列化）
│   ├── middleware/
│   │   ├── auth.py             # JWT 认证中间件（按路径分流 B/C/Public）
│   │   ├── cors.py             # CORS 中间件
│   │   ├── exception.py        # 全局异常处理
│   │   └── trace.py            # 链路追踪中间件（TraceMiddleware）
│   ├── pojo/
│   │   ├── page_bounds.py      # 分页参数
│   │   ├── datetime_mixin.py   # 日期时间序列化混入
│   │   └── ...                 # 其他公共数据对象
│   ├── result/
│   │   └── result.py           # success() / failure() / page_data() 响应工具
│   ├── storage/
│   │   ├── interface.py        # FileStorageInterface 抽象接口
│   │   ├── local_storage.py    # 本地文件存储实现
│   │   ├── minio_storage.py    # MinIO 对象存储实现
│   │   └── s3_storage.py       # S3 兼容对象存储实现
│   └── utils/
│       ├── sm2_crypto_util.py  # SM2 国密加解密
│       ├── excel_utils.py      # Excel 导出导入
│       ├── ip_utils.py         # 客户端 IP 提取
│       ├── snowflake_utils.py  # 雪花 ID 生成
│       ├── model_utils.py      # 模型工具（系统字段剥离、更新、模板）
│       ├── trace_utils.py      # Trace ID 上下文管理
│       └── user_agent_utils.py # User-Agent 解析
├── modules/
│   ├── sys/                    # B端（后台管理）
│   │   ├── auth/               # 认证模块
│   │   │   ├── captcha/        # 图形验证码
│   │   │   ├── sm2/            # SM2 公钥获取
│   │   │   └── username/       # 用户名密码登录/注册/登出
│   │   ├── banner/             # Banner 管理
│   │   ├── config/             # 系统配置管理
│   │   ├── dict/               # 字典管理（树形结构）
│   │   ├── file/               # 文件管理
│   │   ├── group/              # 用户组管理
│   │   ├── home/               # 首页仪表盘（快捷方式）
│   │   ├── log/                # 操作日志查询
│   │   ├── notice/             # 通知管理
│   │   ├── org/                # 组织管理
│   │   ├── permission/         # 权限管理
│   │   ├── position/           # 职位管理
│   │   ├── resource/           # 资源管理（菜单/按钮）
│   │   ├── role/               # 角色管理（含权限/资源分配）
│   │   ├── session/            # 在线会话管理
│   │   ├── analyze/            # 系统分析
│   │   └── user/               # 用户管理（含角色/组分配）
│   ├── client/                 # C端（客户端）
│   │   ├── auth/               # 认证模块
│   │   │   ├── captcha/        # 图形验证码
│   │   │   └── username/       # 用户名密码登录/注册
│   │   ├── session/            # 在线会话管理
│   │   └── user/               # C端用户管理
│   └── biz/                    # 业务模块（用户自定义）
├── scripts/
│   └── sqls/
│       └── hei_ddl.sql         # 数据库建表 DDL
├── .env                        # 环境配置文件
├── main.py                     # 应用入口
└── pyproject.toml              # 项目配置
```

### 模块结构约定

每个业务模块遵循垂直切片布局：

```
modules/<domain>/
├── models.py        # SQLAlchemy ORM 模型（Mapped + mapped_column）
├── params.py        # Pydantic v2 请求/响应模型（VO, PageParam, ExportParam, ImportParam）
├── dao.py           # 数据访问层（继承 BaseDAO）
├── service.py       # 业务逻辑层（继承 BaseService）
└── api/v1/api.py    # FastAPI 路由定义
```

## 快速开始

### 环境要求

- Python 3.10+
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
| `/api/v1/b/*` | HeiAuthTool + 权限装饰器 | B端后台管理 |
| `/api/v1/c/*` | HeiClientAuthTool + 权限装饰器 | C端客户端 |
| `/api/v1/public/b/*`, `/api/v1/public/c/*` | 无认证 | 公开接口 |

认证中间件按路径前缀自动分流，CORS 预检请求（OPTIONS）跳过认证。

## 装饰器参考

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

### 操作日志

```python
from core.log import SysLog

@router.post("/api/v1/sys/config/create")
@SysLog("新增系统配置")  # 自动记录操作人、时间、IP、请求参数
@HeiCheckPermission("sys:config:create")
async def create(...):
    ...
```

### 防重复提交

```python
from core.auth.decorator import NoRepeat

@router.post("/api/v1/sys/xxx/create")
@NoRepeat(interval=3000)  # 3 秒内相同参数禁止重复提交
async def create(...):
    ...
```

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

## 权限数据链路

```
User ──→ RelUserRole ──→ Role ──→ RelRolePermission ──→ Permission
User ──→ RelUserGroup ──→ Group ──→ RelGroupRole ──→ Role ──→ ... ──→ Permission
User ──→ RelUserPermission ──→ Permission (直授)
```

数据范围存储在关系表中，多角色多路径下按最严策略合并（本人 < 自定义 < 本级及以下 < 本级 < 全部）。

## 文件存储配置

框架支持三种存储后端，通过 `STORAGE__ACTIVE` 切换：

```env
# 本地存储（默认）
STORAGE__ACTIVE=local
STORAGE__LOCAL__PATH=./storage

# MinIO
STORAGE__ACTIVE=minio
STORAGE__MINIO__ENDPOINT=http://localhost:9000
STORAGE__MINIO__ACCESS_KEY=minioadmin
STORAGE__MINIO__SECRET_KEY=minioadmin

# S3 兼容
STORAGE__ACTIVE=s3
STORAGE__S3__BUCKET=my-bucket
STORAGE__S3__REGION=us-east-1
```

## 相关项目

- **[Hei Boot](https://github.com/jiangbyte/hei-boot)** — Java Spring Boot 单体版本
- **[Hei Admin Vue](https://github.com/jiangbyte/hei-admin-vue)** — Vue3 前端管理后台

## 开源协议

本项目采用 [MIT License](LICENSE) 开源协议
