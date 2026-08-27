from dataclasses import dataclass, replace

from .preset import SLOTS_PER_HISTORICAL_ROOT
from .type import (
    Bitlist,
    EMPTY_ROOT,
    Gwei,
    Height,
    Root,
    Signature,
    Slot,
    ValidatorIndex,
)
from .vote import AvailableChainVote


@dataclass
class Attestation: ...


@dataclass
class AttesterSlashing: ...


@dataclass
class Validator:
    effective_balance: Gwei


@dataclass
class Checkpoint:
    root: Root
    height: Height


@dataclass
class BeaconBlockHeader:
    slot: Slot
    state_root: Root
    body_root: Root

    def update(self, **kv):
        return replace(self, **kv)


@dataclass(frozen=True)
class BeaconState:
    slot: Slot
    height_slot: Slot
    latest_block_header: BeaconBlockHeader
    target: Checkpoint
    justified_checkpoint: Checkpoint
    finalized_checkpoint: Checkpoint
    target_votes: Bitlist
    progress_votes: Bitlist
    finality_votes: Bitlist
    block_roots: list[Root]
    validators: list[Validator]

    def update(self, **kv):
        return replace(self, **kv)


@dataclass
class FinalityVote:
    slot: Slot
    target: Checkpoint
    finalize_checkpoint: Checkpoint
    validator_index: ValidatorIndex


@dataclass
class BeaconBlockBody:
    attestations: list[Attestation]
    attester_slashings: list[AttesterSlashing]
    available_chain_votes: list[AvailableChainVote]


@dataclass
class BeaconBlock:
    slot: Slot
    state_root: Root
    parent_root: Root
    body: BeaconBlockBody


@dataclass
class SignedBeaconBlock:
    message: BeaconBlock
    signature: Signature


def hash_tree_root(object) -> Root:
    pass


def is_valid_block_signature(state: BeaconState, signed_block: SignedBeaconBlock) -> bool:
    pass


def get_finality_votes(state: BeaconState, block: BeaconBlock) -> list[FinalityVote]:
    pass


def is_active_validator(state: BeaconState, validator: Validator) -> bool:
    pass


def process_attester_slashing(
    pre_state: BeaconState, attester_slashing: AttesterSlashing
) -> BeaconState:
    pass


def get_block_root_at_slot(state: BeaconState, slot: Slot) -> Root:
    assert slot + SLOTS_PER_HISTORICAL_ROOT >= state.slot
    assert slot < state.slot
    return state.block_roots[slot % SLOTS_PER_HISTORICAL_ROOT]


def is_ancestor(state: BeaconState, ancestor_root: Root) -> bool:
    return ancestor_root in state.block_roots


def is_valid_target_vote(state: BeaconState, vote: FinalityVote) -> bool:
    return state.target.root != EMPTY_ROOT and vote.target == state.target


def is_valid_progress_vote(state: BeaconState, vote: FinalityVote) -> bool:
    return (
        # Explicit timeout vote
        vote.target == Checkpoint(root=EMPTY_ROOT, height=state.target.height)
        # Or a vote for an ancestor block
        or (vote.target.height == state.target.height and is_ancestor(state, vote.target.root))
    )


def is_valid_finality_vote(state: BeaconState, vote: FinalityVote) -> bool:
    return (
        state.justified_checkpoint.height > state.finalized_checkpoint.height
        and vote.finalize_checkpoint == state.justified_checkpoint
    )


def process_vote(state: BeaconState, vote: FinalityVote) -> BeaconState:
    target_votes = state.target_votes.copy()
    progress_votes = state.progress_votes.copy()
    finality_votes = state.finality_votes.copy()

    if is_valid_finality_vote(state, vote):
        finality_votes[vote.validator_index] = True

    if is_valid_target_vote(state, vote):
        target_votes[vote.validator_index] = True

    if is_valid_progress_vote(state, vote):
        progress_votes[vote.validator_index] = True

    return state.update(
        target_votes=target_votes,
        progress_votes=progress_votes,
        finality_votes=finality_votes,
    )


def get_support(state: BeaconState, validator_votes: Bitlist) -> Gwei:
    return sum(
        state.validators[index].effective_balance
        for index, supporting in enumerate(validator_votes)
        if supporting
    )


def get_total_active_balance(state: BeaconState) -> Gwei:
    return sum(v.effective_balance for v in state.validators if is_active_validator(state, v))


def has_quorum(state: BeaconState, validator_votes: Bitlist) -> bool:
    support = get_support(validator_votes)
    total_active_balance = get_total_active_balance(state)
    return 3 * support >= 2 * total_active_balance


def advance_height(pre_state: BeaconState) -> BeaconState:
    return pre_state.update(
        height_slot=pre_state.slot,
        target=Checkpoint(root=EMPTY_ROOT, height=pre_state.height + 1),
        target_votes=([False] * len(pre_state.validators)),
        progress_votes=([False] * len(pre_state.validators)),
    )


def reset_finality_votes(pre_state: BeaconState) -> BeaconState:
    return pre_state.update(finality_votes=([False] * len(pre_state.validators)))


def process_finalization(pre_state: BeaconState) -> BeaconState:
    if has_quorum(pre_state, pre_state.finality_votes):
        return pre_state.update(finalized_checkpoint=pre_state.justified_checkpoint)
    return pre_state


def process_justification(pre_state: BeaconState) -> BeaconState:
    state = pre_state
    if has_quorum(state, state.target_votes):
        state = state.update(justified_checkpoint=state.target)
        state = reset_finality_votes(state)
        state = advance_height(state)

    return state


def apply_progress(pre_state: BeaconState) -> BeaconState:
    # If there is a qorum advance height
    if has_quorum(pre_state.progress_votes):
        return advance_height(pre_state)
    else:
        return pre_state


def process_height_events(pre_state: BeaconState) -> BeaconState:
    state = pre_state
    state = process_finalization(state)
    state = process_justification(state)
    state = apply_progress(state)
    return state


def process_previous_roots(pre_state: BeaconState) -> BeaconState:
    state = pre_state

    # Set latest_block_header.state_root
    previous_state_root = hash_tree_root(state)
    if state.latest_block_header.state_root == EMPTY_ROOT:
        latest_block_header = state.latest_block_header.update(state_root=previous_state_root)
    else:
        latest_block_header = state.latest_block_header

    # Accumulate previous block root
    previous_block_root = hash_tree_root(latest_block_header)
    block_roots = state.block_roots.copy()
    block_roots[state.slot % SLOTS_PER_HISTORICAL_ROOT] = previous_block_root

    return state.update(block_roots=block_roots, latest_block_header=latest_block_header)


def process_slot(pre_state: BeaconState) -> BeaconState:
    state = pre_state
    state = process_previous_roots(state)

    # Process height events on each empty slot,
    # this is a no-op, at least for now
    if state.latest_block_header.slot < state.slot:
        state = process_height_events(state)

    # Set new target root when necessary
    if (
        state.target.root == EMPTY_ROOT
        # The check below looks redundant
        # as the state.height_slot is set to state.slot at the same time as state.latest_block_header is recorded
        and state.latest_block_header.slot >= state.height_slot
    ):
        state = state.update(
            target=Checkpoint(
                root=hash_tree_root(state.latest_block_header), height=state.target.height
            )
        )

    # Advance slot and return
    return state.update(slot=state.slot + 1)


def process_block(pre_state: BeaconState, block: BeaconBlock) -> tuple[BeaconState, bool]:
    if pre_state.slot != block.slot:
        return pre_state, False
    if block.parent_root != hash_tree_root(pre_state.latest_block_header):
        return pre_state, False

    state = pre_state

    # Process attestations
    for vote in get_finality_votes(state, block):
        state = process_vote(state, vote)

    # Process attester slashings
    for slashing in block.body.attester_slashings:
        state = process_attester_slashing(state, slashing)

    # Update latest block header
    state.latest_block_header = BeaconBlockHeader(
        slot=block.slot,
        state_root=EMPTY_ROOT,
        body_root=hash_tree_root(block.body),
    )

    return state


def state_transition(
    pre_state: BeaconState, signed_block: SignedBeaconBlock
) -> tuple[BeaconState, bool]:
    if not is_valid_block_signature(pre_state, signed_block):
        return pre_state, False

    state = pre_state
    block = signed_block.message
    while state.slot < block.slot:
        state = process_slot(state)
    state, valid = process_block(state, block)
    if valid:
        state = process_height_events(state)
        return state, True
    else:
        return state, False
