""" Wheel Config
"""
from setuptools import setup


def get_readme_md_contents():
    """ Reads the contents of README file
    """
    return get_file("README.md")


def get_version():
    """ Returns the contents of the VERSION file
    """
    return get_file("VERSION")


def get_file(filename: str) -> str:
    """ Returns the contents of the passed-in filename
    """
    with open(filename, encoding='utf-8') as f:
        return f.read()


setup(
    version=get_version(),
    name="google-domains",
    url="https://github.com/obradovic/google-domains",
    install_requires=[
        "PyYAML",
        "fqdn>=1.2.0",
        "splinter>=0.14.0",
        "tabulate>=0.4.2",
    ],
    entry_points={
        "console_scripts": [
            "google-domains = google_domains.command_line:main",
        ]
    },
    python_requires='>3.6.0',  # for f-strings
    author="Zo Obradovic",
    author_email="ping@obradovic.com",
    description="Command-line client for Google Domains",
    keywords="google domains",
    long_description=get_readme_md_contents(),
    long_description_content_type="text/markdown",
    packages=["google_domains"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
