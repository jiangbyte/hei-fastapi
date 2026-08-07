""" Author: Charlie

加载模块声明的 Celery 任务。
"""
from app.platform.module import load_declared_tasks, load_module_specs

load_declared_tasks(load_module_specs())
