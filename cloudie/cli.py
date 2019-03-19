import os

import click
import munch
import toml

from . import compute, group, security

assert security  # to make pyflakes happy


@click.group(cls=group.Group)
@click.option("--config-file", default="~/.cloudie.toml", type=str)
@click.pass_context
def cli(ctx: click.Context, config_file: str) -> None:
    try:
        config = toml.load(os.path.expanduser(config_file), munch.Munch)
    except toml.TomlDecodeError as e:
        raise click.ClickException("{}: {}".format(config_file, e))

    ctx.obj = munch.Munch(config=config)


cli.add_command(compute.compute)
