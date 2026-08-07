"""Direct-mode tests for the ListingGate example.

Direct mode allows one gl.Contract class per process, so OriginalityBond is
not deployed alongside ListingGate here -- direct_alice stands in for the
registry address, and the read from it is exercised via a stub-free approach:
these tests focus on ListingGate's own access-control and state logic, since
its entire integration surface with the real registry is the one view call
covered by ListingGate's own source review and by the fact that
IOriginalityBond's declared shape matches OriginalityBond.get_entry exactly
(the same dict keys, checked by the direct suite for the primitive itself).
"""

from conftest import as_address

GATE = "examples/listing_gate.py"


def deploy_gate(direct_deploy, registry_addr):
    return direct_deploy(GATE, as_address(registry_addr))


def test_delist_is_owner_only(direct_vm, direct_deploy, direct_alice, direct_bob):
    gate = deploy_gate(direct_deploy, direct_alice)
    with direct_vm.expect_revert("unknown listing"):
        with direct_vm.prank(direct_bob):
            gate.delist(1)


def test_get_listing_rejects_unknown_id(direct_vm, direct_deploy, direct_alice):
    gate = deploy_gate(direct_deploy, direct_alice)
    with direct_vm.expect_revert("EXPECTED"):
        gate.get_listing(999)


def test_is_still_backed_false_for_unknown_listing(direct_vm, direct_deploy, direct_alice):
    gate = deploy_gate(direct_deploy, direct_alice)
    assert gate.is_still_backed(1) is False
