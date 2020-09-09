"""
    Tests for utils
"""
import time
from mock import patch  # create_autospec

from google_domains import utils as test


PACKAGE = "google_domains."


@patch(PACKAGE + "utils.debug")
def test_timer(debug, capsys):
    """ Tests Timer
    """
    with test.Timer("foobar"):
        print("something")

    out, __ = capsys.readouterr()
    assert "something" in out
    assert debug.call_count == 1
    assert "time: foobar" in debug.call_args[0][0]
    assert " took " in debug.call_args[0][0]


def test_click():
    """ Tests click
    """
    result_a = test.click()
    time.sleep(0.1)
    result_b = test.click()

    assert result_b > result_a


def test_fqdn():
    """ Tests fqdn
    """
    domain = "foobar.baz"

    hostnames = [
        "foo",
        "foo.foobar.baz",
        "foo.foobar.baz.",
    ]

    for hostname in hostnames:
        assert test.fqdn(hostname, domain, relative=False) == "foo.foobar.baz."
        assert test.fqdn(hostname, domain, relative=True) == "foo.foobar.baz"
        assert test.fqdn(hostname, domain) == "foo.foobar.baz"


def test_un_fqdn():
    """ Tests un_fqdn
    """
    domain = "bar.com"
    assert test.un_fqdn("foo.bar.com", domain) == "foo"
    assert test.un_fqdn("foo.bar.com.", domain) == "foo"
    assert test.un_fqdn("foo", domain) == "foo"
    assert test.un_fqdn("foo.", domain) == "foo"
