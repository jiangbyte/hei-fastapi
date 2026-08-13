""" Author: Charlie

异步任务运行器：为 worker 进程维护一个持久事件循环，在线程中执行协程。

保证 Redis/DB 等连接绑定到同一事件循环，避免任务执行前循环被关闭。
"""

from __future__ import annotations

import asyncio
import atexit
import threading
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


class WorkerAsyncRunner:
    """每个 worker 进程在单一持久事件循环上运行异步任务体。"""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def run(self, coroutine: Coroutine[Any, Any, T]) -> T:
        """在持久事件循环上执行协程并阻塞等待结果。"""
        loop = self._ensure_loop()
        future = asyncio.run_coroutine_threadsafe(coroutine, loop)
        return future.result()

    def close(self) -> None:
        """停止事件循环并等待线程退出，幂等。"""
        with self._lock:
            loop = self._loop
            thread = self._thread
            self._loop = None
            self._thread = None
        if loop is None:
            return
        loop.call_soon_threadsafe(loop.stop)
        if thread and thread.is_alive():
            thread.join(timeout=5)

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        """返回运行中的持久事件循环，未创建时启动守护线程。"""
        with self._lock:
            if self._loop and self._loop.is_running():
                return self._loop
            ready = threading.Event()
            loop = asyncio.new_event_loop()
            thread = threading.Thread(
                target=self._run_loop,
                args=(loop, ready),
                name="worker-async-runner",
                daemon=True,
            )
            thread.start()
            ready.wait()
            self._loop = loop
            self._thread = thread
            return loop

    def _run_loop(self, loop: asyncio.AbstractEventLoop, ready: threading.Event) -> None:
        """在守护线程中运行事件循环，并在启动前发出就绪信号。"""
        asyncio.set_event_loop(loop)
        ready.set()
        try:
            loop.run_forever()
        finally:
            loop.close()


# 进程级全局异步任务运行器单例。
worker_async_runner = WorkerAsyncRunner()
atexit.register(worker_async_runner.close)
