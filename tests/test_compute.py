from unittest.mock import patch

from libcloud.compute.providers import get_driver, set_driver

from cloudie import cli

from .helpers import ClickTestCase, TexttableMock


class TestCompute(ClickTestCase):
    def setUp(self) -> None:
        super().setUp()

        try:
            get_driver("dummy-extended")
        except AttributeError:
            set_driver(
                "dummy-extended",
                "tests.helpers",
                "ExtendedDummyNodeDriver",
            )

        self.config.write(b"[dummy]\nprovider=dummy\nkey=abcd\n")
        self.config.write(b"[dummy-ext]\nprovider=dummy-extended\nkey=abcd\n")
        self.config.flush()

    def test_list_images(self) -> None:
        args = [
            "--config-file",
            self.config.name,
            "compute",
            "list-images",
            "--role",
            "dummy",
        ]
        result = self.runner.invoke(cli.cli, args)

        images = [
            ["1", "Ubuntu 9.10"],
            ["2", "Ubuntu 9.04"],
            ["3", "Slackware 4"],
        ]

        t = TexttableMock()
        with patch("texttable.Texttable") as mock:
            mock.return_value = t
            result = self.runner.invoke(cli.cli, args)
            self.assertEqual(result.exit_code, 0)

        self.assertEqual(t.headers, ["ID", "Name"])
        self.assertEqual(t.rows, images)
