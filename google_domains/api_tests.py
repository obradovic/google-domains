"""
    api tests
"""
from mock import MagicMock, patch  # create_autospec
from google_domains.log import set_verbose
from google_domains import api as test


PACKAGE = "google_domains.api."


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
    gdomain_ls.return_value = {"baz.foobar.com": "https://dweeb.com"}
    test.api_ls(None, "foobar.com")
    assert gdomain_ls.call_count == 1
    out, __ = capsys.readouterr()
    assert "baz.foobar.com" in out
    assert "dweeb.com" in out


@patch(PACKAGE + "gdomain_ls")
@patch(PACKAGE + "gdomain_del")
def test_api_del(gdomain_del, gdomain_ls, capsys):
    """ Test api_del
    """

    # HAPPY PATH
    gdomain_ls.return_value = {"baz.foobar.com": "https://dweeb.com"}
    test.api_del(None, "foobar.com", "baz.foobar.com")
    assert gdomain_ls.call_count == 1
    assert gdomain_del.call_count == 1
    reset_mocks(gdomain_del, gdomain_ls)

    # VERBOSE MODE
    set_verbose(True)
    gdomain_ls.return_value = {"baz.foobar.com": "https://dweeb.com"}
    test.api_del(None, "foobar.com", "baz.foobar.com")
    assert gdomain_ls.call_count == 2
    assert gdomain_del.call_count == 1
    reset_mocks(gdomain_del, gdomain_ls)

    # ITEM NOT IN RESULTS
    gdomain_ls.return_value = {"baz.foobar.com": "https://dweeb.com"}
    test.api_del(None, "foobar.com", "NOTFOUND.foobar.com")
    assert gdomain_ls.call_count == 1
    assert gdomain_del.call_count == 0
    out, __ = capsys.readouterr()
    assert "Hostname not found" in out
