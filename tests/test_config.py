import tempfile
from unittest import TestCase

from cloudie import config


class TestLoad(TestCase):
    def setUp(self) -> None:
        self.config = tempfile.NamedTemporaryFile("w")

    def tearDown(self) -> None:
        self.config.close()

    def test_file_not_found(self) -> None:
        self.config.close()

        with self.assertRaises(config.ConfigError) as ctx:
            config.load(self.config.name)

        self.assertTrue("No such file or directory" in str(ctx.exception))

    def test_invalid_config(self) -> None:
        self.config.write("x=y")
        self.config.flush()

        with self.assertRaises(config.ConfigError) as ctx:
            config.load(self.config.name)

        self.assertTrue("Invalid date or number" in str(ctx.exception))

    def test_success(self) -> None:
        self.config.write(
            """
            x = 'y'

            [section]
            num = 123
            """
        )
        self.config.flush()

        result = config.load(self.config.name)
        self.assertEqual(result, {"x": "y", "section": {"num": 123}})
