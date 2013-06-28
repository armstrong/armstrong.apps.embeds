import pkg_resources
pkg_resources.declare_namespace(__name__)

from importlib import import_module
from functools import wraps


__all__ = ['InvalidResponseError', 'get_backend', 'proxy']


class InvalidResponseError(Exception):
    pass


def get_backend(name):
    module = "%s.%s" % (__package__, str(name).lower())
    try:
        module = import_module(module)
    except KeyError as e:
        raise ImportError(e)
    return getattr(module, "%sBackend" % name.capitalize())()


def proxy(view_func=None):
    """Mark an attribute as proxyable"""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            return view_func(*args, **kwargs)
        return wrapper

    retval = decorator if not view_func else decorator(view_func)
    retval.proxy = True
    return retval
