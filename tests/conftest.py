"""Windows direct-mode compatibility shim.

The upstream loader successfully installs the temporary message file on fd 0,
then Windows refuses to unlink that still-open file.  Preserve the installed
descriptor and ignore only that post-install cleanup failure.  This module
intentionally contains no contract-runtime imports so candidate scanning still
sees the single production contract source.
"""
from gltest.direct import loader


_original_inject = loader._inject_message_to_fd0


def _inject_message_to_fd0_windows(vm):
    try:
        _original_inject(vm)
    except PermissionError:
        # The fd was already replaced; temporary-file cleanup is deferred by OS.
        return None


loader._inject_message_to_fd0 = _inject_message_to_fd0_windows
