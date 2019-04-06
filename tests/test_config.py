import os
import pathlib
import subprocess
import tempfile
from unittest import TestCase
from unittest.mock import patch

from cloudie import config, utils


class TestConfigPermission(TestCase):
    # pylint: disable=protected-access

    def setUp(self) -> None:
        self.config = tempfile.NamedTemporaryFile("w+")
        self.cache = tempfile.TemporaryDirectory()

        with patch("pathlib.Path.home") as mock:
            mock.return_value = pathlib.Path(self.cache.name)
            self.permission = config.ConfigPermission(self.config)

    def tearDown(self) -> None:
        self.config.close()
        self.cache.cleanup()

    def test_missing_digest_cache(self) -> None:
        self.config.write("abcd")
        self.config.flush()

        with patch("builtins.input") as mock:
            self.permission.ask()
            self.assertEqual(mock.call_count, 1)

    def test_invalid_digest_cache(self) -> None:
        self.config.write("abcd")
        self.config.flush()

        name = os.path.basename(self.config.name)
        self.permission._cache.joinpath(name).write_text(
            "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4"
        )

        with patch("builtins.input") as mock:
            self.permission.ask()
            self.assertEqual(mock.call_count, 1)

    def test_valid_digest_cache(self) -> None:
        self.config.write("abcd")
        self.config.flush()

        name = os.path.basename(self.config.name)
        self.permission._cache.joinpath(name).write_text(
            "88d4266fd4e6338d13b845fcf289579d209c897823b9217da3e161936f031589"
        )

        self.assertTrue(self.permission.ask())

    def test_answer_no(self) -> None:
        for answer in ["", "n", "N", "xyz", "nO", "No", "NO", "not-yes"]:
            self.config.write("x")
            self.config.flush()

            with patch("builtins.input") as mock:
                mock.return_value = answer

                self.assertFalse(self.permission.ask())
                self.assertEqual(mock.call_count, 1)

    def test_answer_yes(self) -> None:
        for answer in ["y", "Y"]:
            self.config.write("x")
            self.config.flush()

            with patch("builtins.input") as mock:
                mock.return_value = answer

                self.assertTrue(self.permission.ask())
                self.assertEqual(mock.call_count, 1)

                name = os.path.basename(self.config.name)
                self.assertEqual(
                    utils.sha256(self.config),
                    self.permission._cache.joinpath(name).read_text()
                )

    def test_mkdir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch("pathlib.Path.home") as mock:
                home = os.path.join(tmp, "x", "y", "z")
                mock.return_value = pathlib.Path(home)
                self.permission = config.ConfigPermission(self.config)
                self.assertTrue(os.path.isdir(home))

    # pylint: enable=protected-access


class TestConfigDecoder(TestCase):
    def setUp(self) -> None:
        self.config = tempfile.NamedTemporaryFile("w")
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.config.close()
        self.tmpdir.cleanup()

    def test_permission_denied(self) -> None:
        self.config.write("[section]\n a = '$(...)'")
        self.config.flush()

        with self.assertRaises(config.ConfigPermissionError):
            with patch("builtins.input") as mock:
                mock.return_value = "noooooo"
                config.load(self.config.name)

    def test_permission_granted(self) -> None:
        self.config.write(
            """
            [section]
            s1 = "normal string"
            s2 = "$normal string"
            s3 = "$(normal string"
            s4 = "$normal string)"
            s5 = "$(echo replacement)"
            """
        )
        self.config.flush()

        with patch("pathlib.Path.home") as home_mock:
            home_mock.return_value = pathlib.Path(self.tmpdir.name)

            with patch("builtins.input") as input_mock:
                input_mock.return_value = "y"
                got = config.load(self.config.name)
                want = {
                    "section": {
                        "s1": "normal string",
                        "s2": "$normal string",
                        "s3": "$(normal string",
                        "s4": "$normal string)",
                        "s5": "replacement"
                    }
                }
                self.assertEqual(got, want)

    def test_execution_failure(self) -> None:
        self.config.write("[section]\n a = '$(...)'")
        self.config.flush()

        with patch("pathlib.Path.home") as home_mock:
            home_mock.return_value = pathlib.Path(self.tmpdir.name)

            with patch("subprocess.check_output") as co_mock_a:
                with self.assertRaises(config.ConfigCommandError):
                    exc = subprocess.CalledProcessError(1, "")
                    co_mock_a.side_effect = exc
                    with patch("builtins.input") as input_mock:
                        input_mock.return_value = "y"
                        config.load(self.config.name)

            with patch("subprocess.check_output") as co_mock_b:
                with self.assertRaises(config.ConfigCommandError):
                    co_mock_b.side_effect = FileNotFoundError
                    with patch("builtins.input") as input_mock:
                        input_mock.return_value = "y"
                        config.load(self.config.name)


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
