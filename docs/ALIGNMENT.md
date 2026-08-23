# hei-fastapi ↔ hei-boot 模块对齐看板

以 **hei-boot** 为 API/数据模型真源；验收工具与 hei-gin 共用 [alignment-status.json](../hei-gin/docs/alignment-status.json)。

## 数据库（MySQL 主库）

| 库 | 用途 |
|----|------|
| `hei_boot` | Boot 活库（真源） |
| `hei_fastapi` | FastAPI 对齐库（`copy-hei-boot-db-mysql.sh hei_fastapi`） |
| `hei_gin` | Gin 对齐库 |

默认连接：`mysql+aiomysql://root:123456@127.0.0.1:3306/hei_fastapi`（见 `.env.example`）

PostgreSQL 仅用于 `scripts/run_dialect_e2e.py` 方言回归。

## 验收命令

```bash
# OpenAPI 契约（field diff = 0 为通过）
python scripts/e2e/boot_contract_full_diff.py --output scripts/e2e/reports/boot_fastapi_full_diff.json

# 运行时 GET JSON（先以 E2E_DISABLE_RATE_LIMIT=1 启动 FastAPI）
E2E_DISABLE_RATE_LIMIT=1 python scripts/e2e/boot_fastapi_runtime_diff.py --module sys/audit

# CRUD
python scripts/e2e/crud.py
```

## 模块状态

见 `hei-gin/docs/alignment-status.json`（双栈同步维护）。
