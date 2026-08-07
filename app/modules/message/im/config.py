""" Author: Charlie

IM 配置（环境变量前缀 IM__）。
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class ImSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="IM__", extra="ignore")

    enabled: bool = True
    ws_host: str = "0.0.0.0"  # nosec B104
    ws_port: int = 18080
    tcp_host: str = "0.0.0.0"  # nosec B104
    tcp_port: int = 18081
    idle_seconds: int = 90
    auth_timeout_seconds: float = 10.0
    max_frame_bytes: int = 1024 * 1024
    ack_window: int = 64
    ack_retry_seconds: float = 2.0
    ack_max_retries: int = 3
    fanout_concurrency: int = 32
    path: str = "/ws"
