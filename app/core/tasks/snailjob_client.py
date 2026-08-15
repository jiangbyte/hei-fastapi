""" Author: Charlie

SnailJob 执行器内嵌：单进程内运行，应用 lifespan 启动后台线程执行客户端主循环。

SnailJob Server 外部提供，应用只需配置 ``SNAIL_JOB__*`` 即可接入；
任务模块在启动时导入以注册执行器。
"""

from __future__ import annotations

import logging
import os
import socket
import sys
import threading

# snailjob 包在导入时即按默认 log/snailjob.log 初始化文件日志；
# 必须先设置环境变量，让默认配置也使用统一日志目录，避免生成独立的 log/ 目录。
os.environ.setdefault("SNAIL_LOG_LOCAL_FILENAME", "logs/snailjob.log")

# Windows 控制台默认 cp1252 编码，snailjob 库的日志含中文会触发 UnicodeEncodeError；
# 在导入库之前把标准流切到 UTF-8（errors=replace 兜底），避免刷屏与日志丢失。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):
        pass

# 先加载应用设置（该模块不导入 snailjob）。
from app.core.config.settings import settings  # noqa: E402

# 关键：snail-job-python 的 __init__ 链在“首次导入”时就会让 log/main/rpc/grpc 各自
# 捕获全局 settings 单例（默认是库的 demo 值），之后调用 configure_settings() 也更新不了
# 这些已捕获的引用——网络层会一直用 demo 的 namespace/group/token 去认证。
# 因此必须在首次导入 snailjob 之前，把应用配置映射为库读取的环境变量（SNAIL_*）。
_sj = settings.snail_job
os.environ["SNAIL_SERVER_HOST"] = str(_sj.server_host)
os.environ["SNAIL_SERVER_PORT"] = str(_sj.server_port)
os.environ["SNAIL_HOST_IP"] = str(_sj.host_ip or "127.0.0.1")
os.environ["SNAIL_HOST_PORT"] = str(_sj.host_port)
os.environ["SNAIL_NAMESPACE"] = _sj.namespace
os.environ["SNAIL_GROUP_NAME"] = _sj.group_name
os.environ["SNAIL_TOKEN"] = _sj.token
os.environ["SNAIL_LABELS"] = _sj.labels

from snailjob.config import configure_settings  # noqa: E402
from snailjob.main import client_main  # noqa: E402


def _fix_snailjob_log_encoding() -> None:
    """库的本地文件日志未指定 encoding，Windows 下按 cp1252 写中文会 UnicodeEncodeError。

    TimedRotatingFileHandler 的流在导入时已打开，这里就地把它切到 UTF-8（errors=replace）。
    """
    for _name in ("SnailJob Local Logger", "SnailJob Remote Logger"):
        _logger = logging.getLogger(_name)
        for _handler in list(_logger.handlers):
            try:
                _handler.stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError):
                pass


_fix_snailjob_log_encoding()

logger = logging.getLogger(__name__)

# 内嵌执行器线程（单进程模型，整个应用生命周期内一个执行器）。
_executor_thread: threading.Thread | None = None


def apply_snailjob_settings() -> None:
    """把应用 Settings 写入 snail-job-python 全局配置（与环境变量预映射保持同步）。"""
    sj = settings.snail_job
    configure_settings(
        snail_server_host=sj.server_host,
        snail_server_port=sj.server_port,
        snail_host_ip=sj.host_ip or "127.0.0.1",
        snail_host_port=sj.host_port,
        snail_namespace=sj.namespace,
        snail_group_name=sj.group_name,
        snail_token=sj.token,
        snail_labels=sj.labels,
    )


def _register_tasks() -> None:
    """导入任务模块，触发 @job 装饰器与 ExecutorManager.register。"""
    from app.modules.iam.account import tasks as _account_tasks  # noqa: F401
    from app.modules.sys.audit import tasks as _audit_tasks  # noqa: F401
    from app.modules.sys.banner import tasks as _banner_tasks  # noqa: F401
    from app.modules.sys.file import tasks as _file_tasks  # noqa: F401


def _executor_loop() -> None:
    """执行器线程主循环：注册任务后阻塞在 gRPC server。"""
    try:
        client_main()
    except Exception:
        logger.exception("SnailJob executor stopped unexpectedly")


def start_executor() -> bool:
    """在后台线程启动 SnailJob 执行器（幂等）；未启用时返回 False。"""
    global _executor_thread
    if not settings.snail_job.enabled:
        logger.warning("SnailJob disabled (SNAIL_JOB__ENABLED=false); executor not started")
        return False
    if _executor_thread is not None and _executor_thread.is_alive():
        return True
    apply_snailjob_settings()
    _register_tasks()
    _executor_thread = threading.Thread(
        target=_executor_loop,
        name="snailjob-executor",
        daemon=True,
    )
    _executor_thread.start()
    logger.info(
        "SnailJob executor started ns=%s group=%s server=%s:%s client=%s:%s",
        settings.snail_job.namespace,
        settings.snail_job.group_name,
        settings.snail_job.server_host,
        settings.snail_job.server_port,
        settings.snail_job.host_ip,
        settings.snail_job.host_port,
    )
    return True


def stop_executor() -> None:
    """停止执行器：gRPC server 无法优雅退出，守护线程随进程结束。"""
    if _executor_thread is not None and _executor_thread.is_alive():
        logger.info("SnailJob executor thread shutting down with process")


def probe_snailjob_server(timeout_seconds: float = 2.0) -> tuple[bool, str]:
    """对 SnailJob Server 做 TCP 探活，返回 (reachable, detail)。"""
    host = settings.snail_job.server_host
    port = settings.snail_job.server_port
    if not host:
        return False, "snailjob server host not configured"
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True, f"tcp {host}:{port} ok"
    except OSError as exc:
        return False, f"tcp {host}:{port} failed: {exc.__class__.__name__}"
