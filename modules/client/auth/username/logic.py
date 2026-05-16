import bcrypt
from fastapi import Request
from core.auth import HeiClientAuthTool
from core.db import SessionLocal
from core.exception import BusinessException
from core.enums import UserStatusEnum
from core.utils import decrypt, generate_id
from core.utils.user_agent_utils import get_browser
from core.captcha import c_captcha
from core.log import record_auth_log
from .params import UsernameLoginParam, UsernameLoginResult, UsernameRegisterParam, UsernameRegisterResult, UsernameLogoutResult
from modules.client.user.models import ClientUser
import logging

logger = logging.getLogger(__name__)

_login_user_api = None


def init_auth(login_user_api):
    global _login_user_api
    _login_user_api = login_user_api


async def do_login(param: UsernameLoginParam, request: Request) -> UsernameLoginResult:
    try:
        await c_captcha.check_captcha(param.captcha_id, param.captcha_code)
    except Exception as e:
        raise BusinessException(str(e))

    user_info = _login_user_api.get_login_user_info_by_username(param.username)

    try:
        if not user_info:
            logger.warning(f"User not found: {param.username}")
            raise BusinessException("用户名或密码错误")

        if user_info.status == UserStatusEnum.LOCKED.value:
            logger.warning(f"User account is locked: {param.username}")
            raise BusinessException("账号已被锁定")
        if user_info.status == UserStatusEnum.INACTIVE.value:
            logger.warning(f"User account is inactive: {param.username}")
            raise BusinessException("账号已停用")
        if user_info.status != UserStatusEnum.ACTIVE.value:
            logger.warning(f"User account status abnormal: {param.username}, status={user_info.status}")
            raise BusinessException("账号状态异常")

        try:
            raw_password = decrypt(param.password)
            if not bcrypt.checkpw(raw_password.encode('utf-8'), user_info.password.encode('utf-8')):
                logger.warning("Password verification failed")
                raise BusinessException("用户名或密码错误")
        except BusinessException:
            raise
        except Exception as e:
            logger.warning(f"Password decryption failed: {e}")
            raise BusinessException("用户名或密码错误")

        extra = {
            "username": user_info.username,
            "nickname": user_info.nickname,
            "status": user_info.status
        }
        # Auto-detect device type from User-Agent, device_id from frontend
        user_agent = request.headers.get("User-Agent", "")
        extra["device_type"] = get_browser(user_agent)
        extra["device_id"] = param.device_id

        token = await HeiClientAuthTool.login(user_info.id, request, extra)

        # 记录登录信息
        db = None
        try:
            db = SessionLocal()
            from modules.client.user.service import ClientUserService
            ClientUserService(db).record_login(user_info.id, request)
        except Exception as e:
            logger.warning(f"Failed to record login info: {e}")
        finally:
            if db:
                db.close()

        # 记录登录日志
        record_auth_log(request, "登录", "LOGIN", op_user=user_info.username)

        return UsernameLoginResult(token=token)
    except BusinessException as e:
        record_auth_log(
            request, "登录", "LOGIN",
            exe_status="FAIL", exe_message=e.message,
            op_user=user_info.username if user_info else param.username,
        )
        request.state._exception_logged = True
        raise


async def do_register(param: UsernameRegisterParam) -> UsernameRegisterResult:
    try:
        await c_captcha.check_captcha(param.captcha_id, param.captcha_code)
    except Exception as e:
        raise BusinessException(str(e))

    db = SessionLocal()
    try:
        from sqlalchemy import select
        existing_user = db.scalar(
            select(ClientUser).where(ClientUser.username == param.username)
        )
        if existing_user:
            raise BusinessException("用户名已存在")

        raw_password = decrypt(param.password)
        hashed_password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user_id = str(generate_id())

        user = ClientUser(
            id=user_id,
            username=param.username,
            password=hashed_password,
            nickname=param.username,
            status=UserStatusEnum.ACTIVE.value,
            created_by=user_id,
        )
        db.add(user)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return UsernameRegisterResult(message="注册成功")


async def do_logout(request: Request) -> UsernameLogoutResult:
    # 获取当前用户用于日志记录
    try:
        user_id = await HeiClientAuthTool.getLoginIdDefaultNull(request)
        if user_id:
            db = SessionLocal()
            try:
                from modules.client.user.service import ClientUserService
                entity = ClientUserService(db).find_by_id(user_id)
                op_user = entity.username if entity else None
                record_auth_log(request, "登出", "LOGOUT", op_user=op_user)
            finally:
                db.close()
    except Exception as e:
        logger.warning(f"Failed to record logout log: {e}")

    await HeiClientAuthTool.logout(request=request)
    return UsernameLogoutResult(message="登出成功")
