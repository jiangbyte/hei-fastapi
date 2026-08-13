""" Author: Charlie

加载模块声明的 SnailJob 执行器任务。
"""
from app.platform.module import load_declared_tasks, load_module_specs

# 导入时扫描模块声明的 tasks，触发 @job 注册。
load_declared_tasks(load_module_specs())
