"""
    Tests for logging
"""
from google_domains import logging as test


def test_print(capsys):
    """ Tests print
    """

    # When VERBOSE is True, it should print something
    test.VERBOSE = True
    test.debug("foobar")
    out, __ = capsys.readouterr()
    assert "foobar" in out

    # When VERBOSE is False, it should NOT print anything
    test.VERBOSE = False
    test.debug("foobar")
    out, __ = capsys.readouterr()
    assert "foobar" not in out


def test_error(capsys):
    """ Tests error
    """
    test.error("foobaz")
    out, __ = capsys.readouterr()
    assert "ERROR: foobaz" in out
