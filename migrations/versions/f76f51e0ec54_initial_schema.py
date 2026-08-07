""" Author: Charlie

初始 schema
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f76f51e0ec54"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### Alembic 自动生成的命令 - 请按需调整! ###
    op.create_table(
        "admin_user_profile",
        sa.Column("account_id", sa.String(length=64), nullable=False, comment="账户ID"),
        sa.Column("name", sa.String(length=64), nullable=True, comment="姓名"),
        sa.Column("nickname", sa.String(length=64), nullable=True, comment="昵称"),
        sa.Column("avatar", sa.Text(), nullable=True, comment="头像"),
        sa.Column("signature", sa.Text(), nullable=True, comment="个性签名"),
        sa.Column("phone", sa.String(length=32), nullable=True, comment="手机号"),
        sa.Column("email", sa.String(length=128), nullable=True, comment="邮箱"),
        sa.Column("remark", sa.Text(), nullable=True, comment="备注"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("account_id", name=op.f("pk_admin_user_profile")),
    )
    op.create_table(
        "msg_announcement",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("title", sa.String(length=255), nullable=False, comment="标题"),
        sa.Column("content", sa.Text(), nullable=False, comment="内容"),
        sa.Column("content_type", sa.String(length=32), nullable=False, comment="内容格式"),
        sa.Column("severity", sa.String(length=32), nullable=False, comment="等级"),
        sa.Column("target_scope", sa.String(length=32), nullable=False, comment="目标范围"),
        sa.Column("target_account_types", sa.JSON(), nullable=False, comment="目标账户类型列表"),
        sa.Column("target_account_ids", sa.JSON(), nullable=False, comment="目标账户ID列表"),
        sa.Column("target_dept_ids", sa.JSON(), nullable=False, comment="目标部门ID列表"),
        sa.Column("target_role_ids", sa.JSON(), nullable=False, comment="目标角色ID列表"),
        sa.Column("publish_locations", sa.JSON(), nullable=False, comment="发布位置列表"),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, comment="是否置顶"),
        sa.Column(
            "pinned_until", sa.DateTime(timezone=True), nullable=True, comment="置顶截止时间"
        ),
        sa.Column(
            "sender_account_type", sa.String(length=32), nullable=True, comment="发布者账户类型"
        ),
        sa.Column("sender_account_id", sa.String(length=64), nullable=True, comment="发布者账户ID"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("publish_at", sa.DateTime(timezone=True), nullable=True, comment="发布时间"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True, comment="撤回时间"),
        sa.Column("expire_at", sa.DateTime(timezone=True), nullable=True, comment="过期时间"),
        sa.Column("view_count", sa.Integer(), nullable=False, comment="查看次数"),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_announcement")),
    )
    op.create_table(
        "msg_announcement_read",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("announcement_id", sa.String(length=64), nullable=False, comment="公告ID"),
        sa.Column("account_type", sa.String(length=32), nullable=False, comment="账户类型"),
        sa.Column("account_id", sa.String(length=64), nullable=False, comment="账户ID"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_announcement_read")),
    )
    op.create_table(
        "msg_conversation",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column(
            "conversation_type",
            sa.String(length=32),
            nullable=False,
            comment="会话类型 DIRECT/GROUP",
        ),
        sa.Column("title", sa.String(length=255), nullable=True, comment="会话标题"),
        sa.Column("avatar", sa.String(length=500), nullable=True, comment="会话头像"),
        sa.Column("group_id", sa.String(length=64), nullable=True, comment="关联群ID"),
        sa.Column(
            "owner_account_type", sa.String(length=32), nullable=True, comment="创建者账户类型"
        ),
        sa.Column("owner_account_id", sa.String(length=64), nullable=True, comment="创建者账户ID"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("last_message_id", sa.String(length=64), nullable=True, comment="最新消息ID"),
        sa.Column(
            "last_message_at", sa.DateTime(timezone=True), nullable=True, comment="最新消息时间"
        ),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_conversation")),
    )
    op.create_table(
        "msg_conversation_member",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("conversation_id", sa.String(length=64), nullable=False, comment="会话ID"),
        sa.Column("account_type", sa.String(length=32), nullable=False, comment="账户类型"),
        sa.Column("account_id", sa.String(length=64), nullable=False, comment="账户ID"),
        sa.Column("role", sa.String(length=32), nullable=False, comment="角色 OWNER/MEMBER"),
        sa.Column("unread_count", sa.Integer(), nullable=False, comment="未读消息数"),
        sa.Column(
            "last_read_message_id", sa.String(length=64), nullable=True, comment="最后已读消息ID"
        ),
        sa.Column(
            "last_read_at", sa.DateTime(timezone=True), nullable=True, comment="最后已读时间"
        ),
        sa.Column(
            "last_delivered_at", sa.DateTime(timezone=True), nullable=True, comment="最后投递时间"
        ),
        sa.Column("is_muted", sa.Boolean(), nullable=False, comment="是否免打扰"),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, comment="是否置顶"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, comment="加入时间"),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True, comment="离开时间"),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_conversation_member")),
        sa.UniqueConstraint(
            "conversation_id", "account_type", "account_id", name="uq_conversation_member"
        ),
    )
    op.create_table(
        "msg_feedback",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("content", sa.Text(), nullable=False, comment="反馈内容"),
        sa.Column("category", sa.String(length=64), nullable=False, comment="反馈分类"),
        sa.Column("contact", sa.String(length=255), nullable=True, comment="联系方式"),
        sa.Column("attach_urls", sa.JSON(), nullable=False, comment="附件URL列表"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("reply", sa.Text(), nullable=True, comment="管理员回复"),
        sa.Column("replied_by", sa.String(length=64), nullable=True, comment="回复人ID"),
        sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True, comment="回复时间"),
        sa.Column(
            "submitter_account_type", sa.String(length=32), nullable=False, comment="提交者账户类型"
        ),
        sa.Column(
            "submitter_account_id", sa.String(length=64), nullable=False, comment="提交者账户ID"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_feedback")),
    )
    op.create_table(
        "msg_friend",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("account_type", sa.String(length=32), nullable=False, comment="账户类型"),
        sa.Column("account_id", sa.String(length=64), nullable=False, comment="账户ID"),
        sa.Column(
            "friend_account_type", sa.String(length=32), nullable=False, comment="好友账户类型"
        ),
        sa.Column("friend_account_id", sa.String(length=64), nullable=False, comment="好友账户ID"),
        sa.Column("remark", sa.String(length=64), nullable=True, comment="备注名"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("friend_at", sa.DateTime(timezone=True), nullable=False, comment="成为好友时间"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_friend")),
    )
    op.create_table(
        "msg_friend_request",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("applicant_type", sa.String(length=32), nullable=False, comment="申请人账户类型"),
        sa.Column("applicant_id", sa.String(length=64), nullable=False, comment="申请人账户ID"),
        sa.Column("recipient_type", sa.String(length=32), nullable=False, comment="接收人账户类型"),
        sa.Column("recipient_id", sa.String(length=64), nullable=False, comment="接收人账户ID"),
        sa.Column("message", sa.String(length=255), nullable=True, comment="申请消息"),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            comment="状态: PENDING/ACCEPTED/REJECTED",
        ),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True, comment="处理时间"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_friend_request")),
        sa.UniqueConstraint(
            "applicant_type",
            "applicant_id",
            "recipient_type",
            "recipient_id",
            name="uq_msg_friend_request_applicant_recipient",
        ),
    )
    op.create_index(
        "ix_msg_friend_request_applicant",
        "msg_friend_request",
        ["applicant_type", "applicant_id"],
        unique=False,
    )
    op.create_index(
        "ix_msg_friend_request_recipient",
        "msg_friend_request",
        ["recipient_type", "recipient_id"],
        unique=False,
    )
    op.create_table(
        "msg_group",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("name", sa.String(length=128), nullable=False, comment="群名称"),
        sa.Column("avatar", sa.String(length=500), nullable=True, comment="群头像"),
        sa.Column("description", sa.Text(), nullable=True, comment="群简介"),
        sa.Column(
            "owner_account_type", sa.String(length=32), nullable=False, comment="群主账户类型"
        ),
        sa.Column("owner_account_id", sa.String(length=64), nullable=False, comment="群主账户ID"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("join_mode", sa.String(length=32), nullable=False, comment="入群方式"),
        sa.Column("max_members", sa.Integer(), nullable=False, comment="最大成员数"),
        sa.Column("member_count", sa.Integer(), nullable=False, comment="当前成员数"),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_group")),
    )
    op.create_table(
        "msg_group_join_request",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("group_id", sa.String(length=64), nullable=False, comment="群ID"),
        sa.Column("applicant_type", sa.String(length=32), nullable=False, comment="申请人账户类型"),
        sa.Column("applicant_id", sa.String(length=64), nullable=False, comment="申请人账户ID"),
        sa.Column("message", sa.Text(), nullable=True, comment="申请附言"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("handled_by_type", sa.String(length=32), nullable=True, comment="处理人账户类型"),
        sa.Column("handled_by_id", sa.String(length=64), nullable=True, comment="处理人账户ID"),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True, comment="处理时间"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_group_join_request")),
    )
    op.create_table(
        "msg_group_member",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("group_id", sa.String(length=64), nullable=False, comment="群ID"),
        sa.Column("account_type", sa.String(length=32), nullable=False, comment="账户类型"),
        sa.Column("account_id", sa.String(length=64), nullable=False, comment="账户ID"),
        sa.Column("role", sa.String(length=32), nullable=False, comment="角色"),
        sa.Column("nickname", sa.String(length=64), nullable=True, comment="群内昵称"),
        sa.Column("is_muted", sa.Boolean(), nullable=False, comment="是否免打扰"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, comment="加入时间"),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True, comment="离开时间"),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_group_member")),
    )
    op.create_table(
        "msg_message",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=False),
        sa.Column("msg_type", sa.String(length=32), nullable=False),
        sa.Column("parent_id", sa.String(length=64), nullable=True),
        sa.Column("sender_type", sa.String(length=32), nullable=False),
        sa.Column("sender_account_type", sa.String(length=32), nullable=True),
        sa.Column("sender_account_id", sa.String(length=64), nullable=True),
        sa.Column("sender_name", sa.String(length=128), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("reply_count", sa.Integer(), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_message")),
    )
    op.create_index(
        "ix_msg_msg_conv_created", "msg_message", ["conversation_id", "created_at"], unique=False
    )
    op.create_index("ix_msg_msg_parent", "msg_message", ["parent_id"], unique=False)
    op.create_index(
        "ix_msg_msg_sender",
        "msg_message",
        ["sender_account_type", "sender_account_id"],
        unique=False,
    )
    op.create_table(
        "msg_message_attachment",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("message_id", sa.String(length=64), nullable=False),
        sa.Column("file_id", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=True),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("attachment_type", sa.String(length=32), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=1024), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("sort", sa.Integer(), nullable=False),
        sa.Column("extra", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_message_attachment")),
    )
    op.create_index(
        "ix_msg_mattach_message", "msg_message_attachment", ["message_id", "sort"], unique=False
    )
    op.create_table(
        "msg_message_read",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=False),
        sa.Column("account_type", sa.String(length=32), nullable=False),
        sa.Column("account_id", sa.String(length=64), nullable=False),
        sa.Column("last_read_message_id", sa.String(length=64), nullable=False),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("terminal_id", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_message_read")),
    )
    op.create_index(
        "ix_msg_mread_account", "msg_message_read", ["account_type", "account_id"], unique=False
    )
    op.create_table(
        "msg_notification",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("title", sa.String(length=255), nullable=False, comment="标题"),
        sa.Column("content", sa.Text(), nullable=False, comment="内容"),
        sa.Column("content_type", sa.String(length=32), nullable=False, comment="内容格式"),
        sa.Column("category", sa.String(length=32), nullable=False, comment="分类"),
        sa.Column("severity", sa.String(length=32), nullable=False, comment="等级"),
        sa.Column("target_scope", sa.String(length=32), nullable=False, comment="目标范围"),
        sa.Column("target_account_types", sa.JSON(), nullable=False, comment="目标账户类型列表"),
        sa.Column("target_account_ids", sa.JSON(), nullable=False, comment="目标账户ID列表"),
        sa.Column("target_dept_ids", sa.JSON(), nullable=False, comment="目标部门ID列表"),
        sa.Column("target_role_ids", sa.JSON(), nullable=False, comment="目标角色ID列表"),
        sa.Column(
            "sender_account_type", sa.String(length=32), nullable=True, comment="发送者账户类型"
        ),
        sa.Column("sender_account_id", sa.String(length=64), nullable=True, comment="发送者账户ID"),
        sa.Column("source_type", sa.String(length=64), nullable=True, comment="来源模块"),
        sa.Column("source_id", sa.String(length=64), nullable=True, comment="来源业务ID"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("publish_at", sa.DateTime(timezone=True), nullable=True, comment="发布时间"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True, comment="撤回时间"),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_notification")),
    )
    op.create_table(
        "msg_notification_read",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("notification_id", sa.String(length=64), nullable=False, comment="通知ID"),
        sa.Column("account_type", sa.String(length=32), nullable=False, comment="账户类型"),
        sa.Column("account_id", sa.String(length=64), nullable=False, comment="账户ID"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False, comment="阅读时间"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_notification_read")),
        sa.UniqueConstraint(
            "notification_id", "account_type", "account_id", name="uq_msg_notification_read_account"
        ),
    )
    op.create_table(
        "msg_terminal",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("account_type", sa.String(length=32), nullable=False, comment="账户类型"),
        sa.Column("account_id", sa.String(length=64), nullable=False, comment="账户ID"),
        sa.Column("device_type", sa.String(length=32), nullable=False, comment="设备类型"),
        sa.Column("device_name", sa.String(length=128), nullable=True, comment="设备名称"),
        sa.Column("device_id", sa.String(length=255), nullable=True, comment="设备唯一标识"),
        sa.Column("push_token", sa.String(length=500), nullable=True, comment="推送Token"),
        sa.Column("push_provider", sa.String(length=32), nullable=True, comment="推送渠道"),
        sa.Column("app_version", sa.String(length=32), nullable=True, comment="App版本号"),
        sa.Column("is_online", sa.Boolean(), nullable=False, comment="是否在线"),
        sa.Column(
            "last_online_at", sa.DateTime(timezone=True), nullable=True, comment="最后在线时间"
        ),
        sa.Column(
            "last_login_at", sa.DateTime(timezone=True), nullable=False, comment="最后登录时间"
        ),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_terminal")),
    )
    op.create_table(
        "portal_user_profile",
        sa.Column("account_id", sa.String(length=64), nullable=False, comment="账户ID"),
        sa.Column("name", sa.String(length=64), nullable=True, comment="姓名"),
        sa.Column("nickname", sa.String(length=64), nullable=True, comment="昵称"),
        sa.Column("avatar", sa.Text(), nullable=True, comment="头像"),
        sa.Column("signature", sa.Text(), nullable=True, comment="个性签名"),
        sa.Column("phone", sa.String(length=32), nullable=True, comment="手机号"),
        sa.Column("email", sa.String(length=128), nullable=True, comment="邮箱"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("account_id", name=op.f("pk_portal_user_profile")),
    )
    op.create_table(
        "sys_account",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("password_hash", sa.String(length=255), nullable=False, comment="密码哈希"),
        sa.Column("account_type", sa.String(length=32), nullable=False, comment="账户类型"),
        sa.Column("account_status", sa.String(length=32), nullable=False, comment="账户状态"),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True, comment="注销时间"),
        sa.Column("cancelled_by", sa.String(length=64), nullable=True, comment="注销人"),
        sa.Column("cancel_reason", sa.Text(), nullable=True, comment="注销原因"),
        sa.Column("last_login_ip", sa.String(length=64), nullable=True, comment="上次登录IP"),
        sa.Column(
            "last_login_address", sa.String(length=255), nullable=True, comment="上次登录地点"
        ),
        sa.Column(
            "last_login_time", sa.DateTime(timezone=True), nullable=True, comment="上次登录时间"
        ),
        sa.Column("last_login_device", sa.Text(), nullable=True, comment="上次登录设备"),
        sa.Column("latest_login_ip", sa.String(length=64), nullable=True, comment="最新登录IP"),
        sa.Column(
            "latest_login_address", sa.String(length=255), nullable=True, comment="最新登录地点"
        ),
        sa.Column(
            "latest_login_time", sa.DateTime(timezone=True), nullable=True, comment="最新登录时间"
        ),
        sa.Column("latest_login_device", sa.Text(), nullable=True, comment="最新登录设备"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_account")),
    )
    op.create_table(
        "sys_account_identity",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("account_id", sa.String(length=64), nullable=False, comment="账户ID"),
        sa.Column("identity_type", sa.String(length=32), nullable=False, comment="登录标识类型"),
        sa.Column("identifier", sa.String(length=128), nullable=False, comment="登录标识"),
        sa.Column("verified", sa.Boolean(), nullable=False, comment="是否已验证"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, comment="是否主标识"),
        sa.Column("bind_status", sa.String(length=32), nullable=False, comment="绑定状态"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_account_identity")),
        sa.UniqueConstraint(
            "identity_type", "identifier", name="uq_sys_account_identity_type_identifier"
        ),
    )
    op.create_table(
        "sys_account_password_history",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("account_id", sa.String(length=64), nullable=False, comment="账户ID"),
        sa.Column("password_hash", sa.String(length=255), nullable=False, comment="密码哈希"),
        sa.Column(
            "changed_by", sa.String(length=64), nullable=True, comment="变更人（账户ID或系统）"
        ),
        sa.Column(
            "change_reason",
            sa.String(length=64),
            nullable=True,
            comment="变更原因: register / admin_reset / self_reset / password_expired",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="变更时间",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_account_password_history")),
    )
    op.create_index(
        "idx_pwd_history_account_created",
        "sys_account_password_history",
        ["account_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "sys_alert_log",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("rule_name", sa.String(length=64), nullable=False, comment="规则名称"),
        sa.Column(
            "severity",
            sa.String(length=16),
            nullable=False,
            comment="严重级别: INFO/WARNING/CRITICAL",
        ),
        sa.Column("summary", sa.String(length=255), nullable=False, comment="告警摘要"),
        sa.Column("details", sa.JSON(), nullable=True, comment="告警详情（JSON）"),
        sa.Column(
            "notified_via", sa.String(length=64), nullable=True, comment="通知方式: email/webhook"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="通知时间",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_alert_log")),
    )
    op.create_table(
        "sys_banner",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("title", sa.String(length=255), nullable=False, comment="标题"),
        sa.Column("image", sa.String(length=500), nullable=False, comment="图片地址"),
        sa.Column("url", sa.String(length=500), nullable=True, comment="跳转地址"),
        sa.Column(
            "link_type",
            sa.String(length=16),
            nullable=False,
            comment="链接类型：展示图链接类型，对应 BANNER_LINK_TYPE 字典组子项 value。",
        ),
        sa.Column("summary", sa.String(length=500), nullable=True, comment="摘要"),
        sa.Column("description", sa.Text(), nullable=True, comment="描述"),
        sa.Column(
            "category",
            sa.String(length=32),
            nullable=False,
            comment="分类：展示图分类，对应 BANNER_CATEGORY 字典组子项 value。",
        ),
        sa.Column(
            "type",
            sa.String(length=32),
            nullable=False,
            comment="类型：展示图类型，对应 BANNER_TYPE 字典组子项 value。",
        ),
        sa.Column(
            "position",
            sa.String(length=32),
            nullable=False,
            comment="显示位置：展示图显示位置，对应 BANNER_POSITION 字典组子项 value。",
        ),
        sa.Column(
            "display_scope",
            sa.String(length=32),
            nullable=False,
            comment="显示端：展示图显示端，对应 BANNER_DISPLAY_SCOPE 字典组子项 value。",
        ),
        sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
        sa.Column("interaction_count", sa.BigInteger(), nullable=False, comment="交互次数"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True, comment="开始展示时间"),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True, comment="结束展示时间"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_banner")),
    )
    op.create_index(
        "ix_sys_banner_scope_position_status_sort",
        "sys_banner",
        ["display_scope", "position", "status", "sort"],
        unique=False,
    )
    op.create_table(
        "sys_codegen_field",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("plan_id", sa.String(length=64), nullable=False, comment="方案ID"),
        sa.Column("table_role", sa.String(length=16), nullable=False, comment="表角色"),
        sa.Column("column_name", sa.String(length=128), nullable=False, comment="字段名"),
        sa.Column("column_comment", sa.String(length=255), nullable=True, comment="字段注释"),
        sa.Column("db_type", sa.String(length=128), nullable=False, comment="数据库类型"),
        sa.Column("python_type", sa.String(length=64), nullable=False, comment="Python类型"),
        sa.Column(
            "typescript_type", sa.String(length=64), nullable=False, comment="TypeScript类型"
        ),
        sa.Column("form_widget", sa.String(length=32), nullable=False, comment="表单控件"),
        sa.Column("dict_code", sa.String(length=128), nullable=True, comment="字典编码"),
        sa.Column("query_operator", sa.String(length=32), nullable=True, comment="查询方式"),
        sa.Column("show_in_table", sa.Boolean(), nullable=False, comment="表格显示"),
        sa.Column("show_in_form", sa.Boolean(), nullable=False, comment="表单显示"),
        sa.Column("show_in_detail", sa.Boolean(), nullable=False, comment="详情显示"),
        sa.Column("show_in_query", sa.Boolean(), nullable=False, comment="查询显示"),
        sa.Column("is_primary_key", sa.Boolean(), nullable=False, comment="是否主键"),
        sa.Column("is_required", sa.Boolean(), nullable=False, comment="是否必填"),
        sa.Column("is_unique", sa.Boolean(), nullable=False, comment="是否唯一"),
        sa.Column("is_nullable", sa.Boolean(), nullable=False, comment="是否可空"),
        sa.Column("max_length", sa.Integer(), nullable=True, comment="最大长度"),
        sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_codegen_field")),
        sa.UniqueConstraint(
            "plan_id", "table_role", "column_name", name="uq_sys_codegen_field_plan_role_column"
        ),
    )
    op.create_index(
        "ix_sys_codegen_field_plan_role_sort",
        "sys_codegen_field",
        ["plan_id", "table_role", "sort"],
        unique=False,
    )
    op.create_table(
        "sys_codegen_plan",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("name", sa.String(length=128), nullable=False, comment="方案名称"),
        sa.Column("gen_type", sa.String(length=32), nullable=False, comment="生成类型"),
        sa.Column("author", sa.String(length=64), nullable=False, comment="作者"),
        sa.Column("description", sa.Text(), nullable=True, comment="描述"),
        sa.Column("main_table", sa.String(length=128), nullable=False, comment="主表名"),
        sa.Column("main_pk", sa.String(length=128), nullable=False, comment="主表主键"),
        sa.Column("main_entity_name", sa.String(length=128), nullable=False, comment="主实体类名"),
        sa.Column(
            "main_module_path", sa.String(length=255), nullable=False, comment="后端模块路径"
        ),
        sa.Column(
            "main_business_name", sa.String(length=128), nullable=False, comment="主业务名称"
        ),
        sa.Column("api_prefix", sa.String(length=255), nullable=False, comment="接口前缀"),
        sa.Column("permission_prefix", sa.String(length=128), nullable=False, comment="权限前缀"),
        sa.Column("resource_module_id", sa.String(length=64), nullable=True, comment="资源模块ID"),
        sa.Column("parent_resource_id", sa.String(length=64), nullable=True, comment="父资源ID"),
        sa.Column("menu_name", sa.String(length=64), nullable=False, comment="菜单名称"),
        sa.Column("menu_path", sa.String(length=255), nullable=False, comment="菜单路径"),
        sa.Column("component_path", sa.String(length=255), nullable=False, comment="组件路径"),
        sa.Column("icon", sa.String(length=255), nullable=True, comment="菜单图标"),
        sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
        sa.Column("tree_parent_field", sa.String(length=128), nullable=True, comment="树父级字段"),
        sa.Column("tree_label_field", sa.String(length=128), nullable=True, comment="树展示字段"),
        sa.Column("sub_table", sa.String(length=128), nullable=True, comment="子表名"),
        sa.Column("sub_pk", sa.String(length=128), nullable=True, comment="子表主键"),
        sa.Column("sub_foreign_key", sa.String(length=128), nullable=True, comment="子表外键"),
        sa.Column("sub_entity_name", sa.String(length=128), nullable=True, comment="子实体类名"),
        sa.Column("sub_business_name", sa.String(length=128), nullable=True, comment="子业务名称"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_codegen_plan")),
        sa.UniqueConstraint("name", name="uq_sys_codegen_plan_name"),
    )
    op.create_index("ix_sys_codegen_plan_gen_type", "sys_codegen_plan", ["gen_type"], unique=False)
    op.create_index(
        "ix_sys_codegen_plan_main_table", "sys_codegen_plan", ["main_table"], unique=False
    )
    op.create_table(
        "sys_config",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("config_key", sa.String(length=255), nullable=False, comment="配置键"),
        sa.Column("config_value", sa.Text(), nullable=True, comment="配置值"),
        sa.Column("category", sa.String(length=255), nullable=True, comment="分类"),
        sa.Column("remark", sa.String(length=255), nullable=True, comment="备注"),
        sa.Column("sort_code", sa.Integer(), nullable=False, comment="排序码"),
        sa.Column("ext_json", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_config")),
    )
    op.create_index("idx_sys_config_category", "sys_config", ["category"], unique=False)
    op.create_index("idx_sys_config_key", "sys_config", ["config_key"], unique=True)
    op.create_table(
        "sys_dept",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("parent_id", sa.String(length=64), nullable=True, comment="父部门ID"),
        sa.Column("master_id", sa.String(length=64), nullable=True, comment="主管ID"),
        sa.Column("deputy_master_id", sa.String(length=64), nullable=True, comment="副主管ID"),
        sa.Column("name", sa.String(length=64), nullable=False, comment="部门名称"),
        sa.Column("category", sa.String(length=64), nullable=False, comment="部门类别"),
        sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
        sa.Column("is_virtual", sa.Boolean(), nullable=False, comment="是否虚拟部门"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_dept")),
    )
    op.create_table(
        "sys_dict",
        sa.Column("id", sa.String(length=32), nullable=False, comment="主键"),
        sa.Column("code", sa.String(length=50), nullable=False, comment="编码"),
        sa.Column("label", sa.String(length=255), nullable=True, comment="标签"),
        sa.Column("value", sa.String(length=255), nullable=True, comment="值"),
        sa.Column("color", sa.String(length=32), nullable=True, comment="颜色"),
        sa.Column(
            "category",
            sa.String(length=64),
            nullable=True,
            comment="系统/业务分类：\n系统/业务分类\n",
        ),
        sa.Column("parent_id", sa.String(length=32), nullable=True, comment="父级ID"),
        sa.Column("status", sa.String(length=16), nullable=False, comment="状态"),
        sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_dict")),
    )
    op.create_index("idx_sys_dict_category", "sys_dict", ["category"], unique=False)
    op.create_index("idx_sys_dict_code", "sys_dict", ["code"], unique=True)
    op.create_index("idx_sys_dict_parent_id", "sys_dict", ["parent_id"], unique=False)
    op.create_table(
        "sys_file",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("object_name", sa.String(length=255), nullable=False, comment="对象存储路径"),
        sa.Column("original_name", sa.String(length=255), nullable=False, comment="原始文件名"),
        sa.Column("storage_config_id", sa.String(length=64), nullable=False, comment="存储配置 ID"),
        sa.Column("storage_provider", sa.String(length=32), nullable=False, comment="存储服务商"),
        sa.Column("bucket", sa.String(length=255), nullable=True, comment="存储桶"),
        sa.Column("content_type", sa.String(length=128), nullable=False, comment="文件类型"),
        sa.Column("size", sa.BigInteger(), nullable=False, comment="文件大小"),
        sa.Column("url", sa.String(length=1024), nullable=False, comment="访问地址"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_file")),
        sa.UniqueConstraint("object_name", name=op.f("uq_sys_file_object_name")),
    )
    op.create_table(
        "sys_group",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("name", sa.String(length=64), nullable=False, comment="账户组名称"),
        sa.Column("owner_dept_id", sa.String(length=64), nullable=True, comment="所属部门ID"),
        sa.Column("description", sa.Text(), nullable=True, comment="描述"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_group")),
        sa.UniqueConstraint("name", name="uq_sys_group_name"),
    )
    op.create_table(
        "sys_iam_relation",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("subject_type", sa.String(length=32), nullable=False, comment="主体类型"),
        sa.Column("subject_id", sa.String(length=64), nullable=False, comment="主体ID"),
        sa.Column("relation_type", sa.String(length=64), nullable=False, comment="关系类型"),
        sa.Column("target_type", sa.String(length=32), nullable=False, comment="目标类型"),
        sa.Column("target_id", sa.String(length=64), nullable=False, comment="目标ID"),
        sa.Column("target_key", sa.String(length=128), nullable=False, comment="目标标识"),
        sa.Column("grant_mode", sa.String(length=32), nullable=False, comment="授权模式"),
        sa.Column("effect", sa.String(length=32), nullable=False, comment="授权效果"),
        sa.Column("data_scope", sa.String(length=32), nullable=False, comment="数据范围"),
        sa.Column(
            "custom_scope_dept_ids", sa.JSON(), nullable=False, comment="自定义数据范围部门ID列表"
        ),
        sa.Column("is_primary", sa.Boolean(), nullable=False, comment="主关系"),
        sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("description", sa.Text(), nullable=True, comment="描述"),
        sa.Column("reason", sa.Text(), nullable=True, comment="授权原因"),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True, comment="失效时间"),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_iam_relation")),
        sa.UniqueConstraint(
            "subject_type",
            "subject_id",
            "relation_type",
            "target_type",
            "target_id",
            "target_key",
            name="uq_sys_iam_relation_subject_relation_target",
        ),
    )
    op.create_index(
        "ix_sys_iam_relation_subject",
        "sys_iam_relation",
        ["subject_type", "subject_id", "relation_type"],
        unique=False,
    )
    op.create_index(
        "ix_sys_iam_relation_target",
        "sys_iam_relation",
        ["target_type", "target_id", "target_key"],
        unique=False,
    )
    op.create_table(
        "sys_operation_audit_log",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("module", sa.String(length=64), nullable=False, comment="模块"),
        sa.Column("resource_type", sa.String(length=128), nullable=True, comment="资源类型"),
        sa.Column("resource_id", sa.String(length=128), nullable=True, comment="资源ID"),
        sa.Column("action", sa.String(length=64), nullable=False, comment="操作"),
        sa.Column("summary", sa.String(length=255), nullable=True, comment="摘要"),
        sa.Column("before_data", sa.JSON(), nullable=True, comment="变更前数据"),
        sa.Column("after_data", sa.JSON(), nullable=True, comment="变更后数据"),
        sa.Column("account_id", sa.String(length=64), nullable=True, comment="操作账号ID"),
        sa.Column("account_type", sa.String(length=32), nullable=True, comment="操作账号类型"),
        sa.Column("request_id", sa.String(length=64), nullable=True, comment="请求ID"),
        sa.Column("ip", sa.String(length=64), nullable=True, comment="客户端IP"),
        sa.Column("user_agent", sa.String(length=512), nullable=True, comment="User-Agent"),
        sa.Column("success", sa.Boolean(), nullable=False, comment="是否成功"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="错误信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_operation_audit_log")),
    )
    op.create_index(
        "idx_sys_operation_audit_account_id",
        "sys_operation_audit_log",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "idx_sys_operation_audit_created_at",
        "sys_operation_audit_log",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "idx_sys_operation_audit_module_action",
        "sys_operation_audit_log",
        ["module", "action"],
        unique=False,
    )
    op.create_index(
        "idx_sys_operation_audit_resource",
        "sys_operation_audit_log",
        ["resource_type", "resource_id"],
        unique=False,
    )
    op.create_table(
        "sys_position",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("name", sa.String(length=64), nullable=False, comment="职位名称"),
        sa.Column("category", sa.String(length=32), nullable=False, comment="职位类别"),
        sa.Column("owner_dept_id", sa.String(length=64), nullable=True, comment="所属部门ID"),
        sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
        sa.Column("is_virtual", sa.Boolean(), nullable=False, comment="是否虚拟职位"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("description", sa.Text(), nullable=True, comment="职位描述"),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_position")),
    )
    op.create_table(
        "sys_resource",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("parent_id", sa.String(length=64), nullable=True, comment="父资源ID"),
        sa.Column("code", sa.String(length=64), nullable=False, comment="资源编码"),
        sa.Column("name", sa.String(length=64), nullable=False, comment="资源名称"),
        sa.Column("resource_type", sa.String(length=32), nullable=False, comment="资源类型"),
        sa.Column("module_id", sa.String(length=64), nullable=True, comment="所属资源模块ID"),
        sa.Column("path", sa.String(length=255), nullable=True, comment="路由路径"),
        sa.Column("component", sa.String(length=255), nullable=True, comment="前端组件"),
        sa.Column("redirect", sa.String(length=255), nullable=True, comment="重定向地址"),
        sa.Column("icon", sa.String(length=255), nullable=True, comment="图标"),
        sa.Column("color", sa.String(length=32), nullable=True, comment="颜色"),
        sa.Column("href", sa.String(length=255), nullable=True, comment="外链地址"),
        sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
        sa.Column("is_visible", sa.Boolean(), nullable=False, comment="是否可见"),
        sa.Column("is_cache", sa.Boolean(), nullable=False, comment="是否缓存"),
        sa.Column("is_affix", sa.Boolean(), nullable=False, comment="是否固定标签"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("description", sa.Text(), nullable=True, comment="描述"),
        sa.Column("layout", sa.String(length=255), nullable=True, comment="布局类型"),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_resource")),
        sa.UniqueConstraint("module_id", "code", name="uq_sys_resource_module_id_code"),
    )
    op.create_table(
        "sys_resource_module",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("name", sa.String(length=64), nullable=False, comment="模块名称"),
        sa.Column("code", sa.String(length=64), nullable=False, comment="模块编码"),
        sa.Column("client", sa.String(length=32), nullable=False, comment="所属端"),
        sa.Column("icon", sa.String(length=255), nullable=True, comment="图标"),
        sa.Column("color", sa.String(length=32), nullable=True, comment="颜色"),
        sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("description", sa.Text(), nullable=True, comment="描述"),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_resource_module")),
        sa.UniqueConstraint("code", name="uq_sys_resource_module_code"),
    )
    op.create_table(
        "sys_role",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("code", sa.String(length=64), nullable=False, comment="角色编码"),
        sa.Column("name", sa.String(length=64), nullable=False, comment="角色名称"),
        sa.Column("category", sa.String(length=64), nullable=False, comment="角色分类"),
        sa.Column("scope_type", sa.String(length=32), nullable=False, comment="角色作用域类型"),
        sa.Column("owner_dept_id", sa.String(length=64), nullable=True, comment="所属部门ID"),
        sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("is_builtin", sa.Boolean(), nullable=False, comment="是否内置角色"),
        sa.Column("description", sa.Text(), nullable=True, comment="描述"),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_role")),
        sa.UniqueConstraint("code", name="uq_sys_role_code"),
    )
    op.create_table(
        "sys_storage_config",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="配置名称"),
        sa.Column(
            "provider",
            sa.String(length=32),
            nullable=False,
            comment="存储服务商：local/minio/s3/oss",
        ),
        sa.Column("bucket", sa.String(length=255), nullable=True, comment="存储桶"),
        sa.Column("endpoint", sa.String(length=500), nullable=True, comment="服务端点"),
        sa.Column("access_key", sa.String(length=255), nullable=True, comment="访问密钥 ID"),
        sa.Column("secret_key", sa.String(length=255), nullable=True, comment="访问密钥 Secret"),
        sa.Column("region", sa.String(length=100), nullable=True, comment="区域"),
        sa.Column("use_ssl", sa.Boolean(), nullable=False, comment="是否使用 SSL 连接"),
        sa.Column("base_url", sa.String(length=500), nullable=True, comment="自定义基础 URL"),
        sa.Column("public_path", sa.String(length=255), nullable=False, comment="公开访问路径"),
        sa.Column("local_root", sa.String(length=500), nullable=False, comment="本地存储根目录"),
        sa.Column(
            "is_default", sa.Boolean(), nullable=False, comment="是否为当前启用的默认配置（互斥）"
        ),
        sa.Column("remark", sa.String(length=255), nullable=True, comment="备注"),
        sa.Column("sort_code", sa.Integer(), nullable=False, comment="排序码"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_storage_config")),
    )
    # ### Alembic 命令结束 ###


def downgrade() -> None:
    # ### Alembic 自动生成的命令 - 请按需调整! ###
    op.drop_table("sys_storage_config")
    op.drop_table("sys_role")
    op.drop_table("sys_resource_module")
    op.drop_table("sys_resource")
    op.drop_table("sys_position")
    op.drop_index("idx_sys_operation_audit_resource", table_name="sys_operation_audit_log")
    op.drop_index("idx_sys_operation_audit_module_action", table_name="sys_operation_audit_log")
    op.drop_index("idx_sys_operation_audit_created_at", table_name="sys_operation_audit_log")
    op.drop_index("idx_sys_operation_audit_account_id", table_name="sys_operation_audit_log")
    op.drop_table("sys_operation_audit_log")
    op.drop_index("ix_sys_iam_relation_target", table_name="sys_iam_relation")
    op.drop_index("ix_sys_iam_relation_subject", table_name="sys_iam_relation")
    op.drop_table("sys_iam_relation")
    op.drop_table("sys_group")
    op.drop_table("sys_file")
    op.drop_index("idx_sys_dict_parent_id", table_name="sys_dict")
    op.drop_index("idx_sys_dict_code", table_name="sys_dict")
    op.drop_index("idx_sys_dict_category", table_name="sys_dict")
    op.drop_table("sys_dict")
    op.drop_table("sys_dept")
    op.drop_index("idx_sys_config_key", table_name="sys_config")
    op.drop_index("idx_sys_config_category", table_name="sys_config")
    op.drop_table("sys_config")
    op.drop_index("ix_sys_codegen_plan_main_table", table_name="sys_codegen_plan")
    op.drop_index("ix_sys_codegen_plan_gen_type", table_name="sys_codegen_plan")
    op.drop_table("sys_codegen_plan")
    op.drop_index("ix_sys_codegen_field_plan_role_sort", table_name="sys_codegen_field")
    op.drop_table("sys_codegen_field")
    op.drop_index("ix_sys_banner_scope_position_status_sort", table_name="sys_banner")
    op.drop_table("sys_banner")
    op.drop_table("sys_alert_log")
    op.drop_index("idx_pwd_history_account_created", table_name="sys_account_password_history")
    op.drop_table("sys_account_password_history")
    op.drop_table("sys_account_identity")
    op.drop_table("sys_account")
    op.drop_table("portal_user_profile")
    op.drop_table("msg_terminal")
    op.drop_table("msg_notification_read")
    op.drop_table("msg_notification")
    op.drop_index("ix_msg_mread_account", table_name="msg_message_read")
    op.drop_table("msg_message_read")
    op.drop_index("ix_msg_mattach_message", table_name="msg_message_attachment")
    op.drop_table("msg_message_attachment")
    op.drop_index("ix_msg_msg_sender", table_name="msg_message")
    op.drop_index("ix_msg_msg_parent", table_name="msg_message")
    op.drop_index("ix_msg_msg_conv_created", table_name="msg_message")
    op.drop_table("msg_message")
    op.drop_table("msg_group_member")
    op.drop_table("msg_group_join_request")
    op.drop_table("msg_group")
    op.drop_index("ix_msg_friend_request_recipient", table_name="msg_friend_request")
    op.drop_index("ix_msg_friend_request_applicant", table_name="msg_friend_request")
    op.drop_table("msg_friend_request")
    op.drop_table("msg_friend")
    op.drop_table("msg_feedback")
    op.drop_table("msg_conversation_member")
    op.drop_table("msg_conversation")
    op.drop_table("msg_announcement_read")
    op.drop_table("msg_announcement")
    op.drop_table("admin_user_profile")
    # ### Alembic 命令结束 ###
