# Scripts

| 路径 | 用途 |
| --- | --- |
| `db/migrate.py` | 执行 Alembic 升级 |
| `db/makemigration.py` | 生成迁移 |
| `db/check_migration.py` | 检查迁移与模型一致性 |
| `db/export_data.py` | 导出业务数据到 `db/seed/data.sql` |
| `db/import_data.py` | 导入 `db/seed/data.sql` |
| `db/seed/` | 数据种子（见其中 README） |
| `docker/` | 本地 SnailJob Server 编排（compose + psql 初始化/种子脚本） |
| `sql/postgres/snailjob/` | SnailJob 数据库 schema（上游 SQL）与 hei-fastapi 种子 |

```bash
python scripts/db/migrate.py
python scripts/db/makemigration.py "describe schema change"
python scripts/db/check_migration.py
python scripts/db/export_data.py
python scripts/db/import_data.py

./scripts/docker/snailjob-init.sh
docker compose -f scripts/docker/docker-compose.snailjob.yml up -d
```

`./entrypoint.sh migrate` 会调用 `python scripts/db/migrate.py`，`seed` 调用 `python scripts/db/import_data.py`。
