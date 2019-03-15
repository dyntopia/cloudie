from typing import Any

import click


class Group(click.Group):
    """
    Helper for `click.Group` that handles unimplemented functionality.

    API calls that are unsupported by the current `libcloud` provider
    throws `NotImplementedError`.  These exceptions are re-raised as an
    exception that click handles so that individual commands don't have
    to deal with them.
    """

    def invoke(self, ctx: click.Context) -> Any:
        try:
            return super().invoke(ctx)
        except NotImplementedError as e:
            raise click.ClickException(str(e))
