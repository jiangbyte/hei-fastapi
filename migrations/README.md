# 数据库迁移

Alembic 版本目录，只管理表结构。当前基线为单一初始迁移 `*_initial_schema.py`。

业务数据不在迁移里维护，见 `scripts/db/seed/`。

```bash
python scripts/db/makemigration.py "describe schema change"
python scripts/db/migrate.py
python scripts/db/check_migration.py
```

```bash
# 容器内执行迁移（需先构建镜像：docker build -t hei-fastapi .）
docker run --rm \
  -e DB__URL="postgresql+asyncpg://postgres:123456@host.docker.internal:5432/hei_fastapi" \
  -e REDIS__URL="redis://host.docker.internal:6379/0" \
  hei-fastapi migrate
```

连接串来自 `.env` 的 `DB__URL`。禁用模块的模型仍会进入 metadata，可正常生成与执行迁移。
