import configparser
from typing import Any, Callable, Union

import click
import libcloud


def pass_driver(driver_type: object) -> Callable:
    def instantiate(
            ctx: click.Context,
            _param: Union[click.Option, click.Parameter],
            role: str,
    ) -> Any:
        """
        Instantiate the driver associated with `--role`.
        """
        try:
            provider = ctx.obj.config.get(role, "provider")
            key = ctx.obj.config.get(role, "key")
        except configparser.NoSectionError:
            raise click.ClickException("missing role '{}'".format(role))
        except configparser.NoOptionError:
            raise click.ClickException(
                "'{}' must specify 'provider' and 'key'".format(role)
            )

        try:
            return libcloud.get_driver(driver_type, provider)(key)
        except AttributeError as e:
            raise click.ClickException("{}".format(e))

    def decorator(f: Callable) -> Callable:
        """
        Add `--role` as a required option.
        """
        return click.option(
            "--role",
            "driver",
            type=str,
            callback=instantiate,
            required=True,
        )(f)

    return decorator
