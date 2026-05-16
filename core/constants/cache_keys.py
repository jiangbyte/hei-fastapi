# Redis cache keys
from core.enums import LoginTypeEnum

# Permission
PERMISSION_CACHE_KEY = "hei:permission:keys"

# Auth token / session
TOKEN_PREFIX_BUSINESS = "hei:auth:" + LoginTypeEnum.BUSINESS + ":token:"
SESSION_PREFIX_BUSINESS = "hei:auth:" + LoginTypeEnum.BUSINESS + ":session:"
DISABLE_KEY_BUSINESS = "hei:auth:" + LoginTypeEnum.BUSINESS + ":disable:"

TOKEN_PREFIX_CONSUMER = "hei:auth:" + LoginTypeEnum.CONSUMER + ":token:"
SESSION_PREFIX_CONSUMER = "hei:auth:" + LoginTypeEnum.CONSUMER + ":session:"
DISABLE_KEY_CONSUMER = "hei:auth:" + LoginTypeEnum.CONSUMER + ":disable:"

# Dict
DICT_CACHE_KEY = "hei:dict:tree"
DICT_TREE_CACHE_KEY = "hei:dict:fulltree"

# Captcha
CAPTCHA_BUSINESS_CACHE_KEY = LoginTypeEnum.BUSINESS + ":captcha:"
CAPTCHA_CONSUMER_CACHE_KEY = LoginTypeEnum.CONSUMER + ":captcha:"

NO_REPEAT_PREFIX = "norepeat:"
