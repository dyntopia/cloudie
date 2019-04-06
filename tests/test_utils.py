import io
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


class TestSha256(TestCase):
    def test_success(self) -> None:
        f = io.StringIO("")
        pos = f.tell()
        self.assertEqual(
            utils.sha256(f),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )
        self.assertEqual(f.tell(), pos)

        f.write("abc\nxyz")
        pos = f.tell()
        self.assertEqual(
            utils.sha256(f),
            "042f01ade2c5988edbe230efc3f48fdcdbbe493931de8cae8bd02156802b77cd"
        )
        self.assertEqual(pos, f.tell())
