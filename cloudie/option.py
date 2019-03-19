from typing import Any, Callable

import click


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
