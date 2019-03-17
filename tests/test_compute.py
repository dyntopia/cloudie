from unittest.mock import patch

from cloudie import cli

from .helpers import ClickTestCase, TexttableMock


class TestCompute(ClickTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.config.write(b"[xyz]\nprovider=dummy\nkey=abcd")
        self.config.flush()

    def test_list_images(self) -> None:
        args = [
            "--config-file",
            self.config.name,
            "compute",
            "list-images",
            "--role",
            "xyz",
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
