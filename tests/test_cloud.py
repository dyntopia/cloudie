from libcloud.common.base import BaseDriver
from libcloud.compute.providers import Provider

from cloudie import cli, cloud

from .helpers import ClickTestCase


class TestPassDriver(ClickTestCase):
    def test_success(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(Provider)
        def command(driver: BaseDriver) -> None:
            print("{} - {}".format(driver.name, driver.creds))

        self.config.write(b"[x]\nprovider=dummy\nkey=abcd\n")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(result.output, "Dummy Node Provider - abcd\n")
        self.assertEqual(result.exit_code, 0)

    def test_success_unsupported_options(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(Provider)
        def command(driver: BaseDriver) -> None:
            print("{} - {}".format(driver.name, driver.creds))

        self.config.write(b"[x]\nprovider=dummy\nkey=abcd\naaa=bbb\ncc=dd\n")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(result.output, "Dummy Node Provider - abcd\n")
        self.assertEqual(result.exit_code, 0)

    def test_missing_role(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(Provider)
        def command(_driver: BaseDriver) -> None:
            pass

        self.config.write(b"[xy]\nprovider=dummy\nkey=abcd\n")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("missing role 'x'" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_missing_provider(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(Provider)
        def command(_driver: BaseDriver) -> None:
            pass

        self.config.write(b"[x]\nprovider1=dummy\nkey=abcd\n")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("must specify 'provider' and 'key'" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_missing_key(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(Provider)
        def command(_driver: BaseDriver) -> None:
            pass

        self.config.write(b"[x]\nprovider=dummy\n")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("must specify 'provider' and 'key'" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_invalid_provider(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(Provider)
        def command(driver: BaseDriver) -> None:
            print("{} - {}".format(driver.name, driver.creds))

        self.config.write(b"[x]\nprovider=nope\nkey=abcd\n")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("Provider nope does not exist" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_no_insecure_connection(self) -> None:
        """
        AbiquoNodeDriver initializes its superclass with `secure=False`.

        See the documentation for `allow_insecure` in security.py.
        """

        @cli.cli.command()
        @cloud.pass_driver(Provider)
        def command(driver: BaseDriver) -> None:
            print("{}".format(driver.name))

        self.config.write(b"[x]\nprovider=abiquo\nkey=a\nsecret=b\nendpoint=c")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(
            str(result.exception),
            "Non https connections are not allowed (use secure=True)"
        )
        self.assertEqual(type(result.exception), ValueError)
        self.assertNotEqual(result.exit_code, 0)
