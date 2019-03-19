from unittest.mock import patch

from libcloud.common.base import BaseDriver
from libcloud.compute import ssh
from libcloud.compute.deployment import SSHKeyDeployment
from libcloud.compute.providers import Provider, get_driver, set_driver
from libcloud.compute.types import DeploymentError

from cloudie import cli, cloud, compute

from .helpers import ClickTestCase, ExtendedDummyNodeDriver, TexttableMock


class TestCompute(ClickTestCase):
    def setUp(self) -> None:
        super().setUp()

        try:
            get_driver("dummy-extended")
        except AttributeError:
            set_driver(
                "dummy-extended",
                "tests.helpers",
                "ExtendedDummyNodeDriver",
            )

        self.config.write(
            b"""
            [role.dummy]
            provider = "dummy"
            key = "abcd"

            [role.dummy-ext]
            provider = "dummy-extended"
            key = "abcd"
            """
        )
        self.config.flush()

    def test_no_ssh_deploy(self) -> None:
        """
        See security.py.
        """

        @compute.compute.command("deploy")
        @cloud.pass_driver(Provider)
        def command(driver: BaseDriver) -> None:
            orig_paramiko = ssh.have_paramiko
            ssh.have_paramiko = True

            deploy = SSHKeyDeployment("ssh-rsa data")
            driver.features["create_node"].append("password")
            driver.deploy_node(deploy=deploy)

            ssh.have_paramiko = orig_paramiko

        args = [
            "--config-file",
            self.config.name,
            "compute",
            command.name,
            "--role",
            "dummy",
        ]
        result = self.runner.invoke(cli.cli, args)
        self.assertEqual(type(result.exception), DeploymentError)
        self.assertEqual(str(result.exception.value), "ssh module is disabled")
        self.assertNotEqual(result.exit_code, 0)

    def test_list_images(self) -> None:
        args = [
            "--config-file",
            self.config.name,
            "compute",
            "list-images",
            "--role",
            "dummy",
        ]
        result = self.runner.invoke(cli.cli, args)

        images = [
            ["1", "Ubuntu 9.10"],
            ["2", "Ubuntu 9.04"],
            ["3", "Slackware 4"],
        ]

        t = TexttableMock()
        with patch("texttable.Texttable") as mock:
            mock.return_value = t
            result = self.runner.invoke(cli.cli, args)
            self.assertEqual(result.exit_code, 0)

        self.assertEqual(t.headers, ["ID", "Name"])
        self.assertEqual(t.rows, images)

    def test_list_key_pairs(self) -> None:
        args = [
            "--config-file",
            self.config.name,
            "compute",
            "list-key-pairs",
            "--role",
            "dummy-ext",
        ]

        t = TexttableMock()
        with patch("texttable.Texttable") as mock:
            mock.return_value = t
            result = self.runner.invoke(cli.cli, args)
            self.assertEqual(result.exit_code, 0)

        self.assertEqual(t.headers, ["ID", "Name", "Public key"])
        for kp in ExtendedDummyNodeDriver.key_pairs:
            row = [kp.extra["id"], kp.name, kp.fingerprint]
            self.assertTrue(row in t.rows)

    def test_list_locations(self) -> None:
        args = [
            "--config-file",
            self.config.name,
            "compute",
            "list-locations",
            "--role",
            "dummy-ext",
        ]

        t = TexttableMock()
        with patch("texttable.Texttable") as mock:
            mock.return_value = t
            result = self.runner.invoke(cli.cli, args)
            self.assertEqual(result.exit_code, 0)

        self.assertEqual(t.headers, ["ID", "Name", "Country"])
        for l in ExtendedDummyNodeDriver("...").list_locations():
            row = [l.id, l.name, l.country]
            self.assertTrue(row in t.rows)

    def test_list_nodes(self) -> None:
        args = [
            "--config-file",
            self.config.name,
            "compute",
            "list-nodes",
            "--role",
            "dummy-ext",
        ]

        t = TexttableMock()
        with patch("texttable.Texttable") as mock:
            mock.return_value = t
            result = self.runner.invoke(cli.cli, args)
            self.assertEqual(result.exit_code, 0)

        headers = [
            "ID",
            "Name",
            "State",
            "Public IP(s)",
            "Private IP(s)",
        ]
        self.assertEqual(t.headers, headers)

        for n in ExtendedDummyNodeDriver("...").nl:
            row = [
                n.id,
                n.name,
                n.state,
                ", ".join(n.public_ips),
                ", ".join(n.private_ips),
            ]
            self.assertTrue(row in t.rows)

    def test_list_sizes(self) -> None:
        args = [
            "--config-file",
            self.config.name,
            "compute",
            "list-sizes",
            "--role",
            "dummy-ext",
        ]

        t = TexttableMock()
        with patch("texttable.Texttable") as mock:
            mock.return_value = t
            result = self.runner.invoke(cli.cli, args)
            self.assertEqual(result.exit_code, 0)

        headers = [
            "ID",
            "Name",
            "VCPU(s)",
            "RAM",
            "Disk",
            "Bandwidth",
            "Price",
        ]
        self.assertEqual(t.headers, headers)

        for s in ExtendedDummyNodeDriver("...").list_sizes():
            row = [
                s.id,
                s.name,
                "",
                str(s.ram),
                str(s.disk),
                str(s.bandwidth),
                str(s.price),
            ]
            self.assertTrue(row in t.rows)
