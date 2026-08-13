""" Author: Charlie

ServiceRegistry — 通用服务注册中心。

注册:  register("interface_name", impl_instance)
消费:  resolve("interface_name") → object（调用方 import Protocol 后 cast）

新增 interface 只需要:
  1. 在 interfaces/ 下定义 Protocol 类
  2. 在模块的 module.py 中声明 ServiceRegistration
"""
from app.platform.interfaces.account_lookup import AccountLookupProtocol
from app.platform.interfaces.data_scope_resolver import DataScopeResolverProtocol

# 接口名到实现实例的注册表。
_registry: dict[str, object] = {}


def register(interface: str, impl: object) -> None:
    """按接口名注册实现实例。"""
    _registry[interface] = impl


def resolve(interface: str) -> object:
    """按接口名解析实现实例，未注册时抛出 RuntimeError。"""
    impl = _registry.get(interface)
    if impl is None:
        raise RuntimeError(f"'{interface}' not registered")
    return impl


def register_data_scope_resolver(impl: DataScopeResolverProtocol) -> None:
    """注册数据范围部门解析器实现。"""
    register("data_scope_resolver", impl)


__all__ = [
    "AccountLookupProtocol",
    "DataScopeResolverProtocol",
    "register",
    "register_data_scope_resolver",
    "resolve",
]
