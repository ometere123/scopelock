"""Windows direct-mode compatibility shim.

The upstream loader successfully installs the temporary message file on fd 0,
then Windows refuses to unlink that still-open file.  Preserve the installed
descriptor and ignore only that post-install cleanup failure.  This module
intentionally contains no contract-runtime imports so candidate scanning still
sees the single production contract source.
"""
import sys

from gltest.direct import loader, vm as direct_vm_module


_original_inject = loader._inject_message_to_fd0


def _inject_message_to_fd0_windows(vm):
    try:
        _original_inject(vm)
    except PermissionError:
        # The fd was already replaced; temporary-file cleanup is deferred by OS.
        return None


loader._inject_message_to_fd0 = _inject_message_to_fd0_windows

# gltest 0.29.2 updates its VM clock on warp, but does not refresh the SDK's
# already-loaded message_raw datetime. Keep the supported warp cheatcode
# authoritative so deadline tests exercise the contract rather than wall time.
_original_warp = direct_vm_module.VMContext.warp


def _warp_with_message_refresh(context, timestamp):
    _original_warp(context, timestamp)
    sdk_gl = sys.modules.get("genlayer.gl")
    if sdk_gl is not None and getattr(sdk_gl, "message_raw", None) is not None:
        sdk_gl.message_raw["datetime"] = timestamp


direct_vm_module.VMContext.warp = _warp_with_message_refresh
