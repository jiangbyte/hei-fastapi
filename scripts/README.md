# Scripts

脚本按用途分目录，避免根目录平铺。

| 目录 | 用途 |
| --- | --- |
| `db/` | Alembic 迁移执行、生成、结构检查；bootstrap SQL 导出 / 加载 |
| `seed/` | 初始化超管、资源菜单等必要业务数据（与 bootstrap 并存） |
| `ops/` | 运维、压测、验收辅助脚本 |
| `sql/` | bootstrap 数据 SQL、历史备份 SQL |
| `codegen/` | 代码生成写盘 / 测试模块再生；`ddl_tests/` 为 DDL 样例 |

## 常用命令

```bash
python scripts/db/migrate.py
python scripts/db/makemigration.py "describe schema change"
python scripts/db/check_migration.py

# 字典 / 配置（脱敏）/ 存储配置：迁移后加载基线数据
python scripts/db/load_bootstrap_sql.py
# 从当前库重新导出（敏感项会脱敏）
python scripts/db/export_bootstrap_sql.py

# 超管与资源菜单（独立于 bootstrap）
python scripts/seed/seed_super_admin.py

python scripts/ops/loadtest_http.py --base-url http://127.0.0.1:8000 --path / --requests 1000 --concurrency 50

# DR 文档门禁（CI 也会跑）
python scripts/ops/check_dr_docs.py

# owner_dept 历史回填（迁移之外的运维补跑）
python scripts/ops/backfill_owner_dept.py

# 代码生成：将方案预览落到仓库（幂等合并 api/index.ts；不改 routes.static.ts）
python scripts/codegen/apply_plan.py --plan-id <plan_id>
# 本地 cg_test_* 测试模块按模板再生（enabled=False）
python scripts/codegen/regen_cg_test_modules.py
```

## Bootstrap 与 seed 并存

两者职责不同，推荐顺序：

1. `python scripts/db/migrate.py` — 建表
2. `python scripts/db/load_bootstrap_sql.py` — 加载字典 / `sys_config`（脱敏）/ `sys_storage_config`（密钥置空）
3. `python scripts/seed/seed_super_admin.py` — 创建超管、补齐资源菜单等

`load_bootstrap_sql.py` 按顺序应用：

- `scripts/sql/sys_dict.sql`
- `scripts/sql/sys_config.sql`（敏感项已置空）
- `scripts/sql/sys_storage_config.sql`（`access_key` / `secret_key` 已置空）
