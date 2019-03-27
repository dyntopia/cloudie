from libcloud.common.exceptions import BaseHTTPError
from libcloud.common.types import InvalidCredsError
from requests.exceptions import RequestException

from cloudie import cli

from .helpers import ClickTestCase


class TestGroup(ClickTestCase):
    def test_not_implemented(self) -> None:
        @cli.cli.command()
        def command() -> None:
            raise NotImplementedError("asdf")

        args = ["--config-file", self.config.name, command.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("asdf" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_invalid_creds(self) -> None:
        @cli.cli.command()
        def command() -> None:
            raise InvalidCredsError("asdf")

        args = ["--config-file", self.config.name, command.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("asdf" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_http_error(self) -> None:
        @cli.cli.command()
        def command() -> None:
            raise BaseHTTPError(400, "asdf")

        args = ["--config-file", self.config.name, command.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("asdf" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_request_exception(self) -> None:
        @cli.cli.command()
        def command() -> None:
            raise RequestException("asdf")

        args = ["--config-file", self.config.name, command.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("connection failure" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_implemented(self) -> None:
        @cli.cli.command()
        def command() -> None:
            print("success")

        args = ["--config-file", self.config.name, command.name]
        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("success" in result.output)
        self.assertEqual(result.exit_code, 0)
