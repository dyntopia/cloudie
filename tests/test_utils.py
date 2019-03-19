import tempfile
from unittest import TestCase

import click

from cloudie import utils


class TestReadPublicKey(TestCase):
    def setUp(self) -> None:
        self.key = tempfile.NamedTemporaryFile("w+")

    def tearDown(self) -> None:
        self.key.close()

    def test_empty_file(self) -> None:
        with self.assertRaises(click.ClickException):
            utils.read_public_key(self.key)

    def test_missing_field(self) -> None:
        self.key.write("ssh-rsa data")
        self.key.flush()
        self.key.seek(0)

        with self.assertRaises(click.ClickException):
            utils.read_public_key(self.key)

    def test_empty_comment(self) -> None:
        self.key.write("ssh-rsa data ")
        self.key.flush()
        self.key.seek(0)

        with self.assertRaises(click.ClickException):
            utils.read_public_key(self.key)

    def test_invalid_kind(self) -> None:
        self.key.write("xyz data comment")
        self.key.flush()
        self.key.seek(0)

        with self.assertRaises(click.ClickException):
            utils.read_public_key(self.key)

    def test_invalid_data(self) -> None:
        self.key.write("ssh-rsa x comment")
        self.key.flush()
        self.key.seek(0)

        with self.assertRaises(click.ClickException):
            utils.read_public_key(self.key)

    def test_success(self) -> None:
        self.key.write("ssh-rsa data comment")
        self.key.flush()
        self.key.seek(0)

        kind, key, comment, data = utils.read_public_key(self.key)
        self.assertEqual(kind, "ssh-rsa")
        self.assertEqual(key, "data")
        self.assertEqual(comment, "comment")
        self.assertEqual(data, "ssh-rsa data comment")
