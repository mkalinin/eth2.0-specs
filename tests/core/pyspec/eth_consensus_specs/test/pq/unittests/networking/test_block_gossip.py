"""Gossip validation of EIP-8453 beacon blocks."""

from dataclasses import fields
from importlib import import_module
from typing import get_origin

import pytest

from eth_consensus_specs.test import context
from eth_consensus_specs.test.helpers.genesis import create_genesis_state
from eth_consensus_specs.test.helpers.keys import privkeys, xmss_pubkeys
from eth_consensus_specs.test.helpers.pq.fork import upgrade_registered_to_pq

pytestmark = pytest.mark.usefixtures("fake_xmss")


@pytest.fixture
def spec(preset, monkeypatch):
    spec = import_module(f"eth_consensus_specs.pq.{context.DEFAULT_TEST_PRESET}")
    monkeypatch.setattr(spec, "config", spec.config._replace(PQ_FORK_EPOCH=spec.Epoch(0)))
    return spec


def test_proposer_signature_uses_parent_branch_registry(spec, monkeypatch):
    eip8483 = import_module(f"eth_consensus_specs.eip8483.{context.DEFAULT_TEST_PRESET}")
    balances = [eip8483.MAX_EFFECTIVE_BALANCE] * 64
    parent_state = upgrade_registered_to_pq(
        spec, create_genesis_state(eip8483, balances, eip8483.MAX_EFFECTIVE_BALANCE)
    )
    spec.process_slots(parent_state, spec.Slot(1))

    finalized = parent_state.finalized_checkpoint.root
    parent = spec.BeaconBlock(slot=1, parent_root=finalized)
    parent.body.signed_execution_payload_bid.message.block_hash = spec.Hash32(b"\x09" * 32)
    parent_root = parent.hash_tree_root()

    advanced = parent_state.copy()
    spec.process_slots(advanced, spec.Slot(2))
    proposer = spec.get_beacon_proposer_index(advanced)
    block = spec.BeaconBlock(slot=2, proposer_index=proposer, parent_root=parent_root)
    bid = block.body.signed_execution_payload_bid.message
    bid.parent_block_root = parent_root
    bid.parent_block_hash = advanced.latest_block_hash
    domain = spec.get_domain(advanced, spec.DOMAIN_BEACON_PROPOSER, spec.Epoch(0))
    signed = spec.SignedBeaconBlock(
        message=block,
        signature=spec.xmss.Sign(
            privkeys[proposer],
            spec.compute_xmss_leaf_index(block.slot, spec.LEAF_OFFSET_BEACON_PROPOSER),
            spec.compute_signing_root(block, domain),
        ),
    )

    # The head is on a sibling branch whose registry has another key at the
    # proposer's index
    head_state = parent_state.copy()
    head_state.validators[proposer].pubkey = xmss_pubkeys[(proposer + 1) % len(balances)]
    head_root = spec.Root(b"\x07" * 32)
    blocks = {
        finalized: spec.BeaconBlock(slot=0),
        parent_root: parent,
        head_root: spec.BeaconBlock(slot=1, parent_root=finalized),
    }
    states = {parent_root: parent_state, head_root: head_state}
    store = spec.Store(
        time_ms=spec.Uint64(0),
        genesis_time_ms=spec.Uint64(0),
        justified_checkpoint=spec.HeightCheckpoint(),
        finalized_checkpoint=spec.HeightCheckpoint(),
        proposer_boost_root=spec.Root(),
        blocks=blocks,
        block_states=states,
        latest_messages={},
        payloads={},
        payload_timeliness_vote={},
        payload_data_availability_vote={},
        max_height=spec.Height(0),
        block_receipt_times={},
        payload_receipt_times={},
        latest_confirmed=spec.ForkChoiceNode(
            root=head_root, payload_status=spec.PAYLOAD_STATUS_PENDING
        ),
        saved_confirmations={},
        locks=set(),
        head_vote_messages={},
        head_vote_message_receipt_times={},
        head_vote_committees={},
    )
    head = spec.ForkChoiceNode(root=head_root, payload_status=spec.PAYLOAD_STATUS_EMPTY)
    monkeypatch.setattr(spec, "get_head", lambda _store: head)
    seen = spec.Seen(
        **{field.name: (get_origin(field.type) or field.type)() for field in fields(spec.Seen)}
    )
    time_ms = spec.compute_time_at_slot_ms(spec.Uint64(0), spec.Slot(2))
    spec.validate_beacon_block_gossip(seen, store, signed, time_ms)
    assert (block.slot, proposer) in seen.proposer_slots
