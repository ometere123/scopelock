"""Direct state-machine tests. This file deliberately contains no GenLayer SDK import."""
import pytest

ONE = 1_000_000_000_000_000_000

def deploy(direct_deploy): return direct_deploy("contracts/scopelock.py")

def create(contract, vm):
    vm.value = 20 * ONE
    return contract.create_program("Scope", "https://example.com", "abc123", "Public security issues in src only.", "2026-08-01T00:00:00Z", "2027-08-01T00:00:00Z", ONE, 2500, ONE, 2*ONE, 3*ONE, 4*ONE)

def test_program_creation_exposes_full_dossier(direct_vm, direct_deploy):
    contract=deploy(direct_deploy); pid=create(contract,direct_vm); item=contract.get_program(pid)
    assert item["name"] == "Scope" and item["remaining_pool"] == str(20*ONE)
    assert item["critical_payout"] == str(4*ONE)

def test_exact_bond_and_submission_window(direct_vm, direct_deploy):
    contract=deploy(direct_deploy); pid=create(contract,direct_vm)
    direct_vm.value=ONE-1
    with direct_vm.expect_revert("exact bond"): contract.submit_report(pid,"issue","bounded synopsis","https://example.com/report","src/auth","HIGH")
    direct_vm.value=ONE
    rid=contract.submit_report(pid,"issue","bounded synopsis","https://example.com/report","src/auth","HIGH")
    assert contract.get_report(rid)["bond"] == str(ONE)

def test_pause_blocks_submissions(direct_vm, direct_deploy):
    contract=deploy(direct_deploy); pid=create(contract,direct_vm); contract.pause_program(pid,True); direct_vm.value=ONE
    with direct_vm.expect_revert("not open"): contract.submit_report(pid,"issue","bounded synopsis","https://example.com/report","src/auth","HIGH")

def test_pagination_is_bounded(direct_vm, direct_deploy):
    contract=deploy(direct_deploy); create(contract,direct_vm)
    assert contract.list_program_ids(0,50)==[1]
    with direct_vm.expect_revert("pagination"): contract.list_program_ids(0,51)
