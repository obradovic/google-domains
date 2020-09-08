"""
    Functions for logging
"""

VERBOSE = False


def debug(message: str) -> None:
    """ Prints an message if VERBOSE is set
    """
    if VERBOSE:
        print(message)


def error(message: str) -> None:
    """ Prints an error message
    """
    print(f"ERROR: {message}")
