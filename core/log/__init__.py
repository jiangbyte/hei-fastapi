from .decorator import sys_log, record_auth_log, save_exception_log

# Uppercase alias for use as @SysLog("名称")
SysLog = sys_log

__all__ = ["sys_log", "SysLog", "record_auth_log", "save_exception_log"]
