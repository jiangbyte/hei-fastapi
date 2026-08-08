""" Author: Charlie

破坏性清理：删除 dotted/废弃 sys_config key，补齐 UPPER_SNAKE 默认行（不覆盖已有值）。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "q0a1b2c3d4e5"
down_revision: str | Sequence[str] | None = "p9d0e1f2a3b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 8, tzinfo=UTC)

_LEGACY_KEYS: tuple[str, ...] = (
    "audit_alert.enabled",
    "audit_alert.webhook_url",
    "audit_alert.webhook_secret",
    "audit_alert.analysis_interval_seconds",
    "audit_alert.alert_cooldown_seconds",
    "audit_alert.rule_brute_force",
    "audit_alert.rule_unusual_hours",
    "audit_alert.rule_sensitive_ops",
    "audit_alert.rule_bulk_delete",
    "audit_alert.rule_ip_anomaly",
    "audit_alert.brute_force_threshold",
    "audit_alert.bulk_delete_threshold",
    "audit_alert.ip_anomaly_threshold",
    "auth.login_failure_window_seconds",
    "auth.login_account_max_failures",
    "auth.login_ip_max_failures",
    "auth.login_lock_seconds",
    "auth.default_password",
    "auth.portal_register_enabled",
    "auth.token_ttl_seconds",
    "auth.password_reset_token_ttl_seconds",
    "mail.host",
    "mail.port",
    "mail.username",
    "mail.password",
    "mail.from_email",
    "mail.from_name",
    "mail.use_tls",
    "mail.template.forgot_password.subject",
    "mail.template.forgot_password.body",
    "storage.presign_expire_seconds",
    "MAIL_LOCAL_USE_TLS",
    "PUSH_WECHAT_WORK_SECRET",
)

_SEED_ROWS: tuple[tuple[str, str, str, str, str, int, str, str, str | None, str | None], ...] = (
    ("cfg_df34085b029aedc6", "AUTH_TOKEN_TTL_SECONDS", "2592000", "AUTH_TOKEN", "Token 过期时间（秒），默认 30 天", 1, "INT", "Token 过期时间（秒），默认 30 天", None, None),
    ("cfg_9f4ba41bf4cec420", "AUTH_PASSWORD_RESET_TOKEN_TTL_SECONDS", "600", "AUTH_TOKEN", "密码重置 Token 有效期（秒）", 2, "INT", "密码重置 Token 有效期（秒）", None, None),
    ("cfg_e292016eaa176cd4", "AUTH_LOGIN_FAILURE_WINDOW_SECONDS", "900", "AUTH_LOGIN", "登录失败统计窗口（秒）", 1, "INT", "登录失败统计窗口（秒）", None, None),
    ("cfg_59196f3cfe0c791e", "AUTH_LOGIN_ACCOUNT_MAX_FAILURES", "5", "AUTH_LOGIN", "单账号最大登录失败次数", 2, "INT", "单账号最大登录失败次数", None, None),
    ("cfg_397798808bce4338", "AUTH_LOGIN_IP_MAX_FAILURES", "30", "AUTH_LOGIN", "单 IP 最大登录失败次数", 3, "INT", "单 IP 最大登录失败次数", None, None),
    ("cfg_68e8e38dfe6653f4", "AUTH_LOGIN_LOCK_SECONDS", "900", "AUTH_LOGIN", "登录锁定时间（秒）", 4, "INT", "登录锁定时间（秒）", None, None),
    ("cfg_9288450cadd9127c", "AUTH_LOGIN_ADMIN_FAILURE_WINDOW_SECONDS", "300", "AUTH_LOGIN", "ADMIN 登录失败窗口（秒）", 10, "INT", "ADMIN 登录失败窗口（秒）", "ADMIN", None),
    ("cfg_521ad6a05b3b4ee2", "AUTH_LOGIN_ADMIN_MAX_FAILURES", "5", "AUTH_LOGIN", "ADMIN 最大失败次数", 11, "INT", "ADMIN 最大失败次数", "ADMIN", None),
    ("cfg_6346132727a3f118", "AUTH_LOGIN_ADMIN_LOCK_SECONDS", "300", "AUTH_LOGIN", "ADMIN 锁定时间（秒）", 12, "INT", "ADMIN 锁定时间（秒）", "ADMIN", None),
    ("cfg_3cf4009b79c4cdc0", "AUTH_LOGIN_ADMIN_ALLOW_PHONE", "TRUE", "AUTH_LOGIN", "ADMIN 允许手机号登录", 13, "BOOL", "ADMIN 允许手机号登录", "ADMIN", None),
    ("cfg_9801c7391e5a784b", "AUTH_LOGIN_ADMIN_PHONE_NO_USER_POLICY", "DENY", "AUTH_LOGIN", "ADMIN 手机号无用户策略", 14, "STRING", "ADMIN 手机号无用户策略", "ADMIN", None),
    ("cfg_85da42c429c11c0d", "AUTH_LOGIN_ADMIN_ALLOW_EMAIL", "TRUE", "AUTH_LOGIN", "ADMIN 允许邮箱登录", 15, "BOOL", "ADMIN 允许邮箱登录", "ADMIN", None),
    ("cfg_df6a5b9741f63718", "AUTH_LOGIN_ADMIN_EMAIL_NO_USER_POLICY", "DENY", "AUTH_LOGIN", "ADMIN 邮箱无用户策略", 16, "STRING", "ADMIN 邮箱无用户策略", "ADMIN", None),
    ("cfg_bd4d8532dd9d2c7b", "AUTH_LOGIN_ADMIN_ALLOW_OTP", "TRUE", "AUTH_LOGIN", "ADMIN 允许 OTP 登录", 17, "BOOL", "ADMIN 允许 OTP 登录", "ADMIN", None),
    ("cfg_a3edc3fb337f0fd5", "AUTH_LOGIN_PORTAL_FAILURE_WINDOW_SECONDS", "300", "AUTH_LOGIN", "PORTAL 登录失败窗口（秒）", 18, "INT", "PORTAL 登录失败窗口（秒）", "PORTAL", None),
    ("cfg_412ec5ff8977bee1", "AUTH_LOGIN_PORTAL_MAX_FAILURES", "5", "AUTH_LOGIN", "PORTAL 最大失败次数", 19, "INT", "PORTAL 最大失败次数", "PORTAL", None),
    ("cfg_c035540f2840759f", "AUTH_LOGIN_PORTAL_LOCK_SECONDS", "300", "AUTH_LOGIN", "PORTAL 锁定时间（秒）", 20, "INT", "PORTAL 锁定时间（秒）", "PORTAL", None),
    ("cfg_73263fd26598e245", "AUTH_LOGIN_PORTAL_ALLOW_PHONE", "TRUE", "AUTH_LOGIN", "PORTAL 允许手机号登录", 21, "BOOL", "PORTAL 允许手机号登录", "PORTAL", None),
    ("cfg_8c93f75be4a015eb", "AUTH_LOGIN_PORTAL_PHONE_NO_USER_POLICY", "DENY", "AUTH_LOGIN", "PORTAL 手机号无用户策略", 22, "STRING", "PORTAL 手机号无用户策略", "PORTAL", None),
    ("cfg_845bdae0cbb2866c", "AUTH_LOGIN_PORTAL_ALLOW_EMAIL", "TRUE", "AUTH_LOGIN", "PORTAL 允许邮箱登录", 23, "BOOL", "PORTAL 允许邮箱登录", "PORTAL", None),
    ("cfg_e4a6b916ed9e923f", "AUTH_LOGIN_PORTAL_EMAIL_NO_USER_POLICY", "DENY", "AUTH_LOGIN", "PORTAL 邮箱无用户策略", 24, "STRING", "PORTAL 邮箱无用户策略", "PORTAL", None),
    ("cfg_b48d4cced07926b7", "AUTH_LOGIN_PORTAL_ALLOW_OTP", "TRUE", "AUTH_LOGIN", "PORTAL 允许 OTP 登录", 25, "BOOL", "PORTAL 允许 OTP 登录", "PORTAL", None),
    ("cfg_7c7536455a677234", "AUTH_REGISTER_ADMIN_ENABLED", "FALSE", "AUTH_REGISTER", "ADMIN 开放注册", 1, "BOOL", "ADMIN 开放注册", "ADMIN", None),
    ("cfg_4c6acf8e5e9275d9", "AUTH_REGISTER_ADMIN_REQUIRE_PHONE", "FALSE", "AUTH_REGISTER", "ADMIN 注册要求手机号", 2, "BOOL", "ADMIN 注册要求手机号", "ADMIN", None),
    ("cfg_6706c37cfca883e5", "AUTH_REGISTER_ADMIN_REQUIRE_EMAIL", "FALSE", "AUTH_REGISTER", "ADMIN 注册要求邮箱", 3, "BOOL", "ADMIN 注册要求邮箱", "ADMIN", None),
    ("cfg_276a9cb536b95fbc", "AUTH_REGISTER_ADMIN_DEFAULT_ROLE_ID", "", "AUTH_REGISTER", "ADMIN 注册默认角色", 4, "STRING", "ADMIN 注册默认角色", "ADMIN", None),
    ("cfg_2a5bdbb1576b09a6", "AUTH_REGISTER_ADMIN_DEFAULT_DEPT_ID", "", "AUTH_REGISTER", "ADMIN 注册默认部门", 5, "STRING", "ADMIN 注册默认部门", "ADMIN", None),
    ("cfg_a319c9d83ece6ada", "AUTH_REGISTER_PORTAL_ENABLED", "TRUE", "AUTH_REGISTER", "PORTAL 开放注册", 6, "BOOL", "PORTAL 开放注册", "PORTAL", None),
    ("cfg_7135b647c2b3c035", "AUTH_REGISTER_PORTAL_REQUIRE_PHONE", "FALSE", "AUTH_REGISTER", "PORTAL 注册要求手机号", 7, "BOOL", "PORTAL 注册要求手机号", "PORTAL", None),
    ("cfg_3ec435822ae2d002", "AUTH_REGISTER_PORTAL_REQUIRE_EMAIL", "TRUE", "AUTH_REGISTER", "PORTAL 注册要求邮箱", 8, "BOOL", "PORTAL 注册要求邮箱", "PORTAL", None),
    ("cfg_df87e86056b8b640", "AUTH_REGISTER_PORTAL_DEFAULT_ROLE_ID", "", "AUTH_REGISTER", "PORTAL 注册默认角色", 9, "STRING", "PORTAL 注册默认角色", "PORTAL", None),
    ("cfg_1b209b614b7b162c", "AUTH_REGISTER_PORTAL_DEFAULT_DEPT_ID", "", "AUTH_REGISTER", "PORTAL 注册默认部门", 10, "STRING", "PORTAL 注册默认部门", "PORTAL", None),
    ("cfg_dcf0f111fb004344", "AUTH_DEFAULT_PASSWORD", "", "AUTH_PASSWORD", "新建账户默认密码", 1, "STRING", "新建账户默认密码", None, None),
    ("cfg_9c870cffa8867b07", "PASSWORD_CHANGE_VERIFY_METHOD", "OLD_PASSWORD", "AUTH_PASSWORD", "自助改密验证方式", 2, "STRING", "自助改密验证方式", None, None),
    ("cfg_21da174072a0f0bb", "PASSWORD_MIN_LENGTH", "8", "AUTH_PASSWORD", "密码最小长度", 10, "INT", "密码最小长度", None, None),
    ("cfg_2e41eb9efc88c078", "PASSWORD_MAX_LENGTH", "128", "AUTH_PASSWORD", "密码最大长度", 11, "INT", "密码最大长度", None, None),
    ("cfg_88c6b448c4e8042e", "PASSWORD_COMPLEXITY", "DIGITS_UPPER_LOWER_SPECIAL", "AUTH_PASSWORD", "密码复杂度", 12, "STRING", "密码复杂度", None, None),
    ("cfg_363c1bd765b8f5be", "PASSWORD_MAX_CONSECUTIVE_CHARS", "3", "AUTH_PASSWORD", "最大连续相同字符数", 13, "INT", "最大连续相同字符数", None, None),
    ("cfg_95047010c8cffed4", "PASSWORD_FORBID_USER_INFO", "TRUE", "AUTH_PASSWORD", "禁止包含用户信息", 14, "BOOL", "禁止包含用户信息", None, None),
    ("cfg_cf505abfcea42e3c", "PASSWORD_FORBID_HISTORICAL", "TRUE", "AUTH_PASSWORD", "禁止复用历史密码", 15, "BOOL", "禁止复用历史密码", None, None),
    ("cfg_1e8e0e5c42c8f7ab", "PASSWORD_HISTORY_CHECK_COUNT", "5", "AUTH_PASSWORD", "历史密码检查条数", 16, "INT", "历史密码检查条数", None, None),
    ("cfg_77632725699872aa", "PASSWORD_FORBID_WEAK_LIST", "TRUE", "AUTH_PASSWORD", "禁止弱密码库命中", 17, "BOOL", "禁止弱密码库命中", None, None),
    ("cfg_5fb99add24efb532", "PASSWORD_VALIDITY_DAYS", "90", "AUTH_PASSWORD", "密码有效期（天）", 18, "INT", "密码有效期（天）", None, None),
    ("cfg_d759b943eb3eba43", "PASSWORD_EXPIRY_WARNING_DAYS", "7", "AUTH_PASSWORD", "密码过期提前提醒（天）", 19, "INT", "密码过期提前提醒（天）", None, None),
    ("cfg_1da3474838da8c34", "PASSWORD_CUSTOM_WEAK_WORDS", "", "AUTH_PASSWORD", "自定义弱密码词（逗号分隔）", 20, "STRING", "自定义弱密码词（逗号分隔）", None, None),
    ("cfg_58414339bc280bd6", "DEFAULT_EMAIL_ENGINE", "LOCAL", "MAIL", "默认邮件引擎", 1, "STRING", "默认邮件引擎", None, None),
    ("cfg_2acb1f201faa512d", "MAIL_LOCAL_HOST", "localhost", "MAIL", "SMTP 服务器地址", 10, "STRING", "SMTP 服务器地址", None, None),
    ("cfg_84f70e8cc74e7e9b", "MAIL_LOCAL_PORT", "1025", "MAIL", "SMTP 端口", 11, "INT", "SMTP 端口", None, None),
    ("cfg_813571013d71784d", "MAIL_LOCAL_USERNAME", "", "MAIL", "SMTP 用户名", 12, "STRING", "SMTP 用户名", None, None),
    ("cfg_717b2404165e2b0a", "MAIL_LOCAL_PASSWORD", "", "MAIL", "SMTP 密码", 13, "STRING", "SMTP 密码", None, None),
    ("cfg_6cff7e453fe2304e", "MAIL_LOCAL_FROM_EMAIL", "test@hei-fastapi.local", "MAIL", "发件人邮箱", 14, "STRING", "发件人邮箱", None, None),
    ("cfg_e099681b11c0ee4f", "MAIL_LOCAL_FROM_NAME", "hei-fastapi", "MAIL", "发件人显示名称", 15, "STRING", "发件人显示名称", None, None),
    ("cfg_b2da3fee87e0dd1f", "MAIL_LOCAL_AUTH_REQUIRED", "FALSE", "MAIL", "SMTP 是否需要认证", 16, "BOOL", "SMTP 是否需要认证", None, None),
    ("cfg_802f8c2f3efd8536", "MAIL_LOCAL_USE_SSL", "FALSE", "MAIL", "SMTP 使用 SSL", 17, "BOOL", "SMTP 使用 SSL", None, None),
    ("cfg_27be176dc9266dcc", "MAIL_LOCAL_USE_STARTTLS", "FALSE", "MAIL", "SMTP 使用 STARTTLS", 18, "BOOL", "SMTP 使用 STARTTLS", None, None),
    ("cfg_b97b4627d571e9e9", "MAIL_ALIYUN_ACCESS_KEY_ID", "", "MAIL", "阿里云邮件 AccessKeyId", 20, "STRING", "阿里云邮件 AccessKeyId", None, None),
    ("cfg_dd0fc126a107b79e", "MAIL_ALIYUN_ACCESS_KEY_SECRET", "", "MAIL", "阿里云邮件 AccessKeySecret", 21, "STRING", "阿里云邮件 AccessKeySecret", None, None),
    ("cfg_972fbb9f8c160446", "MAIL_ALIYUN_ACCOUNT_NAME", "", "MAIL", "阿里云发信地址", 22, "STRING", "阿里云发信地址", None, None),
    ("cfg_75f3eafaf65e3cab", "MAIL_TENCENT_SECRET_ID", "", "MAIL", "腾讯云邮件 SecretId", 30, "STRING", "腾讯云邮件 SecretId", None, None),
    ("cfg_474cf1635e2d65d9", "MAIL_TENCENT_SECRET_KEY", "", "MAIL", "腾讯云邮件 SecretKey", 31, "STRING", "腾讯云邮件 SecretKey", None, None),
    ("cfg_eb6ff89b0555300f", "MAIL_TENCENT_FROM_EMAIL", "", "MAIL", "腾讯云发件邮箱", 32, "STRING", "腾讯云发件邮箱", None, None),
    ("cfg_84d3de8cd967733a", "DEFAULT_SMS_ENGINE", "ALIYUN", "SMS", "默认短信引擎", 1, "STRING", "默认短信引擎", None, None),
    ("cfg_4b0b045351490c90", "SMS_ALIYUN_ACCESS_KEY_ID", "", "SMS", "阿里云短信 AccessKeyId", 10, "STRING", "阿里云短信 AccessKeyId", None, None),
    ("cfg_e2bc3adc53a793ff", "SMS_ALIYUN_ACCESS_KEY_SECRET", "", "SMS", "阿里云短信 AccessKeySecret", 11, "STRING", "阿里云短信 AccessKeySecret", None, None),
    ("cfg_99dabb0bc6e4a331", "SMS_ALIYUN_SIGN_NAME", "", "SMS", "阿里云短信签名", 12, "STRING", "阿里云短信签名", None, None),
    ("cfg_b36d23e6047971bb", "SMS_TENCENT_SECRET_ID", "", "SMS", "腾讯云短信 SecretId", 20, "STRING", "腾讯云短信 SecretId", None, None),
    ("cfg_6028a8f49ab077ba", "SMS_TENCENT_SECRET_KEY", "", "SMS", "腾讯云短信 SecretKey", 21, "STRING", "腾讯云短信 SecretKey", None, None),
    ("cfg_ec651dd2afd644bc", "SMS_TENCENT_SDK_APP_ID", "", "SMS", "腾讯云短信 SdkAppId", 22, "STRING", "腾讯云短信 SdkAppId", None, None),
    ("cfg_e8fb8e521a365dc2", "SMS_TENCENT_SIGN_NAME", "", "SMS", "腾讯云短信签名", 23, "STRING", "腾讯云短信签名", None, None),
    ("cfg_57e28945f48834a9", "DEFAULT_MESSAGE_PUSH_ENGINE", "DINGTALK", "PUSH", "默认消息推送引擎", 1, "STRING", "默认消息推送引擎", None, None),
    ("cfg_89b4b2fd016928e6", "PUSH_DINGTALK_WEBHOOK", "", "PUSH", "钉钉 Webhook", 10, "STRING", "钉钉 Webhook", None, None),
    ("cfg_6d571cb0b08380d9", "PUSH_DINGTALK_SECRET", "", "PUSH", "钉钉加签密钥", 11, "STRING", "钉钉加签密钥", None, None),
    ("cfg_879c74e0d724800e", "PUSH_LARK_WEBHOOK", "", "PUSH", "飞书 Webhook", 20, "STRING", "飞书 Webhook", None, None),
    ("cfg_1d568c38d7ec2f23", "PUSH_LARK_SECRET", "", "PUSH", "飞书加签密钥", 21, "STRING", "飞书加签密钥", None, None),
    ("cfg_0680575e52e15d07", "PUSH_WECHAT_WORK_WEBHOOK", "", "PUSH", "企业微信 Webhook", 30, "STRING", "企业微信 Webhook", None, None),
    ("cfg_a2be24a3a6abeff0", "AUDIT_ALERT_ENABLED", "TRUE", "AUDIT_ALERT", "审计告警总开关", 1, "BOOL", "审计告警总开关", None, None),
    ("cfg_2299a1e718af6f56", "AUDIT_ALERT_NOTIFY_EMAIL", "TRUE", "AUDIT_ALERT", "邮件通知", 2, "BOOL", "邮件通知", None, None),
    ("cfg_bdd06a9ecd9561a0", "AUDIT_ALERT_NOTIFY_PUSH", "TRUE", "AUDIT_ALERT", "推送通知", 3, "BOOL", "推送通知", None, None),
    ("cfg_5ab4365d79759a36", "AUDIT_ALERT_NOTIFY_CUSTOM_WEBHOOK", "FALSE", "AUDIT_ALERT", "自定义 Webhook 通知", 4, "BOOL", "自定义 Webhook 通知", None, None),
    ("cfg_1fb16a022bd1ee13", "AUDIT_ALERT_WEBHOOK_URL", "", "AUDIT_ALERT", "Webhook 地址", 5, "STRING", "Webhook 地址", None, None),
    ("cfg_295649e7a593148c", "AUDIT_ALERT_WEBHOOK_SECRET", "", "AUDIT_ALERT", "Webhook 签名密钥", 6, "STRING", "Webhook 签名密钥", None, None),
    ("cfg_2370fd3a6f2f8c68", "AUDIT_ALERT_ANALYSIS_INTERVAL_SECONDS", "60", "AUDIT_ALERT", "分析周期(秒)", 7, "INT", "分析周期(秒)", None, None),
    ("cfg_3091f8900b127ff5", "AUDIT_ALERT_ALERT_COOLDOWN_SECONDS", "1800", "AUDIT_ALERT", "告警冷却(秒)", 8, "INT", "告警冷却(秒)", None, None),
    ("cfg_f7f86f743c41c302", "AUDIT_ALERT_RULE_BRUTE_FORCE", "TRUE", "AUDIT_ALERT", "暴力破解检测", 10, "BOOL", "暴力破解检测", None, None),
    ("cfg_88059105f3bfd3bd", "AUDIT_ALERT_RULE_UNUSUAL_HOURS", "TRUE", "AUDIT_ALERT", "异常时间操作检测", 11, "BOOL", "异常时间操作检测", None, None),
    ("cfg_8394da8a8cca0551", "AUDIT_ALERT_RULE_SENSITIVE_OPS", "TRUE", "AUDIT_ALERT", "敏感操作监控", 12, "BOOL", "敏感操作监控", None, None),
    ("cfg_1be5b5a733cdb21b", "AUDIT_ALERT_RULE_BULK_DELETE", "TRUE", "AUDIT_ALERT", "批量删除检测", 13, "BOOL", "批量删除检测", None, None),
    ("cfg_452a32888fa5d2f8", "AUDIT_ALERT_RULE_IP_ANOMALY", "TRUE", "AUDIT_ALERT", "IP 异常检测", 14, "BOOL", "IP 异常检测", None, None),
    ("cfg_ad5e5c81c4766435", "AUDIT_ALERT_BRUTE_FORCE_THRESHOLD", "10", "AUDIT_ALERT", "暴力破解阈值", 20, "INT", "暴力破解阈值", None, None),
    ("cfg_a4e7a42d3948bf0b", "AUDIT_ALERT_BULK_DELETE_THRESHOLD", "20", "AUDIT_ALERT", "批量删除阈值", 21, "INT", "批量删除阈值", None, None),
    ("cfg_28c8a4a855e9fad1", "AUDIT_ALERT_IP_ANOMALY_THRESHOLD", "3", "AUDIT_ALERT", "IP异常阈值", 22, "INT", "IP异常阈值", None, None),
    ("cfg_64b21f173dc9b576", "DEFAULT_FILE_ENGINE", "LOCAL", "STORAGE", "默认文件引擎", 1, "STRING", "默认文件引擎", None, None),
    ("cfg_e24c09333bf60a6a", "STORAGE_LOCAL_LOCAL_ROOT", ".runtime/storage", "STORAGE", "LINUX 本地存储根目录", 10, "STRING", "LINUX 本地存储根目录", None, None),
    ("cfg_73079408dc2ff66d", "STORAGE_LOCAL_WINDOWS_ROOT", "", "STORAGE", "WINDOWS 本地存储根目录", 11, "STRING", "WINDOWS 本地存储根目录", None, None),
    ("cfg_765d200f50139dd3", "STORAGE_LOCAL_PUBLIC_PATH", "/api/v1/files", "STORAGE", "本地公开访问路径", 12, "STRING", "本地公开访问路径", None, None),
    ("cfg_345fa302e246c915", "STORAGE_LOCAL_BASE_URL", "", "STORAGE", "本地自定义基础 URL", 13, "STRING", "本地自定义基础 URL", None, None),
    ("cfg_8976797e93df39d7", "STORAGE_UPLOAD_MAX_BYTES", "10485760", "UPLOAD", "上传文件大小上限（字节）", 1, "INT", "上传文件大小上限（字节）", None, None),
    ("cfg_bc42ff611c681cf9", "STORAGE_PRESIGN_EXPIRE_SECONDS", "3600", "UPLOAD", "预签名 URL 有效期（秒）", 3, "INT", "预签名 URL 有效期（秒）", None, None),
    ("cfg_ba5e00e4afcdfec6", "STORAGE_UPLOAD_ALLOWED_CONTENT_TYPES", "[\"image/jpeg\",\"image/png\",\"image/webp\",\"application/pdf\",\"text/plain\",\"application/octet-stream\"]", "UPLOAD", "允许的 MIME 类型列表", 4, "JSON", "允许的 MIME 类型列表", None, None),
    ("cfg_41c747360aa63455", "STORAGE_UPLOAD_ALLOWED_EXTENSIONS", "[\".jpg\",\".jpeg\",\".png\",\".webp\",\".pdf\",\".txt\",\".ini\"]", "UPLOAD", "允许的文件扩展名列表", 5, "JSON", "允许的文件扩展名列表", None, None),
    ("cfg_d8f57d4b6981dbc4", "STORAGE_UPLOAD_DENIED_EXTENSIONS", "[\".exe\",\".bat\",\".cmd\",\".sh\",\".js\",\".html\",\".php\",\".py\",\".jar\"]", "UPLOAD", "禁止上传的扩展名列表", 6, "JSON", "禁止上传的扩展名列表", None, None),
    ("cfg_14f0f67fb5b45132", "STORAGE_UPLOAD_CATEGORY_MAX_LENGTH", "64", "UPLOAD", "上传分类名最大长度", 7, "INT", "上传分类名最大长度", None, None),
    ("cfg_0540565620e0467f", "COPYRIGHT_TEXT", "hei-fastapi", "SYS", "版权文案", 1, "STRING", "版权文案", None, None),
    ("cfg_b43e7757a174ca18", "COPYRIGHT_URL", "", "SYS", "版权链接", 2, "STRING", "版权链接", None, None),
    ("cfg_c00733c0055182cb", "MAIL_TEMPLATE_RESET_PASSWORD_CODE", "{\"subject\": \"{{app_name}} 密码重置\", \"body\": \"请点击以下链接重置密码，该链接将在 {{expire_minutes}} 分钟内有效。\\n\\n{{reset_link}}\"}", "MAIL_TEMPLATE", "重置密码邮件模板", 1, "JSON", "重置密码邮件模板", None, "RESET_PASSWORD_CODE"),
    ("cfg_d61b9f0c91d4d7d0", "MAIL_TEMPLATE_LOGIN_CODE", "{\"subject\": \"{{app_name}} 登录验证码\", \"body\": \"您的登录验证码是 {{code}}，{{expire_minutes}} 分钟内有效。\"}", "MAIL_TEMPLATE", "登录验证码邮件模板", 2, "JSON", "登录验证码邮件模板", None, "LOGIN_CODE"),
    ("cfg_ce9bc36c9f61f79f", "SMS_TEMPLATE_LOGIN_CODE", "{\"code\": \"\", \"content\": \"登录验证码 {{code}}\"}", "SMS_TEMPLATE", "登录验证码短信模板", 1, "JSON", "登录验证码短信模板", None, "LOGIN_CODE"),
    ("cfg_f7804b0c3e90d4d0", "MAIL_TEMPLATE_CHANGE_PASSWORD_CODE", "{\"subject\": \"{{app_name}} 修改密码验证码\", \"body\": \"验证码 {{code}}，{{expire_minutes}} 分钟内有效。\"}", "MAIL_TEMPLATE", "\u4fee\u6539\u5bc6\u7801\u90ae\u4ef6\u6a21\u677f", 3, "JSON", "\u4fee\u6539\u5bc6\u7801\u90ae\u4ef6\u6a21\u677f", None, "CHANGE_PASSWORD_CODE"),
    ("cfg_a488dc18ffd25b5d", "MAIL_TEMPLATE_REGISTER_SUCCESS", "{\"subject\": \"欢迎注册 {{app_name}}\", \"body\": \"账号 {{account}} 注册成功。\"}", "MAIL_TEMPLATE", "\u6ce8\u518c\u6210\u529f\u90ae\u4ef6\u6a21\u677f", 4, "JSON", "\u6ce8\u518c\u6210\u529f\u90ae\u4ef6\u6a21\u677f", None, "REGISTER_SUCCESS"),
    ("cfg_9db853784cc408aa", "SMS_TEMPLATE_CHANGE_PASSWORD_CODE", "{\"code\": \"\", \"content\": \"改密验证码 {{code}}\"}", "SMS_TEMPLATE", "\u4fee\u6539\u5bc6\u7801\u77ed\u4fe1\u6a21\u677f", 2, "JSON", "\u4fee\u6539\u5bc6\u7801\u77ed\u4fe1\u6a21\u677f", None, "CHANGE_PASSWORD_CODE"),
)


def upgrade() -> None:
    conn = op.get_bind()
    # 删除全部 dotted key + 明确废弃 key
    conn.execute(sa.text("DELETE FROM sys_config WHERE config_key LIKE '%.%'"))
    for key in _LEGACY_KEYS:
        if "." in key:
            continue
        conn.execute(
            sa.text("DELETE FROM sys_config WHERE config_key = :key"),
            {"key": key},
        )
    for row_id, key, value, category, remark, sort_code, value_type, label, scope, scene in _SEED_ROWS:
        exists = conn.execute(
            sa.text("SELECT 1 FROM sys_config WHERE config_key = :key LIMIT 1"),
            {"key": key},
        ).scalar()
        if exists:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO sys_config (
                    id, config_key, config_value, category, remark, sort_code,
                    ext_json, value_type, label, scope, scene, is_builtin,
                    created_at, created_by, updated_at, updated_by
                ) VALUES (
                    :id, :key, :value, :category, :remark, :sort_code,
                    CAST('{}' AS json), :value_type, :label, :scope, :scene, true,
                    :now, NULL, :now, NULL
                )
                """
            ),
            {
                "id": row_id,
                "key": key,
                "value": value,
                "category": category,
                "remark": remark,
                "sort_code": sort_code,
                "value_type": value_type,
                "label": label,
                "scope": scope,
                "scene": scene,
                "now": _NOW,
            },
        )


def downgrade() -> None:
    # 破坏性迁移，不回滚种子数据
    pass
