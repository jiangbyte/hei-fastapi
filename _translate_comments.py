# -*- coding: utf-8 -*-
"""Apply Chinese translations to English comments/docstrings under app/modules."""
from __future__ import annotations

from pathlib import Path

ROOT = Path("app/modules")

# (relative_path, old, new) — apply longest strings first per file
REPLACEMENTS: list[tuple[str, str, str]] = [
    (
        'auth/mfa.py',
        'Admin TOTP MFA helpers and challenge store.',
        '管理端 TOTP MFA 辅助工具与 challenge 存储。',
    ),
    (
        'auth/mfa.py',
        'Return updated hash JSON if code matched, else None.',
        '验证码匹配时返回更新后的 hash JSON，否则返回 None。',
    ),
    (
        'auth/protection.py',
        'Redis-backed login throttling by account and client IP.',
        '基于 Redis 的登录限流，按账户与客户端 IP 统计。',
    ),
    (
        'auth/schema.py',
        '# Required when TOTP is enabled; optional for WebAuthn-only accounts (password suffices).',
        '# 启用 TOTP 时必填；仅 WebAuthn 账户可选（密码即可）。',
    ),
    (
        'auth/session_service.py',
        'Build and refresh account sessions without depending on auth workflows.',
        '构建并刷新账户会话，不依赖 auth 业务流程。',
    ),
    (
        'iam/account/password_helper.py',
        'Password management helper — strength validation, history recording,\nreuse checking, and expiry detection.\n\nUsed by ``AuthService`` and ``AccountService`` to enforce password policy.',
        '密码管理辅助工具 — 强度校验、历史记录、\n复用检查与过期检测。\n\n供 ``AuthService`` 与 ``AccountService`` 执行密码策略。',
    ),
    (
        'iam/account/password_helper.py',
        'Safely parse a datetime-or-None value to UTC-aware datetime.',
        '安全地将 datetime 或 None 解析为 UTC 时区的 datetime。',
    ),
    (
        'iam/account/password_helper.py',
        'Validate password strength, check history for reuse, then record.\n\n    Raises ``BusinessError`` on strength or reuse violations.\n    ',
        '校验密码强度、检查历史复用并记录。\n\n    强度或复用违规时抛出 ``BusinessError``。\n    ',
    ),
    (
        'iam/account/password_helper.py',
        'Check if the new password matches any of the recent history entries.',
        '检查新密码是否与最近历史记录中的任一密码相同。',
    ),
    (
        'iam/account/password_helper.py',
        'Return days since the last password change, or ``None`` if unknown.',
        '返回距上次改密的天数，未知时返回 ``None``。',
    ),
    (
        'iam/account/password_helper.py',
        "Check if the account's password is past the configured expiry period.",
        '检查账户密码是否已超过配置的过期期限。',
    ),
    (
        'iam/account/query_service.py',
        'Read-side account composition shared by IAM and user-center modules.',
        'IAM 与用户中心模块共用的账户读侧组装逻辑。',
    ),
    (
        'iam/permission/module.py',
        '# Permission helpers live in service.py; HTTP surface is under iam.resource.',
        '# 权限辅助逻辑在 service.py；HTTP 接口在 iam.resource 下。',
    ),
    (
        'message/announcement/router.py',
        'Register announcement routes for the current authenticated user.',
        '为当前已登录用户注册公告路由。',
    ),
    (
        'message/announcement/router.py',
        '# ==================== Admin CRUD ====================',
        '# ==================== 管理端 CRUD ====================',
    ),
    (
        'message/announcement/router.py',
        '# ==================== Admin Business Operations ====================',
        '# ==================== 管理端业务操作 ====================',
    ),
    (
        'message/announcement/router.py',
        '# ==================== Current-User Routes ====================',
        '# ==================== 当前用户路由 ====================',
    ),
    (
        'message/announcement/service.py',
        'Batch check which announcement ids are read for a given session.',
        '批量检查给定会话下哪些公告 ID 已读。',
    ),
    (
        'message/feedback/router.py',
        '# ==================== Admin CRUD ====================',
        '# ==================== 管理端 CRUD ====================',
    ),
    (
        'message/feedback/router.py',
        '# ==================== Portal Routes ====================',
        '# ==================== Portal 路由 ====================',
    ),
    (
        'message/notification/repository.py',
        'Return (items, total, read_id_set). Only PUBLISHED notifications matching the\n        target scope rules visible to the given account.',
        '返回 (items, total, read_id_set)。仅 PUBLISHED 且符合目标范围、对给定账户可见的通知。',
    ),
    (
        'message/notification/repository.py',
        'Count PUBLISHED notifications visible to the account minus already-read ones.',
        '统计账户可见的 PUBLISHED 通知数，减去已读。',
    ),
    (
        'message/notification/repository.py',
        'Batch insert read records, skip existing (unique constraint).',
        '批量插入已读记录，跳过已存在项（唯一约束）。',
    ),
    (
        'message/notification/repository.py',
        'Mark all PUBLISHED notifications visible to the account as read.',
        '将账户可见的全部 PUBLISHED 通知标记为已读。',
    ),
    (
        'message/notification/router.py',
        'Register notification routes for the currently logged-in user.',
        '为当前已登录用户注册通知路由。',
    ),
    (
        'message/notification/router.py',
        '# ── Admin routes ',
        '# ── 管理端路由 ',
    ),
    (
        'message/notification/router.py',
        '# ── Portal / current-user routes ',
        '# ── Portal / 当前用户路由 ',
    ),
    (
        'message/notification/service.py',
        'Set status=PUBLISHED and publish_at=now (only from DRAFT).',
        '设置 status=PUBLISHED 且 publish_at=now（仅从 DRAFT）。',
    ),
    (
        'message/notification/service.py',
        'Set status=REVOKED and revoked_at=now (only from PUBLISHED).',
        '设置 status=REVOKED 且 revoked_at=now（仅从 PUBLISHED）。',
    ),
    (
        'sys/codegen/apply.py',
        'Write codegen preview files into the workspace with low-invasion merges.',
        '将代码生成预览文件写入工作区，低侵入合并。',
    ),
    (
        'sys/codegen/apply.py',
        'Append codegen API export lines that are not already present.\n\n    Returns ``(new_text, changed)``.\n    ',
        '追加尚未存在的代码生成 API 导出行。\n\n    返回 ``(new_text, changed)``。\n    ',
    ),
    (
        'sys/codegen/apply.py',
        'Materialize preview files under ``root``.\n\n    ``*.index.ts.append`` (or ``web/admin/src/api/index.ts.append``) is merged\n    into ``web/admin/src/api/index.ts`` idempotently instead of being written\n    as a standalone file.\n    ',
        '在 ``root`` 下物化预览文件。\n\n    ``*.index.ts.append``（或 ``web/admin/src/api/index.ts.append``）幂等合并\n    到 ``web/admin/src/api/index.ts``，而非写入独立文件。\n    ',
    ),
    (
        'sys/codegen/apply.py',
        '# Keep non-export lines only when they introduce a new export below.',
        '# 仅当下方有新导出时保留非导出行。',
    ),
    (
        'sys/codegen/templates.py',
        '# Codegen emits Python/TS/Vue source, not HTML — autoescape would corrupt templates.',
        '# 代码生成输出 Python/TS/Vue 源码而非 HTML — autoescape 会破坏模板。',
    ),
    (
        'sys/config/storage_service.py',
        'Never return decrypted AK/SK to API clients.',
        '不向 API 客户端返回解密后的 AK/SK。',
    ),
    (
        'sys/dict/router.py',
        '# Depends(require_permission("sys:dict:tree")),',
        '# Depends(require_permission("sys:dict:tree")),',
    ),
    (
        'sys/file/service.py',
        'Validate file content magic bytes against declared content type.\n\n        Only checks content types that have known magic signatures in the\n        registry below.  Types that were explicitly allowed in the config\n        table (``upload_allowed_content_types``) but *lack* a registered\n        magic signature are silently skipped — this keeps the validator\n        compatible with custom / future types without false positives.\n        ',
        '校验文件内容 magic bytes 是否与声明的 content type 一致。\n\n        仅检查下方注册表中有已知 magic 签名的 content type。\n        配置表 (``upload_allowed_content_types``) 中明确允许但*无*注册\n        magic 签名的类型将静默跳过 — 以兼容自定义/未来类型并避免误报。\n        ',
    ),
    (
        'sys/file/service.py',
        '# Compensate: avoid orphan objects when metadata commit fails.',
        '# 补偿：元数据提交失败时避免孤立对象。',
    ),
    (
        'sys/file/service.py',
        '# Registry: (magic_prefix, content_type_prefix)',
        '# 注册表：(magic_prefix, content_type_prefix)',
    ),
    (
        'sys/file/tasks.py',
        'Periodic cleanup of local storage orphans (object without DB row).',
        '定期清理本地存储孤立对象（有对象无 DB 行）。',
    ),
    (
        'sys/file/tasks.py',
        'Delete local files older than min_age with no matching sys_file row.',
        '删除早于 min_age 且无对应 sys_file 行的本地文件。',
    ),
    (
        'user/utils/profile.py',
        'Fill created_name / updated_name on schema objects from admin/portal profiles.',
        '从 admin/portal profile 填充 schema 对象的 created_name / updated_name。',
    ),
    (
        '__init__.py',
        'Modules package.',
        '模块包。',
    ),
    (
        'auth/__init__.py',
        'Auth module.',
        '认证模块。',
    ),
    (
        'auth/webauthn_service.py',
        'WebAuthn helpers for Admin MFA.',
        '管理端 MFA 的 WebAuthn 辅助工具。',
    ),
    (
        'user/__init__.py',
        'User module.',
        '用户模块。',
    ),
    (
        'user/admin/__init__.py',
        'Admin user profile package.',
        '管理端用户资料包。',
    ),
    (
        'user/portal/__init__.py',
        'Portal user profile package.',
        'Portal 用户资料包。',
    ),
    (
        'sys/file/__init__.py',
        'File module.',
        '文件模块。',
    ),
    (
        'sys/file/portal/__init__.py',
        'Portal file routes.',
        'Portal 文件路由。',
    ),
    (
        'sys/dict/__init__.py',
        'System dictionary module.',
        '系统字典模块。',
    ),
    (
        'sys/config/__init__.py',
        'System config module.',
        '系统配置模块。',
    ),
    (
        'sys/codegen/__init__.py',
        'Code generation module.',
        '代码生成模块。',
    ),
    (
        'sys/banner/portal/__init__.py',
        'Portal display image routes.',
        'Portal 展示图路由。',
    ),
    (
        'sys/audit/__init__.py',
        'Operation audit module.',
        '操作审计模块。',
    ),
    (
        'sys/audit/tasks.py',
        'Audit analysis tasks.',
        '审计分析任务。',
    ),
    (
        'sys/audit/outbox.py',
        'Durable audit outbox for overflow / crash recovery.',
        '持久化审计发件箱，用于溢出/崩溃恢复。',
    ),
    (
        'sys/audit/analyzer.py',
        'Audit log analyzer — detects suspicious patterns and generates alerts.',
        '审计日志分析器 — 检测可疑模式并生成告警。',
    ),
    (
        'sys/audit/alert_model.py',
        'Alert history — records dispatched alerts for cooldown dedup.',
        '告警历史 — 记录已分发告警以供冷却去重。',
    ),
    (
        'sys/audit/alert.py',
        'Alert dispatcher — sends alerts via email and/or webhook with cooldown.',
        '告警分发器 — 通过邮件和/或 webhook 发送告警，含冷却。',
    ),
    (
        'iam/account/password_history.py',
        "Password change history — tracks password hash to prevent reuse and\ndrives密码到期提醒 (等保).\n\nThe latest entry per account is used as the canonical ``password_updated_at``\ntimestamp; accounts without any history fall back to the account row's\n``updated_at`` timestamp (carried from TimestampMixin).",
        '密码变更历史 — 记录密码 hash 以防复用，\n并驱动密码到期提醒（等保）。\n\n每账户最新一条作为 canonical ``password_updated_at`` 时间戳；\n无历史记录的账户回退到账户行的 ``updated_at``（来自 TimestampMixin）。',
    ),
    (
        'dashboard/__init__.py',
        'Admin dashboard package.',
        '管理端仪表盘包。',
    ),
    (
        'internal/__init__.py',
        'Internal modules.',
        '内部模块。',
    ),
    (
        'internal/health/__init__.py',
        'Internal health module.',
        '内部健康检查模块。',
    ),
]

def main() -> None:
    changed_files: set[str] = set()
    missing: list[tuple[str, str]] = []

    by_file: dict[str, list[tuple[str, str]]] = {}
    for rel, old, new in REPLACEMENTS:
        by_file.setdefault(rel, []).append((old, new))

    for rel, pairs in by_file.items():
        path = ROOT / rel
        if not path.exists():
            for old, _ in pairs:
                missing.append((rel, old[:60]))
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in sorted(pairs, key=lambda x: len(x[0]), reverse=True):
            if old not in text:
                missing.append((rel, old[:80]))
                continue
            text = text.replace(old, new, 1)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed_files.add(rel)

    print(f"Changed files: {len(changed_files)}")
    for f in sorted(changed_files):
        print(f"  {f}")
    if missing:
        print(f"\nMissing ({len(missing)}):")
        for rel, snippet in missing[:30]:
            print(f"  {rel}: {snippet!r}")
        if len(missing) > 30:
            print(f"  ... and {len(missing) - 30} more")


if __name__ == "__main__":
    main()
