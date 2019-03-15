from typing import Any

import libcloud.compute.ssh
import libcloud.security


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
