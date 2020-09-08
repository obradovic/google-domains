"""
    Tests for utils
"""
import time

# from mock import MagicMock, patch  # create_autospec
# import pytest
# import .utils as test
from google_domains import utils as test


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
