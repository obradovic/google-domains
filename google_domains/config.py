"""
    Arg-parsing and App Configuration
"""
import argparse
import os.path
import sys
from types import SimpleNamespace
from typing import Dict, List
import yaml
from google_domains.log import set_verbose


# Type alias
ConfigDict = Dict[str, str]


def configure() -> SimpleNamespace:
    """ Initializes config info, from three sources:
        1. Config file
        2. Command line
        3. Environment variables

        Sets global verbosity
        Returns all the config args in a Namespace
    """
    config = initialize_from_files()
    config.update(initialize_from_env())
    config.update(initialize_from_cmdline(sys.argv[1:]))

    ret = SimpleNamespace(**config)
    if ret.verbose:
        print(f"   config verbose: {ret.verbose}")
        print(f"   config target: {ret.browser}")
        print(f"   config username: {ret.username}")
        print(f"   config password: {ret.password}")
        print(f"   config domain: {ret.domain}")
        print(f"   config operation: {ret.operation}")
        print(f"   config hostname: {ret.hostname}")
        print(f"   config target: {ret.target}")
        print()

    set_verbose(ret.verbose)

    try:
        validate_args(ret)
    except RuntimeError as e:
        print(f"\n  {e}\n")

    return ret


def initialize_from_files() -> ConfigDict:
    """ Returns a ConfigDict from the config files
    """
    ret = {}
    for location in get_configfile_locations():
        ret.update(read_configfile(location))
    return ret


def get_configfile_locations() -> List[str]:
    """ Returns a list of possible file locations
    """
    return ["/etc/google-domains.yaml", "~/.google_domains.yaml"]


def read_configfile(location: str) -> Dict[str, str]:
    """ Reads a config file
    """
    expanded = os.path.expanduser(location)
    if os.path.isfile(expanded):
        with open(expanded) as file:
            return yaml.load(file, Loader=yaml.FullLoader)
    return {}


def initialize_from_env() -> ConfigDict:
    """ Returns a ConfigDict from the environment
    """
    ret: ConfigDict = {}

    keys = ["verbose", "browser", "username", "password", "domain"]
    for key in keys:
        set_if_present(ret, key)

    return ret


def set_if_present(config: ConfigDict, key: str) -> None:
    """ Sets the key/val in the passed-in config, IF the env var is present
    """
    env_name = f"GOOGLE_DOMAINS_{key.upper()}"
    env_val = os.environ.get(env_name)
    if env_val:
        config[key] = env_val


def initialize_from_cmdline(the_args: List[str]) -> ConfigDict:
    """ Returns a ConfigDict from the command-line
    """
    ret = {}
    parser = argparse.ArgumentParser()

    # Optional args
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        help="Increase verbosity",
        action="store_true",
    )
    parser.add_argument(
        "-b",
        "--browser",
        dest="browser",
        type=str,
        help="The browser to use",
        default="firefox",
        # https://splinter.readthedocs.io/en/latest/browser.html
        choices=["chrome", "firefox", "zope.testbrowser"],
    )
    parser.add_argument(
        "-q", "--quiet", dest="quiet", help="Decrease verbosity", action="store_true"
    )
    parser.add_argument(
        "-u", "--username", dest="username", help="Google Domains username"
    )
    parser.add_argument(
        "-p", "--password", dest="password", help="Google Domains password"
    )
    parser.add_argument("-d", "--domain", dest="domain", help="The domain suffix")

    # Positional args
    parser.add_argument(
        dest="operation",
        type=str,
        help="The CRUD operation",
        default="ls",
        nargs="?",
        choices=["ls", "add", "del"],
    )
    parser.add_argument(
        dest="hostname",
        type=str,
        help="The hostname, if adding or deleting",
        default="",
        nargs="?",
    )
    parser.add_argument(
        dest="target", help="The target URL, if adding", default="", nargs="?"
    )
    args, _ = parser.parse_known_args(the_args)

    # Conditionally set these
    if args.verbose:
        ret["verbose"] = args.verbose
    if args.quiet:
        ret["verbose"] = not args.quiet

    if args.browser:
        ret["browser"] = args.browser
    if args.username:
        ret["username"] = args.username
    if args.password:
        ret["password"] = args.password
    if args.domain:
        ret["domain"] = args.domain

    # Always set these
    ret["hostname"] = args.hostname
    ret["target"] = args.target
    ret["operation"] = args.operation

    return ret


def validate_args(args: SimpleNamespace) -> None:
    """ Raises an exception if the config is insufficient
    """
    if args.operation == "add":
        if not args.hostname:
            raise RuntimeError("The add operation needs a --hostname")
        if not args.target:
            raise RuntimeError("The add operation needs a --target")

    if args.operation == "del":
        if not args.hostname:
            raise RuntimeError("The del operation needs a --hostname")
