import tempfile
from unittest import TestCase

import click
import click.testing

from cloudie import cli


class TestGroup(TestCase):
    def setUp(self) -> None:
        self.config = tempfile.NamedTemporaryFile()
        self.runner = click.testing.CliRunner()

    def tearDown(self) -> None:
        self.config.close()

    def test_not_implemented(self) -> None:
        @cli.cli.command()
        def command() -> None:
            raise NotImplementedError("asdf")

        args = ["--config-file", self.config.name, command.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("asdf" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_implemented(self) -> None:
        @cli.cli.command()
        def command() -> None:
            print("success")

        args = ["--config-file", self.config.name, command.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("success" in result.output)
        self.assertEqual(result.exit_code, 0)
