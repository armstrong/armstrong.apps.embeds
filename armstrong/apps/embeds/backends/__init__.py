from functools import wraps


class InvalidResponseError(Exception):
    pass


def get_backend(path):
    if not path:
        raise ImportError

    try:
        module, cls = path.rsplit('.', 1)
    except ValueError:
        raise ImportError

    try:
        from importlib import import_module
    except ImportError:  # PY26 # pragma: no cover
        module = __import__(module, fromlist=[''])
    else:  # pragma: no cover
        module = import_module(module)
    return getattr(module, cls)()


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
