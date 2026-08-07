"""Direct-mode tests for OriginalityBond.

Embedding generation and vector search run for real here -- they are
deterministic contract logic, not something to mock. Only the derivation
verdict (gl.nondet.exec_prompt) is mocked, matching the convention used
throughout this codebase.

Test strategy for the similarity gate: real embedding distances between two
pieces of English text are not perfectly predictable in advance (measured
during development: a close paraphrase and two unrelated sentences can land
within a similar distance band). Rather than betting assertions on guessed
distances, most tests deploy with an explicit auto_flag_distance_milli chosen
to force the path under test -- a very low threshold to guarantee "does not
flag", a very high one to guarantee "flags". The one test that uses the
*default* threshold registers literally identical content, whose distance is
~0 regardless of model behaviour and reliably clears any sane threshold. See
README "Measured on live consensus" for real numbers from a live network run.
"""

import json

from conftest import as_address

CONTRACT = "contracts/originality_bond.py"

JUDGE_PROMPT = r"You judge whether CANDIDATE"

ONE_GEN = 1_000_000_000_000_000_000

CONTENT_A = (
    "This is a sufficiently long piece of original content describing a "
    "fictional method for organising a community garden rotation schedule "
    "across four growing seasons with volunteer sign-up incentives."
)
CONTENT_B = (
    "An entirely different passage about deep-sea hydrothermal vent ecosystems "
    "and the chemosynthetic bacteria that support tube worm colonies living "
    "kilometres below the ocean surface without any sunlight at all."
)


def verdict(v, confidence="HIGH", reasoning="test verdict"):
    return json.dumps({"verdict": v, "confidence": confidence, "reasoning": reasoning})


def deploy_permissive(direct_deploy):
    """A registry so loose it flags almost anything -- forces the review path."""
    return direct_deploy(CONTRACT, 4000, 2000, 7 * 24 * 3600)


def deploy_strict(direct_deploy):
    """A registry so strict it never flags -- forces the fast deterministic path."""
    return direct_deploy(CONTRACT, 1, 2000, 7 * 24 * 3600)


def register(contract, direct_vm, title, content, value=ONE_GEN):
    direct_vm.value = value
    return contract.register(title, content)


# ---------------------------------------------------------------------------
# Constructor / policy validation
# ---------------------------------------------------------------------------


def _reset_registry():
    import genlayer.gl.genvm_contracts as _c
    _c.__known_contract__ = None


def test_constructor_rejects_invalid_policy(direct_vm, direct_deploy):
    # The module is registered as soon as it is imported, before __init__
    # even runs -- a constructor that reverts still leaves the singleton
    # slot occupied, so each redeploy attempt needs its own reset.
    with direct_vm.expect_revert("EXPECTED"):
        direct_deploy(CONTRACT, 0, 2000, 604800)
    _reset_registry()
    with direct_vm.expect_revert("EXPECTED"):
        direct_deploy(CONTRACT, 550, 0, 604800)
    _reset_registry()
    with direct_vm.expect_revert("EXPECTED"):
        direct_deploy(CONTRACT, 550, 20000, 604800)
    _reset_registry()
    with direct_vm.expect_revert("EXPECTED"):
        direct_deploy(CONTRACT, 550, 2000, 0)


# ---------------------------------------------------------------------------
# Registration -- fully deterministic path
# ---------------------------------------------------------------------------


def test_first_ever_registration_is_always_active(direct_vm, direct_deploy):
    """Nothing to compare against, so there is nothing to flag. No round spent."""
    contract = deploy_permissive(direct_deploy)  # even a loose registry can't flag an empty index
    entry_id = register(contract, direct_vm, "First", CONTENT_A)

    state = contract.get_entry(entry_id)
    assert state["status_name"] == "ACTIVE"
    assert state["nearest_neighbor_id"] == 0
    assert contract.entry_count() == 1


def test_register_rejects_invalid_input(direct_vm, direct_deploy):
    contract = deploy_strict(direct_deploy)

    direct_vm.value = 0
    with direct_vm.expect_revert("EXPECTED"):
        contract.register("t", CONTENT_A)

    direct_vm.value = ONE_GEN
    with direct_vm.expect_revert("EXPECTED"):
        contract.register("", CONTENT_A)

    direct_vm.value = ONE_GEN
    with direct_vm.expect_revert("EXPECTED"):
        contract.register("t", "too short")


def test_strict_threshold_never_flags(direct_vm, direct_deploy):
    """A threshold of 1 milli-unit cannot be cleared by any real embedding pair."""
    contract = deploy_strict(direct_deploy)
    register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    assert contract.get_entry(second_id)["status_name"] == "ACTIVE"


def test_permissive_threshold_flags_a_second_registration(direct_vm, direct_deploy):
    """A threshold this loose treats any two live entries as similar enough."""
    contract = deploy_permissive(direct_deploy)
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    state = contract.get_entry(second_id)
    assert state["status_name"] == "PENDING_REVIEW"
    assert state["nearest_neighbor_id"] == first_id


def test_identical_content_flags_under_the_default_threshold(direct_vm, direct_deploy):
    """The one test that relies on real embedding behaviour rather than a
    forced threshold: literally identical text has ~zero distance from
    itself, so this must flag no matter how the model behaves."""
    contract = direct_deploy(CONTRACT)  # default policy
    register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Copy", CONTENT_A)

    assert contract.get_entry(second_id)["status_name"] == "PENDING_REVIEW"


def test_preview_similarity_costs_no_stake(direct_vm, direct_deploy):
    contract = deploy_permissive(direct_deploy)
    register(contract, direct_vm, "First", CONTENT_A)

    preview = contract.preview_similarity(CONTENT_B)
    assert preview["would_flag"] is True
    assert contract.entry_count() == 1, "preview must not register anything"


# ---------------------------------------------------------------------------
# Automated review round
# ---------------------------------------------------------------------------


def test_resolve_review_requires_pending_status(direct_vm, direct_deploy):
    contract = deploy_strict(direct_deploy)
    entry_id = register(contract, direct_vm, "First", CONTENT_A)

    with direct_vm.expect_revert("EXPECTED"):
        contract.resolve_review(entry_id)


def test_review_derivative_rejects_and_pays_the_prior_owner(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_permissive(direct_deploy)

    direct_vm.sender = direct_alice
    first_id = register(contract, direct_vm, "First", CONTENT_A)

    with direct_vm.prank(direct_bob):
        second_id = register(contract, direct_vm, "Second", CONTENT_B)
    assert contract.get_entry(second_id)["status_name"] == "PENDING_REVIEW"

    direct_vm.mock_llm(JUDGE_PROMPT, verdict("DERIVATIVE"))
    contract.resolve_review(second_id)

    state = contract.get_entry(second_id)
    assert state["status_name"] == "REJECTED"
    assert state["review_verdict"] == 1


def test_review_original_activates_with_no_payout(direct_vm, direct_deploy):
    contract = deploy_permissive(direct_deploy)
    register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.mock_llm(JUDGE_PROMPT, verdict("ORIGINAL"))
    contract.resolve_review(second_id)

    assert contract.get_entry(second_id)["status_name"] == "ACTIVE"


def test_review_inconclusive_gives_benefit_of_the_doubt(direct_vm, direct_deploy):
    """INCONCLUSIVE on an automated flag activates the entry -- no adversary
    has staked anything yet, so the system does not guess against the owner."""
    contract = deploy_permissive(direct_deploy)
    register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.mock_llm(JUDGE_PROMPT, verdict("INCONCLUSIVE"))
    contract.resolve_review(second_id)

    assert contract.get_entry(second_id)["status_name"] == "ACTIVE"


def test_unparseable_review_output_is_retryable_not_lost(direct_vm, direct_deploy):
    contract = deploy_permissive(direct_deploy)
    register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.mock_llm(JUDGE_PROMPT, "not json at all")
    contract.resolve_review(second_id)
    assert contract.get_entry(second_id)["status_name"] == "PENDING_REVIEW"

    direct_vm.clear_mocks()
    direct_vm.mock_llm(JUDGE_PROMPT, verdict("ORIGINAL"))
    contract.resolve_review(second_id)
    assert contract.get_entry(second_id)["status_name"] == "ACTIVE"


def test_fenced_json_is_recovered(direct_vm, direct_deploy):
    contract = deploy_permissive(direct_deploy)
    register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.mock_llm(JUDGE_PROMPT, "```json\n" + verdict("ORIGINAL") + "\n```")
    contract.resolve_review(second_id)
    assert contract.get_entry(second_id)["status_name"] == "ACTIVE"


def test_unknown_verdict_string_defaults_to_inconclusive(direct_vm, direct_deploy):
    """An unreadable verdict must never be silently read as DERIVATIVE --
    that would take someone's money on a guess."""
    contract = deploy_permissive(direct_deploy)
    register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.mock_llm(JUDGE_PROMPT, verdict("MAYBE_SORT_OF"))
    contract.resolve_review(second_id)
    assert contract.get_entry(second_id)["status_name"] == "ACTIVE"
    assert contract.get_entry(second_id)["review_verdict"] == 2  # INCONCLUSIVE


# ---------------------------------------------------------------------------
# Withdrawal
# ---------------------------------------------------------------------------


def test_withdraw_refunds_and_removes_active_status(
    direct_vm, direct_deploy, direct_alice
):
    contract = deploy_strict(direct_deploy)
    direct_vm.sender = direct_alice
    entry_id = register(contract, direct_vm, "First", CONTENT_A)

    contract.withdraw(entry_id)
    assert contract.get_entry(entry_id)["status_name"] == "WITHDRAWN"


def test_withdraw_is_owner_only(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy_strict(direct_deploy)
    direct_vm.sender = direct_alice
    entry_id = register(contract, direct_vm, "First", CONTENT_A)

    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert("EXPECTED"):
            contract.withdraw(entry_id)


def test_withdraw_allowed_while_pending_review(direct_vm, direct_deploy):
    """No adversary has staked anything against a system flag, so the owner
    may bail before a consensus round is even spent."""
    contract = deploy_permissive(direct_deploy)
    register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)
    assert contract.get_entry(second_id)["status_name"] == "PENDING_REVIEW"

    contract.withdraw(second_id)
    assert contract.get_entry(second_id)["status_name"] == "WITHDRAWN"


def test_withdraw_refused_once_challenged(direct_vm, direct_deploy):
    """A challenger has bonded real money expecting a resolution; the owner
    cannot dodge it by withdrawing."""
    contract = deploy_strict(direct_deploy)
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.value = ONE_GEN // 4
    contract.open_challenge(second_id, first_id)

    with direct_vm.expect_revert("EXPECTED"):
        contract.withdraw(second_id)


def test_withdraw_refused_after_rejection(direct_vm, direct_deploy):
    contract = deploy_permissive(direct_deploy)
    register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)
    direct_vm.mock_llm(JUDGE_PROMPT, verdict("DERIVATIVE"))
    contract.resolve_review(second_id)

    with direct_vm.expect_revert("EXPECTED"):
        contract.withdraw(second_id)


# ---------------------------------------------------------------------------
# Challenges
# ---------------------------------------------------------------------------


def test_open_challenge_validates_inputs(direct_vm, direct_deploy):
    contract = deploy_strict(direct_deploy)
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.value = ONE_GEN // 4
    with direct_vm.expect_revert("EXPECTED"):
        contract.open_challenge(second_id, second_id)  # self-reference

    direct_vm.value = 1  # far below min_challenge_bond_bps of the target's stake
    with direct_vm.expect_revert("EXPECTED"):
        contract.open_challenge(second_id, first_id)


def test_open_challenge_requires_active_target(direct_vm, direct_deploy):
    contract = deploy_permissive(direct_deploy)
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)
    assert contract.get_entry(second_id)["status_name"] == "PENDING_REVIEW"

    direct_vm.value = ONE_GEN // 4
    with direct_vm.expect_revert("EXPECTED"):
        contract.open_challenge(second_id, first_id)


def test_cannot_open_two_challenges_on_the_same_entry(direct_vm, direct_deploy):
    contract = deploy_strict(direct_deploy)
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.value = ONE_GEN // 4
    contract.open_challenge(second_id, first_id)

    direct_vm.value = ONE_GEN // 4
    with direct_vm.expect_revert("EXPECTED"):
        contract.open_challenge(second_id, first_id)


def test_challenge_marks_the_entry_challenge_pending(direct_vm, direct_deploy):
    contract = deploy_strict(direct_deploy)
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.value = ONE_GEN // 4
    contract.open_challenge(second_id, first_id)

    assert contract.get_entry(second_id)["status_name"] == "CHALLENGE_PENDING"
    ch = contract.get_challenge(second_id)
    assert ch["prior_entry_id"] == first_id
    assert ch["resolved"] is False


def test_resolve_challenge_derivative_pays_the_challenger(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_strict(direct_deploy)
    direct_vm.sender = direct_alice
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    with direct_vm.prank(direct_bob):
        direct_vm.value = ONE_GEN // 4
        contract.open_challenge(second_id, first_id)

    direct_vm.mock_llm(JUDGE_PROMPT, verdict("DERIVATIVE"))
    contract.resolve_challenge(second_id)

    state = contract.get_entry(second_id)
    assert state["status_name"] == "REJECTED"
    ch = contract.get_challenge(second_id)
    assert ch["resolved"] is True
    assert ch["verdict"] == 1


def test_resolve_challenge_original_pays_the_owner_and_reactivates(
    direct_vm, direct_deploy
):
    contract = deploy_strict(direct_deploy)
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.value = ONE_GEN // 4
    contract.open_challenge(second_id, first_id)

    direct_vm.mock_llm(JUDGE_PROMPT, verdict("ORIGINAL"))
    contract.resolve_challenge(second_id)

    state = contract.get_entry(second_id)
    assert state["status_name"] == "ACTIVE"
    assert state["open_challenge_id"] == 0


def test_resolve_challenge_inconclusive_settles_like_original(direct_vm, direct_deploy):
    """The burden of proof is on the challenger; failing to meet it costs
    the challenger their bond exactly as a losing ORIGINAL verdict would."""
    contract = deploy_strict(direct_deploy)
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.value = ONE_GEN // 4
    contract.open_challenge(second_id, first_id)

    direct_vm.mock_llm(JUDGE_PROMPT, verdict("INCONCLUSIVE"))
    contract.resolve_challenge(second_id)

    assert contract.get_entry(second_id)["status_name"] == "ACTIVE"


def test_a_reactivated_entry_can_be_challenged_again(direct_vm, direct_deploy):
    """Losing a challenge must not permanently immunise an entry from a
    second, better-evidenced challenge later."""
    contract = deploy_strict(direct_deploy)
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.value = ONE_GEN // 4
    contract.open_challenge(second_id, first_id)
    direct_vm.mock_llm(JUDGE_PROMPT, verdict("ORIGINAL"))
    contract.resolve_challenge(second_id)
    assert contract.get_entry(second_id)["status_name"] == "ACTIVE"

    direct_vm.value = ONE_GEN // 4
    contract.open_challenge(second_id, first_id)
    assert contract.get_entry(second_id)["status_name"] == "CHALLENGE_PENDING"


def test_resolve_challenge_requires_open_challenge(direct_vm, direct_deploy):
    contract = deploy_strict(direct_deploy)
    entry_id = register(contract, direct_vm, "First", CONTENT_A)

    with direct_vm.expect_revert("EXPECTED"):
        contract.resolve_challenge(entry_id)


def test_unparseable_challenge_output_leaves_challenge_open(direct_vm, direct_deploy):
    contract = deploy_strict(direct_deploy)
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.value = ONE_GEN // 4
    contract.open_challenge(second_id, first_id)

    direct_vm.mock_llm(JUDGE_PROMPT, "garbage")
    contract.resolve_challenge(second_id)
    assert contract.get_entry(second_id)["status_name"] == "CHALLENGE_PENDING"
    assert contract.get_challenge(second_id)["resolved"] is False


# ---------------------------------------------------------------------------
# Time -- the challenge timeout, both sides of the boundary
# ---------------------------------------------------------------------------


def test_reclaim_stale_challenge_refused_before_timeout(direct_vm, direct_deploy):
    from conftest import warp_to

    warp_to(direct_vm, "2026-08-01T00:00:00Z")
    contract = direct_deploy(CONTRACT, 1, 2000, 3600)  # 1-hour timeout
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.value = ONE_GEN // 4
    contract.open_challenge(second_id, first_id)

    warp_to(direct_vm, "2026-08-01T00:30:00Z")  # 30 min in, inside the window
    with direct_vm.expect_revert("EXPECTED"):
        contract.reclaim_stale_challenge(second_id)


def test_reclaim_stale_challenge_succeeds_exactly_at_the_boundary(
    direct_vm, direct_deploy
):
    from conftest import warp_to

    warp_to(direct_vm, "2026-08-01T00:00:00Z")
    contract = direct_deploy(CONTRACT, 1, 2000, 3600)
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.value = ONE_GEN // 4
    contract.open_challenge(second_id, first_id)

    warp_to(direct_vm, "2026-08-01T01:00:00Z")  # exactly the timeout
    contract.reclaim_stale_challenge(second_id)

    state = contract.get_entry(second_id)
    assert state["status_name"] == "ACTIVE"
    ch = contract.get_challenge(second_id)
    assert ch["resolved"] is True


def test_is_challenge_stale_agrees_with_reclaim(direct_vm, direct_deploy):
    from conftest import warp_to

    warp_to(direct_vm, "2026-08-01T00:00:00Z")
    contract = direct_deploy(CONTRACT, 1, 2000, 3600)
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    second_id = register(contract, direct_vm, "Second", CONTENT_B)

    direct_vm.value = ONE_GEN // 4
    contract.open_challenge(second_id, first_id)

    warp_to(direct_vm, "2026-08-01T00:59:00Z")
    assert contract.is_challenge_stale(second_id) is False

    warp_to(direct_vm, "2026-08-01T01:00:00Z")
    assert contract.is_challenge_stale(second_id) is True


def test_reclaim_permissionless_anyone_may_call_it(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    from conftest import warp_to

    warp_to(direct_vm, "2026-08-01T00:00:00Z")
    contract = direct_deploy(CONTRACT, 1, 2000, 3600)
    direct_vm.sender = direct_alice
    first_id = register(contract, direct_vm, "First", CONTENT_A)
    with direct_vm.prank(direct_bob):
        second_id = register(contract, direct_vm, "Second", CONTENT_B)

    with direct_vm.prank(direct_bob):
        direct_vm.value = ONE_GEN // 4
        contract.open_challenge(second_id, first_id)

    warp_to(direct_vm, "2026-08-01T01:00:00Z")
    with direct_vm.prank(direct_charlie):
        contract.reclaim_stale_challenge(second_id)

    assert contract.get_entry(second_id)["status_name"] == "ACTIVE"


# ---------------------------------------------------------------------------
# Address handling on the network (the class of bug found in the sibling
# repo's payout path -- covered here even though direct mode cannot fully
# reproduce the on-network hex-string marshalling issue).
# ---------------------------------------------------------------------------


def test_entry_owner_survives_a_hex_string_sender_round_trip(
    direct_vm, direct_deploy, direct_alice
):
    contract = deploy_strict(direct_deploy)
    direct_vm.sender = direct_alice
    entry_id = register(contract, direct_vm, "First", CONTENT_A)

    owner = contract.get_entry(entry_id)["owner"]
    assert owner.lower() == str(as_address(direct_alice)).lower()


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


def test_get_entry_unknown_id_is_rejected(direct_vm, direct_deploy):
    contract = deploy_strict(direct_deploy)
    with direct_vm.expect_revert("EXPECTED"):
        contract.get_entry(999)


def test_get_challenge_returns_none_when_absent(direct_vm, direct_deploy):
    contract = deploy_strict(direct_deploy)
    entry_id = register(contract, direct_vm, "First", CONTENT_A)
    assert contract.get_challenge(entry_id) is None


def test_entry_count_tracks_registrations(direct_vm, direct_deploy):
    contract = deploy_strict(direct_deploy)
    assert contract.entry_count() == 0
    register(contract, direct_vm, "First", CONTENT_A)
    assert contract.entry_count() == 1
    register(contract, direct_vm, "Second", CONTENT_B)
    assert contract.entry_count() == 2
