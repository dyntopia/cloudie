import os
import pathlib
import subprocess
from typing import IO, Any, MutableMapping, Tuple, Type

import toml

from . import __project__, utils


class ConfigError(Exception):
    pass


class ConfigPermissionError(ConfigError):
    pass


class ConfigCommandError(ConfigError):
    pass


class ConfigPermission:
    def __init__(self, f: IO[str]) -> None:
        self._f = f
        self._cache = pathlib.Path.home().joinpath(".cache", __project__)
        self._cache.mkdir(parents=True, exist_ok=True)

    def ask(self) -> bool:
        """
        Return true if permission is granted, false otherwise.
        """
        digest = utils.sha256(self._f)
        cache = self._cache.joinpath(os.path.basename(self._f.name))

        try:
            if cache.read_text() == digest:
                return True
        except OSError:
            pass

        msg = "Allow '{}' to execute commands [y/N]: "
        answer = input(msg.format(self._f.name))
        if answer in ("y", "Y"):
            cache.write_text(digest)
            return True

        return False


class ConfigDecoder(toml.TomlDecoder):  # type: ignore
    """
    TOML decoder.

    This extends the default decoder with a new string sub-type that
    executes values surrounded with $() as commands.  The output from
    the command is used as the actual value for that option.

    Users must permit command substitutions.  If approved, the SHA256
    message digest of the config file is cached in order to avoid
    prompting the next time for that particular configuration.

    Re-approval is required after every change to a configuration file
    that contain commands.
    """

    def __init__(
            self,
            permission: ConfigPermission,
            dict_class: Type[MutableMapping],
    ) -> None:
        super().__init__(dict_class)
        self._permission = permission

    def load_value(self, v: Any, strictly_valid: bool = True) -> Tuple:
        value, vtype = super().load_value(v, strictly_valid)
        if vtype == "str":
            if value.startswith("$(") and value.endswith(")"):
                if not self._permission.ask():
                    msg = "need permission to execute command"
                    raise ConfigPermissionError(msg)

                try:
                    args = value[2:-1].split()
                    value = subprocess.check_output(args).decode().strip()
                except (OSError, subprocess.SubprocessError):
                    raise ConfigCommandError("{} failed".format(value))
        return value, vtype


def load(path: str, dict_class: Type[MutableMapping] = dict) -> MutableMapping:
    """
    Parse a TOML file and return it as `dict_class`.
    """
    try:
        with open(os.path.expanduser(path), "r") as f:
            decoder = ConfigDecoder(ConfigPermission(f), dict_class)
            return toml.load(f, decoder=decoder)  # type: ignore
    except OSError as e:
        raise ConfigError("{}: {}".format(path, e.strerror))
    except toml.TomlDecodeError as e:
        raise ConfigError("{}: {}".format(path, e))
