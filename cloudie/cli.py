import click
import munch

from . import compute, config, group, security

assert security  # to make pyflakes happy


@click.group(cls=group.Group)
@click.option("--config-file", default="~/.cloudie.toml", type=str)
@click.pass_context
def cli(ctx: click.Context, config_file: str) -> None:
    ctx.obj = munch.Munch()

    try:
        ctx.obj.config = config.load(config_file, munch.Munch)
    except config.ConfigError as e:
        raise click.ClickException(str(e))


cli.add_command(compute.compute)
