#!/usr/bin/env python3

from typing import Iterator

from setuptools import setup

import cloudie


def get_requirements(filename: str) -> Iterator[str]:
    with open(filename, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line and not line.startswith("#"):
                name, *_ = line.split("=")[0].split()
                yield name


setup(
    name="cloudie",
    version=cloudie.__version__,
    author="Hans Jerry Illikainen",
    author_email="hji@dyntopia.com",
    install_requires=list(get_requirements("requirements/requirements.txt")),
    entry_points={"console_scripts": ["cloudie = cloudie.cli:cli"]}
)
