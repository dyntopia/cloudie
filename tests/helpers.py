import tempfile
import unittest
from typing import Any, List

import click.testing
from libcloud.compute.base import KeyPair, Node
from libcloud.compute.drivers.dummy import DummyNodeDriver
from texttable import Texttable


class ClickTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.config = tempfile.NamedTemporaryFile()
        self.runner = click.testing.CliRunner()

    def tearDown(self) -> None:
        self.config.close()


class TexttableMock(Texttable):  # type: ignore
    def __init__(self, max_width: int = 80) -> None:
        super().__init__(max_width)
        self.headers = []  # type: List[str]
        self.rows = []  # type: List[List[str]]

    def draw(self) -> None:
        self.headers = self._header
        self.rows = self._rows


class ExtendedDummyNodeDriver(DummyNodeDriver):  # type: ignore
    # pylint: disable=abstract-method
    call_args = {}  # type: dict
    features = {"create_node": ["password", "ssh_key"]}

    key_pairs = [
        KeyPair(
            name="name-1",
            public_key="public-key-1",
            fingerprint="fingerprint-1",
            driver=None,
            extra={"id": "111"}
        ),
        KeyPair(
            name="name-2",
            public_key="public-key-2",
            fingerprint="fingerprint-2",
            driver=None,
            extra={"id": "222"}
        ),
    ]

    def list_key_pairs(self) -> List[KeyPair]:
        return self.key_pairs

    def create_node(self, **kwargs: Any) -> Node:
        self.call_args["create_node"] = kwargs
        return super().create_node(**kwargs)

    # pylint: enable=abstract-method
