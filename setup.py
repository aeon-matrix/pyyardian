
from setuptools import setup, find_packages

setup(
    name="pyyardian",
    version="1.3.0",
    license="MIT",
    author="Yardian Support",
    author_email="contact@aeonmatrix.com",
    description="A module for interacting with the Yardian irrigation controller",
    long_description=" Python module for interacting with the Yardian irrigation controller. This module communicates directly towards the IP address of the Yardian device.",
    long_description_content_type="text/markdown",
    url="https://github.com/aeon-matrix/pyyardian",
    install_requires=["aiohttp"],
    packages=find_packages()
)