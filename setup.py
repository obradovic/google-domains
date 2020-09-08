""" Wheel Config
"""
from setuptools import setup, find_packages


def get_readme_md_contents():
    """read the contents of your README file"""
    with open("README.md", encoding='utf-8') as f:
        long_description = f.read()
        return long_description

setup(
    version="0.1.1",
    name="google-domains-api",
    url="https://github.com/obradovic/google-domains-api",
    install_requires=["fqdn==1.4.0", "PyYAML==5.3.1", "splinter==0.14.0", "tabulate==0.8.7"],
    entry_points={
        "console_scripts": [
            "google-domains = google_domains.command_line:main",
        ]
    },
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
