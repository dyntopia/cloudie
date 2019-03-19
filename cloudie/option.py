import inspect
from typing import Any, Callable, Optional, Union

import click
import libcloud


class Option(click.Option):
    def get_default(self, ctx: click.Context) -> Any:
        """
        Retrieve the default value.

        The value is retrieved from the configuration for the current
        role.  If this fails, `default` is used.
        """
        rv = self._get_config_default(ctx) or self.default
        if callable(rv):
            rv = rv()

        # Strings don't seem to be converted by `type_cast_value()`.
        if rv and self.type == click.STRING:
            return str(rv)
        return self.type_cast_value(ctx, rv)

    def _get_config_default(self, ctx: click.Context) -> Any:
        try:
            return ctx.obj.role[self.name.replace("_", "-")]
        except (AttributeError, KeyError):
            return None


def add(*param_decls: str, **attrs: Any) -> Callable:
    """
    Add a click option with a custom `Option` class.
    """
    return click.option(*param_decls, **attrs, cls=Option)  # type: ignore


def pass_driver(driver_type: object) -> Callable:
    """
    Add `--role` as a required option and instantiate its driver.
    """

    def callback(
            ctx: click.Context,
            _param: Union[click.Option, click.Parameter],
            role: Optional[str],
    ) -> Any:
        role = role or ctx.obj.config.get("role", {}).get("default")
        if not role:
            raise click.ClickException("missing --role and role.default")

        try:
            ctx.obj.role = ctx.obj.config.role[role]
            provider = ctx.obj.role.provider
            key = ctx.obj.role.key
            other = {
                k: v
                for k, v in ctx.obj.role.items()
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

    return add("--role", "driver", is_eager=True, callback=callback)
