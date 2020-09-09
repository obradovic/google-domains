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
    gdomain_api_construct,
    gdomain_api_destruct,
    gdomain_api_add,
    gdomain_api_del,
    gdomain_api_ls,
)


def main():
    """ Reads the config, and performs the CRUDs
    """
    c = configure()
    browser = gdomain_api_construct(c.domain, c.username, c.password, c.browser)

    try:
        if c.operation == "add":
            gdomain_api_add(browser, c.domain, c.hostname, c.target)
        elif c.operation == "del":
            gdomain_api_del(browser, c.domain, c.hostname)
        else:
            gdomain_api_ls(browser, c.domain)

    except Exception as e:  # pylint: disable=broad-except
        print(e)

    gdomain_api_destruct(browser)


if __name__ == "__main__":
    main()
