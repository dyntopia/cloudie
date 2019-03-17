from cloudie import cli

from .helpers import ClickTestCase


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
            ("1", "Ubuntu 9.10"),
            ("2", "Ubuntu 9.04"),
            ("3", "Slackware 4"),
        ]
        lines = result.output.strip().split("\n")[2:]

        self.assertEqual(len(images), len(lines))
        for image, line in zip(images, lines):
            self.assertTrue(image[0] in line)
            self.assertTrue(image[1] in line)
        self.assertEqual(result.exit_code, 0)
