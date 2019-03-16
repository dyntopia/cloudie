import configparser
import os

import click
import munch

from . import compute, group, security

assert security  # to make pyflakes happy


@click.group(cls=group.Group)
@click.option("--config-file", default="~/.cloudie.ini", type=str)
@click.pass_context
def cli(ctx: click.Context, config_file: str) -> None:
    config = configparser.ConfigParser()
    try:
        config.read(os.path.expanduser(config_file))
    except configparser.Error as e:
        raise click.ClickException(str(e).replace("\n", " "))

    ctx.obj = munch.Munch()
    ctx.obj.config = config


cli.add_command(compute.compute)
