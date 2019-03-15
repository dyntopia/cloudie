from unittest import TestCase

import libcloud
import libcloud.compute.deployment
import libcloud.compute.ssh
import libcloud.security

from cloudie import security

assert security  # to make pyflakes happy


class TestSecurity(TestCase):
    def test_ssh_deploy_exception(self) -> None:
        """
        Make sure that the SSH module throws.

        Cloudie does not depend on Paramiko, but it may still be
        installed on a users system.  If it is installed, make sure
        that libclouds insecure usage of it is monkey patched to throw
        an exception.
        """
        driver = libcloud.get_driver(
            libcloud.DriverType.COMPUTE,
            libcloud.DriverType.COMPUTE.DUMMY,
        )(creds="")
        driver.features["create_node"].append("password")

        orig_paramiko = libcloud.compute.ssh.have_paramiko
        libcloud.compute.ssh.have_paramiko = True

        deploy = libcloud.compute.deployment.SSHKeyDeployment("ssh-rsa data")

        with self.assertRaises(libcloud.compute.types.DeploymentError) as ctx:
            driver.deploy_node(deploy=deploy)

        self.assertEqual(str(ctx.exception.value), "ssh module is disabled")

        libcloud.compute.ssh.have_paramiko = orig_paramiko

    def test_ssh_exception(self) -> None:
        for cls in [
                "BaseSSHClient",
                "MockSSHClient",
                "ParamikoSSHClient",
                "ShellOutSSHClient",
                "SSHClient",
        ]:
            with self.assertRaises(RuntimeError) as ctx:
                getattr(libcloud.compute.ssh, cls)()  # pylint: disable=E1120
            self.assertEqual(str(ctx.exception), "ssh module is disabled")

    def test_ssl_cert(self) -> None:
        self.assertTrue(libcloud.security.VERIFY_SSL_CERT)
