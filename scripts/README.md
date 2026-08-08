# Scripts

| 路径 | 用途 |
| --- | --- |
| `db/migrate.py` | 执行 Alembic 升级 |
| `db/makemigration.py` | 生成迁移 |
| `db/check_migration.py` | 检查迁移与模型一致性 |

```bash
python scripts/db/migrate.py
python scripts/db/makemigration.py "describe schema change"
python scripts/db/check_migration.py
```

`./entrypoint.sh migrate` 会调用 `python scripts/db/migrate.py`。
