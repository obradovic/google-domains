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
from google_domains.config import configure
from google_domains.api import (
    api_construct,
    api_destruct,
    api_add,
    api_del,
    api_ls,
)


def main():
    """ Reads the config, and performs the CRUDs
    """
    c = configure()
    browser = api_construct(c.domain, c.username, c.password, c.browser)

    try:
        if c.operation == "add":
            api_add(browser, c.domain, c.hostname, c.target)
        elif c.operation == "del":
            api_del(browser, c.domain, c.hostname)
        else:
            api_ls(browser, c.domain)

    except Exception as e:  # pylint: disable=broad-except
        print(e)

    api_destruct(browser)


if __name__ == "__main__":
    main()
