from . import security  # isort:skip, pylint:disable=C0411,I0021

import base64
import inspect
from typing import Any, Callable

import click
from libcloud.common.base import BaseDriver
from libcloud.compute.base import NodeAuthPassword, NodeAuthSSHKey
from libcloud.compute.providers import Provider
from munch import DefaultMunch, Munch

from . import option, table, utils

assert security  # to make pyflakes happy


@click.group()
def compute() -> None:
    pass


@compute.command("list-images")
@option.pass_driver(Provider)
def list_images(driver: BaseDriver) -> None:
    """
    List images.
    """
    table.show([
        ["ID", "id"],
        ["Name", "name"],
    ], driver.list_images())


@compute.command("list-key-pairs")
@option.pass_driver(Provider)
def list_key_pairs(driver: BaseDriver) -> None:
    """
    List public keys.
    """
    table.show([
        ["ID", "id", "extra.id"],
        ["Name", "name"],
        ["Public key", "fingerprint", "pub_key"],
    ], driver.list_key_pairs())


@compute.command("list-locations")
@option.pass_driver(Provider)
def list_locations(driver: BaseDriver) -> None:
    """
    List locations.
    """
    table.show([
        ["ID", "id"],
        ["Name", "name"],
        ["Country", "country"],
    ], driver.list_locations())


@compute.command("list-nodes")
@option.pass_driver(Provider)
def list_nodes(driver: BaseDriver) -> None:
    """
    List nodes.
    """
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
    """
    List sizes.
    """
    table.show([
        ["ID", "id"],
        ["Name", "name"],
        ["VCPU(s)", "extra.vcpus"],
        ["RAM", "ram"],
        ["Disk", "disk"],
        ["Bandwidth", "bandwidth"],
        ["Price", "extra.price_monthly", "price"],
    ], driver.list_sizes())


@compute.command("import-key-pair")
@option.add("--name", required=True)
@option.add("--ssh-key", required=True, type=click.File("r"))
@option.pass_driver(Provider)
def import_key_pair(driver: BaseDriver, **kwargs: Any) -> None:
    """
    Import a public key.

    This functionality is implemented inconsistently in `libcloud`.  The
    base `NodeDriver` has three methods for creating and importing key
    pairs:

    1. `create_key_pair()` - abstract method that takes a single
        argument, `name`.

    2. `import_key_pair_from_string` - abstract method that takes two
        arguments, `name` and `key_material`.

    3. `import_key_pair_from_file` - takes two arguments, `name` and
       `key_file_path`.  The base implementation calls
       `import_key_pair_from_string`.

    `import_key_pair_from_*()` is used to import the public part of a
    key pair, whereas `create_key_pair()` is used to create the key pair
    server-side and have it returned by the API.

    However, some drivers (DigitalOcean, Packet and Vultr) don't
    implement `import_key_pair_from_*()`.  Instead they use
    `create_key_pair()` to import the public key.

    Gah!
    """
    method = driver.import_key_pair_from_string

    create_key_pair = inspect.signature(driver.create_key_pair).parameters
    if "public_key" in create_key_pair:
        method = driver.create_key_pair

    *_, data = utils.read_public_key(kwargs["ssh_key"])
    if not method(kwargs["name"], data):
        raise click.ClickException("Import failed")

    table.show([
        ["ID", "id", "extra.id"],
        ["Name", "name"],
        ["Public key", "fingerprint", "pub_key"],
    ], driver.list_key_pairs())


@compute.command("delete-key-pair")
@option.add("--id", required=True)
@option.pass_driver(Provider)
def delete_key_pair(driver: BaseDriver, **kwargs: Any) -> None:
    """
    Delete a public key.

    The base `NodeDriver` takes a single argument of the type `KeyPair`.

    Internally, different drivers use different attributes from the
    `KeyPair` to delete a key.  Some use `id` and some use `name`.

    Furthermore, not every driver return a list of `KeyPair` from
    `list_key_pairs()`, and not every driver that returns a `KeyPair`
    use the `id` attribute -- e.g. DigitalOcean sets the ID in an
    `extra` dictionary.  ZZZ.
    """

    def predicate(kp: object) -> bool:
        id_ = getattr(kp, "id", None) or getattr(kp, "extra", {}).get("id", "")
        return str(id_) == kwargs.get("id")

    kp = _get(driver.list_key_pairs, predicate)
    try:
        if not driver.delete_key_pair(kp):
            raise click.ClickException("Delete failed")
    except AttributeError as e:
        raise click.ClickException("Bug: {}: {}".format(driver.name, e))

    table.show([
        ["ID", "id", "extra.id"],
        ["Name", "name"],
        ["Public key", "fingerprint", "pub_key"],
    ], driver.list_key_pairs())


@compute.command("destroy-node")
@option.add("--id", required=True)
@option.pass_driver(Provider)
def destroy_node(driver: BaseDriver, **kwargs: Any) -> None:
    """
    Destroy a node.
    """
    node = _get(driver.list_nodes, lambda n: n.id == kwargs["id"])
    if not driver.destroy_node(node):
        raise click.ClickException("could not destroy node")
    click.echo("Node {name} ({id}) destroyed".format(**node.__dict__))


@compute.command("create-node")
@option.add("--name", required=True)
@option.add("--size", required=True)
@option.add("--image", required=True)
@option.add("--location", required=True)
@option.add("--ssh-key", type=click.File("r"))
@option.add("--password", is_flag=True)
@option.add("--user-data", type=click.File("r"))
@option.add("--script-id", type=int)
@option.add("--wait", default=600)
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
            kw.auth = NodeAuthSSHKey(utils.read_public_key(ssh_key)[3])

    if "password" in features and not kw.auth:
        password = kwargs.pop("password")
        if password:
            value = click.prompt(
                text="Password",
                hide_input=True,
                confirmation_prompt=True,
            )
            kw.auth = NodeAuthPassword(value)  # pylint: disable=R0204

    # Process arguments specific to individual drivers.
    func = globals().get("_create_node_{}".format(driver.type), None)
    if func:
        kw.update(func(driver, kwargs))

    # Arguments local to this function.
    wait = kwargs.pop("wait")

    # Bail there are any unprocessed arguments.
    args = ["--{}".format(k.replace("_", "-")) for k, v in kwargs.items() if v]
    if args:
        raise click.UsageError(
            "{} does not support {}".format(driver.name, ", ".join(args))
        )

    # And finally, create the node.
    node = driver.create_node(**kw)

    click.echo("Waiting for the node to come online...")
    table.show([
        ["ID", "id"],
        ["Name", "name"],
        ["State", "state"],
        ["Public IP(s)", "public_ips"],
        ["Private IP(s)", "private_ips"],
        ["Password", "extra.password"],
    ], [n for n, _ in driver.wait_until_running([node], timeout=wait)])


def _get(func: Callable, pred: Callable, no_error: bool = False) -> Any:
    """
    Retrieve the first instance from `func` that matches `pred`.
    """
    value = next((elm for elm in func() if pred(elm)), None)
    if value or no_error:
        return value
    name = func.__name__.replace("list_", "").replace("_", "-").rstrip("s")
    raise click.ClickException("invalid {}".format(name))


def _create_node_digitalocean(driver: BaseDriver, kwargs: Any) -> Munch:
    """
    Process arguments for DigitalOcean.
    """
    kw = Munch(ex_create_attr=Munch())

    # A list of either integer IDs or string fingerprints is accepted by
    # DigitalOcean.  However, to be consistent with the `ssh_key`
    # feature, only a single key is processed here.
    ssh_key = kwargs.pop("ssh_key", None)
    if ssh_key:
        kind, key, _comment, _data = utils.read_public_key(ssh_key)
        kp = _get(
            driver.list_key_pairs,
            lambda k: k.public_key.split(" ")[:2] == [kind, key]
        )
        kw.ex_create_attr.ssh_keys = [kp.fingerprint]

    # A string with cloud-config data less than 64 KiB is accepted.
    user_data = kwargs.pop("user_data", None)
    if user_data:
        kw.ex_user_data = user_data.read()
        if len(kw.ex_user_data) > 64 * 1024:
            raise click.ClickException(
                "{} is larger than 64 KiB".format(user_data.name)
            )

    return kw


def _create_node_vultr(driver: BaseDriver, kwargs: Any) -> Munch:
    """
    Process arguments for Vultr.
    """
    kw = Munch(ex_create_attr=Munch())

    # A list of string IDs is accepted.  However, to be consistent with the
    # `ssh_key` feature, only a single key is processed here.
    ssh_key = kwargs.pop("ssh_key", None)
    if ssh_key:
        kind, key, _comment, _data = utils.read_public_key(ssh_key)
        kp = _get(
            driver.list_key_pairs,
            lambda k: k.pub_key.split(" ")[:2] == [kind, key]
        )
        kw.ex_ssh_key_ids = [kp.id]

    # A string with base64-encoded cloud-init data is accepted.
    user_data = kwargs.pop("user_data", None)
    if user_data:
        content = user_data.read().encode()
        kw.ex_create_attr.userdata = base64.b64encode(content).decode()

    # An integer ID for a startup script is accepted.
    script_id = kwargs.pop("script_id", None)
    if script_id:
        kw.ex_create_attr.script_id = script_id

    return kw
