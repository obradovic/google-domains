"""
    Functions for logging
    TODO: Move to more pythonic logging
"""

VERBOSE = False


def debug(message: str) -> None:
    """ Prints an message, conditionally
    """
    if is_verbose():
        print(message)


def error(message: str) -> None:
    """ Prints an error message
    """
    print(f"ERROR: {message}")


def is_verbose() -> bool:
    """ Are we operating verbosely?
    """
    return VERBOSE


def set_verbose(verbosity: bool) -> None:
    """ Set our verbosity on or off
    """
    global VERBOSE  # pylint: disable=global-statement
    VERBOSE = verbosity
