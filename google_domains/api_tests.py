"""
    api tests
"""
from mock import MagicMock, patch  # create_autospec
from google_domains import api as test


PACKAGE = "google_domains.api."
SAMPLE_TLD = "foobar.com"
SAMPLE_HOSTNAME = f"baz.{SAMPLE_TLD}"
SAMPLE_TARGET = "https://dweeb.com"


def reset_mocks(*mocks) -> None:
    """ Resets all the mocks
    """
    for mock in mocks:
        mock.reset_mock()


def test_api_destruct():
    """ Test api_destruct
    """
    browser_quit = MagicMock()
    browser = MagicMock(quit=browser_quit)

    test.api_destruct(browser)
    assert browser_quit.call_count == 1


@patch(PACKAGE + "gdomain_ls")
def test_api_ls(gdomain_ls, capsys):
    """ Test api_ls
    """

    # HAPPY PATH
    gdomain_ls.return_value = {SAMPLE_HOSTNAME: SAMPLE_TARGET}
    test.api_ls(None, SAMPLE_TLD)
    assert gdomain_ls.call_count == 1
    out, __ = capsys.readouterr()
    assert SAMPLE_HOSTNAME in out
    assert "dweeb.com" in out


@patch(PACKAGE + "is_verbose")
@patch(PACKAGE + "gdomain_ls")
@patch(PACKAGE + "gdomain_del")
@patch(PACKAGE + "gdomain_add")
def test_api_add(gdomain_add, gdomain_del, gdomain_ls, is_verbose, capsys):
    """ Test api_add
    """

    # HAPPY PATH. Item does not currently exist
    is_verbose.return_value = False
    gdomain_ls.return_value = {}
    test.api_add(None, SAMPLE_TLD, SAMPLE_HOSTNAME, SAMPLE_TARGET)
    assert gdomain_ls.call_count == 1
    assert gdomain_del.call_count == 0
    assert gdomain_add.call_count == 1
    out, __ = capsys.readouterr()
    assert not out
    reset_mocks(gdomain_add, gdomain_del, gdomain_ls, is_verbose)

    # Item already exixts, and is pointed to THE SAME target
    is_verbose.return_value = False
    gdomain_ls.return_value = {SAMPLE_HOSTNAME: SAMPLE_TARGET}
    test.api_add(None, SAMPLE_TLD, SAMPLE_HOSTNAME, SAMPLE_TARGET)
    assert gdomain_ls.call_count == 1
    assert gdomain_del.call_count == 0
    assert gdomain_add.call_count == 0
    out, __ = capsys.readouterr()
    assert "already exists" in out
    reset_mocks(gdomain_add, gdomain_del, gdomain_ls, is_verbose)

    # Item already exixts, and is pointed to A DIFFERENT target
    is_verbose.return_value = False
    gdomain_ls.return_value = {SAMPLE_HOSTNAME: "https://totallytubular.com"}
    test.api_add(None, SAMPLE_TLD, SAMPLE_HOSTNAME, SAMPLE_TARGET)
    assert gdomain_ls.call_count == 1
    assert gdomain_del.call_count == 1
    assert gdomain_add.call_count == 1
    out, __ = capsys.readouterr()
    assert not out


@patch(PACKAGE + "is_verbose")
@patch(PACKAGE + "gdomain_ls")
@patch(PACKAGE + "gdomain_del")
def test_api_del(gdomain_del, gdomain_ls, is_verbose, capsys):
    """ Test api_del
    """

    # HAPPY PATH
    is_verbose.return_value = False
    gdomain_ls.return_value = {SAMPLE_HOSTNAME: SAMPLE_TARGET}
    test.api_del(None, SAMPLE_TLD, SAMPLE_HOSTNAME)
    assert is_verbose.call_count == 1
    assert gdomain_ls.call_count == 1
    assert gdomain_del.call_count == 1
    reset_mocks(gdomain_del, gdomain_ls, is_verbose)

    # VERBOSE MODE
    is_verbose.return_value = True
    gdomain_ls.return_value = {SAMPLE_HOSTNAME: SAMPLE_TARGET}
    test.api_del(None, SAMPLE_TLD, SAMPLE_HOSTNAME)
    assert gdomain_ls.call_count == 2
    assert gdomain_del.call_count == 1
    reset_mocks(gdomain_del, gdomain_ls, is_verbose)

    # ITEM NOT IN RESULTS
    gdomain_ls.return_value = {SAMPLE_HOSTNAME: SAMPLE_TARGET}
    test.api_del(None, SAMPLE_TLD, "NOTFOUND." + SAMPLE_TLD)
    assert gdomain_ls.call_count == 1
    assert gdomain_del.call_count == 0
    out, __ = capsys.readouterr()
    assert "Hostname not found" in out
