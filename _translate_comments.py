# -*- coding: utf-8 -*-
"""Apply Chinese translations to English comments/docstrings under app/modules."""
from __future__ import annotations

from pathlib import Path

ROOT = Path("app/modules")

# (relative_path, old, new) — apply longest strings first per file
REPLACEMENTS: list[tuple[str, str, str]] = [
    # ── auth ──
    (
        "auth/mfa.py",
        """Admin TOTP MFA helpers and challenge store.""",
        """管理端 TOTP MFA 辅助工具与 challenge 存储。""",
    ),
    (
        "auth/mfa.py",
        """Return updated hash JSON if code matched, else None.""",
        """验证码匹配时返回更新后的 hash JSON，否则返回 None。""",
    ),
    (
        "auth/protection.py",
        """Redis-backed login throttling by account and client IP.""",
        """基于 Redis 的登录限流，按账户与客户端 IP 统计。""",
    ),
    (
        "auth/schema.py",
        "# Required when TOTP is enabled; optional for WebAuthn-only accounts (password suffices).",
        "# 启用 TOTP 时必填；仅 WebAuthn 账户可选（密码即可）。",
    ),
    (
        "auth/session_service.py",
        """Build and refresh account sessions without depending on auth workflows.""",
        """构建并刷新账户会话，不依赖 auth 业务流程。""",
    ),
    # ── iam ──
    (
        "iam/account/password_helper.py",
        """Password management helper — strength validation, history recording,
reuse checking, and expiry detection.

Used by ``AuthService`` and ``AccountService`` to enforce password policy.""",
        """密码管理辅助工具 — 强度校验、历史记录、
复用检查与过期检测。

供 ``AuthService`` 与 ``AccountService`` 执行密码策略。""",
    ),
    (
        "iam/account/password_helper.py",
        """Safely parse a datetime-or-None value to UTC-aware datetime.""",
        """安全地将 datetime 或 None 解析为 UTC 时区的 datetime。""",
    ),
    (
        "iam/account/password_helper.py",
        """Validate password strength, check history for reuse, then record.

    Raises ``BusinessError`` on strength or reuse violations.
    """,
        """校验密码强度、检查历史复用并记录。

    强度或复用违规时抛出 ``BusinessError``。
    """,
    ),
    (
        "iam/account/password_helper.py",
        """Check if the new password matches any of the recent history entries.""",
        """检查新密码是否与最近历史记录中的任一密码相同。""",
    ),
    (
        "iam/account/password_helper.py",
        """Return days since the last password change, or ``None`` if unknown.""",
        """返回距上次改密的天数，未知时返回 ``None``。""",
    ),
    (
        "iam/account/password_helper.py",
        """Check if the account's password is past the configured expiry period.""",
        """检查账户密码是否已超过配置的过期期限。""",
    ),
    (
        "iam/account/query_service.py",
        """Read-side account composition shared by IAM and user-center modules.""",
        """IAM 与用户中心模块共用的账户读侧组装逻辑。""",
    ),
    (
        "iam/permission/module.py",
        "# Permission helpers live in service.py; HTTP surface is under iam.resource.",
        "# 权限辅助逻辑在 service.py；HTTP 接口在 iam.resource 下。",
    ),
    # ── message/announcement ──
    (
        "message/announcement/router.py",
        """Register announcement routes for the current authenticated user.""",
        """为当前已登录用户注册公告路由。""",
    ),
    (
        "message/announcement/router.py",
        "# ==================== Admin CRUD ====================",
        "# ==================== 管理端 CRUD ====================",
    ),
    (
        "message/announcement/router.py",
        "# ==================== Admin Business Operations ====================",
        "# ==================== 管理端业务操作 ====================",
    ),
    (
        "message/announcement/router.py",
        "# ==================== Current-User Routes ====================",
        "# ==================== 当前用户路由 ====================",
    ),
    (
        "message/announcement/service.py",
        """Batch check which announcement ids are read for a given session.""",
        """批量检查给定会话下哪些公告 ID 已读。""",
    ),
    # ── message/conversation ──
    (
        "message/conversation/repository.py",
        """Find an existing DIRECT conversation between two users.""",
        """查找两位用户之间已存在的 DIRECT 会话。""",
    ),
    (
        "message/conversation/repository.py",
        """List conversations for a user, ordered by last_message_at DESC, pinned first.""",
        """列出用户的会话，按 last_message_at 降序，置顶优先。""",
    ),
    (
        "message/conversation/repository.py",
        """Soft-delete a conversation member by setting left_at.""",
        """通过设置 left_at 软删除会话成员。""",
    ),
    (
        "message/conversation/repository.py",
        "# ── Generated CRUD ",
        "# ── 生成的 CRUD ",
    ),
    (
        "message/conversation/repository.py",
        "# ── Conversation queries ",
        "# ── 会话查询 ",
    ),
    (
        "message/conversation/repository.py",
        "# Subquery: conversations that have both participants",
        "# 子查询：包含双方参与者的会话",
    ),
    (
        "message/conversation/repository.py",
        "# Count total",
        "# 统计总数",
    ),
    (
        "message/conversation/repository.py",
        "# ── Member management ",
        "# ── 成员管理 ",
    ),
    (
        "message/conversation/repository.py",
        "# ── Message tracking ",
        "# ── 消息追踪 ",
    ),
    (
        "message/conversation/repository.py",
        "# ── Preferences ",
        "# ── 偏好设置 ",
    ),
    (
        "message/conversation/router.py",
        "# ── Portal / current-user routes ",
        "# ── Portal / 当前用户路由 ",
    ),
    (
        "message/conversation/service.py",
        "# ── Preferences ",
        "# ── 偏好设置 ",
    ),
    (
        "message/conversation/service.py",
        "# ── Member actions ",
        "# ── 成员操作 ",
    ),
    # ── message/feedback ──
    (
        "message/feedback/router.py",
        "# ==================== Admin CRUD ====================",
        "# ==================== 管理端 CRUD ====================",
    ),
    (
        "message/feedback/router.py",
        "# ==================== Portal Routes ====================",
        "# ==================== Portal 路由 ====================",
    ),
    # ── message/friend ──
    (
        "message/friend/repository.py",
        "# ── Friendship queries ",
        "# ── 好友关系查询 ",
    ),
    (
        "message/friend/repository.py",
        "# ── Friend Request queries ",
        "# ── 好友申请查询 ",
    ),
    (
        "message/friend/router.py",
        "# ── Current-user routes (admin + portal) ",
        "# ── 当前用户路由（admin + portal） ",
    ),
    (
        "message/friend/schema.py",
        "# ── MsgFriend (legacy codegen) ",
        "# ── MsgFriend（旧版代码生成） ",
    ),
    (
        "message/friend/schema.py",
        "# ── Friend Request ",
        "# ── 好友申请 ",
    ),
    (
        "message/friend/service.py",
        "# ── Apply friend request ",
        "# ── 发起好友申请 ",
    ),
    (
        "message/friend/service.py",
        "# ── Handle friend request ",
        "# ── 处理好友申请 ",
    ),
    (
        "message/friend/service.py",
        "# ── Remove friend ",
        "# ── 删除好友 ",
    ),
    (
        "message/friend/service.py",
        "# ── My friends ",
        "# ── 我的好友 ",
    ),
    (
        "message/friend/service.py",
        "# ── Search users ",
        "# ── 搜索用户 ",
    ),
    (
        "message/friend/service.py",
        "# ── Set remark ",
        "# ── 设置备注 ",
    ),
    (
        "message/friend/service.py",
        "# ── My requests ",
        "# ── 我的申请 ",
    ),
    (
        "message/friend/service.py",
        "# ── My request count ",
        "# ── 我的申请数量 ",
    ),
    # ── message/group/repository ──
    (
        "message/group/repository.py",
        """Search groups by name keyword, excluding dissolved groups and given group IDs.""",
        """按名称关键词搜索群组，排除已解散群组及指定群组 ID。""",
    ),
    (
        "message/group/repository.py",
        """List groups the current user belongs to (active groups only, member not left).""",
        """列出当前用户所属群组（仅活跃群组，成员未退出）。""",
    ),
    (
        "message/group/repository.py",
        """Add a single member to the group. Returns the member entity.""",
        """向群组添加单个成员，返回成员实体。""",
    ),
    (
        "message/group/repository.py",
        """Batch add members to the group.""",
        """批量向群组添加成员。""",
    ),
    (
        "message/group/repository.py",
        """Get active member (not left).""",
        """获取活跃成员（未退出）。""",
    ),
    (
        "message/group/repository.py",
        """List active members ordered by role DESC (OWNER > ADMIN > MEMBER).""",
        """列出活跃成员，按角色降序（OWNER > ADMIN > MEMBER）。""",
    ),
    (
        "message/group/repository.py",
        """Batch count active members for given group IDs.""",
        """批量统计指定群组的活跃成员数。""",
    ),
    (
        "message/group/repository.py",
        """Soft-delete member by setting left_at.""",
        """通过设置 left_at 软删除成员。""",
    ),
    (
        "message/group/repository.py",
        """Update a member's role.""",
        """更新成员角色。""",
    ),
    (
        "message/group/repository.py",
        """Increment group's member_count.""",
        """递增群组的 member_count。""",
    ),
    (
        "message/group/repository.py",
        """Decrement group's member_count by 1.""",
        """递减群组的 member_count（减 1）。""",
    ),
    (
        "message/group/repository.py",
        """Check if the user is the group owner or an admin member.""",
        """检查用户是否为群主或管理员成员。""",
    ),
    (
        "message/group/repository.py",
        """Check if the user is the group owner.""",
        """检查用户是否为群主。""",
    ),
    (
        "message/group/repository.py",
        """Get a pending join request (not yet handled).""",
        """获取待处理的入群申请（尚未处理）。""",
    ),
    (
        "message/group/repository.py",
        """Get latest join request for applicant+group regardless of status.""",
        """获取申请人在指定群组的最新入群申请（不限状态）。""",
    ),
    (
        "message/group/repository.py",
        """Create a new group join request.""",
        """创建新的入群申请。""",
    ),
    (
        "message/group/repository.py",
        """List all pending join requests for the given group IDs.""",
        """列出指定群组的所有待处理入群申请。""",
    ),
    (
        "message/group/repository.py",
        """List all join requests from a specific applicant.""",
        """列出指定申请人的所有入群申请。""",
    ),
    (
        "message/group/repository.py",
        """Batch count pending join requests for given group IDs.""",
        """批量统计指定群组的待处理入群申请数。""",
    ),
    (
        "message/group/repository.py",
        """Update group fields with provided kwargs. Returns the updated entity.""",
        """用给定 kwargs 更新群组字段，返回更新后的实体。""",
    ),
    (
        "message/group/repository.py",
        "# ==================== MsgGroup CRUD ====================",
        "# ==================== MsgGroup CRUD ====================",
    ),
    (
        "message/group/repository.py",
        "# ==================== Group Search ====================",
        "# ==================== 群组搜索 ====================",
    ),
    (
        "message/group/repository.py",
        "# ==================== Group Membership ====================",
        "# ==================== 群组成员 ====================",
    ),
    (
        "message/group/repository.py",
        "# ==================== Group Join Requests ====================",
        "# ==================== 入群申请 ====================",
    ),
    (
        "message/group/repository.py",
        "# ==================== Group Update Helper ====================",
        "# ==================== 群组更新辅助 ====================",
    ),
    # ── message/group/router & schema ──
    (
        "message/group/router.py",
        """Register group routes for the current authenticated user.""",
        """为当前已登录用户注册群组路由。""",
    ),
    (
        "message/group/router.py",
        "# ==================== Current-User Routes ====================",
        "# ==================== 当前用户路由 ====================",
    ),
    (
        "message/group/router.py",
        "# ==================== Members ====================",
        "# ==================== 成员 ====================",
    ),
    (
        "message/group/router.py",
        "# ==================== Join Requests ====================",
        "# ==================== 入群申请 ====================",
    ),
    (
        "message/group/schema.py",
        "# ==================== Group Create (current-user) ====================",
        "# ==================== 创建群组（当前用户） ====================",
    ),
    (
        "message/group/schema.py",
        "# ==================== Group Member ====================",
        "# ==================== 群组成员 ====================",
    ),
    (
        "message/group/schema.py",
        "# ==================== Group Join Request ====================",
        "# ==================== 入群申请 ====================",
    ),
    # ── message/group/service ──
    (
        "message/group/service.py",
        """Create a group: create MsgGroup + add owner as member + auto-create conversation.""",
        """创建群组：创建 MsgGroup + 添加群主为成员 + 自动创建会话。""",
    ),
    (
        "message/group/service.py",
        """Update group info. Only the owner can update.""",
        """更新群组信息，仅群主可操作。""",
    ),
    (
        "message/group/service.py",
        """Dissolve a group. Only the owner can dissolve.""",
        """解散群组，仅群主可操作。""",
    ),
    (
        "message/group/service.py",
        """Leave a group. The owner cannot leave.""",
        """退出群组，群主不可退出。""",
    ),
    (
        "message/group/service.py",
        """List my groups with member_count and pending request count.""",
        """列出我的群组，含 member_count 与待处理申请数。""",
    ),
    (
        "message/group/service.py",
        """Search groups by name; mark membership / pending apply for UI states.""",
        """按名称搜索群组；标记成员关系/待申请状态供 UI 展示。""",
    ),
    (
        "message/group/service.py",
        """Get group detail. Verifies the user is a member.""",
        """获取群组详情，校验用户是否为成员。""",
    ),
    (
        "message/group/service.py",
        """List group members with profile info (name/avatar). Batch load profiles.""",
        """列出群成员及资料（姓名/头像），批量加载 profile。""",
    ),
    (
        "message/group/service.py",
        """Add members to a group. Only owner/admin can do this.""",
        """向群组添加成员，仅群主/管理员可操作。""",
    ),
    (
        "message/group/service.py",
        """Remove a member from a group. Only owner/admin can do this.""",
        """从群组移除成员，仅群主/管理员可操作。""",
    ),
    (
        "message/group/service.py",
        """Set a member's role. Only owner can change roles.""",
        """设置成员角色，仅群主可变更。""",
    ),
    (
        "message/group/service.py",
        """Handle a join request (accept/reject). Only owner/admin can handle.""",
        """处理入群申请（同意/拒绝），仅群主/管理员可操作。""",
    ),
    (
        "message/group/service.py",
        """Push a new join request notification to group owners/admins via IM.""",
        """通过 IM 向群主/管理员推送新入群申请通知。""",
    ),
    (
        "message/group/service.py",
        """List my join requests with profile and group info.""",
        """列出我的入群申请，含 profile 与群组信息。""",
    ),
    (
        "message/group/service.py",
        """List pending join requests for groups I own/admin.""",
        """列出我管理群组的待处理入群申请。""",
    ),
    (
        "message/group/service.py",
        """Get count of pending join requests for groups I manage.""",
        """获取我管理群组的待处理入群申请数量。""",
    ),
    (
        "message/group/service.py",
        """Enrich join requests with applicant name/avatar and group name (batch).""",
        """批量填充入群申请的申请人姓名/头像及群组名称。""",
    ),
    (
        "message/group/service.py",
        """Create a conversation for the group and add the creator as a member.""",
        """为群组创建会话并将创建者添加为成员。""",
    ),
    (
        "message/group/service.py",
        """Get the active group conversation for a group, or None.""",
        """获取群组的活跃会话，无则返回 None。""",
    ),
    (
        "message/group/service.py",
        """Add a user to the group's active conversation if not already a member.""",
        """若尚未是会话成员，将用户加入群组的活跃会话。""",
    ),
    (
        "message/group/service.py",
        """Remove a user from the group's conversation (soft-delete via left_at).""",
        """将会话成员移出群组会话（通过 left_at 软删除）。""",
    ),
    (
        "message/group/service.py",
        """Mark the group's conversation as disabled.""",
        """将群组会话标记为已禁用。""",
    ),
    (
        "message/group/service.py",
        "# ==================== Admin CRUD ====================",
        "# ==================== 管理端 CRUD ====================",
    ),
    (
        "message/group/service.py",
        "# ==================== Current-User Group Management ====================",
        "# ==================== 当前用户群组管理 ====================",
    ),
    (
        "message/group/service.py",
        "# Add owner as member",
        "# 添加群主为成员",
    ),
    (
        "message/group/service.py",
        "# Auto-create conversation",
        "# 自动创建会话",
    ),
    (
        "message/group/service.py",
        "# Mark conversation as disabled",
        "# 将会话标记为已禁用",
    ),
    (
        "message/group/service.py",
        "# ==================== Group Members ====================",
        "# ==================== 群组成员 ====================",
    ),
    (
        "message/group/service.py",
        "# Also add members to the conversation",
        "# 同时将成员加入会话",
    ),
    (
        "message/group/service.py",
        "# Cannot remove the group owner",
        "# 不可移除群主",
    ),
    (
        "message/group/service.py",
        "# ==================== Group Join Requests ====================",
        "# ==================== 入群申请 ====================",
    ),
    (
        "message/group/service.py",
        "# Check if already a member",
        "# 检查是否已是成员",
    ),
    (
        "message/group/service.py",
        "# Also add to conversation",
        "# 同时加入会话",
    ),
    (
        "message/group/service.py",
        "# Push IM notification to applicant about the result",
        "# 通过 IM 向申请人推送处理结果通知",
    ),
    (
        "message/group/service.py",
        "# Also include groups where I am admin",
        "# 同时包含我担任管理员的群组",
    ),
    (
        "message/group/service.py",
        "# ==================== Private Helpers ====================",
        "# ==================== 私有辅助 ====================",
    ),
    (
        "message/group/service.py",
        "# Add the group creator as a conversation member",
        "# 将群组创建者添加为会话成员",
    ),
    # ── message/im ──
    (
        "message/im/__init__.py",
        """IM dual-channel realtime gateway (WebSocket Binary + TCP).""",
        """IM 双通道实时网关（WebSocket Binary + TCP）。""",
    ),
    (
        "message/im/ack.py",
        """Outbound ACK window with limited retries then offline fallback.""",
        """出站 ACK 窗口，有限重试后回退至离线。""",
    ),
    (
        "message/im/ack.py",
        """Track unacked PUSH seqs per session; retry then invoke offline callback.""",
        """按会话追踪未 ACK 的 PUSH seq；重试后调用离线回调。""",
    ),
    (
        "message/im/ack.py",
        "# Drop oldest if window exceeded",
        "# 超出窗口时丢弃最旧项",
    ),
    (
        "message/im/ack.py",
        "# Cumulative ACK: drop all seq <= ack_seq",
        "# 累积 ACK：丢弃所有 seq <= ack_seq",
    ),
    (
        "message/im/auth.py",
        """IM short-lived AUTH tickets (Redis).""",
        """IM 短时 AUTH 票据（Redis）。""",
    ),
    (
        "message/im/auth.py",
        """Mint a one-shot IM AUTH ticket. Returns (ticket, ttl_seconds).""",
        """签发一次性 IM AUTH 票据，返回 (ticket, ttl_seconds)。""",
    ),
    (
        "message/im/auth.py",
        """Validate session token or IM ticket; return (account_type, account_id).""",
        """校验 session token 或 IM 票据，返回 (account_type, account_id)。""",
    ),
    (
        "message/im/auth.py",
        "# GETDEL when available; else GET + DELETE.",
        "# 可用时使用 GETDEL，否则 GET + DELETE。",
    ),
    (
        "message/im/http_router.py",
        """HTTP endpoints for IM gateway helpers (ticket minting).""",
        """IM 网关辅助 HTTP 接口（票据签发）。""",
    ),
    (
        "message/im/http_router.py",
        """Issue a short-lived one-shot ticket for IM AUTH frames.""",
        """签发用于 IM AUTH 帧的短时一次性票据。""",
    ),
    (
        "message/im/protocol.py",
        """IM binary protocol: frame layout, cmd and push-event enums.""",
        """IM 二进制协议：帧布局、cmd 与 push-event 枚举。""",
    ),
    (
        "message/im/protocol.py",
        """Return (cmd, flags, seq, ack, body_len, total_frame_len) or None if incomplete.""",
        """返回 (cmd, flags, seq, ack, body_len, total_frame_len)，不完整时返回 None。""",
    ),
    (
        "message/im/protocol.py",
        """Accumulate TCP bytes and yield complete frames.""",
        """累积 TCP 字节并产出完整帧。""",
    ),
    (
        "message/im/protocol.py",
        "# Allow exact frame only for WS; TCP stream uses try_parse + slice",
        "# WS 仅允许精确帧；TCP 流使用 try_parse + slice",
    ),
    (
        "message/im/registry.py",
        """Session registry + Redis online/pubsub routing.""",
        """会话注册表 + Redis 在线/pubsub 路由。""",
    ),
    (
        "message/im/registry.py",
        """Process-local sessions with Redis presence and per-user pub/sub.""",
        """进程内会话，Redis 在线状态与按用户 pub/sub。""",
    ),
    (
        "message/im/registry.py",
        """Register session; returns kicked previous session on same terminal if any.""",
        """注册会话；同终端若有旧会话则返回被踢出的会话。""",
    ),
    (
        "message/im/registry.py",
        "# channel -> account_id -> terminal_id -> SessionContext",
        "# channel -> account_id -> terminal_id -> SessionContext",
    ),
    (
        "message/im/registry.py",
        "# im:user:{type}:{id}",
        "# im:user:{type}:{id}",
    ),
    (
        "message/im/router.py",
        """Business push router: local registry + Redis fanout + offline queue.""",
        """业务推送路由：本地注册表 + Redis 扇出 + 离线队列。""",
    ),
    (
        "message/im/router.py",
        """Push business events to online users; enqueue offline when needed.""",
        """向在线用户推送业务事件；必要时写入离线队列。""",
    ),
    (
        "message/im/server.py",
        """In-process dual-channel IM realtime server (WS Binary + TCP).""",
        """进程内双通道 IM 实时服务（WS Binary + TCP）。""",
    ),
    (
        "message/im/server.py",
        """Start/stop WS:18080 and TCP:18081 on the shared asyncio loop.""",
        """在共享 asyncio 循环上启停 WS:18080 与 TCP:18081。""",
    ),
    (
        "message/im/server.py",
        """Only one gunicorn worker may bind IM ports (Redis NX lock).""",
        """仅一个 gunicorn worker 可绑定 IM 端口（Redis NX 锁）。""",
    ),
    (
        "message/im/server.py",
        "# Single-process / no Redis: allow bind (dev / tests).",
        "# 单进程/无 Redis：允许绑定（开发/测试）。",
    ),
    (
        "message/im/server.py",
        "# Still start ACK tracker for local pushes if any session somehow exists.",
        "# 若仍有会话存在，仍启动 ACK 追踪器以处理本地推送。",
    ),
    (
        "message/im/server.py",
        "# Wait for AUTH frame",
        "# 等待 AUTH 帧",
    ),
    (
        "message/im/server.py",
        "# First frame must be AUTH",
        "# 首帧必须为 AUTH",
    ),
    (
        "message/im/server.py",
        "# Extra frames after AUTH are ignored until authed loop — shouldn't happen",
        "# AUTH 后的额外帧在认证循环前被忽略 — 不应发生",
    ),
    (
        "message/im/server.py",
        "# Soft check — hard idle is enforced by recv timeout",
        "# 软检查 — 硬空闲由 recv 超时强制",
    ),
    # ── message/message ──
    (
        "message/message/model.py",
        """MsgMessage - chat message, immutable (only revocable).""",
        """MsgMessage - 聊天消息，不可变（仅可撤回）。""",
    ),
    (
        "message/message/model.py",
        """Chat message. Not editable, only revocable (is_revoked).
    Does NOT extend TimestampMixin — only created_at is needed (updated doesn't apply).""",
        """聊天消息，不可编辑，仅可撤回 (is_revoked)。
    不继承 TimestampMixin — 仅需 created_at（无 updated）。""",
    ),
    (
        "message/message/model.py",
        """Cursor-based read tracking per account per conversation per terminal.""",
        """按账户、会话、终端的游标式已读追踪。""",
    ),
    (
        "message/message/model.py",
        """Message attachment, linked to sys_file for raw file storage.""",
        """消息附件，关联 sys_file 存储原始文件。""",
    ),
    (
        "message/message/model.py",
        "# UniqueConstraint for cursor: one per conversation+account+terminal",
        "# 游标 UniqueConstraint：每个 conversation+account+terminal 一条",
    ),
    (
        "message/message/repository.py",
        """Get the message immediately before a given message_id in the conversation.""",
        """获取会话中指定 message_id 之前紧邻的消息。""",
    ),
    (
        "message/message/repository.py",
        """Count messages after the user's last_read_message_id.""",
        """统计用户 last_read_message_id 之后的消息数。""",
    ),
    (
        "message/message/repository.py",
        "# Save attachments",
        "# 保存附件",
    ),
    (
        "message/message/service.py",
        """Send a message. Auto-creates conversation if needed (direct with participant_refs).""",
        """发送消息；必要时自动创建会话（direct 含 participant_refs）。""",
    ),
    (
        "message/message/service.py",
        """Paginate messages in a conversation, newest first.""",
        """分页查询会话消息，最新优先。""",
    ),
    (
        "message/message/service.py",
        """Mark conversation as read. Finds the latest message and uses it as cursor.""",
        """标记会话已读，取最新消息作为游标。""",
    ),
    (
        "message/message/service.py",
        """Push MESSAGE event after DB commit.""",
        """DB 提交后推送 MESSAGE 事件。""",
    ),
    (
        "message/message/service.py",
        "# Idempotent resend: same client_msg_id returns existing message",
        "# 幂等重发：相同 client_msg_id 返回已有消息",
    ),
    (
        "message/message/service.py",
        "# Auto-create conversation for this group",
        "# 为该群组自动创建会话",
    ),
    (
        "message/message/service.py",
        "# Add all active group members to the conversation",
        "# 将所有活跃群成员加入会话",
    ),
    (
        "message/message/service.py",
        "# ── Access control: conversation must be ACTIVE and sender must be a member ",
        "# ── 访问控制：会话须为 ACTIVE 且发送者须为成员 ",
    ),
    (
        "message/message/service.py",
        "# Auto-fill sender_name from profile if not provided (single lookup)",
        "# 未提供时从 profile 自动填充 sender_name（单次查询）",
    ),
    (
        "message/message/service.py",
        "# Update conversation last_message",
        "# 更新会话 last_message",
    ),
    (
        "message/message/service.py",
        "# Increment unread for other participants",
        "# 为其他参与者递增未读数",
    ),
    (
        "message/message/service.py",
        "# Fanout only after DB commit",
        "# 仅在 DB 提交后扇出",
    ),
    (
        "message/message/service.py",
        "# Enrich sender profiles",
        "# 填充发送者 profile",
    ),
    # ── message/notification ──
    (
        "message/notification/repository.py",
        """Return (items, total, read_id_set). Only PUBLISHED notifications matching the
        target scope rules visible to the given account.""",
        """返回 (items, total, read_id_set)。仅 PUBLISHED 且符合目标范围、对给定账户可见的通知。""",
    ),
    (
        "message/notification/repository.py",
        """Count PUBLISHED notifications visible to the account minus already-read ones.""",
        """统计账户可见的 PUBLISHED 通知数，减去已读。""",
    ),
    (
        "message/notification/repository.py",
        """Batch insert read records, skip existing (unique constraint).""",
        """批量插入已读记录，跳过已存在项（唯一约束）。""",
    ),
    (
        "message/notification/repository.py",
        """Mark all PUBLISHED notifications visible to the account as read.""",
        """将账户可见的全部 PUBLISHED 通知标记为已读。""",
    ),
    (
        "message/notification/router.py",
        """Register notification routes for the currently logged-in user.""",
        """为当前已登录用户注册通知路由。""",
    ),
    (
        "message/notification/router.py",
        "# ── Admin routes ",
        "# ── 管理端路由 ",
    ),
    (
        "message/notification/router.py",
        "# ── Portal / current-user routes ",
        "# ── Portal / 当前用户路由 ",
    ),
    (
        "message/notification/service.py",
        """Set status=PUBLISHED and publish_at=now (only from DRAFT).""",
        """设置 status=PUBLISHED 且 publish_at=now（仅从 DRAFT）。""",
    ),
    (
        "message/notification/service.py",
        """Set status=REVOKED and revoked_at=now (only from PUBLISHED).""",
        """设置 status=REVOKED 且 revoked_at=now（仅从 PUBLISHED）。""",
    ),
    (
        "message/notification/service.py",
        "# Push via IM to target users (after commit)",
        "# 提交后通过 IM 推送给目标用户",
    ),
    # ── message/offline ──
    (
        "message/offline/__init__.py",
        "# Package marker for message.offline",
        "# message.offline 包标记",
    ),
    # ── sys ──
    (
        "sys/codegen/apply.py",
        """Write codegen preview files into the workspace with low-invasion merges.""",
        """将代码生成预览文件写入工作区，低侵入合并。""",
    ),
    (
        "sys/codegen/apply.py",
        """Append codegen API export lines that are not already present.

    Returns ``(new_text, changed)``.
    """,
        """追加尚未存在的代码生成 API 导出行。

    返回 ``(new_text, changed)``。
    """,
    ),
    (
        "sys/codegen/apply.py",
        """Materialize preview files under ``root``.

    ``*.index.ts.append`` (or ``web/admin/src/api/index.ts.append``) is merged
    into ``web/admin/src/api/index.ts`` idempotently instead of being written
    as a standalone file.
    """,
        """在 ``root`` 下物化预览文件。

    ``*.index.ts.append``（或 ``web/admin/src/api/index.ts.append``）幂等合并
    到 ``web/admin/src/api/index.ts``，而非写入独立文件。
    """,
    ),
    (
        "sys/codegen/apply.py",
        "# Keep non-export lines only when they introduce a new export below.",
        "# 仅当下方有新导出时保留非导出行。",
    ),
    (
        "sys/codegen/templates.py",
        "# Codegen emits Python/TS/Vue source, not HTML — autoescape would corrupt templates.",
        "# 代码生成输出 Python/TS/Vue 源码而非 HTML — autoescape 会破坏模板。",
    ),
    (
        "sys/config/storage_service.py",
        """Never return decrypted AK/SK to API clients.""",
        """不向 API 客户端返回解密后的 AK/SK。""",
    ),
    (
        "sys/dict/router.py",
        '# Depends(require_permission("sys:dict:tree")),',
        '# Depends(require_permission("sys:dict:tree")),',
    ),
    (
        "sys/file/service.py",
        """Validate file content magic bytes against declared content type.

        Only checks content types that have known magic signatures in the
        registry below.  Types that were explicitly allowed in the config
        table (``upload_allowed_content_types``) but *lack* a registered
        magic signature are silently skipped — this keeps the validator
        compatible with custom / future types without false positives.
        """,
        """校验文件内容 magic bytes 是否与声明的 content type 一致。

        仅检查下方注册表中有已知 magic 签名的 content type。
        配置表 (``upload_allowed_content_types``) 中明确允许但*无*注册
        magic 签名的类型将静默跳过 — 以兼容自定义/未来类型并避免误报。
        """,
    ),
    (
        "sys/file/service.py",
        "# Compensate: avoid orphan objects when metadata commit fails.",
        "# 补偿：元数据提交失败时避免孤立对象。",
    ),
    (
        "sys/file/service.py",
        "# Registry: (magic_prefix, content_type_prefix)",
        "# 注册表：(magic_prefix, content_type_prefix)",
    ),
    (
        "sys/file/tasks.py",
        """Periodic cleanup of local storage orphans (object without DB row).""",
        """定期清理本地存储孤立对象（有对象无 DB 行）。""",
    ),
    (
        "sys/file/tasks.py",
        """Delete local files older than min_age with no matching sys_file row.""",
        """删除早于 min_age 且无对应 sys_file 行的本地文件。""",
    ),
    # ── user ──
    (
        "user/utils/profile.py",
        """Fill created_name / updated_name on schema objects from admin/portal profiles.""",
        """从 admin/portal profile 填充 schema 对象的 created_name / updated_name。""",
    ),
    # ── batch 2: module docstrings & remaining ──
    ("__init__.py", "Modules package.", "模块包。"),
    ("auth/__init__.py", "Auth module.", "认证模块。"),
    (
        "auth/webauthn_service.py",
        "WebAuthn helpers for Admin MFA.",
        "管理端 MFA 的 WebAuthn 辅助工具。",
    ),
    ("user/__init__.py", "User module.", "用户模块。"),
    ("user/admin/__init__.py", "Admin user profile package.", "管理端用户资料包。"),
    ("user/portal/__init__.py", "Portal user profile package.", "Portal 用户资料包。"),
    ("sys/file/__init__.py", "File module.", "文件模块。"),
    ("sys/file/portal/__init__.py", "Portal file routes.", "Portal 文件路由。"),
    ("sys/dict/__init__.py", "System dictionary module.", "系统字典模块。"),
    ("sys/config/__init__.py", "System config module.", "系统配置模块。"),
    ("sys/codegen/__init__.py", "Code generation module.", "代码生成模块。"),
    (
        "sys/banner/portal/__init__.py",
        "Portal display image routes.",
        "Portal 展示图路由。",
    ),
    ("sys/audit/__init__.py", "Operation audit module.", "操作审计模块。"),
    ("sys/audit/tasks.py", "Audit analysis tasks.", "审计分析任务。"),
    (
        "sys/audit/outbox.py",
        "Durable audit outbox for overflow / crash recovery.",
        "持久化审计发件箱，用于溢出/崩溃恢复。",
    ),
    (
        "sys/audit/analyzer.py",
        "Audit log analyzer — detects suspicious patterns and generates alerts.",
        "审计日志分析器 — 检测可疑模式并生成告警。",
    ),
    (
        "sys/audit/alert_model.py",
        "Alert history — records dispatched alerts for cooldown dedup.",
        "告警历史 — 记录已分发告警以供冷却去重。",
    ),
    (
        "sys/audit/alert.py",
        "Alert dispatcher — sends alerts via email and/or webhook with cooldown.",
        "告警分发器 — 通过邮件和/或 webhook 发送告警，含冷却。",
    ),
    (
        "message/offline/model.py",
        "Offline message queue. Delivered on IM reconnect (WS/TCP).",
        "离线消息队列，IM 重连 (WS/TCP) 时投递。",
    ),
    (
        "message/im/handler.py",
        "Shared IM frame handler for WS Binary and TCP.",
        "WS Binary 与 TCP 共用的 IM 帧处理器。",
    ),
    (
        "message/im/connection.py",
        "Realtime connection abstractions for WS Binary and TCP.",
        "WS Binary 与 TCP 的实时连接抽象。",
    ),
    (
        "message/im/config.py",
        "IM settings (env prefix IM__).",
        "IM 配置（环境变量前缀 IM__）。",
    ),
    (
        "iam/account/password_history.py",
        """Password change history — tracks password hash to prevent reuse and
drives密码到期提醒 (等保).

The latest entry per account is used as the canonical ``password_updated_at``
timestamp; accounts without any history fall back to the account row's
``updated_at`` timestamp (carried from TimestampMixin).""",
        """密码变更历史 — 记录密码 hash 以防复用，
并驱动密码到期提醒（等保）。

每账户最新一条作为 canonical ``password_updated_at`` 时间戳；
无历史记录的账户回退到账户行的 ``updated_at``（来自 TimestampMixin）。""",
    ),
    ("dashboard/__init__.py", "Admin dashboard package.", "管理端仪表盘包。"),
    ("internal/__init__.py", "Internal modules.", "内部模块。"),
    ("internal/health/__init__.py", "Internal health module.", "内部健康检查模块。"),
    (
        "message/group/service.py",
        """Apply to join a group（已是成员 / 已有待处理申请时幂等成功）。""",
        """申请加入群组（已是成员 / 已有待处理申请时幂等成功）。""",
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
