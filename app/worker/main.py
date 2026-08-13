""" Author: Charlie

SnailJob Python 执行器进程入口。
"""

from app.platform.tasks.snailjob_client import run_executor


def main() -> None:
    """启动执行器主循环（阻塞）。"""
    run_executor()


if __name__ == "__main__":
    main()
