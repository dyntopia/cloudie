from typing import Any
from unittest.mock import patch

from libcloud.compute.providers import Provider as ComputeProvider
from munch import Munch

from cloudie import cli, cloud, option

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
        @cloud.pass_driver(ComputeProvider)
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
