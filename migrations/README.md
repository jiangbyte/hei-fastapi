# 数据库迁移

Alembic 版本目录，只管理表结构。当前基线为单一初始迁移 `*_initial_schema.py`。

业务数据不在迁移里维护，见 `scripts/db/seed/`。

```bash
python scripts/db/makemigration.py "describe schema change"
python scripts/db/migrate.py
python scripts/db/check_migration.py
```

```bash
docker compose run --rm hei migrate
```

连接串来自 `.env` 的 `DB__URL`。禁用模块的模型仍会进入 metadata，可正常生成与执行迁移。
