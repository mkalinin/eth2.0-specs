import random

from eth_utils import encode_hex
from eth2spec.test.context import MINIMAL, spec_state_test, with_altair_and_later, with_presets
from eth2spec.test.helpers.attestations import (
    get_valid_attestations_for_block_at_slot,
)
from eth2spec.test.helpers.block import (
    build_empty_block_for_next_slot,
)
from eth2spec.test.helpers.fork_choice import (
    add_block,
    get_genesis_forkchoice_store_and_block,
    on_tick_and_append_step,
    add_attestations,
)
from eth2spec.test.helpers.state import (
    payload_state_transition,
    state_transition_and_sign_block,
)
from eth2spec.utils.ssz.ssz_impl import hash_tree_root


def on_slot_after_attestations_applied_and_append_step(spec, store, test_steps):
    spec.on_slot_after_attestations_applied(store)
    test_steps.append({"slot_after_attestations_applied": spec.get_current_slot(store)})
    checks = {
        "time": int(store.time),
        "prev_epoch_unrealized_justified_checkpoint": {
            "epoch": int(store.prev_epoch_unrealized_justified_checkpoint.epoch),
            "root": encode_hex(store.prev_epoch_unrealized_justified_checkpoint.root),
        },
        "prev_slot_head": encode_hex(store.prev_slot_head),
        "confirmed_root": encode_hex(store.confirmed_root),
    }

    test_steps.append({"checks": checks})


@with_altair_and_later
@spec_state_test
@with_presets([MINIMAL], reason="too slow")
def test_fast_confirm_an_epoch(spec, state):
    test_steps = []
    # Initialization
    store, anchor_block = get_genesis_forkchoice_store_and_block(spec, state)
    yield "anchor_state", state
    yield "anchor_block", anchor_block

    current_time = state.slot * spec.config.SECONDS_PER_SLOT + store.genesis_time
    on_tick_and_append_step(spec, store, current_time, test_steps)

    # run for each slot of the first epoch
    for slot in range(spec.GENESIS_SLOT, spec.SLOTS_PER_EPOCH):
        # build and sign a block
        if slot > spec.GENESIS_SLOT:
            block = build_empty_block_for_next_slot(spec, state)
            for attestation in attestations:
                block.body.attestations.append(attestation)
            signed_block = state_transition_and_sign_block(spec, state, block)
            yield from add_block(spec, store, signed_block, test_steps)
            payload_state_transition(spec, store, signed_block.message)
        else:
            block = anchor_block

        # attest and keep attestations for onchain inclusion
        attestations = get_valid_attestations_for_block_at_slot(
            spec, state, state.slot, spec.get_head(store)
        )

        # move to the next slot
        current_time = (slot + 1) * spec.config.SECONDS_PER_SLOT + store.genesis_time
        on_tick_and_append_step(spec, store, current_time, test_steps)

        # apply attestations and run FCR
        yield from add_attestations(spec, store, attestations, test_steps)
        on_slot_after_attestations_applied_and_append_step(spec, store, test_steps)

        assert store.confirmed_root == block.hash_tree_root()

    yield "steps", test_steps
