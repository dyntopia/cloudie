import click

from cloudie import cli

from .helpers import ClickTestCase


class TestCli(ClickTestCase):
    def test_missing_command(self) -> None:
        args = ["--config-file", self.config.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("Missing command" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_invalid_config(self) -> None:
        @cli.cli.command()
        def command() -> None:
            pass

        self.config.write(b"[asdf")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("Key group not on a line by itself" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_valid_config(self) -> None:
        @cli.cli.command()
        @click.pass_context
        def command(ctx: click.Context) -> None:
            print(ctx.obj.config.role.asdf.key)

        self.config.write(b"[role.asdf]\nkey='value'\n")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(result.output, "value\n")
        self.assertEqual(result.exit_code, 0)
