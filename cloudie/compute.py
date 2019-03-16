import click
from libcloud.common.base import BaseDriver
from libcloud.compute.providers import Provider

from . import cloud


@click.group()
def compute() -> None:
    pass


@compute.command("list-images")
@cloud.pass_driver(Provider)
def list_images(driver: BaseDriver) -> None:
    for image in driver.list_images():
        print("{} - {}".format(image.id, image.name))
