# IAM 设计说明

HEI FastAPI 的 IAM（Identity and Access Management）基于 RBAC 模型扩展，支持账号、角色、部门、用户组、岗位、资源菜单和权限的统一管理。

---

## 核心概念

### 账号体系

| 概念 | 说明 |
|---|---|
| `sys_account` | 统一账号表，存储密码哈希、状态、登录追踪等通用属性 |
| `sys_account_identity` | 登录身份表，一个账号可绑定多个身份（用户名、邮箱、手机号） |
| 账号类型 | `ADMIN`（管理端）和 `PORTAL`（门户 API / React 门户客户端），独立登录入口 |
| 密码策略 | 复杂度要求（大小写/数字/特殊字符）、过期天数、历史检查（最近 5 次）、常见密码黑名单 |

账号状态：正常、锁定、禁用、已注销。注销的账号有定时清理任务。

### 权限核心实体

| 实体 | 表 | 说明 |
|---|---|---|
| 角色 | `sys_role` | 权限集合，支持 scope 类型、内置标识、分类 |
| 部门 | `sys_dept` | 组织架构树 |
| 用户组 | `sys_group` | 跨部门的用户集合 |
| 岗位 | `sys_position` | 职能岗位 |
| 资源 | `sys_resource` | 菜单/功能/页面 5 级树形结构 |
| 资源模块 | `sys_resource_module` | 资源按模块分组 |

### 统一关系模型

**`sys_iam_relation`** — 所有 IAM 关系通过这一张多态关系表表达：

- 账号 ↔ 角色
- 账号 ↔ 部门
- 角色 ↔ 资源
- 角色 ↔ 权限
- 资源 ↔ 权限

关系支持属性：

| 属性 | 说明 |
|---|---|
| `grant_mode` | 授权模式 |
| `effect` | `ALLOW` / `DENY`，判断优先级 |
| `data_scope` | 数据范围：`ALL` / `DEPT_AND_CHILD` / `DEPT` / `SELF` / `CUSTOM` |
| `expired_at` | 过期时间 |

---

## 权限判定流程

1. 用户登录 → 获取账号信息和角色列表
2. 根据角色关联的资源 → 计算可访问菜单和页面
3. 根据角色关联的权限键 → 计算按钮级操作权限
4. 根据角色的数据范围 → 限制数据查询范围

### 数据范围说明

| 范围 | 含义 |
|---|---|
| `ALL` | 全部数据 |
| `DEPT_AND_CHILD` | 本部门及子部门 |
| `DEPT` | 仅本部门 |
| `SELF` | 仅本人 |
| `CUSTOM` | 自定义范围（配合部门选择） |

业务列表（如 `page_admin`）通过 `build_data_scope_filter` 注入 SQL 条件：

- **SELF**：按 `created_by`（账号 ID）过滤。
- **DEPT / DEPT_AND_CHILD / CUSTOM**：需要模型上的部门列。Codegen 主表已混入 `OwnerDeptMixin.owner_dept_id`；`service` 传 `dept_column=getattr(Model, "owner_dept_id", None)`。
- 若角色含部门范围但模型**没有** `owner_dept_id`，会降级为 SELF（避免误放行全部数据）。
- 存量 biz 主表已混入 `OwnerDeptMixin`；迁移 `c3d4e5f6a7b8_biz_owner_dept` 在表存在时 `add_column`；`d4e5f6a7b8c9_mfa_owner_backfill` 按 `ACCOUNT_DEPT` 回填历史行。
- 创建时：`default_owner_dept_id(session)` 取 `session.dept_ids[0]` 写入（账号无部门则为空）；历史行可为空，SELF 仍靠 `created_by`。
- **Admin MFA**：TOTP + WebAuthn/Passkey；`AUTH__MFA_REQUIRED` 时可强制开通；密码通过后 challenge，再 `POST /v1/admin/login/mfa`；Portal / Uniapp 不参与 MFA 完成流程。

---

## 权限注册与同步

系统启动时自动扫描所有路由的标签和元数据，提取权限键并注册到 Redis 权限注册表。

- 权限键格式遵循资源路由路径
- 管理端 `sys_resource` 模块提供页面前端可见资源的查询接口
- 启动时通过 `apply_all_config()` 将 `sys_config` 覆盖到 `settings`（Auth、Storage、Mail、Audit、PasswordPolicy）

---

## 会话管理

| 特性 | 说明 |
|---|---|
| Token 存储 | Redis，支持集群共享 |
| 传输形态 | HttpOnly Cookie 优先（Web）；原生可传裸 token 于 `Authorization`（无 Bearer） |
| Token 绑定 | 可选 IP 绑定、User-Agent 绑定 |
| 并发限制 | 可配置最大并发会话数 |
| 空闲超时 | 可配置空闲超时时间 |
| 有效期 | `token_ttl_seconds`（记住我）/ `token_ttl_short_seconds` |

---

## 登录安全

| 防护 | 机制 |
|---|---|
| 暴力破解 | 账号级和 IP 级登录失败计数，超过阈值临时锁定 |
| 密码加密 | RSA 公钥加密传输 |
| 验证码 | 登录/注册支持验证码校验 |
| 二次认证 | Admin TOTP / WebAuthn |
| 审计告警 | 异常时段登录、敏感操作、批量删除、IP 异常行为检测 |

---

## 审计

关键操作通过 `app.middleware.asgi_rest.OperationAuditMiddleware` 写入有界队列，持久化到 `sys_operation_audit_log`，溢出可落 `sys_operation_audit_outbox` / Redis spill：

- 写路径不阻塞请求；队满时降级到 outbox，而不是静默丢弃关键写操作
- Celery 定时任务（间隔取 `audit_alert.analysis_interval_seconds`）分析异常行为并生成审计告警
- 支持的告警规则：暴力破解、非常规时段操作、敏感操作、批量删除、IP 异常

---

## 账号类型隔离

| 维度 | 管理端 (ADMIN) | 门户端 (PORTAL) |
|---|---|---|
| 典型客户端 | Vue 3 管理端 / Admin Uniapp | React 门户 / 其他门户 API 客户端 |
| 登录入口 | `/api/v1/admin/login`（MFA：`/api/v1/admin/login/mfa`、`/api/v1/admin/auth/mfa/*`） | `/api/v1/portal/login` |
| 用户资料表 | `admin_user_profile` | `portal_user_profile` |
| 注册方式 | 不开放 HTTP 注册 | 可配置开放注册 |
| 功能范围 | 系统管理、IAM、业务管理 | 个人门户、消息、空间 |

两个端共享统一的账号表（`sys_account`），但通过 `account_type` 字段隔离，各自拥有独立的登录身份和会话上下文。`PORTAL` 面向门户 API 客户端（含 React 门户），与管理端路由和会话上下文分离。

---

## 字典待补

IAM 管理页已统一走字典工具，不写本地枚举。在字典管理中补充下列字典后页面会直接生效：

| 字典编码 | 用途 | 建议值 |
| --- | --- | --- |
| `ACCOUNT_TYPE` | 账号类型 | `ADMIN`、`PORTAL` |
| `ACCOUNT_STATUS` | 账号状态 | `ENABLED`、`DISABLED`、`CANCELLED` |
| `COMMON_STATUS` | 通用状态 | `ENABLED`、`DISABLED` |
| `DEPT_CATEGORY` | 部门分类 | 按业务补充 |
| `POSITION_CATEGORY` | 岗位分类 | 按业务补充 |
| `ROLE_CATEGORY` | 角色分类 | 按业务补充 |
| `ROLE_SCOPE_TYPE` | 角色数据范围 | `PLATFORM`、`DEPT` |
| `RESOURCE_TYPE` | 资源类型 | `CATALOG`、`MENU`、`PAGE`、`BUTTON`、`ACTION`、`API_GROUP` |

颜色建议统一使用十六进制颜色值。
