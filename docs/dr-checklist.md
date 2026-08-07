# 灾备检查清单（发布前）

生产上线 / 大版本发布前勾选。细则见 [production.md](./production.md)「灾备与备份」。

## 备份与保留

- [ ] PostgreSQL：PITR / 持续归档（或云自动备份）；每日全量 + WAL；保留 ≥ 7 天
- [ ] Redis：RDB 或 AOF 已启用；监控重启后会话重建
- [ ] 对象存储：Local 卷备份，或 S3/OSS 版本控制 / 跨区域复制（按合规）

## 目标与演练

- [ ] RPO ≤ 15min、RTO ≤ 2h（内网中台建议值）已书面确认
- [ ] 最近一个季度内完成一次恢复演练并留档
- [ ] 演练步骤可复现：停写 → 隔离恢复 → `alembic upgrade head` → `/api/v1/internal/health/ready` + 登录冒烟 → 切流

## 会话 / TLS（与 DR 切流相关）

- [ ] `AUTH__SESSION_COOKIE_SECURE=true`（HTTPS 终结后）
- [ ] `AUTH__SESSION_IDLE_TIMEOUT_SECONDS=1800`（或组织约定值）
- [ ] 边缘 TLS / HSTS（`HSTS_HEADER`）已配置

## 演练证明

- 完成后将记录写入 [dr-drills/](./dr-drills/)（`YYYY-MM-DD-drill.md`）
- CI 校验最新 `drill_date` 时效（默认 120 天）

## CI 门禁

仓库通过 `scripts/ops/check_dr_docs.py` 校验清单、演练证明与关键文档锚点；**不替代**真实备份与演练。
