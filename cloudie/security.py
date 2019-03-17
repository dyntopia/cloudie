from typing import Any

import libcloud.common.base
import libcloud.common.ovh
import libcloud.compute.ssh
import libcloud.security

# The `secure` argument for `BaseDriver.__init__` is used to enable
# HTTPS.  It is `True` by default, but some drivers set it to `False`:
#
# PowerDNS set it to `False` by default, but it can be overridden in the
# instantiation of the driver.
#
# Docker, Joyent and Kubernetes set it to `False` by default, but they
# may set it to `True` depending on the other arguments to __init__.  It
# can also be overridden in the instantiation of the drivers.
#
# Abiquo has `secure` hardcoded to `False`.
#
# The `Connection` class uses the `secure` argument from the driver in
# the following conditional:
#
# > if not self.allow_insecure and not secure:
# >     raise ValueError('Non https connections are not allowed (use '
# >                      'secure=True)')
#
# `allow_insecure` is `True` in libcloud 2.4.0.  Some classes that
# derive from `Connection` set it to False.  The only derived class that
# set it to `True` is `OvhConnection`.
#
# This will break some drivers.
CONNECTIONS = [
    libcloud.common.base.Connection,
    libcloud.common.ovh.OvhConnection,
]

for cls in CONNECTIONS:
    assert hasattr(cls, "allow_insecure")
    setattr(cls, "allow_insecure", False)


# The ssh module in libcloud 2.4.0 automatically adds unknown host keys
# with paramiko.AutoAddPolicy (sigh!), so it is monkey patched to avoid
# it.
#
# Many drivers expose provider-specific functionality for adding client
# keys and/or running initialization scripts without using the ssh
# module -- use that instead.
class NoSSH:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("ssh module is disabled")


SSH_CLIENTS = [
    "BaseSSHClient",
    "MockSSHClient",
    "ParamikoSSHClient",
    "ShellOutSSHClient",
    "SSHClient",
]

for cls in SSH_CLIENTS:
    assert hasattr(libcloud.compute.ssh, cls)
    setattr(libcloud.compute.ssh, cls, NoSSH)

# This has been enabled by default for some time, but just in case.
libcloud.security.VERIFY_SSL_CERT = True
