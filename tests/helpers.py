import tempfile
import unittest
from typing import List

import click.testing
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
