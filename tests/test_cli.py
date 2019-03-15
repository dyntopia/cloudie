import tempfile
from unittest import TestCase

import click
import click.testing

from cloudie import cli


class TestCli(TestCase):
    def setUp(self) -> None:
        self.config = tempfile.NamedTemporaryFile()
        self.runner = click.testing.CliRunner()

    def tearDown(self) -> None:
        self.config.close()

    def test_missing_command(self) -> None:
        args = ["--config-file", self.config.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("Missing command" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_invalid_config(self) -> None:
        @cli.cli.command()
        def command() -> None:
            pass

        self.config.write(b"asdf")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("File contains no section headers" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_valid_config(self) -> None:
        @cli.cli.command()
        @click.pass_context
        def command(ctx: click.Context) -> None:
            print(ctx.obj.config.get("asdf", "key"))

        self.config.write(b"[asdf]\nkey=value\n")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(result.output, "value\n")
        self.assertEqual(result.exit_code, 0)
