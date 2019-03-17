import click
from libcloud.common.base import BaseDriver
from libcloud.compute.providers import Provider

from . import cloud, table


@click.group()
def compute() -> None:
    pass


@compute.command("list-images")
@cloud.pass_driver(Provider)
def list_images(driver: BaseDriver) -> None:
    table.show([
        ["ID", "id"],
        ["Name", "name"],
    ], driver.list_images())


@compute.command("list-key-pairs")
@cloud.pass_driver(Provider)
def list_key_pairs(driver: BaseDriver) -> None:
    table.show([
        ["ID", "id", "extra.id"],
        ["Name", "name"],
        ["Public key", "fingerprint", "pub_key"],
    ], driver.list_key_pairs())


@compute.command("list-nodes")
@cloud.pass_driver(Provider)
def list_nodes(driver: BaseDriver) -> None:
    table.show([
        ["ID", "id"],
        ["Name", "name"],
        ["State", "state"],
        ["Public IP(s)", "public_ips"],
        ["Private IP(s)", "private_ips"],
    ], driver.list_nodes())
