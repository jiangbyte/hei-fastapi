# Scripts

| 路径 | 用途 |
| --- | --- |
| `db.sql` | PostgreSQL 演示库全量重建（表结构 + 种子数据，对齐 hei-boot） |

```bash
# PostgreSQL 空库全量导入（演示 / 本地重建）
psql -U postgres -h 127.0.0.1 -d hei_fastapi -f scripts/db.sql
```

MySQL 与可移植建表请使用项目根目录 Alembic（见 `migrations/README.md`）：

```bash
# 设置 DB__URL 为 postgresql+asyncpg://... 或 mysql+aiomysql://...
alembic upgrade head
alembic revision --autogenerate -m "describe schema change"
```

应用启动（`entrypoint.sh`）不执行迁移或导入。
