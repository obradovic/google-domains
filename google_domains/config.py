"""
    Arg-parsing and App Configuration
"""
import argparse
import os.path
import sys
from typing import Dict, List, Optional
from box import Box
import yaml
from google_domains.log import set_verbose


# Type alias
ConfigDict = Dict[str, str]


def configure() -> Optional[Box]:
    """ Initializes config info, from three sources:
        1. Config file
        2. Command line
        3. Environment variables

        Sets global verbosity
        Returns all the config args
    """
    config = initialize_from_files()
    config.update(initialize_from_env())
    config.update(initialize_from_cmdline(sys.argv[1:]))

    if config["verbose"]:
        keys = [
            "verbose",
            "browser",
            "username",
            "password",
            "domain",
            "operation",
            "hostname",
            "target",
        ]
        for key in keys:
            print(f"   config {key}: {config.get(key, '')}")
        print()

    ret = Box(config)
    set_verbose(ret.verbose)

    error_message = validate_args(ret)
    if error_message:
        print(f"\n  {error_message}\n")
        return None

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
    filename = "google-domains.yaml"
    return [f"/etc/{filename}", f"~/.{filename}"]


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
        help="Increase verbosity. Will display the browser",
        action="store_true",
    )
    parser.add_argument(
        "-b",
        "--browser",
        dest="browser",
        type=str,
        help="The browser to use. Requires it to be installed",
        default="firefox",
        # https://splinter.readthedocs.io/en/latest/browser.html
        choices=["chrome", "firefox", "zope.testbrowser"],
    )
    parser.add_argument(
        "-q", "--quiet", dest="quiet", help="Decrease verbosity", action="store_true"
    )
    parser.add_argument(
        "-u", "--username", dest="username", help="Your Google Domains username"
    )
    parser.add_argument(
        "-p", "--password", dest="password", help="Your Google Domains password"
    )
    parser.add_argument("-d", "--domain", dest="domain", help="The domain suffix")

    # Positional args
    parser.add_argument(
        dest="operation",
        type=str,
        help="The CRUD operation. List redirects, add a redirect, or delete a redirect",
        default="ls",
        nargs="?",
        choices=["ls", "add", "del"],
    )
    parser.add_argument(
        dest="hostname",
        type=str,
        help="The hostname to add or delete",
        default="",
        nargs="?",
    )
    parser.add_argument(
        dest="target", help="The target URL to add", default="", nargs="?"
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


def validate_args(args: Box) -> Optional[str]:
    """ Returns an error string if the args werent validated
        Returns None if everything's ok
    """

    # these operations require these arguments to be present
    operation_dependencies = {
        "add": ["hostname", "target"],
        "del": ["hostname"],
    }

    for operation, dependencies in operation_dependencies.items():
        if args.operation == operation:
            for key in dependencies:
                if key not in args:
                    return f"The {args.operation} operation needs a --{key}"

    # All of these arguments are required for everything
    for key in ["username", "password", "domain"]:
        if key not in args:
            return f"Needs a {key}. Please either use the -{key[0]} option, set GOOGLE_DOMAINS_{key.upper()}, or set it in the config file(s)"  # noqa  # pylint: disable=line-too-long

    return None
