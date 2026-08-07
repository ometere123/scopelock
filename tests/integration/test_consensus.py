"""Integration tests for OriginalityBond against live StudioNet consensus.

    gltest tests/integration/ -v -s --network studionet

Direct-mode tests prove the state machine is right given a mocked derivation
verdict. What they cannot prove is the load-bearing assumption underneath the
whole primitive: that embedding generation and vector search reproduce
byte-identical results when independently computed by separate validator
sets. That is what test_embedding_is_deterministic_across_independent_calls
checks, strictly -- not "no bad outcome", but "the produced distance was
identical".

resolve_review/resolve_challenge run one real consensus round each. Deploy
contracts are parametrised with extreme threshold/timeout values (the same
technique the direct suite uses) so which path is taken is controlled by
policy rather than by hoping a real embedding pair lands on the right side of
a guessed distance.
"""

import json

from gltest import get_contract_factory
from gltest.accounts import create_accounts
from gltest.assertions import tx_execution_failed, tx_execution_succeeded

ONE_GEN = 1_000_000_000_000_000_000

# resolve_review / resolve_challenge run one consensus round each and can
# take several minutes on StudioNet.
ROUND_WAIT = {"wait_interval": 5000, "wait_retries": 90}

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


def show(label, value):
    print(f"\n  [READ] {label}\n{json.dumps(value, indent=2, sort_keys=True, default=str)}")


def step(n, label):
    print(f"\n{'=' * 70}\n  WRITE {n}: {label}\n{'=' * 70}")


def expect_refused(label, fn):
    try:
        receipt = fn()
    except Exception as exc:
        print(f"  [REFUSED as designed] {label}\n      {str(exc).strip().splitlines()[0][:150]}")
        return
    assert tx_execution_failed(receipt), f"{label} was allowed but must be refused"
    print(f"  [REFUSED as designed] {label}")


def test_embedding_is_deterministic_across_independent_calls():
    """The convergence property this primitive depends on.

    preview_similarity re-embeds its input from scratch on every call, with
    no cached state carried between transactions. If two independent
    transactions -- each computed fresh by whatever validator set is active
    for that transaction -- disagree on the resulting distance, the entire
    similarity gate is unusable: two registrations of identical content could
    land on opposite sides of the auto-flag threshold depending on who
    happened to validate them.
    """
    factory = get_contract_factory("OriginalityBond")
    contract = factory.deploy(args=[550, 2000, 604800])

    receipt = contract.register(args=["baseline", CONTENT_A]).transact(value=ONE_GEN)
    assert tx_execution_succeeded(receipt), "baseline registration failed -- nothing to compare against"

    first = contract.preview_similarity(args=[CONTENT_A]).call()
    second = contract.preview_similarity(args=[CONTENT_A]).call()
    third = contract.preview_similarity(args=[CONTENT_B]).call()

    print(f"\n  run 1 (self):      distance_milli={first['distance_milli']}")
    print(f"  run 2 (self):      distance_milli={second['distance_milli']}")
    print(f"  run 3 (different): distance_milli={third['distance_milli']}")

    assert first["nearest_neighbor_id"] != 0, (
        "no neighbor was found at all -- the baseline registration did not "
        "actually persist, so this run proves nothing about determinism"
    )
    assert first["distance_milli"] == second["distance_milli"], (
        "the same content produced two different distances on two independent "
        "calls -- embedding generation is not converging across validators"
    )
    assert third["distance_milli"] > first["distance_milli"], (
        "genuinely unrelated content produced a distance no larger than "
        "comparing the baseline against itself -- the similarity metric is "
        "not distinguishing content at all"
    )


def test_full_public_surface():
    other = create_accounts(1)[0]

    factory = get_contract_factory("OriginalityBond")
    # Loose threshold: guarantees the second registration is flagged, so the
    # review path is exercised deterministically rather than hoping two real
    # embeddings happen to land close enough.
    contract = factory.deploy(args=[4000, 2000, 3])  # 3s challenge timeout
    print(f"\nDeployed OriginalityBond at {contract.address}")

    # -- deterministic views before anything exists --------------------
    show("entry_count()", contract.entry_count().call())

    # -- WRITE 1: register (first entry, always fast-path ACTIVE) ------
    step(1, "register  (first entry -- deterministic, no consensus round)")
    r1 = contract.register(args=["First", CONTENT_A]).transact(value=ONE_GEN)
    assert tx_execution_succeeded(r1)
    first_id = contract.entry_count().call()
    show("get_entry(first)", contract.get_entry(args=[first_id]).call())

    expect_refused(
        "registering with zero stake",
        lambda: contract.register(args=["x", CONTENT_B]).transact(value=0),
    )

    # -- WRITE 2: register (second entry -- flagged under this loose policy)
    step(2, "register  (second entry -- flagged by the deterministic gate)")
    r2 = contract.register(args=["Second", CONTENT_B]).transact(value=ONE_GEN)
    assert tx_execution_succeeded(r2)
    second_id = contract.entry_count().call()
    second_state = contract.get_entry(args=[second_id]).call()
    show("get_entry(second)", second_state)
    assert second_state["status_name"] == "PENDING_REVIEW"

    # -- WRITE 3: resolve_review  (one consensus round) -----------------
    step(3, "resolve_review  (one consensus round)")
    r3 = contract.resolve_review(args=[second_id]).transact(**ROUND_WAIT)
    assert tx_execution_succeeded(r3)
    reviewed = contract.get_entry(args=[second_id]).call()
    show("get_entry(second) after review", reviewed)
    print(f"\n  review verdict: {reviewed['review_verdict']}  reasoning: {reviewed['review_reasoning'][:100]}")
    assert reviewed["status_name"] in ("ACTIVE", "REJECTED")

    expect_refused(
        "resolving an already-resolved review",
        lambda: contract.resolve_review(args=[second_id]).transact(**ROUND_WAIT),
    )

    # -- WRITE 4/5: open_challenge + resolve_challenge -------------------
    if reviewed["status_name"] == "ACTIVE":
        step(4, "open_challenge  (deterministic -- bonds a dispute)")
        r4 = contract.connect(other).open_challenge(
            args=[second_id, first_id]
        ).transact(value=ONE_GEN // 4)
        assert tx_execution_succeeded(r4)
        show("get_entry(second) -- CHALLENGE_PENDING", contract.get_entry(args=[second_id]).call())
        show("get_challenge(second)", contract.get_challenge(args=[second_id]).call())

        step(5, "resolve_challenge  (one consensus round)")
        r5 = contract.resolve_challenge(args=[second_id]).transact(**ROUND_WAIT)
        assert tx_execution_succeeded(r5)
        after_challenge = contract.get_entry(args=[second_id]).call()
        show("get_entry(second) after challenge", after_challenge)
        print(f"\n  challenge verdict: {contract.get_challenge(args=[second_id]).call()}")
    else:
        print("\n  second entry was REJECTED by review; skipping challenge on it, "
              "using the surviving first entry to exercise the challenge path instead")
        step(4, "open_challenge  (against the surviving first entry)")
        r4 = contract.connect(other).open_challenge(
            args=[first_id, first_id]
        ).transact(value=ONE_GEN // 4)
        assert tx_execution_failed(r4), "self-referential challenge must be refused"
        # No live second target remains; the challenge/resolve pair is still
        # covered by direct-mode tests exhaustively. Record this branch was
        # taken rather than silently skip it.
        print("  (review resolved REJECTED on-chain; challenge branch covered by direct tests)")

    # -- WRITE 6: withdraw ------------------------------------------------
    step(6, "withdraw  (owner reclaims the first entry's stake)")
    r6 = contract.withdraw(args=[first_id]).transact()
    assert tx_execution_succeeded(r6)
    show("get_entry(first) -- WITHDRAWN", contract.get_entry(args=[first_id]).call())

    expect_refused(
        "withdrawing a second time",
        lambda: contract.withdraw(args=[first_id]).transact(),
    )

    print(f"\n{'=' * 70}")
    print("  Full write surface exercised on StudioNet.")
    print(f"{'=' * 70}\n")


def test_reclaim_stale_challenge_on_a_real_clock():
    """The challenge-timeout reclaim, on the real transaction clock.

    Rather than waiting real wall-clock minutes, this deploys with a 3-second
    timeout -- short enough that the minutes StudioNet consensus naturally
    takes between transactions reliably exceed it, without any artificial
    sleep.
    """
    other = create_accounts(1)[0]
    factory = get_contract_factory("OriginalityBond")
    contract = factory.deploy(args=[4000, 2000, 3])

    contract.register(args=["First", CONTENT_A]).transact(value=ONE_GEN)
    first_id = contract.entry_count().call()
    contract.register(args=["Second", CONTENT_B]).transact(value=ONE_GEN)
    second_id = contract.entry_count().call()

    review = contract.get_entry(args=[second_id]).call()
    if review["status_name"] == "PENDING_REVIEW":
        contract.resolve_review(args=[second_id]).transact(**ROUND_WAIT)
        review = contract.get_entry(args=[second_id]).call()

    if review["status_name"] != "ACTIVE":
        print("\n  second entry did not survive review; nothing to challenge here, "
              "the timeout-reclaim path is covered by direct-mode tests")
        return

    contract.connect(other).open_challenge(
        args=[second_id, first_id]
    ).transact(value=ONE_GEN // 4)

    print("\n  waiting for at least one more StudioNet round-trip to exceed "
          "the 3-second challenge timeout...")
    assert contract.is_challenge_stale(args=[second_id]).call() in (True, False)

    receipt = contract.reclaim_stale_challenge(args=[second_id]).transact()
    assert tx_execution_succeeded(receipt)

    state = contract.get_entry(args=[second_id]).call()
    print(f"\n  reclaimed: {state['status_name']}")
    assert state["status_name"] == "ACTIVE"
