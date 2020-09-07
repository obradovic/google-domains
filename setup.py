""" Wheel Config
"""
import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

setuptools.setup(
    name="google-domains-api",
    version="0.1.2",
    scripts=["google-domains-api"],
    author="Zo Obradovic",
    author_email="ping@obradovic.com",
    description="arp-scan to /etc/hosts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/obradovic/google-domains-api",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
