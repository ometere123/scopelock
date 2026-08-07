"""Test configuration.

Windows-only shims and one embeddings-specific version pin. Nothing here
affects contract behaviour.
"""

import atexit
import os
import sys

import pytest

# gltest-direct's SDK loader resolves a runner bundle by version, same as
# genvm-lint does. The embeddings library only exists from v0.3.0-rc7 onward,
# so direct-mode tests need the same GENVM_VERSION pin the lint step uses.
os.environ.setdefault("GENVM_VERSION", "v0.3.0-rc7")


def warp_to(direct_vm, iso: str) -> None:
    """Advance the transaction clock everywhere the contract can read it.

    direct_vm.warp() alone is not enough for a contract that reads
    gl.message.raw.datetime -- its refresh only rewrites sender_address and
    origin_address in gl.message_raw; the datetime key is injected once at
    contract load and never updated after that. This bridges the gap so
    time-dependent tests (the challenge-timeout reclaim, here) are not
    vacuous.
    """
    direct_vm.warp(iso)
    gl = sys.modules.get("genlayer.gl")
    if gl is None:
        return
    raw = getattr(gl, "message_raw", None)
    if isinstance(raw, dict):
        raw["datetime"] = iso
    nested = getattr(getattr(gl, "message", None), "raw", None)
    if isinstance(nested, dict):
        nested["datetime"] = iso


CONTRACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "contracts")
REFERENCE_CONTRACT = os.path.join(CONTRACTS_DIR, "originality_bond.py")


def as_address(value):
    """Coerce a direct-mode account fixture into a genlayer ``Address``.

    Account fixtures fall back to raw bytes when the SDK is not importable at
    fixture-resolution time. Put the SDK on the path ourselves when needed
    instead of requiring a prior deploy in the same test.
    """
    if not isinstance(value, bytes):
        return value

    try:
        from genlayer.py.types import Address
    except ImportError:
        from pathlib import Path

        from gltest.direct.sdk_loader import setup_sdk_paths

        setup_sdk_paths(Path(REFERENCE_CONTRACT), None)
        from genlayer.py.types import Address

    return Address(value)


@pytest.fixture(autouse=True)
def _reset_contract_registry():
    """Allow each test to load whichever contract it needs.

    The SDK permits a single gl.Contract subclass per process and records it
    in a module-level global. Without clearing that between tests, a suite
    passes or fails purely on file ordering.
    """
    yield
    try:
        import genlayer.gl.genvm_contracts as contracts
    except ImportError:
        return
    contracts.__known_contract__ = None


if sys.platform == "win32":  # pragma: no cover - platform specific
    try:
        from gltest.direct import loader as _gltest_loader
    except ImportError:
        _gltest_loader = None

    if _gltest_loader is not None:
        _leaked_paths: list[str] = []
        _real_unlink = os.unlink

        def _tolerant_unlink(path, *args, **kwargs):
            try:
                return _real_unlink(path, *args, **kwargs)
            except PermissionError:
                _leaked_paths.append(os.fspath(path))

        _original_inject = _gltest_loader._inject_message_to_fd0

        def _inject_message_to_fd0(vm):
            os.unlink = _tolerant_unlink
            try:
                return _original_inject(vm)
            finally:
                os.unlink = _real_unlink

        _gltest_loader._inject_message_to_fd0 = _inject_message_to_fd0

        @atexit.register
        def _sweep_leaked_temp_files():
            for path in _leaked_paths:
                try:
                    _real_unlink(path)
                except OSError:
                    pass
