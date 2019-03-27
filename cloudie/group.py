from typing import Any

import click
from libcloud.common.exceptions import BaseHTTPError
from libcloud.common.types import LibcloudError
from requests.exceptions import RequestException


class Group(click.Group):
    """
    Helper for `click.Group` that handles libcloud errors.

    Exceptions from API calls in `libcloud` are re-raised as exceptions
    that click handles so that individual commands don't have to deal
    with them.
    """

    def invoke(self, ctx: click.Context) -> Any:
        try:
            return super().invoke(ctx)
        except LibcloudError as e:
            raise click.ClickException(e.value)
        except (BaseHTTPError, NotImplementedError) as e:
            raise click.ClickException(str(e))
        except RequestException:
            raise click.ClickException("connection failure")
