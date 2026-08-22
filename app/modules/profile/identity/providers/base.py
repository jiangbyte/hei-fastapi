"""Author: Charlie

第三方实人认证 Provider 协议。
"""

from typing import Protocol

from app.modules.profile.identity.model import RealNameCase
from app.modules.profile.identity.schema import (
    RealNameCaseCallbackRequest,
    RealNameCaseInitResponse,
    RealNameCaseInitThirdPartyRequest,
)


class IdentityVerifyProvider(Protocol):
    def provider_code(self) -> str: ...

    def supports(self, verify_channel: str, document_type: str) -> bool: ...

    async def init_verify(
        self,
        case: RealNameCase,
        param: RealNameCaseInitThirdPartyRequest,
    ) -> RealNameCaseInitResponse: ...

    async def handle_callback(
        self,
        case: RealNameCase,
        param: RealNameCaseCallbackRequest,
    ) -> None: ...
