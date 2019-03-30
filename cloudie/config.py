import os
from typing import MutableMapping, Type

import toml


class ConfigError(Exception):
    pass


def load(path: str, dict_class: Type[MutableMapping] = dict) -> MutableMapping:
    """
    Parse a TOML file and return it as `dict_class`.
    """
    try:
        with open(os.path.expanduser(path), "r") as f:
            return toml.load(f, dict_class)
    except OSError as e:
        raise ConfigError("{}: {}".format(path, e.strerror))
    except toml.TomlDecodeError as e:
        raise ConfigError("{}: {}".format(path, e))
