# Design: `sys_iam_relation.account_type`

Date: 2026-08-08  
Status: approved (conversation) — pending implementation plan

## Goal

所有 IAM 关系行必填 `account_type`（`ADMIN` / `PORTAL`），使角色、用户组、部门、资源授权可按账户类型分套管理与解析，避免 ADMIN / PORTAL 混用同一关系集合。

## Decisions

| 项 | 选择 |
| --- | --- |
| 范围 | 全部关系类型必填（含 `GROUP_ROLE`、资源/权限授权） |
| 方案 | 单列 + 唯一约束包含 `account_type` |
| 存量非账号关系回填 | 默认 `ADMIN` |
| 改账号类型时迁移关系 | 不做（后续若需要另开需求） |

## Data model

表：`sys_iam_relation`

- 新增列：`account_type` `String(32)`，非空，注释「账户类型」
- 取值：与 `AccountType` 枚举一致（当前 `ADMIN`、`PORTAL`）
- 唯一约束（替换原约束）：  
  `(subject_type, subject_id, relation_type, target_type, target_id, target_key, account_type)`
- 建议索引：`(account_type, relation_type)`

## Migration

1. 增加可空列 `account_type`
2. 回填：
   - 主体或目标为 `ACCOUNT` 的行：从 `sys_account.account_type` 按账号 ID 回填
   - 其余行：`ADMIN`
3. 将列改为非空
4. 删除旧唯一约束，创建带 `account_type` 的新唯一约束
5. 创建建议索引

若回填后仍有空值（孤立账号 ID），迁移应失败并暴露数据问题，不静默填默认（账号侧必须能解析到账户）。

## Write path

工厂方法（`IamRelationRepository.account_role` / `account_group` / `account_dept` / `group_role` / `subject_resource_grant` 等）一律接收并写入 `account_type`。

规则：

- **账号成员关系**（`ACCOUNT_ROLE` / `ACCOUNT_GROUP` / `ACCOUNT_DEPT`）：`account_type` 必须等于该账号的 `sys_account.account_type`；服务层从账号加载后写入，前端可不传；不一致则业务错误
- **组角色、主体资源/权限授权**：调用方显式传入 `account_type`
- **删除**：`delete_subject_relations*` 在替换授权场景须带 `account_type`（或等价过滤），避免删掉另一账户类型下的关系

## Read / authorization path

- `get_account_authorization` 及内部角色/组/部门/权限聚合：只使用 `relation.account_type == account.account_type` 的行
- 经组间接得到的角色：`ACCOUNT_GROUP` 与 `GROUP_ROLE` 均须匹配同一 `account_type`
- 管理端 `own_*`：返回的已授权列表按上下文账户类型过滤；左侧候选分页保持现有 `page` API，授权写入时带类型

## API / admin UI (minimal)

- 账号侧 grant：后端从账号推导 `account_type`，请求体可不增加字段
- 组授角色、角色/组授资源等：请求增加 `account_type`（或 query）；管理端从当前 Tab / 选择器传入
- 前端：角色、用户组相关授权抽屉增加账户类型（与账号管理 `ADMIN` / `PORTAL` Tab 一致）；账号授权抽屉用当前账号类型即可

## Out of scope

- 不拆分关系表
- 不改变 `sys_account.account_type` 含义
- 不做账号改类型时的关系自动迁移
- 不扩展 `MERCHANT` / `CONSUMER`（枚举预留即可，无额外种子要求）

## Verification

- 迁移后：无空 `account_type`；唯一约束含该列
- 新建 ADMIN 账号授权角色后，PORTAL 会话鉴权看不到该关系
- 同一 `group_id + role_id` 可分别存在 ADMIN / PORTAL 两行
- 账号 grant 时伪造错误 `account_type` 被拒绝（若 API 接受该字段）或强制覆盖为账号真实类型
- 现有账号授权 / 组授角色主路径手动冒烟通过

## Non-goals for first PR

- 大规模重构前端 IAM 列表布局（仅加类型入参与必要筛选）
- 历史审计日志改写
