"""
    CRUD operations for Google Domains

    Examples:
        > google-domains ls                             # lists the current redirects
        > google-domains add foo https://google.com     # adds a redirect from foo to google.com
        > google-domains del foo                        # deletes the "foo" hostname redirect

    YAML config file in ~/.google_domains.yaml can contain:
        verbose: False
        domain: "<your domain suffix>"
        username: "<your Google Domains username>"
        password: "<your Google Domains password>"

    Alternatively, set environment variables:
        GOOGLE_DOMAINS_DOMAIN
        GOOGLE_DOMAINS_USERNAME
        GOOGLE_DOMAINS_PASSWORD

"""
import argparse
from functools import wraps
import os.path
import sys
import time
from types import SimpleNamespace
from typing import Dict, List
from fqdn import FQDN
from selenium.common.exceptions import (
    StaleElementReferenceException,
    WebDriverException,
)
from splinter import Browser
from splinter.element_list import ElementList
from splinter.driver.webdriver import WebDriverElement
from tabulate import tabulate
import yaml


VERBOSE = False  # should we run headless and output lots of messages?
DOM_MAX_ATTEMPTS = (
    10  # How many times to retry DOM errors. Reasonably large, somewhat arbitrary
)
ConfigDict = Dict[str, str]  # type alias for mypy


def main():
    """ Reads the args, and performs the CRUDs
    """
    args = initialize_args()
    browser = gdomain_api_login(args.domain, args.username, args.password)

    try:
        if args.operation == "add":
            gdomain_api_add(browser, args.domain, args.hostname, args.target)
        elif args.operation == "del":
            gdomain_api_del(browser, args.domain, args.hostname)
        else:
            gdomain_api_ls(browser, args.domain)

    except WebDriverException as e:
        print(e)

    browser.quit()


class Timer:
    """ Timer block
    """

    first_click = None

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.first_click = click()

    def __exit__(self, the_type, the_value, the_traceback):
        # if an exception was raised, ignore
        if the_type:
            return

        ms = click() - self.first_click
        debug(f"   time: {self.name} took {ms} ms")


def print_timing(function):
    """ Decorator, prints out the execution time of the function in ms
    """

    @wraps(function)
    def decorated_function(*args, **kwargs):
        """ the decorating fx
        """
        debug(f"   call: {function.__name__}")
        with Timer(function.__name__):
            ret = function(*args, **kwargs)

        return ret

    return decorated_function


@print_timing
def gdomain_api_login(domain: str, username: str, password: str) -> Browser:
    """ Logs in, and returns a headless browser at the DNS page
    """
    browser = Browser("firefox", headless=not VERBOSE)
    browser.visit("https://domains.google.com/registrar/")

    link = browser.links.find_by_partial_text("Sign")
    link.click()

    # Enter username, wait, enter password
    browser.find_by_id("identifierId").fill(username)
    click_next(browser)

    wait_for_tag(browser, "div", "Enter your password")

    browser.find_by_name("password").fill(password)
    click_next(browser)

    browser.visit(f"https://domains.google.com/registrar/{domain}/dns")
    wait_for_tag(browser, "h3", "Synthetic records")
    return browser


def gdomain_api_ls(browser: Browser, domain: str) -> None:
    """ Prints the current list of redirects
    """
    entries = gdomain_ls(browser, domain)

    # Convert it to a list of lists, tabulate handles this natively
    array = []
    for key, val in entries.items():
        array.append([key, val])
    headers = ["Hostname", "Redirect URL"]

    print()
    print(tabulate(array, headers, tablefmt="simple"))
    print()


def gdomain_api_add(browser: Browser, domain: str, hostname: str, target: str) -> None:
    """ Adds the hostname-to-target redirect to Google Domains
    """
    hostname = fqdn(hostname, domain)
    entries = gdomain_ls(browser, domain)

    # if its already here and pointed to the right place, do nothing
    if hostname in entries and entries[hostname] == target:
        print(f"{hostname} already exists. Doing nothing.")
        return

    # if its already here, and pointed to the wrong place. delete it
    if hostname in entries:
        gdomain_del(browser, domain, hostname)

    gdomain_add(browser, domain, hostname, target)

    if VERBOSE:
        gdomain_api_ls(browser, domain)


def gdomain_api_del(browser: Browser, domain: str, hostname: str) -> None:
    """ Deletes the redirect
    """
    hostname = fqdn(hostname, domain)
    entries = gdomain_ls(browser, domain)

    if hostname not in entries:
        print(f"Hostname not found: {hostname}. Doing nothing.")
        return

    gdomain_del(browser, domain, hostname)

    if VERBOSE:
        gdomain_api_ls(browser, domain)


@print_timing
def gdomain_ls(browser: Browser, domain: str) -> Dict[str, str]:
    """ Returns a dict of hostnames to targets
    """
    records = get_synthetic_records_div(browser)
    divs = records.find_by_xpath(f"//div[contains(text(), '{domain}')]")
    ret = {}
    for div in divs:
        arr = div.html.split()
        hostname = arr[0]
        target = arr[-1]

        # skips skippable elements
        if "→" in target:
            continue
        if domain not in hostname:
            continue

        ret[hostname] = target

    return ret


@print_timing
def gdomain_add(browser: Browser, domain: str, hostname: str, target: str) -> None:
    """ Adds a redirect from the hostname to the target url
    """
    hostname = un_fqdn(fqdn(hostname, domain), domain)  # make sure hostname is good

    records = get_synthetic_records_div(browser)
    get_element_by_placeholder(records, "Subdomain").fill(hostname)
    get_element_by_placeholder(records, "Destination URL").fill(target)

    records.find_by_text("Temporary redirect (302)").click()
    records.find_by_text("Forward path").click()
    records.find_by_text("Enable SSL").click()

    button = records.find_by_text("Add")
    button.click()

    wait_for_success_notification(browser)


@print_timing
def gdomain_del(browser: Browser, domain: str, hostname: str) -> None:
    """ Deletes the passed-in hostname from Google Domains
        WARNING: THIS SEEMS BRITTLE
    """
    hostname = fqdn(hostname, domain)

    # find the right div for this hostname
    records = get_synthetic_records_div(browser)
    # xpath = "//div[contains(@class, 'H2OGROB-d-t')]"
    xpath = f"//div[contains(text(), '{hostname}')]/../.."
    divs = records.find_by_xpath(xpath)
    div = divs.first

    # click the delete button
    delete_button = get_element_by_substring("Delete", div.find_by_tag("button"))
    delete_button.click()

    # wait for the modal dialog
    wait_for_tag(browser, "h3", "Delete synthetic record?")

    # get the form element for the modal dialog
    modal_form = get_element_by_substring(
        "Delete synthetic record?", browser.find_by_tag("form")
    )
    modal_button = get_element_by_substring("Delete", modal_form.find_by_tag("button"))
    modal_button.click()

    wait_for_success_notification(browser)


def get_synthetic_records_div(browser: Browser) -> WebDriverElement:
    """ Returns the parent div of the "Synthetic records" h3
    """
    xpath = '//h3[contains(text(), "Synthetic records")]/..'
    ret = browser.find_by_xpath(xpath).first
    return ret


def get_element_by_substring(substring: str, elements: ElementList) -> WebDriverElement:
    """ Returns the first element in the passed-in list that contains the substring
    """
    for element in elements:
        if substring in element.html:
            return element

    error(f"Element not found: {substring}")
    return None


def get_element_by_placeholder(
    element: WebDriverElement, placeholder: str
) -> WebDriverElement:
    """ Returns the element containing the placeholder attribute
        TODO: Probably cleaner to use an xpath expression here, but
    """
    inputs = element.find_by_tag("input")
    for x in inputs:
        if f'placeholder="{placeholder}"' in x.outer_html:
            return x

    raise RuntimeError(f"Placeholder element not found: {placeholder}")


def wait_for_success_notification(browser: Browser) -> None:
    """ Wait until we get the success message
        TODO: What if it fails?
    """
    wait_for_tag(browser, "a", "Dismiss")


@print_timing
def wait_for_tag(browser: Browser, tag: str, substring: str) -> None:
    """ Waits indefinitely for the string to appear in the
        This is faster than the wait_for method, if we happen to know what tag we're looking for
    """
    debug(f"   wait: ({tag}) {substring}")

    attempts = 0
    while True:
        try:
            # try to find the element
            while not does_element_exist(browser, tag, substring):

                # if it doesnt exist, sleep and try again
                debug(f"  sleep: ({tag}) {substring}")
                time.sleep(0.5)
                continue

            # it does exist! return
            debug(f"  found: ({tag}) {substring}")
            return

        except StaleElementReferenceException:
            # NOTE: https://stackoverflow.com/questions/41539231/splinter-is-text-present-causes-intermittent-staleelementreferenceexception-wi  # pylint: disable=line-too-long  # noqa
            attempts += 1
            if attempts == DOM_MAX_ATTEMPTS:
                raise
            continue


@print_timing
def does_element_exist(browser: Browser, tag: str, substring: str) -> bool:
    """ Returns True if an element with the substring exists in the DOM, and is visible
    """
    xpath = f"//{tag}"
    elements = browser.find_by_xpath(xpath)
    for element in elements:
        if substring in element.html:
            if element.visible:
                return True

    return False


def click_next(browser: Browser) -> None:
    """ Clicks Next in the browser
    """
    attempts = 0

    buttons = browser.find_by_tag("button")
    for button in buttons:
        try:
            if button.text == "Next":
                button.click()

        # NOTE: https://stackoverflow.com/questions/41539231/splinter-is-text-present-causes-intermittent-staleelementreferenceexception-wi  # pylint: disable=line-too-long  # noqa
        except StaleElementReferenceException:
            attempts += 1
            if attempts == DOM_MAX_ATTEMPTS:
                raise
            continue


def fqdn(hostname: str, domain: str, relative: bool = True) -> str:
    """ Returns the FQDN of the passed-in hostname
    """
    if domain not in hostname:
        hostname = f"{hostname}.{domain}."

    this_fqdn = FQDN(hostname)

    if relative:
        return this_fqdn.relative
    return this_fqdn.absolute


def un_fqdn(hostname: str, domain: str) -> str:
    """ Returns the relative hostname, sans domain
    """
    ret = hostname.replace(domain, "")
    ret = ret.strip(".")
    return ret


def error(message: str) -> None:
    """ Prints an error message
    """
    print(f"ERROR: {message}")


def debug(message: str) -> None:
    """ Prints an message if VERBOSE is set
    """
    if VERBOSE:
        print(message)


def click() -> int:
    """ Returns milliseconds since the epoch
    """
    return int(round(time.time() * 1000))


def initialize_args() -> SimpleNamespace:
    """ Initializes config info, from three sources:
        1. Config file
        2. Command line
        3. Environment variables

        Sets the VERBOSE global variable
        Returns all the config args in a Namespace
    """
    config = initialize_from_files()
    config.update(initialize_from_env())
    config.update(initialize_from_cmdline(sys.argv[1:]))

    ret = SimpleNamespace(**config)
    if ret.verbose:
        print(f"   config verbose: {ret.verbose}")
        print(f"   config username: {ret.username}")
        print(f"   config password: {ret.password}")
        print(f"   config domain: {ret.domain}")
        print(f"   config operation: {ret.operation}")
        print(f"   config hostname: {ret.hostname}")
        print(f"   config target: {ret.target}")
        print()

    global VERBOSE  # pylint: disable=global-statement
    VERBOSE = ret.verbose

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
        expanded = os.path.expanduser(location)
        if os.path.isfile(expanded):
            with open(expanded) as file:
                ret.update(yaml.load(file, Loader=yaml.FullLoader))

    return ret


def get_configfile_locations() -> List[str]:
    """ Returns a list of possible file locations
    """
    return ["/etc/google-domains.yaml", "~/.google_domains.yaml"]


def initialize_from_env() -> ConfigDict:
    """ Returns a ConfigDict from the environment
    """
    ret: ConfigDict = {}

    keys = ["debug", "username", "password", "domain"]
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
        dest="hostname", type=str, help="The hostname, if adding or deleting", default="", nargs="?",
    )
    parser.add_argument(dest="target", help="The target URL, if adding", default="", nargs="?")
    args, _ = parser.parse_known_args(the_args)

    # Conditionally set these
    if args.verbose:
        ret["verbose"] = args.verbose
    if args.quiet:
        ret["verbose"] = not args.quiet
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


if __name__ == "__main__":
    main()
