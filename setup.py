import os
import re
from setuptools import setup, find_packages

def get_version():
    """Extract version from pyyardian/__init__.py"""
    init_py = os.path.join(os.path.abspath(os.path.dirname(__file__)), "pyyardian", "__init__.py")
    with open(init_py, "r", encoding="utf-8") as f:
        # Look for the line __version__ = "..."
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', f.read())
        if match:
            return match.group(1)
    raise RuntimeError("Unable to find version string.")

# Read the contents of your README file for the long description
# This ensures your PyPI page looks as good as your GitHub page
long_description = ""
readme_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    # Fallback if README.md is missing
    long_description = "A Python module for interacting with the Yardian irrigation controller."

setup(
    name="pyyardian",
    version=get_version(),  # Dynamically pulled from __init__.py
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
    ],
    python_requires=">=3.9",
    
    # Metadata
    license="MIT",
    author="Yardian Support",
    author_email="contact@aeonmatrix.com",
    description="A module for interacting with the Yardian irrigation controller",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aeon-matrix/pyyardian",
    
    # Classifiers help users find your project on PyPI
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Home Automation",
    ],
)