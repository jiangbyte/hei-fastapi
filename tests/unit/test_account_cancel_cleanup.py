""" Author: Charlie """

from app.modules.iam.account.repository import _ACCOUNT_SUBJECT_RELATION_TYPES
from app.modules.iam.enums import IamRelationType


def test_account_cleanup_covers_client_resource_grants():
    assert IamRelationType.SUBJECT_CLIENT_RESOURCE_GRANT in _ACCOUNT_SUBJECT_RELATION_TYPES
    assert IamRelationType.SUBJECT_RESOURCE_GRANT in _ACCOUNT_SUBJECT_RELATION_TYPES
    assert IamRelationType.ACCOUNT_ROLE in _ACCOUNT_SUBJECT_RELATION_TYPES
