""" Author: Charlie """

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config.enums import StorageProvider
from app.platform.module.paths import DEFAULT_FILES_PUBLIC_PATH

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    name: str = "hei-fastapi"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    workers: int = 1
    worker_max: int = 4
    process_role: str = "all"
    config_crypto_key: str = ""
    timezone: str = "Asia/Shanghai"
    trusted_proxy_ips: list[str] = []


class DatabaseSettings(BaseSettings):
    url: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/hei_fastapi"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout_seconds: float = 30.0
    pool_recycle_seconds: int = 1800
    pool_pre_ping: bool = True


class AuditSettings(BaseSettings):
    operation_queue_size: int = 1000
    operation_shutdown_timeout_seconds: float = 5.0


class RedisSettings(BaseSettings):
    url: str = "redis://localhost:6379/0"
    max_connections: int = 1000


class AuthSettings(BaseSettings):
    token_name: str = "Authorization"
    token_ttl_seconds: int = 60 * 60 * 4
    token_ttl_short_seconds: int = 60 * 60 * 2
    portal_register_enabled: bool = True
    login_failure_window_seconds: int = 15 * 60
    login_account_max_failures: int = 5
    login_ip_max_failures: int = 30
    login_lock_seconds: int = 15 * 60
    password_reset_token_ttl_seconds: int = 10 * 60
    default_password: str = ""
    captcha_ttl_seconds: int = 5 * 60
    password_crypto_key_ttl_seconds: int = 10 * 60
    # 0 = 禁用（本地/开发）。Docker compose 生产类栈常设为 1800。
    session_idle_timeout_seconds: int = 0
    session_bind_ip: bool = True
    session_bind_user_agent: bool = False
    max_concurrent_sessions: int = 5
    # Cookie 优先的 Web 会话；原生客户端可在 token_name 头发送不透明 token
    # （非 HTTP Bearer）。Cookie 名与 token_name 同为 Authorization；
    # 登录/登出时 Path 取自请求路径父级；session_cookie_path 仅用于清理旧版 Path=/。
    session_cookie_enabled: bool = True
    session_cookie_name: str = "Authorization"
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"
    session_cookie_path: str = "/"
    # 额外鉴权豁免路径（精确或 fnmatch），与内置白名单合并。
    auth_whitelist: list[str] = []


class SecretsSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    # fernet = APP__CONFIG_CRYPTO_KEY；vault = 从 KV v2 加载 Fernet 密钥
    backend: str = "fernet"
    vault_addr: str = ""
    vault_token: str = ""
    vault_mount: str = "secret"
    vault_path: str = "hei/fernet"
    vault_key_field: str = "fernet_key"
    vault_timeout_seconds: float = 5.0
    # 生产加固：APP__DEBUG=false 时，除非显式豁免，否则拒绝仅 Fernet 后端。
    require_vault: bool = False
    allow_fernet_in_prod: bool = True


class MailSettings(BaseSettings):
    host: str = ""
    port: int = 587
    username: str = ""
    password: str = ""
    from_email: str = ""
    from_name: str = "hei-fastapi"
    use_tls: bool = True
    timeout_seconds: float = 10.0


class CorsSettings(BaseSettings):
    allow_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5163",
        "http://127.0.0.1:5163",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]
    allow_credentials: bool = True
    allow_methods: list[str] = [
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ]
    allow_headers: list[str] = [
        "Authorization",
        "Content-Type",
        "X-Request-Id",
        "Accept",
        "Origin",
    ]


class CelerySettings(BaseSettings):
    # 优先 Redis broker（独立 DB）。
    broker_url: str = "redis://127.0.0.1:6379/1"
    # 空 → Redis 结果后端（settings.redis.url）。
    result_backend: str = ""
    # 必须大于最长任务墙钟时间。Redis broker 超时后会 un-ack。
    broker_visibility_timeout: int = 3600
    worker_log_level: str = "INFO"
    log_dir: str = "logs"
    log_file_max_mb: int = 100
    beat_log_level: str = "INFO"
    worker_pool: str = "solo"
    worker_concurrency: int = 1
    worker_without_mingle: bool = True
    worker_without_gossip: bool = True
    worker_remote_control_enabled: bool = False
    worker_cancel_long_running_tasks_on_connection_loss: bool = True


class StorageSettings(BaseSettings):
    provider: StorageProvider = StorageProvider.LOCAL
    bucket: str = ""
    endpoint: str = ""
    access_key: str = ""
    secret_key: str = ""
    region: str = ""
    use_ssl: bool = False
    presign_expire_seconds: int = 3600
    base_url: str = ""
    public_path: str = DEFAULT_FILES_PUBLIC_PATH
    local_root: str = ".runtime/storage"
    upload_max_bytes: int = 10 * 1024 * 1024
    upload_allowed_content_types: list[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
        "text/plain",
        "video/mp4",
        "video/webm",
        "video/quicktime",
    ]
    upload_allowed_extensions: list[str] = [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".pdf",
        ".txt",
        ".mp4",
        ".webm",
        ".mov",
    ]
    upload_denied_extensions: list[str] = [
        ".exe",
        ".bat",
        ".cmd",
        ".sh",
        ".js",
        ".html",
        ".php",
        ".py",
        ".jar",
    ]
    upload_category_max_length: int = 64


class IdGeneratorSettings(BaseSettings):
    # 0 = 从 hostname/pid 自动派生唯一 worker（多副本推荐）
    worker_id: int = 0
    datacenter_id: int = 1


class SwaggerSettings(BaseSettings):
    enabled: bool = False


class ObservabilitySettings(BaseSettings):
    enabled: bool = False
    service_name: str = "hei-fastapi"
    service_version: str = "0.1.0"
    environment: str = "dev"
    log_enabled: bool = True
    log_level: str = "INFO"
    log_json: bool = False
    log_dir: str = "logs"
    log_file_max_mb: int = 100
    metrics_enabled: bool = False
    metrics_path: str = "/metrics"
    tracing_enabled: bool = False
    otlp_enabled: bool = False
    otlp_endpoint: str = ""
    sample_ratio: float = 1.0
    celery_observability_enabled: bool = False
    db_observability_enabled: bool = False
    http_client_observability_enabled: bool = False


class AuditAlertSettings(BaseSettings):
    enabled: bool = False
    notify_email: bool = True
    notify_push: bool = True
    notify_custom_webhook: bool = False
    webhook_url: str = ""
    webhook_secret: str = ""
    analysis_interval_seconds: int = 300
    alert_cooldown_seconds: int = 1800
    rule_brute_force: bool = True
    rule_unusual_hours: bool = True
    rule_sensitive_ops: bool = True
    rule_bulk_delete: bool = True
    rule_ip_anomaly: bool = True
    brute_force_threshold: int = 10
    bulk_delete_threshold: int = 20
    ip_anomaly_threshold: int = 3


class PasswordPolicySettings(BaseSettings):
    min_length: int = 8
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = True
    expire_days: int = 90
    history_check_count: int = 5
    common_password_check: bool = True
    # UPPER_SNAKE complexity: NO_LIMIT | DIGITS_AND_LETTERS | ...
    complexity: str = "DIGITS_UPPER_LOWER_SPECIAL"
    max_consecutive_chars: int = 3
    forbid_user_info: bool = True
    forbid_historical: bool = True
    expiry_warning_days: int = 3


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", PROJECT_ROOT / ".env.local"),
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppSettings = Field(default_factory=AppSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    audit: AuditSettings = Field(default_factory=AuditSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    secrets: SecretsSettings = Field(default_factory=SecretsSettings)
    mail: MailSettings = Field(default_factory=MailSettings)
    cors: CorsSettings = Field(default_factory=CorsSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    password_policy: PasswordPolicySettings = Field(default_factory=PasswordPolicySettings)
    audit_alert: AuditAlertSettings = Field(default_factory=AuditAlertSettings)
    id_generator: IdGeneratorSettings = Field(default_factory=IdGeneratorSettings)
    swagger: SwaggerSettings = Field(default_factory=SwaggerSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)

    module_configs: dict[str, Any] = Field(default_factory=dict, exclude=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
