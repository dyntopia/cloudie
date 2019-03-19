from typing import Any
from unittest.mock import patch

from libcloud.common.base import BaseDriver
from libcloud.compute.providers import Provider as ComputeProvider
from libcloud.dns.providers import Provider as DNSProvider
from munch import Munch

from cloudie import cli, option

from .helpers import ClickTestCase


class TestOption(ClickTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.config.write(
            b"""
            [role.name]
            provider = "dummy"
            key = "..."
            config-str = "aaa"
            config-override-default-int = "123"
            config-override-default-str = "ccc"
            config-override-default-callable = "no-call"
            user-override-config-and-defalut-str = "x"
            """
        )
        self.config.flush()

    def test_combination(self) -> None:
        kw = Munch()

        @cli.cli.command()
        @option.add("--config-str", required=True)
        @option.add("--config-override-default-int", type=int, default=1)
        @option.add("--config-override-default-str", default="x")
        @option.add("--config-override-default-callable", default=lambda: "x")
        @option.add("--default-str-if-nothing-else", default="def")
        @option.add("--default-callable-if-nothing-else", default=lambda: "x")
        @option.add("--user-override-config-and-defalut-str", default="y")
        @option.pass_driver(ComputeProvider)
        def command(**kwargs: Any) -> None:
            nonlocal kw
            kw.update(kwargs)

        args = [
            "--config-file",
            self.config.name,
            command.name,
            "--role",
            "name",
            "--user-override-config-and-defalut-str",
            "overridden",
        ]
        result = self.runner.invoke(cli.cli, args)

        self.assertIsInstance(kw.config_str, str)
        self.assertEqual(kw.config_str, "aaa")

        self.assertIsInstance(kw.config_override_default_int, int)
        self.assertEqual(kw.config_override_default_int, 123)

        self.assertIsInstance(kw.config_override_default_str, str)
        self.assertEqual(kw.config_override_default_str, "ccc")

        self.assertIsInstance(kw.config_override_default_callable, str)
        self.assertEqual(kw.config_override_default_callable, "no-call")

        self.assertIsInstance(kw.default_str_if_nothing_else, str)
        self.assertEqual(kw.default_str_if_nothing_else, "def")

        self.assertIsInstance(kw.default_callable_if_nothing_else, str)
        self.assertEqual(kw.default_callable_if_nothing_else, "x")

        self.assertIsInstance(kw.user_override_config_and_defalut_str, str)
        self.assertEqual(kw.user_override_config_and_defalut_str, "overridden")

        self.assertEqual(result.exit_code, 0)

    def test_missing_role(self) -> None:
        @cli.cli.command()
        @option.add("--a", required=True)
        def command(**_kwargs: Any) -> None:
            pass

        args = [
            "--config-file",
            self.config.name,
            command.name,
        ]

        result = self.runner.invoke(cli.cli, args)
        self.assertTrue("Error: Missing option \"--a\"" in result.output)
        self.assertNotEqual(result.exit_code, 0)


class TestAdd(ClickTestCase):
    @staticmethod
    def test_add() -> None:
        with patch("click.option") as mock:
            option.add("--x", a=1)

        mock.assert_called_with("--x", a=1, cls=option.Option)


class TestPassDriver(ClickTestCase):
    def test_success(self) -> None:
        @cli.cli.command()
        @option.pass_driver(ComputeProvider)
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
        @option.pass_driver(ComputeProvider)
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

    def test_unspecified_role(self) -> None:
        @cli.cli.command()
        @option.pass_driver(ComputeProvider)
        def command(_driver: BaseDriver) -> None:
            pass

        self.config.write(b"[role.xy]\nprovider='dummy'\nkey='abcd'\n")
        self.config.flush()

        args = ["--config-file", self.config.name, command.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(
            result.output,
            "Error: missing --role and role.default\n",
        )
        self.assertNotEqual(result.exit_code, 0)

    def test_default_role(self) -> None:
        @cli.cli.command()
        @option.pass_driver(ComputeProvider)
        def command(driver: BaseDriver) -> None:
            print("{} - {}".format(driver.name, driver.creds))

        self.config.write(
            b"""
            [role]\n
            default = "xy"

            [role.x]
            provider="dummy"
            key="ijkl"

            [role.xy]
            provider="dummy"
            key="abcd"
            """
        )
        self.config.flush()

        args = ["--config-file", self.config.name, command.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(result.output, "Dummy Node Provider - abcd\n")
        self.assertEqual(result.exit_code, 0)

    def test_override_default_role(self) -> None:
        @cli.cli.command()
        @option.pass_driver(ComputeProvider)
        def command(driver: BaseDriver) -> None:
            print("{} - {}".format(driver.name, driver.creds))

        self.config.write(
            b"""
            [role]\n
            default = "xy"

            [role.x]
            provider="dummy"
            key="ijkl"

            [role.xy]
            provider="dummy"
            key="abcd"
            """
        )
        self.config.flush()

        args = ["--config-file", self.config.name, command.name, "--role", "x"]
        result = self.runner.invoke(cli.cli, args)

        self.assertEqual(result.output, "Dummy Node Provider - ijkl\n")
        self.assertEqual(result.exit_code, 0)

    def test_missing_role(self) -> None:
        @cli.cli.command()
        @option.pass_driver(ComputeProvider)
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
        @option.pass_driver(ComputeProvider)
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
        @option.pass_driver(ComputeProvider)
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
        @option.pass_driver(ComputeProvider)
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
        @option.pass_driver(ComputeProvider)
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
        @option.pass_driver(DNSProvider)
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
        @option.pass_driver(DNSProvider)
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
