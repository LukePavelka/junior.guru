from functools import wraps
from time import time

from juniorguru.lib.log import get_log


try:
    import pync
except (Exception, ImportError):
    pync = None


log = get_log('timer')


def notify(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time()
        try:
            return fn(*args, **kwargs)
        finally:
            t = time() - t0
            print('\a', end='', flush=True)
            if pync:
                fn_name = f'{fn.__module__}.{fn.__name__}()'
                pync.Notifier.notify(f'{t / 60:.1f}min',
                                     title=f'Finished: {fn_name}')
    return wrapper


def measure(name=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            t0 = time()
            try:
                return fn(*args, **kwargs)
            finally:
                t = time() - t0
                log.info(f'{name or fn.__name__}() took {t / 60:.1f}min')
        return wrapper
    return decorator
