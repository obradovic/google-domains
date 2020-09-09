""" Wheel Config
"""
from setuptools import setup


def get_readme_md_contents():
    """read the contents of your README file"""
    with open("README.md", encoding='utf-8') as f:
        long_description = f.read()
        return long_description

setup(
    version="0.1.3",
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
