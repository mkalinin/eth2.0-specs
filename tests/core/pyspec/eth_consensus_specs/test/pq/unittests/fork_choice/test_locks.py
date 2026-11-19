"""Locks and confirmed tips on a small fork with real payload-status nodes."""

from dataclasses import replace
from importlib import import_module
from types import SimpleNamespace

import pytest

from eth_consensus_specs.test import context
from eth_consensus_specs.test.helpers.genesis import create_genesis_state
from eth_consensus_specs.test.helpers.keys import privkeys
from eth_consensus_specs.test.helpers.pq.fork import upgrade_registered_to_pq

pytestmark = pytest.mark.usefixtures("fake_xmss")


@pytest.fixture
def spec(preset, monkeypatch):
    spec = import_module(f"eth_consensus_specs.pq.{context.DEFAULT_TEST_PRESET}")
    monkeypatch.setattr(spec, "config", spec.config._replace(PQ_FORK_EPOCH=0))
    return spec


def at_slot(spec, slot):
    return spec.compute_time_at_slot_ms(spec.Uint64(0), spec.Slot(slot))


@pytest.fixture
def tree(spec):
    # F -- P -- A -- A1
    #       \-- B -- B1
    blocks = {}
    states = {}
    nodes = {}
    for index, (name, parent, slot) in enumerate(
        [
            ("F", None, 0),
            ("P", "F", 1),
            ("A", "P", 2),
            ("B", "P", 3),
            ("A1", "A", 4),
            ("B1", "B", 5),
        ],
        start=1,
    ):
        root = spec.Root(index.to_bytes(32, "little"))
        block = spec.BeaconBlock(
            slot=slot, parent_root=nodes[parent].root if parent else spec.Root()
        )
        # Children build on EMPTY. Payloads are absent unless a test adds one.
        block.body.signed_execution_payload_bid.message.block_hash = root
        blocks[root] = block
        states[root] = spec.BeaconState(slot=11)
        nodes[name] = spec.ForkChoiceNode(root=root, payload_status=spec.PAYLOAD_STATUS_EMPTY)
    finalized = spec.HeightCheckpoint(height=0, root=nodes["F"].root)
    store = spec.Store(
        time_ms=at_slot(spec, 11) + spec.get_support_cutoff_ms(),
        genesis_time_ms=spec.Uint64(0),
        justified_checkpoint=finalized,
        finalized_checkpoint=finalized,
        proposer_boost_root=spec.Root(),
        blocks=blocks,
        block_states=states,
        latest_messages={},
        payloads={},
        payload_timeliness_vote={},
        payload_data_availability_vote={},
        max_height=spec.Height(0),
        block_receipt_times=dict.fromkeys(blocks, spec.Uint64(0)),
        payload_receipt_times={},
        latest_confirmed=spec.ForkChoiceNode(
            root=nodes["F"].root, payload_status=spec.PAYLOAD_STATUS_PENDING
        ),
        saved_confirmations={},
        locks=set(),
        head_vote_messages={},
        head_vote_message_receipt_times={},
        head_vote_committees={},
    )
    return store, nodes


def lock(spec, node, slot=9, fast=True, expiry=13):
    return spec.ACLock(node=node, slot=spec.Slot(slot), fast=fast, expiry_slot=spec.Slot(expiry))


def vote(spec, store, node, validator, slot=10, received=None):
    message = spec.HeadVoteMessage(
        validator_index=validator,
        data=spec.HeadVoteData(
            slot=slot, beacon_block_root=node.root, payload_status=node.payload_status
        ),
    )
    store.head_vote_messages.setdefault(spec.Slot(slot), []).append(message)
    store.head_vote_message_receipt_times[spec.hash_tree_root(message)] = (
        at_slot(spec, slot) if received is None else received
    )
    store.head_vote_committees.setdefault(
        spec.Slot(slot), spec.HeadVoteCommittee(data=list(range(spec.HEAD_VOTE_COMMITTEE_SIZE)))
    )


def vote_half(spec, store, node, slot=10):
    for validator in range(spec.HEAD_VOTE_COMMITTEE_SIZE // 2):
        vote(spec, store, node, validator, slot)


def test_fast_expiry_grows_and_is_capped(spec, tree):
    store, nodes = tree
    expiries = []
    for slot in range(10, 43):
        store.time_ms = at_slot(spec, slot + 1) + spec.get_support_cutoff_ms()
        vote(spec, store, nodes["A"], 0, slot=slot)
        half = spec.HEAD_VOTE_COMMITTEE_SIZE // 2
        store.head_vote_committees[slot] = spec.HeadVoteCommittee(data=[0] * half + [1] * half)
        spec.update_confirmation(store, spec.Slot(slot))
        current = [item for item in store.locks if item.slot == slot and item.fast]
        assert len(current) == 1
        expiries.append(int(current[0].expiry_slot))
    assert expiries == list(range(12, 73, 2)) + [73, 74]


def test_fast_expiry_paper_example_and_gap(spec, tree, monkeypatch):
    store, nodes = tree
    monkeypatch.setattr(spec, "SLOW_LOCK_WINDOW", spec.Slot(6))
    expiries = []
    for slot in [10, 11, 12, 13, 14, 16]:
        store.time_ms = at_slot(spec, slot + 1) + spec.get_support_cutoff_ms()
        vote_half(spec, store, nodes["A"], slot=slot)
        spec.update_confirmation(store, spec.Slot(slot))
        current = [item for item in store.locks if item.slot == slot and item.fast]
        assert len(current) == 1
        expiries.append(int(current[0].expiry_slot))
    assert expiries == [12, 14, 16, 18, 20, 22]


@pytest.mark.parametrize("kind", ["slow", "same_slot", "newer_slot", "expired", "outside_frame"])
def test_fast_expiry_ignores_ineligible_locks(spec, tree, kind):
    store, nodes = tree
    existing = lock(spec, nodes["A"])
    if kind == "slow":
        existing = replace(existing, fast=False)
    elif kind == "same_slot":
        existing = replace(existing, slot=spec.Slot(10))
    elif kind == "newer_slot":
        existing = replace(existing, slot=spec.Slot(11))
    elif kind == "expired":
        existing = replace(existing, expiry_slot=spec.Slot(10))
    else:
        existing = replace(existing, node=replace(nodes["A"], root=spec.Root(b"\xff" * 32)))
    store.locks = {existing}
    assert (
        spec.compute_fast_lock_expiry(
            spec.get_live_locks(store, spec.get_fg_frame(store), store.time_ms), spec.Slot(10)
        )
        == 12
    )


def test_fast_expiry_counts_lock_moved_to_finalized(spec, tree):
    store, _ = tree
    frame = spec.get_fg_frame(store)
    store.locks = {lock(spec, frame.finalized_node, expiry=12)}
    assert (
        spec.compute_fast_lock_expiry(
            spec.get_live_locks(store, frame, store.time_ms), spec.Slot(10)
        )
        == 14
    )


def test_fast_and_slow_locks_with_same_node_and_expiry(spec, tree, monkeypatch):
    monkeypatch.setattr(spec, "SLOW_LOCK_WINDOW", spec.Slot(4))
    store, nodes = tree
    store.saved_confirmations = dict.fromkeys(range(7, 10), nodes["A"])
    store.locks = {lock(spec, nodes["A"], expiry=12)}
    vote_half(spec, store, nodes["A"])
    spec.update_confirmation(store, spec.Slot(10))
    new = {item for item in store.locks if item.slot == 10}
    assert new == {
        lock(spec, nodes["A"], slot=10, fast=True, expiry=14),
        lock(spec, nodes["A"], slot=10, fast=False, expiry=14),
    }
    assert store.latest_confirmed == nodes["A"]


def test_fast_and_slow_locks_can_have_different_nodes(spec, tree, monkeypatch):
    monkeypatch.setattr(spec, "SLOW_LOCK_WINDOW", spec.Slot(4))
    store, nodes = tree
    store.saved_confirmations = dict.fromkeys(range(7, 10), nodes["P"])
    vote_half(spec, store, nodes["A"])
    spec.update_confirmation(store, spec.Slot(10))
    assert store.locks == {
        lock(spec, nodes["A"], slot=10, fast=True, expiry=12),
        lock(spec, nodes["P"], slot=10, fast=False, expiry=14),
    }


def test_veto_records_candidate_and_locks_shared_ancestor(spec, tree, monkeypatch):
    monkeypatch.setattr(spec, "SLOW_LOCK_WINDOW", spec.Slot(4))
    store, nodes = tree
    store.latest_confirmed = nodes["A"]
    existing = lock(spec, nodes["A"])
    store.locks = {existing}
    store.saved_confirmations = dict.fromkeys(range(7, 10), nodes["B"])
    vote_half(spec, store, nodes["B"])
    spec.update_confirmation(store, spec.Slot(10))
    assert store.saved_confirmations[10] == nodes["B"]
    assert store.latest_confirmed == nodes["A"]
    assert store.locks == {
        existing,
        lock(spec, nodes["P"], slot=10, fast=True, expiry=14),
        lock(spec, nodes["P"], slot=10, fast=False, expiry=14),
    }


@pytest.mark.parametrize("missing", ["absent", "removed"])
def test_missing_candidate_breaks_slow_streak(spec, tree, missing):
    store, nodes = tree
    store.saved_confirmations = dict.fromkeys(range(10, 41), nodes["A"])
    assert (
        spec.compute_slow_lock(store, spec.get_fg_frame(store), set(), spec.Slot(41), nodes["A"])
        == nodes["A"]
    )
    if missing == "absent":
        del store.saved_confirmations[10]
    else:
        store.saved_confirmations[10] = replace(nodes["A"], root=spec.Root(b"\xff" * 32))
    assert (
        spec.compute_slow_lock(store, spec.get_fg_frame(store), set(), spec.Slot(41), nodes["A"])
        is None
    )


def test_no_candidate_clears_saved_slot(spec, tree):
    store, nodes = tree
    store.saved_confirmations[10] = nodes["A"]
    store.head_vote_committees[10] = spec.HeadVoteCommittee(
        data=list(range(spec.HEAD_VOTE_COMMITTEE_SIZE))
    )
    spec.update_confirmation(store, spec.Slot(10))
    assert 10 not in store.saved_confirmations


def test_expiry_at_slot_start(spec, tree):
    store, nodes = tree
    store.locks = {lock(spec, nodes["A"], expiry=12)}
    frame = spec.get_fg_frame(store)
    assert len(spec.get_live_locks(store, frame, at_slot(spec, 13) - 1)) == 1
    assert not spec.get_live_locks(store, frame, at_slot(spec, 13))
    assert not spec.get_live_locks(store, frame, at_slot(spec, 13) + spec.get_head_vote_due_ms())


def test_live_locks_move_to_viable_ancestor_and_stay_there(spec, tree):
    store, nodes = tree
    original = lock(spec, nodes["A"])
    store.locks = {original}
    full_frame = spec.get_fg_frame(store)
    frame = replace(full_frame, viable_heads={nodes["B"]})
    moved = replace(original, node=nodes["P"])
    assert spec.get_live_locks(store, frame, store.time_ms) == {moved}
    assert spec.get_head_walk_anchor(store, frame) == nodes["P"]
    assert not spec.conflicts_with_lock(
        store, spec.get_live_locks(store, frame, store.time_ms), nodes["B"]
    )
    # Even an empty lock update must store the moved node.
    spec.add_locks(store, frame, set())
    assert spec.get_live_locks(store, full_frame, store.time_ms) == {moved}


def test_anchor_uses_frame_root_when_lock_is_its_ancestor(spec, tree):
    store, nodes = tree
    store.locks = {lock(spec, nodes["P"])}
    frame = replace(
        spec.get_fg_frame(store), forkchoice_root=nodes["A"], viable_heads={nodes["A1"]}
    )
    assert spec.get_head_walk_anchor(store, frame) == nodes["A"]
    assert not spec.conflicts_with_lock(
        store, spec.get_live_locks(store, frame, store.time_ms), nodes["A1"]
    )


def test_unlock_half_moves_to_common_ancestor_preserving_fields(spec, tree):
    store, nodes = tree
    original = lock(spec, nodes["A"], fast=False)
    store.locks = {original}
    vote_half(spec, store, nodes["B"])
    spec.unlock(
        store,
        spec.Slot(10),
        *spec.get_combined_local_view(
            store, spec.Slot(10), spec.INFINITE_TIME_MS, spec.INFINITE_TIME_MS
        ),
    )
    assert store.locks == {replace(original, node=nodes["P"])}


def test_unlock_below_half_keeps_lock(spec, tree):
    store, nodes = tree
    original = lock(spec, nodes["A"])
    store.locks = {original}
    for validator in range(spec.HEAD_VOTE_COMMITTEE_SIZE // 2 - 1):
        vote(spec, store, nodes["B"], validator)
    spec.unlock(
        store,
        spec.Slot(10),
        *spec.get_combined_local_view(
            store, spec.Slot(10), spec.INFINITE_TIME_MS, spec.INFINITE_TIME_MS
        ),
    )
    assert store.locks == {original}


@pytest.mark.parametrize("lock_slot", [10, 11])
def test_unlock_does_not_move_same_or_newer_slot_lock(spec, tree, lock_slot):
    store, nodes = tree
    original = lock(spec, nodes["A"], slot=lock_slot)
    store.locks = {original}
    vote_half(spec, store, nodes["B"])
    spec.unlock(
        store,
        spec.Slot(10),
        *spec.get_combined_local_view(
            store, spec.Slot(10), spec.INFINITE_TIME_MS, spec.INFINITE_TIME_MS
        ),
    )
    assert store.locks == {original}


def test_unlock_equivocators_count_without_resolved_votes(spec, tree):
    store, nodes = tree
    original = lock(spec, nodes["A"])
    store.locks = {original}
    unknown_a = replace(nodes["A"], root=spec.Root(b"\xfe" * 32))
    unknown_b = replace(nodes["B"], root=spec.Root(b"\xff" * 32))
    for validator in range(spec.HEAD_VOTE_COMMITTEE_SIZE // 2):
        vote(spec, store, unknown_a, validator)
        vote(spec, store, unknown_b, validator)
    spec.unlock(
        store,
        spec.Slot(10),
        *spec.get_combined_local_view(
            store, spec.Slot(10), spec.INFINITE_TIME_MS, spec.INFINITE_TIME_MS
        ),
    )
    # Half equivocating opposes every ancestor, including F. Use the explicit F fallback.
    assert store.locks == {replace(original, node=spec.get_fg_frame(store).finalized_node)}


def test_unlock_equivocator_not_counted_twice(spec, tree):
    store, nodes = tree
    original = lock(spec, nodes["A"])
    store.locks = {original}
    # One equivocator plus half-minus-two clean opponents is still below half.
    vote(spec, store, nodes["A"], 0)
    vote(spec, store, nodes["B"], 0)
    for validator in range(1, spec.HEAD_VOTE_COMMITTEE_SIZE // 2 - 1):
        vote(spec, store, nodes["B"], validator)
    spec.unlock(
        store,
        spec.Slot(10),
        *spec.get_combined_local_view(
            store, spec.Slot(10), spec.INFINITE_TIME_MS, spec.INFINITE_TIME_MS
        ),
    )
    assert store.locks == {original}


def test_unlock_counts_duplicate_committee_seats(spec, tree):
    store, nodes = tree
    original = lock(spec, nodes["A"])
    store.locks = {original}
    vote(spec, store, nodes["B"], 0)
    half = spec.HEAD_VOTE_COMMITTEE_SIZE // 2
    store.head_vote_committees[10] = spec.HeadVoteCommittee(data=[0] * half + [1] * half)
    spec.unlock(
        store,
        spec.Slot(10),
        *spec.get_combined_local_view(
            store, spec.Slot(10), spec.INFINITE_TIME_MS, spec.INFINITE_TIME_MS
        ),
    )
    assert store.locks == {replace(original, node=nodes["P"])}


def test_unlock_full_empty_conflict_moves_to_pending(spec, tree):
    store, nodes = tree
    original = lock(spec, nodes["A"])
    store.locks = {original}
    store.payloads[nodes["A"].root] = spec.ExecutionPayloadEnvelope()
    store.payload_receipt_times[nodes["A"].root] = spec.Uint64(0)
    full = replace(nodes["A"], payload_status=spec.PAYLOAD_STATUS_FULL)
    vote_half(spec, store, full)
    spec.unlock(
        store,
        spec.Slot(10),
        *spec.get_combined_local_view(
            store, spec.Slot(10), spec.INFINITE_TIME_MS, spec.INFINITE_TIME_MS
        ),
    )
    pending = replace(nodes["A"], payload_status=spec.PAYLOAD_STATUS_PENDING)
    assert store.locks == {replace(original, node=pending)}


def test_unlock_removes_expired_locks(spec, tree):
    store, nodes = tree
    store.locks = {lock(spec, nodes["A"], expiry=10)}
    spec.unlock(
        store,
        spec.Slot(10),
        *spec.get_combined_local_view(
            store, spec.Slot(10), spec.INFINITE_TIME_MS, spec.INFINITE_TIME_MS
        ),
    )
    assert not store.locks


def test_confirmation_tick_uses_current_time_for_lock_expiry(spec, tree):
    store, nodes = tree
    store.latest_confirmed = nodes["A"]
    store.locks = {lock(spec, nodes["A"], slot=8, expiry=10)}
    store.time_ms = at_slot(spec, 11) - 1
    vote_half(spec, store, nodes["B"])
    tick_time = at_slot(spec, 11) + spec.get_support_cutoff_ms()
    spec.on_tick(store, tick_time)
    assert store.time_ms == tick_time
    assert store.latest_confirmed == nodes["B"]
    assert store.locks == {lock(spec, nodes["B"], slot=10, expiry=12)}


def test_equivocators_do_not_supply_fast_lock_support(spec, tree):
    store, nodes = tree
    vote(spec, store, nodes["A"], 0)
    vote(spec, store, nodes["B"], 0)
    for validator in range(1, spec.HEAD_VOTE_COMMITTEE_SIZE // 2):
        vote(spec, store, nodes["A"], validator)
    spec.update_confirmation(store, spec.Slot(10))
    # The clean votes exceed half of participation, but are below half of the committee.
    assert store.latest_confirmed == nodes["A"]
    assert not store.locks


@pytest.mark.parametrize(
    ("confirmed_name", "head_name", "expected_name"),
    [("A1", "A", "A"), ("A", "A1", "A"), ("A1", "B1", "P")],
)
def test_confirmed_tip_common_ancestor(spec, tree, confirmed_name, head_name, expected_name):
    store, nodes = tree
    store.latest_confirmed = nodes[confirmed_name]
    vote_half(spec, store, nodes[head_name], slot=11)
    assert spec.get_head(store) == nodes[head_name]
    assert spec.get_confirmed_node(store) == nodes[expected_name]
    assert store.latest_confirmed == nodes[confirmed_name]


@pytest.mark.parametrize(
    ("confirmed_status", "head_status"),
    [("FULL", "EMPTY"), ("EMPTY", "FULL"), ("PENDING", "FULL")],
)
def test_confirmed_tip_payload_status(spec, tree, confirmed_status, head_status):
    store, nodes = tree
    store.payloads[nodes["A"].root] = spec.ExecutionPayloadEnvelope()
    store.payload_receipt_times[nodes["A"].root] = spec.Uint64(0)
    store.latest_confirmed = replace(
        nodes["A"], payload_status=getattr(spec, f"PAYLOAD_STATUS_{confirmed_status}")
    )
    head = replace(nodes["A"], payload_status=getattr(spec, f"PAYLOAD_STATUS_{head_status}"))
    vote_half(spec, store, head, slot=11)
    assert spec.get_head(store) == head
    assert spec.get_confirmed_node(store) == replace(
        nodes["A"], payload_status=spec.PAYLOAD_STATUS_PENDING
    )


def test_confirmed_tip_outside_frame(spec, tree):
    store, nodes = tree
    store.latest_confirmed = replace(nodes["A"], root=spec.Root(b"\xff" * 32))
    vote_half(spec, store, nodes["B1"], slot=11)
    assert spec.get_head(store) == nodes["B1"]
    assert spec.get_confirmed_node(store) == spec.get_fg_frame(store).finalized_node


@pytest.mark.parametrize("receipt_offset", [-1, 0, 1])
@pytest.mark.parametrize("with_payload", [False, True])
def test_ac_vote_head_viable_tree_fallback(spec, tree, receipt_offset, with_payload):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11) + spec.get_head_vote_due_ms()
    freeze = at_slot(spec, 10) + spec.get_view_freeze_ms()
    store.max_height = spec.Height(2)
    # Only the two leaves pass the height floor.
    for name in ["A1", "B1"]:
        store.block_states[nodes[name].root].target_checkpoint.height = spec.Height(2)
    store.block_receipt_times[nodes["A1"].root] = freeze + receipt_offset
    store.block_receipt_times[nodes["B1"].root] = freeze
    if with_payload:
        for name in ["A1", "B1"]:
            store.payloads[nodes[name].root] = spec.ExecutionPayloadEnvelope()
            store.payload_receipt_times[nodes[name].root] = spec.Uint64(0)

    frame = spec.get_fg_frame(store)
    restricted = spec.get_voter_subtree(store, frame.tree, spec.Slot(11))
    # The restricted tree is nonempty even when none of its nodes is viable.
    assert restricted
    assert bool(spec.get_viable_subtree(store, frame, restricted)) == (receipt_offset < 0)
    expected = nodes["A1"] if receipt_offset < 0 else nodes["B1"]
    if with_payload:
        expected = replace(expected, payload_status=spec.PAYLOAD_STATUS_FULL)
    assert spec.get_ac_vote_head(store) == expected


def test_ac_vote_head_keeps_payload_restriction(spec, tree):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11) + spec.get_head_vote_due_ms()
    freeze = at_slot(spec, 10) + spec.get_view_freeze_ms()
    store.max_height = spec.Height(2)
    store.block_states[nodes["A1"].root].target_checkpoint.height = spec.Height(2)
    store.payloads[nodes["A1"].root] = spec.ExecutionPayloadEnvelope()
    store.payload_receipt_times[nodes["A1"].root] = freeze
    full = replace(nodes["A1"], payload_status=spec.PAYLOAD_STATUS_FULL)
    frame = spec.get_fg_frame(store)
    restricted = spec.get_voter_subtree(store, frame.tree, spec.Slot(11))
    assert full in frame.viable_heads
    assert full not in restricted
    assert nodes["A1"] in spec.get_viable_subtree(store, frame, restricted)
    assert spec.get_ac_vote_head(store) == nodes["A1"]


@pytest.mark.parametrize("proposal", [False, True])
def test_duty_unlock_uses_its_view(spec, tree, proposal):
    store, nodes = tree
    original = lock(spec, nodes["A"])
    store.locks = {original}
    late = at_slot(spec, 10) + spec.get_view_freeze_ms()
    for validator in range(spec.HEAD_VOTE_COMMITTEE_SIZE // 2):
        vote(spec, store, nodes["B"], validator, received=late)
    store.time_ms = at_slot(spec, 11)
    if proposal:
        head, _, _ = spec.get_ac_proposal(store)
        assert head == nodes["B"]
        assert store.locks == {replace(original, node=nodes["P"])}
    else:
        spec.on_tick(store, store.time_ms + spec.get_head_vote_due_ms())
        assert spec.get_ac_vote_head(store) == nodes["A"]
        assert store.locks == {original}


def test_voter_unlock_uses_proposer_support_once(spec, tree):
    store, nodes = tree
    original = lock(spec, nodes["A"])
    store.locks = {original}
    proposal = store.blocks[nodes["B1"].root]
    proposal.slot = spec.Slot(11)
    indices = list(range(spec.HEAD_VOTE_COMMITTEE_SIZE // 2))
    proposal.body.head_votes.append(
        spec.HeadVote(
            data=spec.HeadVoteData(
                slot=10, beacon_block_root=nodes["B"].root, payload_status=spec.PAYLOAD_STATUS_EMPTY
            ),
            voter_indices=spec.HeadVoteCommitteeIndices(data=indices),
        )
    )
    proposal.body.head_vote_support.append(True)
    store.head_vote_committees[10] = spec.HeadVoteCommittee(
        data=list(range(spec.HEAD_VOTE_COMMITTEE_SIZE))
    )
    state = store.block_states[nodes["B1"].root]
    epoch = spec.compute_epoch_at_slot(spec.Slot(10))
    offset = int(epoch - spec.get_current_epoch(state) + 1) * int(spec.SLOTS_PER_EPOCH)
    state.head_vote_committee_window[offset + 10 % spec.SLOTS_PER_EPOCH] = (
        store.head_vote_committees[10]
    )
    store.time_ms = at_slot(spec, 11)
    head = spec.get_ac_vote_head(store)
    assert head == replace(nodes["B1"], payload_status=spec.PAYLOAD_STATUS_PENDING)
    assert store.locks == {replace(original, node=nodes["P"])}
    # Subsequent evidence cannot change this slot's prepared vote or unlock again.
    proposal.body.head_votes[0].data.beacon_block_root = nodes["A"].root
    assert spec.get_ac_vote_head(store) == head
    assert store.locks == {replace(original, node=nodes["P"])}


def propose_votes(spec, store, nodes, votes):
    proposal = store.blocks[nodes["B1"].root]
    proposal.slot = spec.Slot(11)
    store.head_vote_committees[10] = spec.get_head_vote_committee(
        store.block_states[nodes["B1"].root], spec.Slot(10)
    )
    for node, voters, supported in votes:
        proposal.body.head_votes.append(
            spec.HeadVote(
                data=spec.HeadVoteData(
                    slot=10, beacon_block_root=node.root, payload_status=node.payload_status
                ),
                voter_indices=spec.HeadVoteCommitteeIndices(data=voters),
            )
        )
        proposal.body.head_vote_support.append(supported)


def merged_voters(spec, view):
    votes, support = spec.compute_merged_view(([], []), view)
    return {int(v.validator_index) for v in votes}, {int(v.validator_index) for v in support}


def test_proposer_support_needs_known_verified_head(spec, tree):
    store, nodes = tree
    unknown = spec.ForkChoiceNode(
        root=spec.Root(b"\x99" * 32), payload_status=spec.PAYLOAD_STATUS_EMPTY
    )
    full = replace(nodes["A"], payload_status=spec.PAYLOAD_STATUS_FULL)
    propose_votes(
        spec,
        store,
        nodes,
        [(unknown, [0, 1], True), (full, [2, 3], True), (nodes["B"], [4, 5], True)],
    )
    view = spec.get_proposer_view(store, spec.Slot(11), spec.Slot(10))
    assert merged_voters(spec, view) == ({0, 1, 2, 3, 4, 5}, {4, 5})
    # Verifying the payload lets the proposer's support count for the full vote
    store.payloads[nodes["A"].root] = spec.ExecutionPayloadEnvelope()
    view = spec.get_proposer_view(store, spec.Slot(11), spec.Slot(10))
    assert merged_voters(spec, view) == ({0, 1, 2, 3, 4, 5}, {2, 3, 4, 5})


def test_split_aggregate_unions_voters_and_keeps_set_support(spec, tree):
    store, nodes = tree
    propose_votes(
        spec, store, nodes, [(nodes["B"], [0, 1, 2], True), (nodes["B"], [3, 4, 5], False)]
    )
    view = spec.get_proposer_view(store, spec.Slot(11), spec.Slot(10))
    assert merged_voters(spec, view) == ({0, 1, 2, 3, 4, 5}, {0, 1, 2})


def test_proposer_support_follows_bits_when_both_resolve_locally(spec, tree):
    store, nodes = tree
    propose_votes(spec, store, nodes, [(nodes["A"], [0, 1], False), (nodes["B"], [2, 3], True)])
    proposer_view = spec.get_proposer_view(store, spec.Slot(11), spec.Slot(10))
    assert proposer_view[1] == [False, True]
    assert merged_voters(spec, proposer_view) == ({0, 1, 2, 3}, {2, 3})
    infinite = spec.INFINITE_TIME_MS
    local_view = spec.get_local_view_from_blocks(store, spec.Slot(10), infinite, infinite)
    assert local_view[1] == [True, True]
    assert merged_voters(spec, local_view) == ({0, 1, 2, 3}, {0, 1, 2, 3})


@pytest.mark.parametrize("offset", [0, 1])
def test_restart_waits_for_full_previous_slot(spec, tree, offset):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11)
    original = lock(spec, nodes["A"], expiry=12)
    store.locks = {original}
    store.latest_confirmed = nodes["A"]
    store.saved_confirmations[10] = nodes["B"]
    store.prepared_head_vote = (spec.Slot(10), nodes["B"])
    vote_half(spec, store, nodes["B"])
    restart = at_slot(spec, 11) + offset
    spec.on_ac_restart(store, restart)
    assert store.locks == {original}
    assert store.latest_confirmed == nodes["A"]
    assert not store.saved_confirmations
    assert not store.head_vote_messages
    assert store.prepared_head_vote is None
    assert set(store.block_receipt_times.values()) == {restart}
    assert spec.get_ac_proposal(store) is None
    assert spec.get_ac_vote_head(store) is None
    spec.on_tick(store, at_slot(spec, 11) + spec.get_support_cutoff_ms())
    assert spec.get_ac_frame(store) is None
    assert store.latest_confirmed == nodes["A"]
    spec.on_tick(store, at_slot(spec, 12) + spec.get_head_vote_due_ms())
    assert spec.is_ac_joined(store) == (offset == 0)
    assert (store.prepared_head_vote is not None) == (offset == 0)
    spec.on_tick(store, at_slot(spec, 13) + spec.get_head_vote_due_ms())
    assert spec.is_ac_joined(store)
    assert not store.locks


@pytest.mark.parametrize(
    ("age", "fast", "expiry", "expected"),
    [
        (2, True, 13, "A"),
        (3, True, 40, None),
        (1, False, 40, None),
        (1, True, 10, None),
    ],
)
def test_fg_source_requires_recent_live_fast_lock(spec, tree, age, fast, expiry, expected):
    store, nodes = tree
    store.locks = {lock(spec, nodes["A"], slot=11 - age, fast=fast, expiry=expiry)}
    spec.update_confirmation(store, spec.Slot(10))
    assert spec.get_ac_frame(store) == (nodes[expected] if expected else None)


def test_fg_source_uses_viable_lock_ancestor(spec, tree):
    store, nodes = tree
    store.locks = {lock(spec, nodes["A1"], slot=10)}
    store.max_height = spec.Height(2)
    store.block_states[nodes["B1"].root].target_checkpoint.height = spec.Height(2)
    assert spec.get_ac_frame(store) == nodes["P"]


@pytest.mark.parametrize("vote_slot", [10, 11])
def test_head_vote_admission_and_gossip_cap(spec, tree, monkeypatch, vote_slot):
    store, nodes = tree
    monkeypatch.setattr(spec, "config", spec.config._replace(PQ_FORK_EPOCH=0))
    for state in store.block_states.values():
        state.slot = spec.Slot(11)
        state.finalized_checkpoint = store.finalized_checkpoint.copy()
        state.validators.append(spec.Validator(pubkey=spec.xmss.SkToPk(1)))
    seen = SimpleNamespace(head_vote_validator_slots={})
    state = store.block_states[nodes["F"].root]
    messages = []
    for name in ["A", "B", "P"]:
        data = spec.HeadVoteData(
            slot=vote_slot,
            beacon_block_root=nodes[name].root,
            payload_status=spec.PAYLOAD_STATUS_EMPTY,
        )
        domain = spec.get_domain(
            state, spec.DOMAIN_HEAD_VOTE, spec.compute_epoch_at_slot(data.slot)
        )
        messages.append(
            spec.HeadVoteMessage(
                validator_index=0,
                data=data,
                signature=spec.xmss.Sign(
                    1,
                    spec.compute_xmss_leaf_index(data.slot, spec.LEAF_OFFSET_HEAD_VOTE),
                    spec.compute_signing_root(data, domain),
                ),
            )
        )
    invalid = messages[0].copy()
    invalid.signature = spec.XMSSSignature()
    with pytest.raises(spec.GossipReject):
        spec.validate_head_vote_gossip(seen, store, invalid, store.time_ms, {})
    with pytest.raises(AssertionError):
        spec.on_head_vote_message(store, invalid)
    assert not seen.head_vote_validator_slots
    assert not store.head_vote_messages
    if vote_slot == 11:
        store.time_ms = at_slot(spec, 11) - spec.config.MAXIMUM_GOSSIP_CLOCK_DISPARITY - 1
        with pytest.raises(spec.GossipIgnore):
            spec.validate_head_vote_gossip(seen, store, messages[0], store.time_ms, {})
        spec.on_head_vote_message(store, messages[0])
        assert not store.pending_head_votes
        store.time_ms += 1
        spec.validate_head_vote_gossip(seen, store, messages[0], store.time_ms, {})
        spec.on_head_vote_message(store, messages[0])
        assert [message for message, _ in store.pending_head_votes] == [messages[0]]
        assert not store.head_vote_messages
        # A changed head-state validation context cannot abort queued admission.
        for block_state in store.block_states.values():
            block_state.validators[0].pubkey = spec.xmss.SkToPk(2)
        spec.on_tick(store, at_slot(spec, 11))
        for block_state in store.block_states.values():
            block_state.validators[0].pubkey = spec.xmss.SkToPk(1)
        assert not store.pending_head_votes
        assert store.head_vote_messages[11] == [messages[0]]
        seen.head_vote_validator_slots = {}
    for message in messages[:2]:
        spec.validate_head_vote_gossip(seen, store, message, store.time_ms, {})
        spec.on_head_vote_message(store, message)
    receipt_times = dict(store.head_vote_message_receipt_times)
    for message in [messages[0], messages[2]]:
        with pytest.raises(spec.GossipIgnore):
            spec.validate_head_vote_gossip(seen, store, message, store.time_ms, {})
        spec.on_head_vote_message(store, message)
    assert store.head_vote_messages[vote_slot] == messages[:2]
    assert store.head_vote_message_receipt_times == receipt_times
    spec.on_tick(store, at_slot(spec, vote_slot + 2) + spec.config.MAXIMUM_GOSSIP_CLOCK_DISPARITY)
    assert not store.head_vote_messages
    assert not store.head_vote_message_receipt_times
    with pytest.raises(spec.GossipIgnore):
        spec.validate_head_vote_gossip(seen, store, messages[0], store.time_ms, {})
    assert not seen.head_vote_validator_slots


@pytest.mark.parametrize("payload_available", [False, True])
def test_responsive_vote_waits_for_support_payload(spec, tree, payload_available):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11)
    proposal = store.blocks[nodes["B1"].root]
    proposal.slot = spec.Slot(11)
    proposal.body.head_votes.append(
        spec.HeadVote(
            data=spec.HeadVoteData(
                slot=10, beacon_block_root=nodes["A"].root, payload_status=spec.PAYLOAD_STATUS_FULL
            ),
            voter_indices=spec.HeadVoteCommitteeIndices(data=[0]),
        )
    )
    proposal.body.head_vote_support.append(True)
    store.head_vote_committees[10] = spec.HeadVoteCommittee(
        data=[0] * spec.HEAD_VOTE_COMMITTEE_SIZE
    )
    assert spec.get_ac_vote_head(store) is None
    if payload_available:
        store.payloads[nodes["A"].root] = spec.ExecutionPayloadEnvelope()
        store.payload_receipt_times[nodes["A"].root] = store.time_ms
        early = spec.get_ac_vote_head(store)
        assert early is not None
    else:
        assert store.prepared_head_vote is None
        # One ready equivocation suffices even if its sibling is unready.
        store.blocks[nodes["A1"].root].slot = spec.Slot(11)
        assert spec.get_ac_vote_head(store) is not None
    spec.on_tick(store, at_slot(spec, 11) + spec.get_head_vote_due_ms())
    assert spec.get_ac_vote_head(store) is not None
    if payload_available:
        assert spec.get_ac_vote_head(store) == early


@pytest.mark.parametrize(
    ("supported", "matching"),
    [(False, False), (False, True), (True, False), (True, True), (True, None)],
)
def test_vote_readiness_waits_only_for_supported_heads(spec, tree, supported, matching):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11)
    unknown = spec.ForkChoiceNode(
        root=spec.Root(b"\x99" * 32), payload_status=spec.PAYLOAD_STATUS_EMPTY
    )
    propose_votes(spec, store, nodes, [(unknown, [0], supported)])
    # The proposal is by the proposer that the head chain expects
    for state in store.block_states.values():
        state.proposer_lookahead[11 % spec.SLOTS_PER_EPOCH] = 1
    store.blocks[nodes["B1"].root].proposer_index = 1
    if matching is None:
        del store.head_vote_committees[10]
    elif not matching:
        store.head_vote_committees[10] = spec.HeadVoteCommittee(
            data=[1] * spec.HEAD_VOTE_COMMITTEE_SIZE
        )
    ready = not (matching and supported)
    assert spec.is_ac_vote_ready(store) == ready
    assert (spec.get_ac_vote_head(store) is not None) == ready


def test_responsive_vote_deadline_and_duplicate_preparation(spec, tree):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11)
    assert spec.get_ac_vote_head(store) is None
    store.blocks[nodes["B1"].root].slot = spec.Slot(11)
    vote_half(spec, store, nodes["B"])
    expected = replace(nodes["B1"], payload_status=spec.PAYLOAD_STATUS_PENDING)
    assert spec.get_ac_vote_head(store) == expected
    store.time_ms += spec.get_head_vote_due_ms() + 1
    assert spec.get_ac_vote_head(store) == expected
    store.time_ms = at_slot(spec, 12) + spec.get_head_vote_due_ms() + 1
    assert spec.get_ac_vote_head(store) is None


@pytest.mark.parametrize(
    ("seat_offset", "cutoff_offset", "joined", "conflict", "expected"),
    [
        (0, -1, True, False, "A"),
        (-1, -1, True, False, "F"),
        (0, 0, True, False, "F"),
        (0, -1, False, False, "F"),
        (0, -1, True, True, "P"),
    ],
)
def test_optimistic_threshold_cutoff_and_veto(
    spec, tree, seat_offset, cutoff_offset, joined, conflict, expected
):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11) + spec.get_support_cutoff_ms() + cutoff_offset
    if not joined:
        store.restart_time_ms = at_slot(spec, 11)
    if conflict:
        store.locks = {lock(spec, nodes["B"], slot=10, expiry=15)}
    vote(spec, store, nodes["A"], 0, slot=11)
    seats = 3 * spec.HEAD_VOTE_COMMITTEE_SIZE // 4 + seat_offset
    store.head_vote_committees[11] = spec.HeadVoteCommittee(
        data=[0] * seats + [1] * (spec.HEAD_VOTE_COMMITTEE_SIZE - seats)
    )
    spec.update_optimistic_confirmation(store)
    confirmed = store.latest_confirmed
    assert confirmed.root == nodes[expected].root
    if expected != "F":
        expiry = 17 if conflict else 13
        assert lock(spec, nodes[expected], slot=11, expiry=expiry) in store.locks
        assert 11 not in store.saved_confirmations
        # Repeating the optimistic check does not extend same-slot expiry.
        spec.update_optimistic_confirmation(store)
        assert {item.expiry_slot for item in store.locks if item.slot == 11} == {expiry}
        store.time_ms = at_slot(spec, 11) + spec.get_support_cutoff_ms()
        assert spec.get_ac_frame(store) == nodes["B" if conflict else expected]


def test_optimistic_equivocator_counts_once_per_candidate(spec, tree):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11) + 1
    vote(spec, store, nodes["A"], 0, slot=11)
    vote(spec, store, nodes["B"], 0, slot=11)
    vote(spec, store, nodes["A"], 1, slot=11)
    quarter = spec.HEAD_VOTE_COMMITTEE_SIZE // 4
    store.head_vote_committees[11] = spec.HeadVoteCommittee(
        data=[0] * quarter + [1] * quarter + [2] * (2 * quarter)
    )
    spec.update_optimistic_confirmation(store)
    assert store.latest_confirmed.root == nodes["F"].root
    vote(spec, store, nodes["A"], 2, slot=11)
    spec.update_optimistic_confirmation(store)
    assert store.latest_confirmed == nodes["A"]
    assert lock(spec, nodes["A"], slot=11, expiry=13) in store.locks
    store.time_ms = at_slot(spec, 12) + spec.get_support_cutoff_ms()
    spec.update_confirmation(store, spec.Slot(11))
    assert store.saved_confirmations[11] == nodes["A"]
    assert spec.get_ac_frame(store) == nodes["A"]


def test_queued_vote_with_changed_slot_committee_does_not_abort_tick(spec, tree):
    store, nodes = tree
    message = spec.HeadVoteMessage(
        validator_index=0,
        data=spec.HeadVoteData(
            slot=12, beacon_block_root=nodes["A"].root, payload_status=spec.PAYLOAD_STATUS_EMPTY
        ),
    )
    store.pending_head_votes = [
        (message, spec.HeadVoteCommittee(data=[0] * spec.HEAD_VOTE_COMMITTEE_SIZE))
    ]
    store.head_vote_committees[12] = spec.HeadVoteCommittee(
        data=[1] * spec.HEAD_VOTE_COMMITTEE_SIZE
    )
    spec.on_tick(store, at_slot(spec, 12) + spec.get_head_vote_due_ms())
    assert not store.pending_head_votes
    assert 12 not in store.head_vote_messages
    assert store.prepared_head_vote[0] == 12
    assert list(store.head_vote_committees[12]) == [1] * spec.HEAD_VOTE_COMMITTEE_SIZE


def test_responsive_vote_requires_head_chain_proposer(spec, tree):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11)
    for state in store.block_states.values():
        state.proposer_lookahead[11 % spec.SLOTS_PER_EPOCH] = 1
    proposal = store.blocks[nodes["B1"].root]
    proposal.slot = spec.Slot(11)
    proposal.proposer_index = 2
    vote_half(spec, store, nodes["B"])
    assert not spec.is_ac_vote_ready(store)
    assert spec.get_ac_vote_head(store) is None
    proposal.proposer_index = 1
    assert spec.is_ac_vote_ready(store)
    assert spec.get_ac_vote_head(store) == replace(
        nodes["B1"], payload_status=spec.PAYLOAD_STATUS_PENDING
    )


@pytest.mark.parametrize("status", [0, 1, 2])
@pytest.mark.parametrize("in_frame", [False, True])
def test_readiness_matches_proposer_support(spec, tree, status, in_frame):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11)
    proposal = store.blocks[nodes["B1"].root]
    proposal.slot = spec.Slot(11)
    store.blocks[nodes["A"].root].slot = spec.Slot(10)
    # The support is for an off-branch block in the vote's own slot.
    store.blocks[nodes["A1"].root].slot = spec.Slot(11)
    store.blocks[nodes["A1"].root].proposer_index = 1
    store.payloads[nodes["A"].root] = spec.ExecutionPayloadEnvelope()
    # PQ has no inclusion lists; the payload has no PTC votes
    store.payload_timeliness_vote[nodes["A"].root] = [None] * spec.PTC_SIZE
    store.payload_data_availability_vote[nodes["A"].root] = [None] * spec.PTC_SIZE
    if not in_frame:
        store.finalized_checkpoint = spec.HeightCheckpoint(height=0, root=nodes["B"].root)
        store.justified_checkpoint = store.finalized_checkpoint.copy()
    proposal.body.head_votes.append(
        spec.HeadVote(
            data=spec.HeadVoteData(
                slot=10, beacon_block_root=nodes["A"].root, payload_status=status
            ),
            voter_indices=spec.HeadVoteCommitteeIndices(data=[0]),
        )
    )
    proposal.body.head_vote_support.append(True)
    store.head_vote_committees[10] = spec.HeadVoteCommittee(
        data=[0] * spec.HEAD_VOTE_COMMITTEE_SIZE
    )
    usable = in_frame and status == spec.PAYLOAD_STATUS_PENDING
    assert spec.is_ac_vote_ready(store) == usable
    _, support = spec.get_proposer_view(store, spec.Slot(11), spec.Slot(10))
    assert support == [usable]


def test_genesis_deadline_vote(spec, tree):
    store, nodes = tree
    store.blocks = {nodes["F"].root: store.blocks[nodes["F"].root]}
    store.time_ms = spec.get_head_vote_due_ms() - 1
    assert spec.get_ac_vote_head(store) is None
    spec.on_tick(store, spec.get_head_vote_due_ms())
    expected = replace(nodes["F"], payload_status=spec.PAYLOAD_STATUS_PENDING)
    assert store.prepared_head_vote == (spec.GENESIS_SLOT, expected)
    assert spec.get_ac_vote_head(store) == expected
    store.time_ms += 1
    assert spec.get_ac_vote_head(store) == expected


def test_head_vote_gossip_pulls_up_stale_head(spec, tree, monkeypatch):
    store, nodes = tree
    monkeypatch.setattr(spec, "config", spec.config._replace(PQ_FORK_EPOCH=0))
    eip8483 = import_module(f"eth_consensus_specs.eip8483.{context.DEFAULT_TEST_PRESET}")
    pre = create_genesis_state(
        eip8483, [eip8483.MIN_ACTIVATION_BALANCE] * 64, eip8483.MIN_ACTIVATION_BALANCE
    )
    state = upgrade_registered_to_pq(spec, pre)
    state.finalized_checkpoint = store.finalized_checkpoint.copy()
    store.block_states = {root: state.copy() for root in store.blocks}
    slot = spec.Slot(2 * spec.SLOTS_PER_EPOCH + 1)
    store.time_ms = at_slot(spec, slot)
    pulled = spec.get_pulled_up_state(store, spec.get_head(store).root)
    index = spec.get_head_vote_committee(pulled, slot)[0]
    data = spec.HeadVoteData(
        slot=slot, beacon_block_root=nodes["B1"].root, payload_status=spec.PAYLOAD_STATUS_EMPTY
    )
    domain = spec.get_domain(pulled, spec.DOMAIN_HEAD_VOTE, spec.compute_epoch_at_slot(slot))
    message = spec.HeadVoteMessage(
        validator_index=index,
        data=data,
        signature=spec.xmss.Sign(
            privkeys[index],
            spec.compute_xmss_leaf_index(data.slot, spec.LEAF_OFFSET_HEAD_VOTE),
            spec.compute_signing_root(data, domain),
        ),
    )
    seen = SimpleNamespace(head_vote_validator_slots={})
    spec.validate_head_vote_gossip(seen, store, message, store.time_ms, {})
    assert seen.head_vote_validator_slots[(slot, index)] == {spec.hash_tree_root(data)}
    spec.on_head_vote_message(store, message)
    assert store.head_vote_messages[slot] == [message]
    assert all(block_state.slot == 0 for block_state in store.block_states.values())


@pytest.mark.parametrize("matching", [False, True])
def test_block_committee_mismatch_excludes_votes_not_block(spec, tree, monkeypatch, matching):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11) + spec.get_head_vote_due_ms() + 1
    propose_votes(spec, store, nodes, [(nodes["B"], [0], True)])
    block = store.blocks.pop(nodes["B1"].root)
    if not matching:
        store.head_vote_committees[10] = spec.HeadVoteCommittee(
            data=[1] * spec.HEAD_VOTE_COMMITTEE_SIZE
        )
    expected_committee = store.head_vote_committees[10]
    # Isolate fork-choice admission from the already-validated state transition.
    monkeypatch.setattr(spec, "state_transition", lambda state, signed, validate_result: None)
    signed = spec.SignedBeaconBlock(message=block)
    spec.on_block(store, signed)
    assert spec.hash_tree_root(block) in store.blocks
    assert store.head_vote_committees[10] == expected_committee
    for view in (
        spec.get_proposer_view(store, spec.Slot(11), spec.Slot(10)),
        spec.get_local_view_from_blocks(
            store, spec.Slot(10), spec.INFINITE_TIME_MS, spec.INFINITE_TIME_MS
        ),
    ):
        assert len(view[0]) == int(matching)
        assert view[1] == ([True] if matching else [])


@pytest.mark.parametrize("status", [0, 1, 2])
def test_optimistic_confirmation_requires_resolved_support(spec, tree, status):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11) + 1
    store.blocks[nodes["A1"].root].slot = spec.Slot(11)
    store.payloads[nodes["A1"].root] = spec.ExecutionPayloadEnvelope()
    store.payload_receipt_times[nodes["A1"].root] = store.time_ms
    node = replace(nodes["A1"], payload_status=spec.PayloadStatus(status))
    vote(spec, store, node, 0, slot=11)
    store.head_vote_committees[11] = spec.HeadVoteCommittee(
        data=[0] * spec.HEAD_VOTE_COMMITTEE_SIZE
    )
    spec.update_optimistic_confirmation(store)
    if status == spec.PAYLOAD_STATUS_PENDING:
        assert store.latest_confirmed == node
    else:
        assert store.latest_confirmed.root == nodes["F"].root
        assert not store.locks


@pytest.mark.parametrize(("block_slot", "status"), [(11, 0), (11, 1), (11, 2), (4, 2), (4, 0)])
def test_receipt_enforces_vote_slot_payload_status(spec, tree, monkeypatch, block_slot, status):
    store, nodes = tree
    monkeypatch.setattr(spec, "config", spec.config._replace(PQ_FORK_EPOCH=0))
    store.time_ms = at_slot(spec, 11) + 1
    store.blocks[nodes["A1"].root].slot = spec.Slot(block_slot)
    for state in store.block_states.values():
        state.validators.append(spec.Validator(pubkey=spec.xmss.SkToPk(1)))
    data = spec.HeadVoteData(slot=11, beacon_block_root=nodes["A1"].root, payload_status=status)
    state = store.block_states[nodes["F"].root]
    domain = spec.get_domain(state, spec.DOMAIN_HEAD_VOTE, spec.compute_epoch_at_slot(data.slot))
    message = spec.HeadVoteMessage(
        validator_index=0,
        data=data,
        signature=spec.xmss.Sign(
            1,
            spec.compute_xmss_leaf_index(data.slot, spec.LEAF_OFFSET_HEAD_VOTE),
            spec.compute_signing_root(data, domain),
        ),
    )
    if (block_slot == 11) == (status == spec.PAYLOAD_STATUS_PENDING):
        spec.on_head_vote_message(store, message)
        assert store.head_vote_messages[11] == [message]
        assert store.latest_confirmed == replace(
            nodes["A1"], payload_status=spec.PayloadStatus(status)
        )
    else:
        with pytest.raises(AssertionError):
            spec.on_head_vote_message(store, message)
        assert not store.head_vote_messages
        assert not store.locks


@pytest.mark.parametrize("block_slot", [10, 11])
@pytest.mark.parametrize("status", [0, 1, 2])
@pytest.mark.parametrize("block_first", [False, True])
def test_vote_resolution_enforces_status_in_both_arrival_orders(
    spec, tree, block_slot, status, block_first
):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11) + 1
    root = nodes["A1"].root
    store.blocks[root].slot = spec.Slot(block_slot)
    store.payloads[root] = spec.ExecutionPayloadEnvelope()
    store.payload_receipt_times[root] = store.time_ms
    for state in store.block_states.values():
        state.validators.append(spec.Validator(pubkey=spec.xmss.SkToPk(1)))
    data = spec.HeadVoteData(slot=11, beacon_block_root=root, payload_status=status)
    state = store.block_states[nodes["F"].root]
    message = spec.HeadVoteMessage(
        validator_index=0,
        data=data,
        signature=spec.get_head_vote_signature(state, data, 1),
    )
    valid = (block_slot == 11) == (status == spec.PAYLOAD_STATUS_PENDING)
    if not block_first:
        block = store.blocks.pop(root)
    if block_first and not valid:
        with pytest.raises(AssertionError):
            spec.on_head_vote_message(store, message)
    else:
        spec.on_head_vote_message(store, message)
    if not block_first:
        assert (
            spec.get_local_view_from_p2p_messages(
                store, spec.Slot(11), spec.INFINITE_TIME_MS, spec.INFINITE_TIME_MS
            )[1]
            == []
        )
        store.blocks[root] = block
        store.block_receipt_times[root] = store.time_ms + 1
    view = spec.get_local_view_from_p2p_messages(
        store, spec.Slot(11), spec.INFINITE_TIME_MS, spec.INFINITE_TIME_MS
    )
    assert view[1] == ([0] if valid else [])
    tree_nodes = spec.get_fg_frame(store).tree
    assert spec.is_usable_proposer_support(store, tree_nodes, data) == valid
    spec.update_optimistic_confirmation(store)
    assert (store.latest_confirmed.root == root) == valid


def test_optimistic_payload_tie_uses_lowest_status(spec, tree):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11) + 1
    store.payloads[nodes["A"].root] = spec.ExecutionPayloadEnvelope()
    store.payload_receipt_times[nodes["A"].root] = store.time_ms
    for status in (spec.PAYLOAD_STATUS_FULL, spec.PAYLOAD_STATUS_EMPTY):
        vote(spec, store, replace(nodes["A"], payload_status=status), 0, slot=11)
    store.head_vote_committees[11] = spec.HeadVoteCommittee(
        data=[0] * spec.HEAD_VOTE_COMMITTEE_SIZE
    )
    spec.update_optimistic_confirmation(store)
    assert store.latest_confirmed == nodes["A"]


@pytest.mark.parametrize("root_byte", [7, 8, 9, 10])
def test_optimistic_equal_rank_uses_lowest_root(spec, tree, root_byte):
    store, nodes = tree
    store.time_ms = at_slot(spec, 11) + 1
    original = nodes["B1"].root
    root = spec.Root(bytes([root_byte]) * 32)
    for mapping in (store.blocks, store.block_states, store.block_receipt_times):
        mapping[root] = mapping.pop(original)
    node_b = replace(nodes["B1"], root=root)
    store.blocks[root].slot = store.blocks[nodes["A1"].root].slot
    for node in (nodes["A1"], node_b):
        vote(spec, store, node, 0, slot=11)
    store.head_vote_committees[11] = spec.HeadVoteCommittee(
        data=[0] * spec.HEAD_VOTE_COMMITTEE_SIZE
    )
    spec.update_optimistic_confirmation(store)
    assert store.latest_confirmed == nodes["A1"]


def test_slow_lock_does_not_require_fast_threshold(spec, tree):
    store, nodes = tree
    store.saved_confirmations = dict.fromkeys(range(10, 41), nodes["A"])
    store.time_ms = at_slot(spec, 42) + spec.get_support_cutoff_ms()
    vote(spec, store, nodes["A"], 0, slot=41)
    spec.update_confirmation(store, spec.Slot(41))
    assert store.locks == {lock(spec, nodes["A"], slot=41, fast=False, expiry=73)}
