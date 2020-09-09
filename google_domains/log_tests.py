"""
    Tests for log
"""
from google_domains import log as test


def test_print(capsys):
    """ Tests print
    """

    # When VERBOSE is True, it should print something
    test.set_verbose(True)
    test.debug("foobar")
    out, __ = capsys.readouterr()
    assert "foobar" in out

    # When VERBOSE is False, it should NOT print anything
    test.set_verbose(False)
    test.debug("foobar")
    out, __ = capsys.readouterr()
    assert "foobar" not in out


def test_error(capsys):
    """ Tests error
    """
    test.error("foobaz")
    out, __ = capsys.readouterr()
    assert "ERROR: foobaz" in out


def test_verbosity():
    """ Tests verbosity attribute
    """
    test.set_verbose(True)
    assert test.is_verbose() is True

    test.set_verbose(False)
    assert test.is_verbose() is False
