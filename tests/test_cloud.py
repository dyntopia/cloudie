from unittest.mock import patch

from libcloud.common.base import BaseDriver
from libcloud.compute.providers import Provider as ComputeProvider
from libcloud.dns.providers import Provider as DNSProvider

from cloudie import cli, cloud

from .helpers import ClickTestCase


class TestPassDriver(ClickTestCase):
    def test_success(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(ComputeProvider)
        def command(driver: BaseDriver) -> None:
            print("{} - {}".format(driver.name, driver.creds))

        self.config.write(b"[role.x]\nprovider='dummy'\nkey='abcd'\n")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(result.output, "Dummy Node Provider - abcd\n")
        self.assertEqual(result.exit_code, 0)

    def test_success_unsupported_options(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(ComputeProvider)
        def command(driver: BaseDriver) -> None:
            print("{} - {}".format(driver.name, driver.creds))

        self.config.write(
            b"""
            [role.x]
            provider='dummy'
            key='abcd'
            aaa='bbb'
            cc='dd'
            """
        )
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(result.output, "Dummy Node Provider - abcd\n")
        self.assertEqual(result.exit_code, 0)

    def test_missing_role(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(ComputeProvider)
        def command(_driver: BaseDriver) -> None:
            pass

        self.config.write(b"[role.xy]\nprovider='dummy'\nkey='abcd'\n")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(result.output, "Error: unknown role 'x'\n")
        self.assertNotEqual(result.exit_code, 0)

    def test_missing_provider(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(ComputeProvider)
        def command(_driver: BaseDriver) -> None:
            pass

        self.config.write(b"[role.x]\nprovider1='dummy'\nkey='abcd'\n")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(result.output, "Error: missing 'provider' for 'x'\n")
        self.assertNotEqual(result.exit_code, 0)

    def test_missing_key(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(ComputeProvider)
        def command(_driver: BaseDriver) -> None:
            pass

        self.config.write(b"[role.x]\nprovider='dummy'\n")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(result.output, "Error: missing 'key' for 'x'\n")
        self.assertNotEqual(result.exit_code, 0)

    def test_invalid_provider(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(ComputeProvider)
        def command(driver: BaseDriver) -> None:
            print("{} - {}".format(driver.name, driver.creds))

        self.config.write(b"[role.x]\nprovider='nope'\nkey='abcd'\n")
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
        @cloud.pass_driver(ComputeProvider)
        def command(driver: BaseDriver) -> None:
            print("{}".format(driver.name))

        self.config.write(
            b"""
            [role.x]
            provider='abiquo'
            key='a'
            secret='b'
            endpoint='c'
            """
        )
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(
            str(result.exception),
            "Non https connections are not allowed (use secure=True)"
        )
        self.assertEqual(type(result.exception), ValueError)
        self.assertNotEqual(result.exit_code, 0)

    def test_secure(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(DNSProvider)
        def command(driver: BaseDriver) -> None:
            print("{}".format(driver.name))

        self.config.write(b"[role.x]\nprovider='powerdns'\nkey='abc'\n")
        self.config.flush()

        with patch("libcloud.dns.base.DNSDriver.__init__") as mock:
            args = [
                "--config-file",
                self.config.name,
                command.name,
                "--role",
                "x",
            ]
            result = self.runner.invoke(cli.cli, args)
            self.assertEqual(result.output, "PowerDNS\n")

            mock.assert_called_with(
                key="abc",
                secure=True,
                host=None,
                port=None,
            )

    def test_overridden_secure(self) -> None:
        @cli.cli.command()
        @cloud.pass_driver(DNSProvider)
        def command(driver: BaseDriver) -> None:
            print("{}".format(driver.name))

        self.config.write(
            b"""
            [role.x]
            provider='powerdns'
            key='abc'
            secure='nope'
            """
        )
        self.config.flush()

        with patch("libcloud.dns.base.DNSDriver.__init__") as mock:
            args = [
                "--config-file",
                self.config.name,
                command.name,
                "--role",
                "x",
            ]
            result = self.runner.invoke(cli.cli, args)
            self.assertEqual(result.output, "PowerDNS\n")

            mock.assert_called_with(
                key="abc",
                secure=True,
                host=None,
                port=None,
            )
