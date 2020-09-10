"""
    Tests for utils
"""
from types import SimpleNamespace
from mock import patch  # create_autospec
from google_domains import command_line as test


PACKAGE = "google_domains.command_line."


def reset_mocks(*mocks):
    """ Resets all the mocks passed in
    """
    for mock in mocks:
        mock.reset_mock()


@patch(PACKAGE + "configure")
@patch(PACKAGE + "api_construct")
@patch(PACKAGE + "api_destruct")
@patch(PACKAGE + "api_ls")
@patch(PACKAGE + "api_add")
@patch(PACKAGE + "api_del")
def test_main(
    api_del, api_add, api_ls, api_destruct, api_construct, configure, capsys
):  # pylint: disable=too-many-arguments
    """ Tests main
    """

    #
    # HAPPY PATH
    #
    config = {
        "verbose": True,
        "browser": "foo_firefox",
        "domain": "foobar.com",
        "username": "foo_username",
        "password": "foo_password",
        "hostname": "foo_hostname",
        "target": "foo_target",
        "operation": "add",
    }
    configure.return_value = SimpleNamespace(**config)

    test.main()
    assert configure.call_count == 1
    assert api_construct.call_count == 1
    assert api_destruct.call_count == 1
    assert api_ls.call_count == 0
    assert api_add.call_count == 1
    assert api_del.call_count == 0

    assert api_construct.call_args[0][0] == "foobar.com"
    assert api_construct.call_args[0][1] == "foo_username"
    assert api_construct.call_args[0][2] == "foo_password"
    assert api_construct.call_args[0][3] == "foo_firefox"
    out, err = capsys.readouterr()
    assert not out
    assert not err
    reset_mocks(api_del, api_add, api_ls, api_destruct, api_construct, configure)

    #
    # destruct still gets called when an exception is thrown
    #
    api_add.side_effect = Exception("borkborkbork")
    test.main()
    assert configure.call_count == 1
    assert api_construct.call_count == 1
    assert api_destruct.call_count == 1
    assert api_ls.call_count == 0
    assert api_add.call_count == 1
    assert api_del.call_count == 0
    out, err = capsys.readouterr()
    assert "borkborkbork" in out
    assert not err
    reset_mocks(api_del, api_add, api_ls, api_destruct, api_construct, configure)

    #
    # del gets called
    #
    config["operation"] = "del"
    configure.return_value = SimpleNamespace(**config)
    test.main()
    assert configure.call_count == 1
    assert api_construct.call_count == 1
    assert api_destruct.call_count == 1
    assert api_ls.call_count == 0
    assert api_add.call_count == 0
    assert api_del.call_count == 1
    reset_mocks(api_del, api_add, api_ls, api_destruct, api_construct, configure)

    #
    # ls gets called
    #
    config["operation"] = "ls"
    configure.return_value = SimpleNamespace(**config)
    test.main()
    assert configure.call_count == 1
    assert api_construct.call_count == 1
    assert api_destruct.call_count == 1
    assert api_ls.call_count == 1
    assert api_add.call_count == 0
    assert api_del.call_count == 0
    reset_mocks(api_del, api_add, api_ls, api_destruct, api_construct, configure)
