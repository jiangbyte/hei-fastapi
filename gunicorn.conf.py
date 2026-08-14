from app.core.config.settings import settings

bind = f"{settings.app.host}:{settings.app.port}"
worker_class = "uvicorn.workers.UvicornWorker"
# 单进程运行：SnailJob 执行器内嵌于本 worker（lifespan 启动后台线程）。
# 多 worker 会同时启动多个执行器实例竞争同一组任务，故强制 1 个 worker。
workers = 1
max_requests = 10000
max_requests_jitter = 1000
timeout = 30
graceful_timeout = 30
keepalive = 5
accesslog = None  # App AccessLogMiddleware owns access logging
errorlog = "-"
loglevel = "info"
