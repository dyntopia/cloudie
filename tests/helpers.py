import tempfile
import unittest
from typing import Any, Dict, List

import click.testing
from libcloud import get_driver
from libcloud.compute.base import (
    KeyPair, Node, NodeImage, NodeLocation, NodeSize
)
from libcloud.compute.drivers.dummy import DummyNodeDriver
from libcloud.compute.drivers.vultr import SSHKey
from libcloud.compute.providers import Provider as ComputeProvider
from texttable import Texttable


class ClickTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.config = tempfile.NamedTemporaryFile()
        self.runner = click.testing.CliRunner()

    def tearDown(self) -> None:
        self.config.close()


class TexttableMock(Texttable):  # type: ignore
    def __init__(self, max_width: int = 80) -> None:
        super().__init__(max_width)
        self.headers = []  # type: List[str]
        self.rows = []  # type: List[List[str]]

    def draw(self) -> None:
        self.headers = self._header
        self.rows = self._rows


class ExtendedDummyNodeDriver(DummyNodeDriver):  # type: ignore
    # pylint: disable=abstract-method
    call_args = {}  # type: dict
    features = {"create_node": ["password", "ssh_key"]}

    key_pairs = [
        KeyPair(
            name="name-1",
            public_key="public-key-1",
            fingerprint="fingerprint-1",
            driver=None,
            extra={"id": "111"}
        ),
        KeyPair(
            name="name-2",
            public_key="public-key-2",
            fingerprint="fingerprint-2",
            driver=None,
            extra={"id": "222"}
        ),
    ]

    def list_key_pairs(self) -> List[KeyPair]:
        return self.key_pairs

    def delete_key_pair(self, _key_pair: KeyPair) -> bool:
        return True

    def create_node(self, **kwargs: Any) -> Node:
        self.call_args["create_node"] = kwargs
        return super().create_node(**kwargs)

    # pylint: enable=abstract-method


class DigitalOceanDummyNodeDriver(DummyNodeDriver):  # type: ignore
    # pylint: disable=abstract-method,arguments-differ,protected-access
    type = ComputeProvider.DIGITAL_OCEAN
    call_args = {}  # type: dict

    images = [
        {
            "id": 1,
            "name": "first",
            "distribution": "dist",
            "public": True,
            "slug": "a",
            "regions": ["a", "b", "c"],
            "min_disk_size": 1,
            "created_at": "1234"
        },
        {
            "id": 2,
            "name": "second",
            "distribution": "dist",
            "public": True,
            "slug": "b",
            "regions": ["a", "b", "c"],
            "min_disk_size": 1,
            "created_at": "1234"
        },
    ]

    locations = [
        {
            "slug": "1",
            "name": "location 1",
            "country": "country 1",
        },
        {
            "slug": "2",
            "name": "location 2",
            "country": "country 2",
        },
    ]

    sizes = [
        {
            "slug": "1",
            "memory": 512,
            "transfer": 1024,
            "disk": 25,
            "vcpus": 1,
            "regions": ["a", "b", "c"],
            "price_hourly": 0.007,
            "price_monthly": 5,
        },
        {
            "slug": "2",
            "memory": 1024,
            "transfer": 2048,
            "disk": 50,
            "vcpus": 2,
            "regions": ["a", "b", "c"],
            "price_hourly": 0.014,
            "price_monthly": 10,
        },
    ]

    key_pairs = [
        {
            "id": 1,
            "name": "key pair 1",
            "fingerprint": "11:22:33:44",
            "public_key": "ssh-rsa data first",
        },
        {
            "id": 2,
            "name": "key pair 2",
            "fingerprint": "55:66:77:88",
            "public_key": "ssh-rsa abcd second",
        },
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.do = get_driver(ComputeProvider, "digitalocean")("x")

    def create_key_pair(self, name: str, public_key: str = "") -> Dict:
        ssh_key = {
            "id": 3,
            "fingerprint": "aa:bb:cc:dd",
            "public_key": public_key,
            "name": name,
        }

        self.key_pairs.append(ssh_key)
        self.call_args["create_key_pair"] = ssh_key
        return ssh_key

    def list_images(self) -> List[NodeImage]:
        return [self.do._to_image(x) for x in self.images]

    def list_key_pairs(self) -> List[KeyPair]:
        return [self.do._to_key_pair(x) for x in self.key_pairs]

    def list_locations(self) -> List[NodeLocation]:
        return [self.do._to_location(x) for x in self.locations]

    def list_sizes(self) -> List[NodeSize]:
        return [self.do._to_size(x) for x in self.sizes]

    def create_node(self, **kwargs: Any) -> Node:
        self.call_args["create_node"] = kwargs
        return super().create_node(**kwargs)

    # pylint: enable=abstract-method,arguments-differ,protected-access


class VultrDummyNodeDriver(DummyNodeDriver):  # type: ignore
    # pylint: disable=abstract-method,arguments-differ,protected-access
    type = ComputeProvider.VULTR
    call_args = {}  # type: dict
    images = [
        {
            "OSID": "1",
            "name": "first",
            "arch": "x64",
            "family": "centos",
            "windows": False
        },
        {
            "OSID": "2",
            "name": "second",
            "arch": "i386",
            "family": "debian",
            "windows": False
        },
    ]

    locations = [
        {
            "DCID": "1",
            "name": "location 1",
            "country": "country 1",
            "continent": "continent 1",
            "state": "state 2",
            "ddos_protection": False,
            "block_storage": False,
            "regioncode": "R1",
        },
        {
            "DCID": "2",
            "name": "location 2",
            "country": "country 2",
            "continent": "continent 2",
            "state": "state 2",
            "ddos_protection": False,
            "block_storage": False,
            "regioncode": "R2",
        },
    ]

    sizes = [
        {
            "VPSPLANID": "1",
            "name": "plan 1",
            "vcpu_count": "1",
            "ram": "111",
            "disk": "10",
            "bandwidth": "1",
            "price_per_month": "1.00",
            "windows": False,
            "plan_type": "SSD",
            "available_locations": [1, 2]
        },
        {
            "VPSPLANID": "2",
            "name": "plan 2",
            "vcpu_count": "2",
            "ram": "222",
            "disk": "20",
            "bandwidth": "2",
            "price_per_month": "2.00",
            "windows": False,
            "plan_type": "SSD",
            "available_locations": [1, 2]
        },
    ]

    key_pairs = [
        {
            "SSHKEYID": "1",
            "name": "key pair 1",
            "ssh_key": "ssh-rsa data first",
        },
        {
            "SSHKEYID": "2",
            "name": "key pair 2",
            "ssh_key": "ssh-rsa abcd second",
        },
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.vultr = get_driver(ComputeProvider, "vultr")("x")

    def create_key_pair(self, **kwargs: Any) -> bool:
        self.call_args["create_key_pair"] = kwargs
        super().create_key_pair(**kwargs)
        return True

    def create_node(self, **kwargs: Any) -> Node:
        self.call_args["create_node"] = kwargs
        return super().create_node(**kwargs)

    def list_images(self) -> List[NodeImage]:
        return [self.vultr._to_image(x) for x in self.images]

    def list_key_pairs(self) -> List[SSHKey]:
        return [self.vultr._to_ssh_key(x) for x in self.key_pairs]

    def list_locations(self) -> List[NodeLocation]:
        return [self.vultr._to_location(x) for x in self.locations]

    def list_sizes(self) -> List[NodeSize]:
        return [self.vultr._to_size(x) for x in self.sizes]

    # pylint: enable=abstract-method,arguments-differ,protected-access
