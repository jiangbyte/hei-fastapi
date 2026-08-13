""" Author: Charlie

进程组管理：在同一进程中拉起 API 与 SnailJob worker 两个子进程并统一协调生命周期。

监听 SIGINT/SIGTERM，任一子进程退出或收到信号时优雅终止其余进程。
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys


def _env(name: str, default: str) -> str:
    """读取环境变量，缺失时返回默认值。"""
    return os.environ.get(name, default)


def _worker_command() -> list[str]:
    """构造 SnailJob Python 执行器子进程命令行。"""
    return [sys.executable, "-m", "app.worker.main"]


def _api_command() -> list[str]:
    """构造 Gunicorn 运行 FastAPI 应用的子进程命令行。"""
    return ["gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]


async def _terminate(processes: dict[str, asyncio.subprocess.Process]) -> None:
    """先 terminate、超时后 kill 地终止所有子进程。"""
    timeout = float(_env("APP__PROCESS_SHUTDOWN_TIMEOUT_SECONDS", "20"))
    for process in processes.values():
        if process.returncode is None:
            process.terminate()

    try:
        await asyncio.wait_for(
            asyncio.gather(*(process.wait() for process in processes.values())),
            timeout=timeout,
        )
    except TimeoutError:
        for process in processes.values():
            if process.returncode is None:
                process.kill()
        await asyncio.gather(*(process.wait() for process in processes.values()))


async def run_all() -> int:
    """启动并监管全部子进程，返回进程退出码。"""
    commands = {
        "worker": _worker_command(),
        "api": _api_command(),
    }
    processes: dict[str, asyncio.subprocess.Process] = {}
    try:
        for name, command in commands.items():
            processes[name] = await asyncio.create_subprocess_exec(*command)
    except BaseException:
        await _terminate(processes)
        raise

    stopping = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signum, stopping.set)
        except NotImplementedError:
            signal.signal(signum, lambda *_: stopping.set())

    wait_tasks = {asyncio.create_task(process.wait()): name for name, process in processes.items()}
    stop_task = asyncio.create_task(stopping.wait())
    done, pending = await asyncio.wait(
        [*wait_tasks.keys(), stop_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    exit_code = 143 if stop_task in done else 1
    for task in done:
        name = wait_tasks.get(task)
        if name is not None:
            exit_code = task.result()
            print(f"{name} exited with status {exit_code}", file=sys.stderr)
            break

    await _terminate(processes)

    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
    return exit_code


def main() -> None:
    """命令行入口：运行进程组并按退出码退出。"""
    raise SystemExit(asyncio.run(run_all()))


if __name__ == "__main__":
    main()
