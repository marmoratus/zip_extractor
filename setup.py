"""Setup script for the zip_extractor package."""

from setuptools import find_packages, setup

setup(
    name="zip_extractor",
    version="1.0.0",
    description="Multithreaded ZIP extraction with diff copy functionality",
    packages=find_packages(include=["src", "src.*"]),
    python_requires=">=3.8",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "zip-extractor=src.main:main",
        ],
    },
)
