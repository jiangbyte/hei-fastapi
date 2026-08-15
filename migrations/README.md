# 数据库迁移

Alembic 版本目录，只管理表结构。当前基线为单一初始迁移 `*_initial_schema.py`。

业务数据不在迁移里维护，见 `scripts/db/seed/`。

```bash
python scripts/db/makemigration.py "describe schema change"
python scripts/db/migrate.py
python scripts/db/check_migration.py
```

连接串来自 `.env` 的 `DB__URL`。

> 数据库表结构由人工维护：应用启动（`entrypoint.sh`）不会执行迁移，以上命令仅在维护机手动执行。禁用模块的模型仍会进入 metadata，可正常生成与执行迁移。
