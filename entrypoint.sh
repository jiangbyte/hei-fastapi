#!/bin/sh
set -eu

# 仅启动 API（单进程内嵌 SnailJob 执行器，对接外部 SnailJob Server）。
# 数据库表结构由人工维护：应用启动不执行迁移/种子。
exec gunicorn app.main:app -c gunicorn.conf.py
