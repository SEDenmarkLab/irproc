from setuptools import setup, find_packages
from glob import glob
import os

setup(
    name="irproc",
    # packages=find_packages(include="irproc"),
    data_files=[],
    version="0.1.0",
    author="Alexander S. Shved",
    author_email="shvedalx@illinois.edu",
    install_requires=[
        "matplotlib>=3.4.3",
        "numpy>=1.21.1",
        "scipy>=1.4.1",
        "pandas>1.3.5",
    ],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["irproc = irproc:main.main"]},
)
