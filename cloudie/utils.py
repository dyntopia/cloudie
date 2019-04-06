import base64
import hashlib
from typing import IO, Tuple

import click


def read_public_key(f: IO[str]) -> Tuple[str, str, str, str]:
    """
    Read a public SSH key.

    This function does some basic verification to see if the content
    looks like a public key.
    """
    data = f.read()
    try:
        kind, key, comment = data.split(" ")
        if kind.startswith("ssh-") and comment:
            base64.b64decode(key)
            return (kind, key, comment, data)
    except ValueError:
        pass

    raise click.ClickException("{} is not a valid SSH key".format(f.name))


def sha256(f: IO[str]) -> str:
    """
    Calculate the sha256 message digest for a file.
    """
    pos = f.tell()
    f.seek(0)
    digest = hashlib.sha256(f.read().encode()).hexdigest()
    f.seek(pos)

    return digest
