""" Author: Charlie

HTTP 客户端异常：外部 HTTP 访问失败时抛出的统一异常类型。
"""


class HttpClientError(Exception):
    """外部 HTTP 访问失败时抛出。"""
