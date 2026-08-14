"""Direct tests against the production contract. No GenLayer SDK import here."""
import json

ONE = 1_000_000_000_000_000_000
RESEARCHER = bytes.fromhex("11" * 20)
OTHER = bytes.fromhex("22" * 20)
SDK_VERSION = "v0.2.12"

def deploy(direct_deploy): return direct_deploy("contracts/scopelock.py", sdk_version=SDK_VERSION)

def create(contract, vm):
    vm.warp("2026-08-14T12:00:00Z"); vm.value = 20 * ONE
    return contract.create_program("Scope", "https://example.com", "abc123", "Public security issues in src only.", "2026-08-01T00:00:00Z", "2027-08-01T00:00:00Z", ONE, 2500, ONE, 2*ONE, 3*ONE, 4*ONE)

def submit(contract, vm, title="issue", researcher=RESEARCHER):
    vm.value = ONE
    with vm.prank(researcher): rid = contract.submit_report(1, title, "bounded security synopsis", "https://example.com/report", "src/auth", "HIGH")
    vm.value = 0
    return rid

def mock_outcome(vm, outcome, severity="NONE", duplicate_of=0):
    vm.clear_mocks()
    vm.mock_web(r"https://example\.com", {"status": 200, "body": "bounded public security evidence body for deterministic testing"})
    vm.mock_llm(r"ScopeLock's public-security adjudicator", json.dumps({"outcome":outcome,"severity":severity,"duplicate_of":duplicate_of,"reasoning":f"Direct evidence supports {outcome}.","evidence_summary":f"Evidence digest for {outcome}."}))

def setup_report(vm, direct_deploy):
    contract=deploy(direct_deploy); create(contract,vm); return contract,submit(contract,vm)

def assert_terminal(contract,rid,status,verdict,payout,refund,slash,pool):
    item=contract.get_report(rid); program=contract.get_program(1)
    assert item["status"]==status and item["verdict"]==verdict
    assert item["payout"]==str(payout) and item["refund"]==str(refund) and item["slash"]==str(slash)
    assert program["remaining_pool"]==str(pool) and program["open_report_count"]==0

def test_program_creation_exposes_full_dossier(direct_vm,direct_deploy):
    contract=deploy(direct_deploy); pid=create(contract,direct_vm); item=contract.get_program(pid)
    assert item["name"]=="Scope" and item["remaining_pool"]==str(20*ONE) and item["critical_payout"]==str(4*ONE)

def test_exact_bond_and_submission_window(direct_vm,direct_deploy):
    contract=deploy(direct_deploy); pid=create(contract,direct_vm); direct_vm.value=ONE-1
    with direct_vm.expect_revert("exact bond"): contract.submit_report(pid,"issue","bounded synopsis","https://example.com/report","src/auth","HIGH")
    direct_vm.value=ONE; rid=contract.submit_report(pid,"issue","bounded synopsis","https://example.com/report","src/auth","HIGH")
    assert contract.get_report(rid)["bond"]==str(ONE)

def test_pause_blocks_submissions(direct_vm,direct_deploy):
    contract=deploy(direct_deploy); pid=create(contract,direct_vm); direct_vm.value=0; contract.pause_program(pid,True); direct_vm.value=ONE
    with direct_vm.expect_revert("not open"): contract.submit_report(pid,"issue","bounded synopsis","https://example.com/report","src/auth","HIGH")

def test_pagination_is_bounded(direct_vm,direct_deploy):
    contract=deploy(direct_deploy); create(contract,direct_vm); assert contract.list_program_ids(0,50)==[1]
    with direct_vm.expect_revert("pagination"): contract.list_program_ids(0,51)

def test_valid_high_settlement_and_double_adjudication_block(direct_vm,direct_deploy):
    contract,rid=setup_report(direct_vm,direct_deploy); mock_outcome(direct_vm,"VALID","HIGH"); contract.adjudicate(rid)
    assert contract.get_report(rid)["severity"]=="HIGH"; assert_terminal(contract,rid,3,"VALID",3*ONE,ONE,0,17*ONE)
    with direct_vm.expect_revert("not reviewable"): contract.adjudicate(rid)

def test_known_issue_refunds_bond_without_pool_change(direct_vm,direct_deploy):
    contract,rid=setup_report(direct_vm,direct_deploy); mock_outcome(direct_vm,"KNOWN_ISSUE"); contract.adjudicate(rid)
    assert contract.get_report(rid)["severity"]=="NONE"; assert_terminal(contract,rid,5,"KNOWN_ISSUE",0,ONE,0,20*ONE)

def test_out_of_scope_applies_exact_slash(direct_vm,direct_deploy):
    contract,rid=setup_report(direct_vm,direct_deploy); mock_outcome(direct_vm,"OUT_OF_SCOPE"); contract.adjudicate(rid); slash=ONE*2500//10000
    assert_terminal(contract,rid,6,"OUT_OF_SCOPE",0,ONE-slash,slash,20*ONE+slash)

def test_unestablished_refunds_bond_without_slash(direct_vm,direct_deploy):
    contract,rid=setup_report(direct_vm,direct_deploy); mock_outcome(direct_vm,"EXPLOITABILITY_NOT_ESTABLISHED"); contract.adjudicate(rid)
    assert_terminal(contract,rid,7,"EXPLOITABILITY_NOT_ESTABLISHED",0,ONE,0,20*ONE)

def test_needs_evidence_records_deadline_without_settlement(direct_vm,direct_deploy):
    contract,rid=setup_report(direct_vm,direct_deploy); mock_outcome(direct_vm,"NEEDS_EVIDENCE"); contract.adjudicate(rid); item=contract.get_report(rid)
    assert item["status"]==2 and item["verdict"]=="NEEDS_EVIDENCE" and item["evidence_deadline"]
    assert item["evidence_deadline"]>item["submitted_at"]
    assert item["reasoning"] and item["evidence_digest"] and item["payout"]==item["refund"]==item["slash"]=="0"
    assert contract.get_program(1)["open_report_count"]==1

def test_supplementary_evidence_is_researcher_only_and_returns_submitted(direct_vm,direct_deploy):
    contract,rid=setup_report(direct_vm,direct_deploy); mock_outcome(direct_vm,"NEEDS_EVIDENCE"); contract.adjudicate(rid)
    with direct_vm.prank(OTHER),direct_vm.expect_revert("researcher evidence only"): contract.add_supplementary_evidence(rid,"https://example.com/more")
    with direct_vm.prank(RESEARCHER): contract.add_supplementary_evidence(rid,"https://example.com/more")
    item=contract.get_report(rid); assert item["supplementary_url"]=="https://example.com/more" and item["status"]==1
    assert item["payout"]==item["refund"]==item["slash"]=="0" and contract.get_program(1)["open_report_count"]==1

def test_supplementary_recovery_can_be_readjudicated_to_settlement(direct_vm,direct_deploy):
    contract,rid=setup_report(direct_vm,direct_deploy); mock_outcome(direct_vm,"NEEDS_EVIDENCE"); contract.adjudicate(rid)
    with direct_vm.prank(RESEARCHER): contract.add_supplementary_evidence(rid,"https://example.com/more")
    mock_outcome(direct_vm,"KNOWN_ISSUE"); contract.adjudicate(rid); assert_terminal(contract,rid,5,"KNOWN_ISSUE",0,ONE,0,20*ONE)

def test_needs_evidence_cannot_expire_before_deadline(direct_vm,direct_deploy):
    contract,rid=setup_report(direct_vm,direct_deploy); mock_outcome(direct_vm,"NEEDS_EVIDENCE"); contract.adjudicate(rid)
    with direct_vm.prank(OTHER),direct_vm.expect_revert("deadline not reached"): contract.expire_needs_evidence(rid)

def test_anyone_can_expire_after_deadline_with_full_refund(direct_vm,direct_deploy):
    contract,rid=setup_report(direct_vm,direct_deploy); mock_outcome(direct_vm,"NEEDS_EVIDENCE"); contract.adjudicate(rid); direct_vm.warp("2026-08-22T00:00:00Z")
    with direct_vm.prank(OTHER): contract.expire_needs_evidence(rid)
    assert_terminal(contract,rid,8,"EXPIRED",0,ONE,0,20*ONE)
    with direct_vm.expect_revert("not awaiting evidence"): contract.expire_needs_evidence(rid)

def test_invalid_duplicate_reference_cannot_settle(direct_vm,direct_deploy):
    contract,rid=setup_report(direct_vm,direct_deploy); mock_outcome(direct_vm,"DUPLICATE",duplicate_of=999)
    with direct_vm.expect_revert("invalid duplicate precedent"): contract.adjudicate(rid)
    item=contract.get_report(rid); assert item["status"]==1 and item["payout"]==item["refund"]==item["slash"]=="0"
    assert contract.get_program(1)["open_report_count"]==1
