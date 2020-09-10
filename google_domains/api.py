"""
    CRUD operations for Google Domains
"""
import time
from typing import Dict
from selenium.common.exceptions import StaleElementReferenceException
from splinter import Browser
from splinter.element_list import ElementList
from splinter.driver.webdriver import WebDriverElement
from tabulate import tabulate
from google_domains.log import debug, error, is_verbose
from google_domains.utils import fqdn, un_fqdn, print_timing


# How many times to retry DOM errors. Reasonably large, somewhat arbitrary
DOM_MAX_ATTEMPTS = 10


@print_timing
def api_construct(
    domain: str, username: str, password: str, browser_name: str = "firefox"
) -> Browser:
    """ Lifecycle creation
        Logs in, and returns a headless browser at the DNS page
    """
    browser = Browser(browser_name, headless=not is_verbose())
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


def api_destruct(browser: Browser) -> None:
    """ Lifecycle end
    """
    browser.quit()


def api_ls(browser: Browser, domain: str) -> None:
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


def api_add(browser: Browser, domain: str, hostname: str, target: str) -> None:
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

    if is_verbose():
        api_ls(browser, domain)


def api_del(browser: Browser, domain: str, hostname: str) -> None:
    """ Deletes the redirect
    """
    hostname = fqdn(hostname, domain)
    entries = gdomain_ls(browser, domain)

    if hostname not in entries:
        print(f"Hostname not found: {hostname}. Doing nothing.")
        return

    gdomain_del(browser, domain, hostname)

    if is_verbose():
        api_ls(browser, domain)


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
