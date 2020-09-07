"""
    CRUD operations for Google Domains
"""
import argparse
from functools import wraps
import sys
import time
from typing import Dict, List, Tuple
import delegator
from fqdn import FQDN
from selenium.common.exceptions import StaleElementReferenceException
from splinter import Browser
from splinter.element_list import ElementList
from splinter.driver.webdriver import WebDriverElement


DOMAIN = ""
GOOGLE_DOMAINS_USERNAME = ""
GOOGLE_DOMAINS_PASSWORD = ""
GCLOUD_TARGET = "ghs.googlehosted.com."
GCLOUD_PROJECT = ""
GCLOUD_ZONE = ""
DEBUG = False


def print_timing(func):
    """ Decorator function, prints out the execution time in ms
    """

    @wraps(func)
    def decorated_function(*args, **kwargs):
        """ the decorated fx
        """

        # time the method
        debug(f"   call: {func.__name__}")
        a = click()
        ret = func(*args, **kwargs)
        ms = click() - a
        debug(f"   time: {func.__name__} took {ms} ms.")

        return ret

    return decorated_function


@print_timing
def gdomain_login() -> Browser:
    """ Logs in, and returns a headless browser at the DNS page
    """
    browser = Browser("firefox", headless=not DEBUG)
    browser.visit("https://domains.google.com/registrar/")

    link = browser.links.find_by_partial_text("Sign").first
    link.click()

    # Enter username
    login_name = browser.find_by_id("identifierId").first
    login_name.fill(GOOGLE_DOMAINS_USERNAME)
    # browser.type('type', '\n')
    click_next(browser)

    # Enter password (there MUST be a better way to do this??)
    wait_for(browser, "Enter your password")

    pwd = browser.find_by_name("password").first
    pwd.fill(GOOGLE_DOMAINS_PASSWORD)
    click_next(browser)

    browser.visit(f"https://domains.google.com/registrar/{DOMAIN}/dns")
    wait_for(browser, "Synthetic records")
    return browser


@print_timing
def gdomain_list(browser: Browser) -> Dict[str, str]:
    """ This xpath does NOT seem stable
    """
    divs = browser.find_by_xpath(" //div[contains(@class, 'H2OGROB-q-Mb')]")
    ret = {}
    for div in divs:
        if f".{DOMAIN} " in div.html:
            arr = div.html.split()
            ret[arr[0]] = arr[-1]
    return ret


def gdomain_operation_ls(browser: Browser) -> None:
    """ Prints the current list of redirects
    """
    entries = gdomain_list(browser)
    print()
    for hostname, url in entries.items():
        print(f"{hostname} : {url}")
    print()


def gdomain_operation_add(browser: Browser, hostname: str, destination: str) -> None:
    """ Adds the hostname -> destination redirect to Google Domains
    """
    entries = gdomain_list(browser)
    hostname = fqdn(hostname, relative=True)

    # if its already here and pointed to the right place, do nothing
    if hostname in entries and entries[hostname] == destination:
        print(f"{hostname} already exists. Doing nothing.")
        return

    # if its still here, its pointed to the wrong place. delete it
    if hostname in entries:
        gdomain_delete(browser, hostname)

    # add it
    gdomain_add(browser, hostname, destination)
    gdomain_operation_ls(browser)

    # Add to Google Cloud DNS
    if not clouddns_contains(hostname):
        clouddns_add(hostname)


def gdomain_operation_del(browser: Browser, hostname: str) -> None:
    """ Deletes the redirect
    """
    entries = gdomain_list(browser)
    hostname = fqdn(hostname, relative=True)
    if hostname not in entries:
        print(f"Not found: {hostname}")
        return

    gdomain_delete(browser, hostname)


@print_timing
def gdomain_add(browser: Browser, hostname: str, destination: str) -> None:
    """ Adds a redirect from the hostname to the destination url
    """
    hostname = un_fqdn(fqdn(hostname, relative=True))  # make sure hostname is good

    div = get_synthetic_records_div(browser)
    get_element_by_placeholder(div, "Subdomain").fill(hostname)
    get_element_by_placeholder(div, "Destination URL").fill(destination)

    div.find_by_text("Temporary redirect (302)").click()
    div.find_by_text("Forward path").click()
    div.find_by_text("Enable SSL").click()

    button = div.find_by_text("Add")
    button.click()

    # Wait until we get the success message. TODO: What if it fails?
    wait_for(browser, f"Changes to {DOMAIN} saved")


@print_timing
def gdomain_delete(browser: Browser, hostname: str) -> None:
    """ Deletes the passed-in hostname from Google Domains
    """
    hostname = fqdn(hostname, relative=True)

    # find the right div for this hostname
    div = get_element_by_substring(
        hostname, browser.find_by_xpath("//div[contains(@class, 'H2OGROB-d-t')]")
    )

    # click the delete button
    delete_button = get_element_by_substring("Delete", div.find_by_tag("button"))
    delete_button.click()

    # wait for the modal dialog
    wait_for(browser, "Delete synthetic record?")

    # get the form element for the modal dialog
    modal_form = get_element_by_substring(
        "Delete synthetic record?", browser.find_by_tag("form")
    )
    modal_button = get_element_by_substring("Delete", modal_form.find_by_tag("button"))
    modal_button.click()

    # Wait until we get the success message. TODO: What if it fails?
    wait_for(browser, f"Changes to {DOMAIN} saved")


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

    error(f"ELEMENT NOT FOUND: {substring}")
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


@print_timing
def wait_for(browser: WebDriverElement, string: str) -> None:
    """ Waits indefinitely for the string to appear in the browser
    """
    debug(f'   wait: "{string}"')
    while not browser.is_text_present(string):
        debug(f'  sleep: "{string}"')
        time.sleep(0.5)

    debug(f'  found: "{string}"')


def click_next(browser: Browser) -> None:
    """ Clicks Next in the browser
    """
    max_attempts = 10  # arbitrary, somewhat large
    attempts = 0

    buttons = browser.find_by_tag("button")
    for button in buttons:
        try:
            if button.text == "Next":
                button.click()
        except StaleElementReferenceException:
            # NOTE: https://stackoverflow.com/questions/41539231/splinter-is-text-present-causes-intermittent-staleelementreferenceexception-wi  # pylint: disable=line-too-long  # noqa
            attempts += 1
            if attempts == max_attempts:
                raise
            continue


def clouddns_contains(hostname: str) -> bool:
    """ Returns True if it already exists in cloud dns
    """
    hostname = fqdn(hostname)
    if hostname in clouddns_list():
        return True
    return False


def clouddns_list() -> List[str]:
    """ Returns a sorted list of Cloud DNS entries that point to Google Domains
    """
    zone = f"--zone={GCLOUD_ZONE}"
    cmd = f"gcloud dns record-sets list {zone}"
    output = run_command(cmd)
    ret = []

    # parse and check the output
    entries = output.split("\n")
    for entry in entries:
        if not entry:
            continue

        items = entry.split()
        dns_name = items[0]
        dns_type = items[1]
        # dns_ttl = items[2]
        dns_target = items[3]
        if dns_type == "CNAME" and dns_target == GCLOUD_TARGET:
            ret.append(dns_name)

    return sorted(ret)


def clouddns_add(hostname: str) -> bool:
    """ Sets Cloud DNS to use Google Domains for the redirect
        Returns True if all went well. False otherwise
    """
    hostname = fqdn(hostname)

    tx = f"gcloud dns record-sets transaction --project={GCLOUD_PROJECT}"
    zone = f"--zone={GCLOUD_ZONE}"
    commands = [
        f"{tx} start {zone}",
        f"{tx} add {GCLOUD_TARGET} --name={hostname} --ttl=5 --type=CNAME {zone}",
        f"{tx} execute {zone}",
    ]

    try:
        for command in commands:
            run_command(command)
    except:  # pylint: disable=bare-except  # noqa
        delegator.run(f"{tx} abort")
        return False

    return True


def run_command(command: str) -> str:
    """ Returns the output of the command
        Raises a RuntimeError if something went sideways
    """
    response = delegator.run(command)
    if not response.ok:
        error(f"running: {command}: {response.err}")
        raise RuntimeError

    return response.out


def fqdn(hostname: str, relative: bool = False) -> str:
    """ Returns the absolute FQDN of the passed-in hostname
    """
    if DOMAIN not in hostname:
        hostname = f"{hostname}.{DOMAIN}."

    the_fqdn = FQDN(hostname)

    if relative:
        return the_fqdn.relative
    return the_fqdn.absolute


def un_fqdn(hostname: str) -> str:
    """ Returns the relative hostname, sans domain
    """
    ret = hostname.replace(DOMAIN, "")
    ret = ret.strip(".")
    return ret


def error(message: str) -> None:
    """ Prints an error message
    """
    print(f"ERROR: {message}")


def debug(message: str) -> None:
    """ Prints an message if DEBUG is set
    """
    if DEBUG:
        print(message)


def click() -> int:
    """ Returns milliseconds since the epoch
    """
    return int(round(time.time() * 1000))


# pylint: disable=global-statement
def initialize_args(the_args: List[str]) -> Tuple[str, str, str]:
    """ parses command-line args
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-d",
        "--debug",
        dest="debug",
        help="Print debug info",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "-u",
        "--username",
        dest="username",
        help="Google Domains username",
        required=True,
    )
    parser.add_argument(
        "-p",
        "--password",
        dest="password",
        help="Google Domains password",
        required=True,
    )

    parser.add_argument(
        "--gcloud-project",
        dest="gcloud_project",
        help="The gcloud project name",
        required=False,
    )
    parser.add_argument(
        "--gcloud-zone", dest="gcloud_zone", help="The gcloud zone", required=False
    )

    parser.add_argument("--domain", dest="domain", help="Domain suffix", required=True)
    parser.add_argument(
        "--hostname", dest="hostname", help="The hostname", required=False
    )
    parser.add_argument(
        "--destination", dest="destination", help="The destination", required=False
    )

    parser.add_argument(dest="operation", choices=["add", "del", "ls"])

    args, _ = parser.parse_known_args(the_args)
    hostname = args.hostname
    destination = args.destination
    operation = args.operation

    global DEBUG
    DEBUG = args.debug

    global GOOGLE_DOMAINS_USERNAME
    GOOGLE_DOMAINS_USERNAME = args.username

    global GOOGLE_DOMAINS_PASSWORD
    GOOGLE_DOMAINS_PASSWORD = args.password

    global DOMAIN
    DOMAIN = args.domain

    global GCLOUD_PROJECT
    GCLOUD_PROJECT = args.gcloud_project

    global GCLOUD_ZONE
    GCLOUD_ZONE = args.gcloud_zone

    if operation == "add":
        if not hostname:
            raise RuntimeError("The add operation needs a --hostname")
        if not destination:
            raise RuntimeError("The add operation needs a --destination")

    if operation == "del":
        if not hostname:
            raise RuntimeError("The del operation needs a --hostname")

    if DEBUG:
        print(f"   param debug: {DEBUG}")
        print(f"   param username: {GOOGLE_DOMAINS_USERNAME}")
        print(f"   param password: {GOOGLE_DOMAINS_PASSWORD}")
        print(f"   param gcloud project: {GCLOUD_PROJECT}")
        print(f"   param gcloud zone: {GCLOUD_ZONE}")
        print(f"   param domain: {DOMAIN}")
        print(f"   param operation: {operation}")
        print(f"   param hostname: {hostname}")
        print()

    return operation, hostname, destination


def main():
    """ well, this is main
    """
    try:
        operation, hostname, destination = initialize_args(sys.argv[1:])
    except RuntimeError as e:
        print()
        print(f"  {e}")
        print()
        return

    browser = gdomain_login()

    if operation == "add":
        gdomain_operation_add(browser, hostname, destination)
    if operation == "del":
        gdomain_operation_del(browser, hostname)
    if operation == "ls":
        gdomain_operation_ls(browser)

    browser.quit()


if __name__ == "__main__":
    main()
