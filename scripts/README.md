# Scripts

| 路径 | 用途 |
| --- | --- |
| `db.sql` | 演示库全量重建（表结构 + 种子数据，对齐 hei-boot） |

```bash
# 空库全量导入（演示 / 本地重建）
psql -U postgres -h 127.0.0.1 -d hei_fastapi -f scripts/db.sql
```

增量 schema 变更使用项目根目录 Alembic（见 `migrations/README.md`）：

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe schema change"
```

应用启动（`entrypoint.sh`）不执行迁移或导入。
