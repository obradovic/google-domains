"""
    Shared utilities
"""
from functools import wraps
import time
from fqdn import FQDN
from google_domains.log import debug


class Timer:
    """ Lets us time a block. Like: with Timer('doing something interesting'):
    """

    first_click = None

    def __init__(self, name: str) -> None:
        self.name = name

    def __enter__(self):
        self.first_click = click()

    def __exit__(self, the_type, the_value, the_traceback):
        # if an exception was raised, ignore
        if the_type:
            return

        ms = click() - self.first_click
        debug(f"   time: {self.name} took {ms} ms")


def print_timing(function):
    """ Decorator, prints out the execution time of the function in ms
    """

    @wraps(function)
    def decorated_function(*args, **kwargs):
        """ the decorating fx
        """
        debug(f"   call: {function.__name__}")
        with Timer(function.__name__):
            ret = function(*args, **kwargs)

        return ret

    return decorated_function


def click() -> int:
    """ Returns milliseconds since the epoch
    """
    return int(round(time.time() * 1000))


def fqdn(hostname: str, domain: str, relative: bool = True) -> str:
    """ Returns the FQDN of the passed-in hostname
    """
    if domain not in hostname:
        hostname = f"{hostname}.{domain}."

    this_fqdn = FQDN(hostname)

    if relative:
        return this_fqdn.relative
    return this_fqdn.absolute


def un_fqdn(hostname: str, domain: str) -> str:
    """ Returns the relative hostname, sans domain
    """
    ret = hostname.replace(domain, "")
    ret = ret.strip(".")
    return ret
