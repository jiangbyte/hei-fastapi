""" Author: Charlie """

from app.core.config.enums import AccountType
from app.core.config.settings import settings
from app.core.exceptions.business import AuthenticationError
from app.modules.auth.policy import get_login_policy
from app.platform.cache.keys import (
    login_failure_account_key,
    login_failure_ip_key,
    login_lock_account_key,
    login_lock_ip_key,
)
from app.platform.cache.redis import get_redis
from app.platform.observability.metrics import record_login_lock


class LoginProtectionService:
    """基于 Redis 的登录限流，按账户与客户端 IP 统计。"""

    async def ensure_allowed(
        self,
        *,
        account_type: AccountType,
        account: str,
        client_ip: str | None,
    ) -> None:
        redis = get_redis()
        if redis is None:
            return
        normalized_account = self._normalize_account(account)
        if await redis.get(login_lock_account_key(account_type.value, normalized_account)):
            raise AuthenticationError("Account is temporarily locked")
        if client_ip and await redis.get(login_lock_ip_key(account_type.value, client_ip)):
            raise AuthenticationError("Too many failed login attempts from this IP")

    async def record_failure(
        self,
        *,
        account_type: AccountType,
        account: str,
        client_ip: str | None,
    ) -> None:
        redis = get_redis()
        if redis is None:
            return
        policy = get_login_policy(account_type)
        normalized_account = self._normalize_account(account)
        await self._increase_failure(
            redis,
            key=login_failure_account_key(account_type.value, normalized_account),
            lock_key=login_lock_account_key(account_type.value, normalized_account),
            max_failures=policy.max_failures,
            window_seconds=policy.failure_window_seconds,
            lock_seconds=policy.lock_seconds,
            account_type=account_type.value,
            scope="account",
        )
        if client_ip:
            await self._increase_failure(
                redis,
                key=login_failure_ip_key(account_type.value, client_ip),
                lock_key=login_lock_ip_key(account_type.value, client_ip),
                max_failures=settings.auth.login_ip_max_failures,
                window_seconds=settings.auth.login_failure_window_seconds,
                lock_seconds=settings.auth.login_lock_seconds,
                account_type=account_type.value,
                scope="ip",
            )

    async def record_success(
        self,
        *,
        account_type: AccountType,
        account: str,
        client_ip: str | None,
    ) -> None:
        redis = get_redis()
        if redis is None:
            return
        normalized_account = self._normalize_account(account)
        keys = [login_failure_account_key(account_type.value, normalized_account)]
        if client_ip:
            keys.append(login_failure_ip_key(account_type.value, client_ip))
        try:
            await redis.delete(*keys)
        except TypeError:
            for key in keys:
                await redis.delete(key)

    async def _increase_failure(
        self,
        redis,
        *,
        key: str,
        lock_key: str,
        max_failures: int,
        window_seconds: int,
        lock_seconds: int,
        account_type: str,
        scope: str,
    ) -> None:
        count = await self._increment_failure_counter(redis, key, window_seconds)
        if count >= max_failures:
            await redis.setex(lock_key, lock_seconds, "1")
            await redis.delete(key)
            record_login_lock(account_type, scope)

    async def _increment_failure_counter(self, redis, key: str, window_seconds: int) -> int:
        if hasattr(redis, "incr"):
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, window_seconds)
            return int(count)
        raw = await redis.get(key)
        count = int(raw or 0) + 1
        await redis.setex(key, window_seconds, str(count))
        return count

    def _normalize_account(self, account: str) -> str:
        return account.strip().lower()


login_protection_service = LoginProtectionService()
