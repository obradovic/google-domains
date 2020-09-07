"""
    Tests for google-domains-api
"""
import time

# from mock import MagicMock, patch  # create_autospec
# import pytest
import google_domains_api as test


def reset_mocks(*mocks):
    """ Resets all the mocks passed in
    """
    for mock in mocks:
        mock.reset_mock()


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


def test_initialize_from_cmdline():
    """ Tests initialize_from_cmdline
    """
    response = test.initialize_from_cmdline([])
    assert response.get("operation") == "ls"

    response = test.initialize_from_cmdline(["-v", "ls"])
    assert response.get("verbose") is True
    assert response.get("operation") == "ls"

    response = test.initialize_from_cmdline(["--domain", "foo.bar", "ls"])
    assert response.get("verbose") is None
    assert response.get("domain") == "foo.bar"
