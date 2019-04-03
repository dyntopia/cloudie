#!/usr/bin/env python3

import re
import sys
from typing import Iterator

from setuptools import setup

import cloudie


def get_requirements(filename: str) -> Iterator[str]:
    with open(filename, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line and not line.startswith("#"):
                m = re.match(r"([a-zA-Z0-9-_]+)[ \t]==[ \t]+([0-9\.]+)", line)
                if not m:
                    sys.exit("ERROR: invalid requirements.txt")
                yield "{0} >= {1}".format(*m.groups())


setup(
    name="cloudie",
    version=cloudie.__version__,
    author="Hans Jerry Illikainen",
    author_email="hji@dyntopia.com",
    license="BSD-2-Clause",
    description="Command-line interface for various cloud services",
    long_description="See https://github.com/dyntopia/cloudie",
    url="https://github.com/dyntopia/cloudie",
    install_requires=list(get_requirements("requirements/requirements.txt")),
    packages=["cloudie"],
    entry_points={"console_scripts": ["cloudie = cloudie.cli:cli"]}
)
