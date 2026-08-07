"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:52
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import BusinessError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.security.session import SessionPayload
from app.modules.message.enums import (
    ConversationMemberRole,
    ConversationStatus,
    ConversationType,
    GroupJoinRequestStatus,
    GroupStatus,
)
from app.modules.message.group.model import (
    MsgGroupJoinRequest,
    MsgGroupMember,
)
from app.modules.message.group.repository import (
    MsgGroupRepository,
)
from app.modules.message.group.schema import (
    GroupCreateRequest,
    GroupDetailRequest,
    GroupJoinRequestCreate,
    GroupJoinRequestHandle,
    GroupJoinRequestSchema,
    GroupMemberAddRequest,
    GroupMemberRemoveRequest,
    GroupMemberSchema,
    GroupSearchQuery,
    GroupUpdateRequest,
    MsgGroupAdminPageQuery,
    MsgGroupCreateRequest,
    MsgGroupSchema,
    MsgGroupUpdateRequest,
    SetMemberRoleRequest,
)
from app.modules.user.utils.profile import get_profiles_batch
from app.platform.db.transaction import transactional
from app.platform.storage.url import resolve_file_url


class MsgGroupService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MsgGroupRepository(db)

    # ==================== 管理端 CRUD ====================

    async def create(self, payload: MsgGroupCreateRequest) -> None:
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: MsgGroupUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> MsgGroupSchema:
        return to_schema(MsgGroupSchema, await self.repo.get_required(query.id))

    async def page_admin(self, query: MsgGroupAdminPageQuery) -> PageData[MsgGroupSchema]:
        items, total = await self.repo.page_admin(query)
        return build_page(query, total, to_schema_list(MsgGroupSchema, items))

    # ==================== 当前用户群组管理 ====================

    async def create_group(
        self, payload: GroupCreateRequest, session: SessionPayload
    ) -> MsgGroupSchema:
        """创建群组：创建 MsgGroup + 添加群主为成员 + 自动创建会话。"""
        async with transactional(self.db):
            group = await self.repo.create(
                MsgGroupCreateRequest(
                    name=payload.name,
                    avatar=payload.avatar,
                    description=payload.description,
                    owner_account_type=str(session.account_type),
                    owner_account_id=session.account_id,
                    status=GroupStatus.ENABLED.value,
                    join_mode=payload.join_mode,
                    max_members=payload.max_members,
                    member_count=1,
                    extra={},
                )
            )
            # 添加群主为成员
            await self.repo.add_member(
                group_id=group.id,
                account_type=str(session.account_type),
                account_id=session.account_id,
                role=ConversationMemberRole.OWNER.value,
            )
            # 自动创建会话
            await self._create_group_conversation(group.id, payload.name, session)

        return to_schema(MsgGroupSchema, group)

    async def update_group(
        self, payload: GroupUpdateRequest, session: SessionPayload
    ) -> MsgGroupSchema:
        """更新群组信息，仅群主可操作。"""
        async with transactional(self.db):
            if not await self.repo.is_owner(
                payload.id, str(session.account_type), session.account_id
            ):
                raise BusinessError("Only the group owner can update group info")

            group = await self.repo.update_group_fields(
                group_id=payload.id,
                name=payload.name,
                avatar=payload.avatar,
                description=payload.description,
                join_mode=payload.join_mode,
                max_members=payload.max_members,
            )
        return to_schema(MsgGroupSchema, group)

    async def dissolve(self, payload: GroupDetailRequest, session: SessionPayload) -> None:
        """解散群组，仅群主可操作。"""
        group_id = payload.id
        async with transactional(self.db):
            if not await self.repo.is_owner(
                group_id, str(session.account_type), session.account_id
            ):
                raise BusinessError("Only the group owner can dissolve the group")

            await self.repo.update_group_fields(
                group_id=group_id, status=GroupStatus.DISSOLVED.value
            )
            # 将会话标记为已禁用
            await self._disable_group_conversation(group_id)

    async def leave(self, payload: GroupDetailRequest, session: SessionPayload) -> None:
        """退出群组，群主不可退出。"""
        group_id = payload.id
        account_type = str(session.account_type)
        account_id = session.account_id

        if await self.repo.is_owner(group_id, account_type, account_id):
            raise BusinessError(
                "Owner cannot leave the group. Dissolve or transfer ownership first."
            )

        member = await self.repo.get_member(group_id, account_type, account_id)
        if member is None:
            raise BusinessError("You are not a member of this group")

        async with transactional(self.db):
            await self.repo.remove_member(group_id, account_type, account_id)
            await self.repo.decrement_member_count(group_id)
            await self._remove_member_from_conversation(group_id, account_type, account_id)

    async def my_list(self, session: SessionPayload) -> list[MsgGroupSchema]:
        """列出我的群组，含 member_count 与待处理申请数。"""
        account_type = str(session.account_type)
        account_id = session.account_id

        groups = await self.repo.list_my_groups(account_type, account_id)
        schemas = to_schema_list(MsgGroupSchema, groups)
        return schemas

    async def search_groups(
        self, query: GroupSearchQuery, session: SessionPayload
    ) -> list[MsgGroupSchema]:
        """按名称搜索群组；标记成员关系/待申请状态供 UI 展示。"""
        keyword = query.keyword
        account_type = str(session.account_type)
        account_id = session.account_id
        my_groups = await self.repo.list_my_groups(account_type, account_id)
        member_ids = {g.id for g in my_groups}
        my_reqs = await self.repo.list_my_join_requests(account_type, account_id)
        pending_ids = {
            r.group_id for r in my_reqs if r.status == GroupJoinRequestStatus.PENDING.value
        }
        groups = await self.repo.search_groups(keyword, exclude_group_ids=[])
        result: list[MsgGroupSchema] = []
        for g in groups:
            schema = to_schema(MsgGroupSchema, g)
            schema.is_member = g.id in member_ids
            schema.has_pending_request = g.id in pending_ids
            result.append(schema)
        return result

    async def group_detail(self, query: IdQuery, session: SessionPayload) -> MsgGroupSchema:
        """获取群组详情，校验用户是否为成员。"""
        group_id = query.id
        account_type = str(session.account_type)
        account_id = session.account_id

        group = await self.repo.get_required(group_id)
        member = await self.repo.get_member(group_id, account_type, account_id)
        if member is None:
            raise BusinessError("You are not a member of this group")
        return to_schema(MsgGroupSchema, group)

    # ==================== 群组成员 ====================

    async def list_members(
        self, query: IdQuery, session: SessionPayload
    ) -> list[GroupMemberSchema]:
        """列出群成员及资料（姓名/头像），批量加载 profile。"""
        group_id = query.id
        members = await self.repo.list_members(group_id)
        if not members:
            return []

        admin_ids = []
        portal_ids = []
        for m in members:
            (admin_ids if m.account_type == "ADMIN" else portal_ids).append(m.account_id)
        admin_profiles = await get_profiles_batch(self.db, "ADMIN", admin_ids) if admin_ids else {}
        portal_profiles = (
            await get_profiles_batch(self.db, "PORTAL", portal_ids) if portal_ids else {}
        )

        schemas = []
        for m in members:
            schema = to_schema(GroupMemberSchema, m)
            profiles = admin_profiles if m.account_type == "ADMIN" else portal_profiles
            profile = profiles.get(m.account_id)
            if profile:
                schema.profile_name = profile.name or profile.nickname
                schema.profile_avatar = resolve_file_url(profile.avatar)
            schemas.append(schema)
        return schemas

    async def add_members(self, payload: GroupMemberAddRequest, session: SessionPayload) -> None:
        """向群组添加成员，仅群主/管理员可操作。"""
        async with transactional(self.db):
            if not await self.repo.is_owner_or_admin(
                payload.group_id, str(session.account_type), session.account_id
            ):
                raise BusinessError("Only owner or admin can add members")

            group = await self.repo.get_required(payload.group_id)
            count = len(payload.members)
            if group.member_count + count > group.max_members:
                raise BusinessError("Group is full")

            member_tuples = [(m["account_type"], m["account_id"]) for m in payload.members]
            await self.repo.add_members_batch(payload.group_id, member_tuples)
            await self.repo.increment_member_count(payload.group_id, delta=count)

            # 同时将成员加入会话
            for acct_type, acct_id in member_tuples:
                await self._add_member_to_conversation(
                    payload.group_id, acct_type, acct_id, role="MEMBER"
                )

    async def remove_members(
        self, payload: GroupMemberRemoveRequest, session: SessionPayload
    ) -> None:
        """从群组移除成员，仅群主/管理员可操作。"""
        async with transactional(self.db):
            if not await self.repo.is_owner_or_admin(
                payload.group_id, str(session.account_type), session.account_id
            ):
                raise BusinessError("Only owner or admin can remove members")

            # 不可移除群主
            group = await self.repo.get_required(payload.group_id)
            if (
                group.owner_account_type == payload.account_type
                and group.owner_account_id == payload.account_id
            ):
                raise BusinessError("Cannot remove the group owner")

            member = await self.repo.get_member(
                payload.group_id, payload.account_type, payload.account_id
            )
            if member is None:
                raise BusinessError("User is not a member of this group")

            await self.repo.remove_member(
                payload.group_id, payload.account_type, payload.account_id
            )
            await self.repo.decrement_member_count(payload.group_id)
            await self._remove_member_from_conversation(
                payload.group_id,
                payload.account_type,
                payload.account_id,
            )

    async def set_member_role(self, payload: SetMemberRoleRequest, session: SessionPayload) -> None:
        """设置成员角色，仅群主可变更。"""
        async with transactional(self.db):
            if not await self.repo.is_owner(
                payload.group_id, str(session.account_type), session.account_id
            ):
                raise BusinessError("Only the group owner can set member roles")

            member = await self.repo.get_member(
                payload.group_id, payload.account_type, payload.account_id
            )
            if member is None:
                raise BusinessError("User is not a member of this group")

            await self.repo.update_member_role(
                payload.group_id, payload.account_type, payload.account_id, payload.role
            )

    # ==================== 入群申请 ====================

    async def apply_join(self, payload: GroupJoinRequestCreate, session: SessionPayload) -> None:
        """申请加入群组（已是成员 / 已有待处理申请时幂等成功）。"""
        group = await self.repo.get_required(payload.group_id)
        if group.status == GroupStatus.DISSOLVED.value:
            raise BusinessError("Group has been dissolved")

        account_type = str(session.account_type)
        account_id = session.account_id

        existing_member = await self.repo.get_member(payload.group_id, account_type, account_id)
        if existing_member is not None:
            return

        existing_pending = await self.repo.get_pending_join_request(
            payload.group_id, account_type, account_id
        )
        if existing_pending is not None:
            return

        created_or_reactivated = False
        request = None

        async with transactional(self.db):
            existing_any = await self.repo.get_any_join_request(
                payload.group_id, account_type, account_id
            )
            if existing_any is not None:
                if existing_any.status == GroupJoinRequestStatus.ACCEPTED.value:
                    return
                # REJECTED → 允许重新申请
                existing_any.status = GroupJoinRequestStatus.PENDING.value
                existing_any.message = payload.message
                existing_any.handled_by_type = None
                existing_any.handled_by_id = None
                existing_any.handled_at = None
                await self.db.flush()
                request = existing_any
                created_or_reactivated = True
            else:
                request = await self.repo.create_join_request(
                    group_id=payload.group_id,
                    applicant_type=account_type,
                    applicant_id=account_id,
                    message=payload.message,
                )
                created_or_reactivated = True

        if created_or_reactivated and request is not None:
            try:
                await self._push_join_request_created(
                    request,
                    payload,
                    account_type,
                    account_id,
                    group.name,
                )
            except Exception:
                pass

    async def handle_join_request(
        self, payload: GroupJoinRequestHandle, session: SessionPayload
    ) -> None:
        """处理入群申请（同意/拒绝），仅群主/管理员可操作。"""
        async with transactional(self.db):
            join_request = await self.repo.get_join_request_by_id(payload.id)
            if join_request is None:
                raise BusinessError("Join request not found")
            if join_request.status != GroupJoinRequestStatus.PENDING.value:
                raise BusinessError("Join request has already been handled")

            group = await self.repo.get_required(join_request.group_id)

            if not await self.repo.is_owner_or_admin(
                join_request.group_id, str(session.account_type), session.account_id
            ):
                raise BusinessError("Only owner or admin can handle join requests")

            now = datetime.now(UTC)
            join_request.status = payload.status
            join_request.handled_by_type = str(session.account_type)
            join_request.handled_by_id = session.account_id
            join_request.handled_at = now

            if payload.status == GroupJoinRequestStatus.ACCEPTED.value:
                # 检查是否已是成员
                existing_member = await self.repo.get_member(
                    join_request.group_id,
                    join_request.applicant_type,
                    join_request.applicant_id,
                )
                if existing_member is None:
                    if group.member_count + 1 > group.max_members:
                        raise BusinessError("Group is full, cannot accept this request")
                    await self.repo.add_member(
                        group_id=join_request.group_id,
                        account_type=join_request.applicant_type,
                        account_id=join_request.applicant_id,
                    )
                    await self.repo.increment_member_count(join_request.group_id)
                    # 同时加入会话
                    await self._add_member_to_conversation(
                        join_request.group_id,
                        join_request.applicant_type,
                        join_request.applicant_id,
                        role="MEMBER",
                    )

            await self.db.flush()

        # 通过 IM 向申请人推送处理结果通知
        try:
            from app.modules.message.im import PushEvent, im_router

            await im_router.push(
                join_request.applicant_type,
                join_request.applicant_id,
                PushEvent.GROUP_JOIN_HANDLED,
                {
                    "request_id": join_request.id,
                    "group_id": group.id,
                    "group_name": group.name,
                    "status": payload.status,
                },
                enqueue_offline_if_absent=False,
            )
        except Exception:
            pass

    async def _push_join_request_created(
        self,
        request: object,
        payload: object,
        account_type: str,
        account_id: str,
        group_name: str | None = None,
    ) -> None:
        """通过 IM 向群主/管理员推送新入群申请通知。"""
        from app.modules.message.im import PushEvent, im_router

        try:
            profiles = await get_profiles_batch(self.db, account_type, [account_id])
            profile = profiles.get(account_id)
        except Exception:
            profile = None

        push_payload = {
            "id": request.id,
            "group_id": payload.group_id,
            "applicant_type": account_type,
            "applicant_id": account_id,
            "message": payload.message,
            "status": "PENDING",
            "created_at": (
                request.created_at.isoformat()
                if hasattr(request, "created_at") and request.created_at
                else None
            ),
            "applicant_name": profile.name if profile else None,
            "applicant_avatar": profile.avatar if profile else None,
            "group_name": group_name,
        }

        members = await self.repo.list_members(payload.group_id)
        targets = [
            (member.account_type, member.account_id)
            for member in members
            if member.role in ("OWNER", "ADMIN")
        ]
        await im_router.push_many(
            targets,
            PushEvent.GROUP_JOIN_REQUEST,
            push_payload,
        )

    async def my_join_requests(self, session: SessionPayload) -> list[GroupJoinRequestSchema]:
        """列出我的入群申请，含 profile 与群组信息。"""
        requests = await self.repo.list_my_join_requests(
            str(session.account_type), session.account_id
        )
        return await self._enrich_join_requests(requests)

    async def pending_requests(self, session: SessionPayload) -> list[GroupJoinRequestSchema]:
        """列出我管理群组的待处理入群申请。"""
        account_type = str(session.account_type)
        account_id = session.account_id

        my_groups = await self.repo.list_my_groups(account_type, account_id)
        managed_group_ids = [
            g.id
            for g in my_groups
            if g.owner_account_type == account_type and g.owner_account_id == account_id
        ]
        # 同时包含我担任管理员的群组
        stmt = select(MsgGroupMember.group_id).where(
            MsgGroupMember.account_type == account_type,
            MsgGroupMember.account_id == account_id,
            MsgGroupMember.left_at.is_(None),
            MsgGroupMember.role.in_(
                [
                    ConversationMemberRole.OWNER.value,
                    ConversationMemberRole.ADMIN.value,
                ]
            ),
        )
        rows = list((await self.db.execute(stmt)).scalars().all())
        managed_group_ids = list(set(managed_group_ids + rows))

        if not managed_group_ids:
            return []

        requests = await self.repo.list_pending_requests(managed_group_ids)
        return await self._enrich_join_requests(requests)

    async def pending_count(self, session: SessionPayload) -> int:
        """获取我管理群组的待处理入群申请数量。"""
        account_type = str(session.account_type)
        account_id = session.account_id

        stmt = select(MsgGroupMember.group_id).where(
            MsgGroupMember.account_type == account_type,
            MsgGroupMember.account_id == account_id,
            MsgGroupMember.left_at.is_(None),
            MsgGroupMember.role.in_(
                [
                    ConversationMemberRole.OWNER.value,
                    ConversationMemberRole.ADMIN.value,
                ]
            ),
        )
        rows = list((await self.db.execute(stmt)).scalars().all())
        managed_group_ids = list(set(rows))

        if not managed_group_ids:
            return 0

        counts = await self.repo.count_pending_requests(managed_group_ids)
        return sum(counts.values())

    # ==================== 私有辅助 ====================

    async def _enrich_join_requests(
        self, requests: list[MsgGroupJoinRequest]
    ) -> list[GroupJoinRequestSchema]:
        """批量填充入群申请的申请人姓名/头像及群组名称。"""
        if not requests:
            return []

        admin_ids = []
        portal_ids = []
        group_ids = set()
        for req in requests:
            (admin_ids if req.applicant_type == "ADMIN" else portal_ids).append(req.applicant_id)
            group_ids.add(req.group_id)

        admin_profiles = await get_profiles_batch(self.db, "ADMIN", admin_ids) if admin_ids else {}
        portal_profiles = (
            await get_profiles_batch(self.db, "PORTAL", portal_ids) if portal_ids else {}
        )

        group_names = {}
        if group_ids:
            from sqlalchemy import select

            from app.modules.message.group.model import MsgGroup

            stmt = select(MsgGroup.id, MsgGroup.name).where(MsgGroup.id.in_(list(group_ids)))
            rows = (await self.db.execute(stmt)).all()
            group_names = {str(r[0]): str(r[1]) for r in rows}

        schemas = []
        for req in requests:
            schema = to_schema(GroupJoinRequestSchema, req)
            profiles = admin_profiles if req.applicant_type == "ADMIN" else portal_profiles
            profile = profiles.get(req.applicant_id)
            if profile:
                schema.applicant_name = profile.name or profile.nickname
                schema.applicant_avatar = resolve_file_url(profile.avatar)
            schema.group_name = group_names.get(req.group_id)
            schemas.append(schema)
        return schemas

    async def _create_group_conversation(
        self, group_id: str, group_name: str, session: SessionPayload
    ) -> None:
        """为群组创建会话并将创建者添加为成员。"""
        from datetime import datetime

        from app.modules.message.conversation.model import MsgConversation, MsgConversationMember

        conversation = MsgConversation(
            conversation_type=ConversationType.GROUP.value,
            title=group_name,
            group_id=group_id,
            owner_account_type=str(session.account_type),
            owner_account_id=session.account_id,
            status=ConversationStatus.ACTIVE.value,
        )
        self.db.add(conversation)
        await self.db.flush()

        # 将群组创建者添加为会话成员
        member = MsgConversationMember(
            conversation_id=conversation.id,
            account_type=str(session.account_type),
            account_id=session.account_id,
            role=ConversationMemberRole.OWNER.value,
            joined_at=datetime.now(UTC),
        )
        self.db.add(member)
        await self.db.flush()

    async def _get_group_conversation(self, group_id: str):
        """获取群组的活跃会话，无则返回 None。"""
        from app.modules.message.conversation.model import MsgConversation

        stmt = select(MsgConversation).where(
            MsgConversation.group_id == group_id,
            MsgConversation.conversation_type == ConversationType.GROUP.value,
            MsgConversation.status == ConversationStatus.ACTIVE.value,
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def _add_member_to_conversation(
        self, group_id: str, account_type: str, account_id: str, role: str = "MEMBER"
    ) -> None:
        """若尚未是会话成员，将用户加入群组的活跃会话。"""
        from datetime import datetime

        from app.modules.message.conversation.model import MsgConversationMember

        conversation = await self._get_group_conversation(group_id)
        if conversation is None:
            return

        existing = select(MsgConversationMember).where(
            MsgConversationMember.conversation_id == conversation.id,
            MsgConversationMember.account_type == account_type,
            MsgConversationMember.account_id == account_id,
            MsgConversationMember.left_at.is_(None),
        )
        if (await self.db.execute(existing)).scalar_one_or_none() is not None:
            return

        member = MsgConversationMember(
            conversation_id=conversation.id,
            account_type=account_type,
            account_id=account_id,
            role=role,
            joined_at=datetime.now(UTC),
        )
        self.db.add(member)

    async def _remove_member_from_conversation(
        self, group_id: str, account_type: str, account_id: str
    ) -> None:
        """将会话成员移出群组会话（通过 left_at 软删除）。"""
        from app.modules.message.conversation.model import MsgConversation

        stmt = select(MsgConversation).where(
            MsgConversation.group_id == group_id,
            MsgConversation.conversation_type == ConversationType.GROUP.value,
        )
        conversation = (await self.db.execute(stmt)).scalar_one_or_none()
        if conversation is None:
            return

        from app.modules.message.conversation.repository import MsgConversationRepository

        await MsgConversationRepository(self.db).remove_member(
            conversation.id, account_type, account_id
        )

    async def _disable_group_conversation(self, group_id: str) -> None:
        """将群组会话标记为已禁用。"""
        from app.modules.message.conversation.model import MsgConversation

        stmt = select(MsgConversation).where(
            MsgConversation.group_id == group_id,
            MsgConversation.conversation_type == ConversationType.GROUP.value,
        )
        conversation = (await self.db.execute(stmt)).scalar_one_or_none()
        if conversation:
            conversation.status = ConversationStatus.DISABLED.value
            await self.db.flush()
