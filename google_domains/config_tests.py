"""
    Tests for config
"""
import os
from mock import patch  # create_autospec
import google_domains.config as test


@patch("google_domains.config.read_configfile")
def test_initialize_from_files(read_configfile):
    """ Tests initialize_from_files
    """
    # File has something
    read_configfile.return_value = {"domain": "foobar"}
    response = test.initialize_from_files()
    assert response["domain"] == "foobar"

    # File has nothing
    read_configfile.return_value = {}
    response = test.initialize_from_files()
    assert not len(response)


def test_initialize_from_env():
    """ Tests initialize_from_env
    """
    env = "GOOGLE_DOMAINS_DOMAIN"

    # set the env var to something
    os.environ[env] = "foobar"
    response = test.initialize_from_env()
    assert response["domain"] == "foobar"

    # set the env var to nothing
    os.environ[env] = ""
    response = test.initialize_from_env()
    assert response.get("domain") is None

    del os.environ[env]
    response = test.initialize_from_env()
    assert response.get("domain") is None


def test_initialize_from_cmdline():
    """ Tests initialize_from_cmdline
    """
    response = test.initialize_from_cmdline([])
    assert response.get("operation") == "ls"

    response = test.initialize_from_cmdline("-v ls".split())
    assert response.get("verbose") is True
    assert response.get("operation") == "ls"

    response = test.initialize_from_cmdline("-q add".split())
    assert response.get("verbose") is False
    assert response.get("operation") == "add"

    response = test.initialize_from_cmdline("--domain foo.bar del".split())
    assert response.get("verbose") is None
    assert response.get("domain") == "foo.bar"
    assert response.get("operation") == "del"
