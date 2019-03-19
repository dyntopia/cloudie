import tempfile
from unittest.mock import patch

import click
from libcloud.common.base import BaseDriver
from libcloud.compute import ssh
from libcloud.compute.deployment import SSHKeyDeployment
from libcloud.compute.providers import Provider, get_driver, set_driver
from libcloud.compute.types import DeploymentError

from cloudie import cli, compute, option

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
        @option.pass_driver(Provider)
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


class TestCreateNode(ClickTestCase):
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
        self.ssh_key = tempfile.NamedTemporaryFile()
        self.ssh_key.write(b"ssh-ed25519 data comment")
        self.ssh_key.flush()

        self.config.write(
            """
            [role.dummy]
            provider = "dummy"
            key = "key-dummy"

            [role.dummy-ext]
            provider = "dummy-extended"
            key = "key-dummy-ext"

            [role.dummy-ext-with-required-options]
            provider = "dummy-extended"
            key = "key-dummy-ext-with-required-options"
            image = 1
            size = "3"
            location = "2"

            [role.dummy-ext-with-required-options-and-ssh-key]
            provider = "dummy-extended"
            key = "key-dummy-ext-with-required-options-and-ssh-key"
            image = 1
            size = "3"
            location = "2"
            ssh-key = "{ssh_key}"

            [role.dummy-ext-with-required-options-and-password]
            provider = "dummy-extended"
            key = "key-dummy-ext-with-required-options-and-password"
            image = 1
            size = "3"
            location = "2"
            password = true

            [role.dummy-with-required-options]
            provider = "dummy"
            key = "key-dummy-with-options"
            image = 1
            size = "3"
            location = "2"
            """.format(ssh_key=self.ssh_key.name).encode("ascii")
        )
        self.config.flush()

    def tearDown(self) -> None:
        super().tearDown()
        self.ssh_key.close()

    def test_conflicting_arguments(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            args = [
                "--config-file",
                self.config.name,
                "compute",
                "create-node",
                "--role",
                "dummy-ext-with-required-options",
                "--name",
                "name",
                "--ssh-key",
                tmp.name,
                "--password",
            ]
            result = self.runner.invoke(cli.cli, args)

            self.assertEqual(
                result.output,
                "Error: Use either --ssh-key or --password\n",
            )
            self.assertNotEqual(result.exit_code, 0)

    def test_missing_required_args(self) -> None:
        required = ["--name", "--image", "--location", "--size"]
        for skip in required:
            args = [
                "--config-file",
                self.config.name,
                "compute",
                "create-node",
                "--role",
                "dummy",
            ]

            for arg in required:
                if not arg == skip:
                    args += [arg, "value"]

            result = self.runner.invoke(cli.cli, args)

            self.assertTrue(
                "Error: Missing option \"{}\"".format(skip) in result.output
            )
            self.assertNotEqual(result.exit_code, 0)

    def test_invalid_required_args(self) -> None:
        required = [
            ["--image", "3"],
            ["--location", "2"],
            ["--size", "1"],
        ]
        for invalid in required:
            args = [
                "--config-file",
                self.config.name,
                "compute",
                "create-node",
                "--role",
                "dummy",
                "--name",
                "name",
            ]

            for arg in required:
                if arg == invalid:
                    args += [arg[0], "999"]
                else:
                    args += arg

            result = self.runner.invoke(cli.cli, args)

            self.assertEqual(
                result.output,
                "Error: invalid {}\n".format(invalid[0][2:]),
            )
            self.assertNotEqual(result.exit_code, 0)

    def test_maybe_use_config_required_args(self) -> None:
        driver = ExtendedDummyNodeDriver("")
        options = [
            ["image", "3", "1", driver.list_images],
            ["location", "3", "2", driver.list_locations],
            ["size", "1", "3", driver.list_sizes],
        ]

        for override in options:
            args = [
                "--config-file",
                self.config.name,
                "compute",
                "create-node",
                "--role",
                "dummy-ext-with-required-options",
                "--name",
                "name123",
                "--{}".format(override[0]),
                override[1],
            ]

            result = self.runner.invoke(cli.cli, args)

            for opt in options:
                identifier = driver.call_args["create_node"][opt[0]].id
                if opt == override:
                    self.assertEqual(identifier, opt[1])
                else:
                    self.assertEqual(identifier, opt[2])
            self.assertEqual(result.exit_code, 0)

    def test_feature_missing_ssh_key(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            pass

        args = [
            "--config-file",
            self.config.name,
            "compute",
            "create-node",
            "--role",
            "dummy-ext-with-required-options",
            "--name",
            "name123",
            "--ssh-key",
            tmp.name,
        ]

        result = self.runner.invoke(cli.cli, args)

        self.assertTrue("No such file or directory" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_feature_ssh_key_from_arg(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"ssh-rsa asdf something")
            tmp.flush()

            args = [
                "--config-file",
                self.config.name,
                "compute",
                "create-node",
                "--role",
                "dummy-ext-with-required-options",
                "--name",
                "name123",
                "--ssh-key",
                tmp.name,
            ]

            result = self.runner.invoke(cli.cli, args)

            auth = ExtendedDummyNodeDriver.call_args["create_node"]["auth"]
            self.assertEqual(auth.pubkey, "ssh-rsa asdf something")
            self.assertEqual(result.exit_code, 0)

    def test_feature_ssh_key_from_config(self) -> None:
        args = [
            "--config-file",
            self.config.name,
            "compute",
            "create-node",
            "--role",
            "dummy-ext-with-required-options-and-ssh-key",
            "--name",
            "name123",
        ]

        result = self.runner.invoke(cli.cli, args)

        auth = ExtendedDummyNodeDriver.call_args["create_node"]["auth"]
        self.assertEqual(auth.pubkey, "ssh-ed25519 data comment")
        self.assertEqual(result.exit_code, 0)

    def test_feature_password_from_arg(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"keydata")
            tmp.flush()

            args = [
                "--config-file",
                self.config.name,
                "compute",
                "create-node",
                "--role",
                "dummy-ext-with-required-options-and-password",
                "--name",
                "name123",
                "--password",
            ]

            with patch("click.prompt") as mock:
                mock.return_value = "supersecret"
                result = self.runner.invoke(cli.cli, args)

            auth = ExtendedDummyNodeDriver.call_args["create_node"]["auth"]
            self.assertEqual(auth.password, "supersecret")
            self.assertEqual(result.exit_code, 0)

    def test_feature_password_from_config(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"keydata")
            tmp.flush()

            args = [
                "--config-file",
                self.config.name,
                "compute",
                "create-node",
                "--role",
                "dummy-ext-with-required-options-and-password",
                "--name",
                "name123",
            ]

            with patch("click.prompt") as mock:
                mock.return_value = "supersecret"
                result = self.runner.invoke(cli.cli, args)

            auth = ExtendedDummyNodeDriver.call_args["create_node"]["auth"]
            self.assertEqual(auth.password, "supersecret")
            self.assertEqual(result.exit_code, 0)

    def test_feature_none_used(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"keydata")
            tmp.flush()

            args = [
                "--config-file",
                self.config.name,
                "compute",
                "create-node",
                "--role",
                "dummy-ext",
                "--name",
                "name123",
                "--image",
                "1",
                "--size",
                "3",
                "--location",
                "2",
            ]
            result = self.runner.invoke(cli.cli, args)

            auth = ExtendedDummyNodeDriver.call_args["create_node"].get("auth")
            self.assertIsNone(auth)
            self.assertEqual(result.exit_code, 0)

    def test_unsupported_arg(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            args = [
                "--config-file",
                self.config.name,
                "compute",
                "create-node",
                "--role",
                "dummy-with-required-options",
                "--name",
                "name123",
                "--ssh-key",
                tmp.name,
            ]

            with patch("click.prompt") as mock:
                mock.return_value = "supersecret"
                result = self.runner.invoke(cli.cli, args)

            self.assertTrue("does not support --ssh-key" in result.output)
            self.assertNotEqual(result.exit_code, 0)


class TestGet(ClickTestCase):
    # pylint: disable=protected-access
    def setUp(self) -> None:
        super().setUp()

        self.driver = ExtendedDummyNodeDriver("")

    def test_exception(self) -> None:
        with self.assertRaises(click.exceptions.ClickException):
            compute._get(self.driver.list_images, lambda x: None)

    def test_image_by_id(self) -> None:
        result = compute._get(self.driver.list_images, lambda x: x.id == "2")
        self.assertEqual(result.id, "2")

    def test_image_by_name(self) -> None:
        result = compute._get(
            self.driver.list_images, lambda x: x.name == "Slackware 4"
        )
        self.assertEqual(result.name, "Slackware 4")

    def test_location_by_id(self) -> None:
        result = compute._get(
            self.driver.list_locations, lambda x: x.id == "1"
        )
        self.assertEqual(result.id, "1")

    def test_location_by_name(self) -> None:
        result = compute._get(
            self.driver.list_locations, lambda x: x.name == "Island Datacenter"
        )
        self.assertEqual(result.name, "Island Datacenter")

    def test_size_by_id(self) -> None:
        result = compute._get(self.driver.list_sizes, lambda x: x.id == "3")
        self.assertEqual(result.id, "3")

    def test_size_by_name(self) -> None:
        result = compute._get(
            self.driver.list_sizes, lambda x: x.name == "Small"
        )
        self.assertEqual(result.name, "Small")

    # pylint: enable=protected-access
