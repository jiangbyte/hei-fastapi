-- Author: Charlie
-- 个人工作台按钮权限绑定（RESOURCE -> PERMISSION）
BEGIN;

INSERT INTO sys_iam_relation (
  id, subject_type, subject_id, account_type, relation_type, target_type, target_id, target_key,
  grant_mode, effect, data_scope, custom_scope_dept_ids, is_primary, sort, status, description, extra
)
VALUES
  ('202311', 'RESOURCE', '202301', 'ADMIN', 'RESOURCE_PERMISSION', 'PERMISSION', '', 'workbench:shortcut:page', 'CASCADE', 'ALLOW', 'ALL', '[]', false, 10, 'ENABLED', '查看快捷入口', '{}'),
  ('202312', 'RESOURCE', '202302', 'ADMIN', 'RESOURCE_PERMISSION', 'PERMISSION', '', 'workbench:shortcut:create', 'CASCADE', 'ALLOW', 'ALL', '[]', false, 20, 'ENABLED', '添加快捷入口', '{}'),
  ('202313', 'RESOURCE', '202303', 'ADMIN', 'RESOURCE_PERMISSION', 'PERMISSION', '', 'workbench:shortcut:update', 'CASCADE', 'ALLOW', 'ALL', '[]', false, 30, 'ENABLED', '排序快捷入口', '{}'),
  ('202314', 'RESOURCE', '202304', 'ADMIN', 'RESOURCE_PERMISSION', 'PERMISSION', '', 'workbench:shortcut:delete', 'CASCADE', 'ALLOW', 'ALL', '[]', false, 40, 'ENABLED', '删除快捷入口', '{}')
ON CONFLICT (id)
DO UPDATE SET
  account_type = EXCLUDED.account_type,
  target_key = EXCLUDED.target_key,
  description = EXCLUDED.description,
  updated_at = now();

COMMIT;
