from . import security  # isort:skip, pylint:disable=C0411,I0021

from typing import Any, Callable

import click
from libcloud.common.base import BaseDriver
from libcloud.compute.base import NodeAuthPassword, NodeAuthSSHKey
from libcloud.compute.providers import Provider
from munch import DefaultMunch

from . import option, table

assert security  # to make pyflakes happy


@click.group()
def compute() -> None:
    pass


@compute.command("list-images")
@option.pass_driver(Provider)
def list_images(driver: BaseDriver) -> None:
    table.show([
        ["ID", "id"],
        ["Name", "name"],
    ], driver.list_images())


@compute.command("list-key-pairs")
@option.pass_driver(Provider)
def list_key_pairs(driver: BaseDriver) -> None:
    table.show([
        ["ID", "id", "extra.id"],
        ["Name", "name"],
        ["Public key", "fingerprint", "pub_key"],
    ], driver.list_key_pairs())


@compute.command("list-locations")
@option.pass_driver(Provider)
def list_locations(driver: BaseDriver) -> None:
    table.show([
        ["ID", "id"],
        ["Name", "name"],
        ["Country", "country"],
    ], driver.list_locations())


@compute.command("list-nodes")
@option.pass_driver(Provider)
def list_nodes(driver: BaseDriver) -> None:
    table.show([
        ["ID", "id"],
        ["Name", "name"],
        ["State", "state"],
        ["Public IP(s)", "public_ips"],
        ["Private IP(s)", "private_ips"],
    ], driver.list_nodes())


@compute.command("list-sizes")
@option.pass_driver(Provider)
def list_sizes(driver: BaseDriver) -> None:
    table.show([
        ["ID", "id"],
        ["Name", "name"],
        ["VCPU(s)", "extra.vcpus"],
        ["RAM", "ram"],
        ["Disk", "disk"],
        ["Bandwidth", "bandwidth"],
        ["Price", "extra.price_monthly", "price"],
    ], driver.list_sizes())


@compute.command("create-node")
@option.add("--name", required=True)
@option.add("--size", required=True)
@option.add("--image", required=True)
@option.add("--location", required=True)
@option.add("--ssh-key")
@option.add("--password", is_flag=True)
@option.pass_driver(Provider)
def create_node(driver: BaseDriver, **kwargs: Any) -> None:
    """
    Create a new node.

    This command is quite hard to generalize because different drivers
    implement `create_node()` in different ways.

    Some drivers specify their required and optional arguments in the
    method signature.  Others simply take `**kwargs` and process it in
    the method body.

    Furthermore, different drivers handle extra arguments differently.
    Some accept `ex_<name>` as keyword arguments; some take a separate
    dictionary with any extra arguments; and some simply process them as
    part of `**kwargs.`

    The documentation for the base `NodeDriver` state that individual
    drivers should use the `features` attribute to declare what
    variations of the API they support.  However, `features` is not
    all-encompassing.  It only seems to allow specifying support for
    `ssh_key`, `password` and/or `generates_password`.
    """
    kw = DefaultMunch()

    # Bail on conflicting arguments
    if kwargs.get("ssh_key") and kwargs.get("password"):
        raise click.ClickException("Use either --ssh-key or --password")

    # Process arguments common for all compute drivers.
    kw.name = kwargs.pop("name")

    image = kwargs.pop("image")
    kw.image = _get(driver.list_images, lambda i: i.id == image)

    location = kwargs.pop("location")
    kw.location = _get(driver.list_locations, lambda l: l.id == location)

    size = kwargs.pop("size")
    kw.size = _get(driver.list_sizes, lambda s: s.id == size)

    # Process arguments declared in `features`.  There are two arguments
    # that need processing: `ssh_key` and `password`.  These are
    # supposed to be used to instantiate an appropriate object and
    # passed as the `auth` parameter.
    #
    # Unfortunately, the `ssh_key` feature is horribly inconsistent:
    #
    # - Some drivers declare support for `ssh_key` in `features` and
    #   accept an instance of `NodeAuthSSHKey` as the `auth` parameter.
    #
    # - Some drivers declare support for `ssh_key` in `features` and
    #   accept an instance of `NodeAuthSSHKey` as the `auth` parameter
    #   while *also* accepting another parameter with the key to use.
    #   See e.g. EC2, where an exception is raised if both are provided.
    #
    # - Some drivers don't declare support for `ssh_key` in `features`
    #   but still accept SSH keys as an extra argument (some as a string
    #   with the fingerprint, some as a name of the key, some as a list
    #   of integer IDs and some as a list of string IDs).
    #
    # GAH!
    features = getattr(driver, "features", {}).get("create_node", [])

    if "ssh_key" in features:
        ssh_key = kwargs.pop("ssh_key")
        if ssh_key:
            try:
                with open(ssh_key, "r") as f:
                    kw.auth = NodeAuthSSHKey(f.read())
            except OSError as e:
                raise click.ClickException(
                    "{}: {}".format(e.filename, e.strerror)
                )

    if "password" in features and not kw.auth:
        password = kwargs.pop("password")
        if password:
            value = click.prompt(
                text="Password",
                hide_input=True,
                confirmation_prompt=True,
            )
            kw.auth = NodeAuthPassword(value)  # pylint: disable=R0204

    # Bail there are any unprocessed arguments.
    args = ["--{}".format(k.replace("_", "-")) for k, v in kwargs.items() if v]
    if args:
        raise click.UsageError(
            "{} does not support {}".format(driver.name, ", ".join(args))
        )

    # And finally, create the node.
    table.show([
        ["UUID", "uuid"],
        ["Name", "name"],
        ["State", "state"],
        ["Public IP(s)", "public_ips"],
        ["Private IP(s)", "private_ips"],
        ["Password", "extra.password"],
    ], [driver.create_node(**kw)])


def _get(func: Callable, pred: Callable) -> Any:
    """
    Retrieve the first instance from `func` that matches `pred`.
    """
    value = next((elm for elm in func() if pred(elm)), None)
    if not value:
        name = func.__name__.replace("list_", "").replace("_", "-").rstrip("s")
        raise click.ClickException("invalid {}".format(name))
    return value
