# 数据库种子数据

| 文件 | 说明 |
| --- | --- |
| `data.sql` | 从当前库导出的业务数据（`INSERT`，不含 `alembic_version`） |
| `tables.txt` | 导出时的表清单 |

## 导出

```bash
python scripts/db/export_data.py
```

## 导入（表结构需已 migrate）

```bash
python scripts/db/migrate.py
python scripts/db/import_data.py
```

`data.sql` 内使用 `session_replication_role = replica`，可绕过自引用外键顺序问题。
