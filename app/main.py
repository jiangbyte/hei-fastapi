""" Author: Charlie

应用入口：修正导入路径并创建应用实例供 ASGI 服务器加载。
"""

import sys
from pathlib import Path

# 以脚本方式直接运行时，确保项目根目录在 sys.path 上，便于导入 app 包。
if __package__ in {None, ""}:
    app_dir = Path(__file__).resolve().parent
    project_root = app_dir.parent
    sys.path = [path for path in sys.path if Path(path or ".").resolve() != app_dir]
    sys.path.insert(0, str(project_root))

from app.factory import create_app

app = create_app()
