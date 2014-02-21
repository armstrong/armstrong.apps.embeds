import pkg_resources
pkg_resources.declare_namespace(__name__)

from functools import wraps


class InvalidResponseError(Exception):
    pass


def get_backend(name):
    if not name:
        raise ImportError

    name = str(name).lower()
    module = "%s.%s" % (__package__, name)
    try:
        from importlib import import_module
    except ImportError:  # Python 2.6 support
        module = __import__(module, globals(), locals(), [name], 0)
    else:
        module = import_module(module)
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
