import inspect
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
            config = ctx.obj.config.role[role]
            provider = config.provider
            key = config.key
            other = {
                k: v
                for k, v in config.items()
                if k not in ["provider", "key"]
            }
        except KeyError:
            raise click.ClickException("unknown role '{}'".format(role))
        except AttributeError as e:
            raise click.ClickException("missing '{}' for '{}'".format(e, role))

        try:
            driver = libcloud.get_driver(driver_type, provider)
            params = inspect.signature(driver).parameters
            kwargs = {k: v for k, v in other.items() if k in params}

            # See the comment on secure/allow_insecure in security.py.
            if "secure" in params:
                kwargs["secure"] = True

            return driver(key, **kwargs)
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
