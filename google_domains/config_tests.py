"""
    Tests for config
"""
# from mock import MagicMock, patch  # create_autospec
# import pytest
import google_domains.config as test


def reset_mocks(*mocks):
    """ Resets all the mocks passed in
    """
    for mock in mocks:
        mock.reset_mock()


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
