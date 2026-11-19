# PQ -- Fork Choice

*Note*: This document is a work-in-progress for researchers and implementers.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Constants](#constants)
  - [Time](#time)
- [Configs](#configs)
  - [Time parameters](#time-parameters)
  - [Misc](#misc)
- [Helpers](#helpers)
  - [New `ACLock`](#new-aclock)
  - [Modified `Store`](#modified-store)
  - [Modified `get_forkchoice_store`](#modified-get_forkchoice_store)
  - [New `upgrade_store_to_pq`](#new-upgrade_store_to_pq)
  - [New `is_ac_joined`](#new-is_ac_joined)
  - [New `on_ac_restart`](#new-on_ac_restart)
  - [New `get_head_vote_due_ms`](#new-get_head_vote_due_ms)
  - [New `get_support_cutoff_ms`](#new-get_support_cutoff_ms)
  - [New `get_view_freeze_ms`](#new-get_view_freeze_ms)
  - [New `is_ancestor_root`](#new-is_ancestor_root)
  - [New `is_strict_ancestor_root`](#new-is_strict_ancestor_root)
  - [New `get_deepest_node`](#new-get_deepest_node)
  - [New `is_compatible`](#new-is_compatible)
  - [New `get_subtree`](#new-get_subtree)
  - [Modified `get_parent_payload_status`](#modified-get_parent_payload_status)
  - [Modified `is_parent_node_full`](#modified-is_parent_node_full)
  - [New `get_upgraded_state`](#new-get_upgraded_state)
  - [New `get_block_state`](#new-get_block_state)
  - [New `get_block_pre_state`](#new-get_block_pre_state)
  - [New `get_pulled_up_state`](#new-get_pulled_up_state)
  - [Finality gadget](#finality-gadget)
    - [New `FGFrame`](#new-fgframe)
    - [New `get_fg_frame`](#new-get_fg_frame)
    - [New `get_viable_subtree`](#new-get_viable_subtree)
    - [New `is_fg_contest`](#new-is_fg_contest)
    - [New `is_fg_viable_block`](#new-is_fg_viable_block)
    - [New `has_viable_descendant`](#new-has_viable_descendant)
  - [Available chain](#available-chain)
    - [New `ACVote`](#new-acvote)
    - [New `get_ac_vote`](#new-get_ac_vote)
    - [New `get_head_vote_committee_seats_count`](#new-get_head_vote_committee_seats_count)
    - [New `get_validator_seats_count`](#new-get_validator_seats_count)
    - [New `get_block_and_payload_receipt_time`](#new-get_block_and_payload_receipt_time)
    - [New `get_vote_resolution_time`](#new-get_vote_resolution_time)
    - [New `get_local_view_from_p2p_messages`](#new-get_local_view_from_p2p_messages)
    - [New `get_view_from_blocks`](#new-get_view_from_blocks)
    - [New `get_local_view_from_blocks`](#new-get_local_view_from_blocks)
    - [New `is_usable_proposer_support`](#new-is_usable_proposer_support)
    - [New `get_proposer_view`](#new-get_proposer_view)
    - [New `compute_merged_view`](#new-compute_merged_view)
    - [New `get_combined_local_view`](#new-get_combined_local_view)
    - [New `get_equivocating_indices`](#new-get_equivocating_indices)
    - [New `get_viable_ancestor`](#new-get_viable_ancestor)
    - [New `get_live_locks`](#new-get_live_locks)
    - [New `conflicts_with_lock`](#new-conflicts_with_lock)
    - [New `compute_fast_lock_expiry`](#new-compute_fast_lock_expiry)
    - [New `compute_ghost_head`](#new-compute_ghost_head)
    - [New `compute_head_walk_score`](#new-compute_head_walk_score)
    - [New `is_eligible_for_head_walk`](#new-is_eligible_for_head_walk)
    - [New `get_head_walk_anchor`](#new-get_head_walk_anchor)
    - [New `get_head_in_tree`](#new-get_head_in_tree)
    - [New `get_voter_subtree`](#new-get_voter_subtree)
    - [New `compute_confirmation_score`](#new-compute_confirmation_score)
    - [New `get_confirmed_head`](#new-get_confirmed_head)
    - [New `compute_confirmed_lock`](#new-compute_confirmed_lock)
    - [New `compute_fast_lock`](#new-compute_fast_lock)
    - [New `compute_slow_lock`](#new-compute_slow_lock)
  - [Store mutators](#store-mutators)
    - [New `update_finality`](#new-update_finality)
    - [New `add_locks`](#new-add_locks)
    - [New `update_locks_and_confirmation`](#new-update_locks_and_confirmation)
    - [New `record_block_receipt_time`](#new-record_block_receipt_time)
    - [New `record_payload_receipt_time`](#new-record_payload_receipt_time)
    - [New `record_head_vote_committee`](#new-record_head_vote_committee)
    - [New `record_head_vote_message`](#new-record_head_vote_message)
  - [`on_tick` helpers](#on_tick-helpers)
    - [New `update_confirmation`](#new-update_confirmation)
    - [New `update_optimistic_confirmation`](#new-update_optimistic_confirmation)
    - [New `unlock`](#new-unlock)
  - [`on_head_vote_message` helpers](#on_head_vote_message-helpers)
    - [New `is_valid_head_vote_message`](#new-is_valid_head_vote_message)
- [Handlers](#handlers)
  - [Modified `on_tick`](#modified-on_tick)
  - [Modified `on_block`](#modified-on_block)
  - [Modified `on_execution_payload_envelope`](#modified-on_execution_payload_envelope)
  - [Modified `notify_ptc_messages`](#modified-notify_ptc_messages)
  - [Modified `on_payload_attestation_message`](#modified-on_payload_attestation_message)
  - [New `on_head_vote_message`](#new-on_head_vote_message)
- [Internal API](#internal-api)
  - [New `get_ac_proposal`](#new-get_ac_proposal)
  - [New `is_ac_vote_ready`](#new-is_ac_vote_ready)
  - [New `get_ac_vote_head`](#new-get_ac_vote_head)
  - [New `get_ac_frame`](#new-get_ac_frame)
  - [New `get_confirmed_execution_block_hash`](#new-get_confirmed_execution_block_hash)
- [External API](#external-api)
  - [New `get_confirmed_node`](#new-get_confirmed_node)
  - [Modified `get_head`](#modified-get_head)

<!-- mdformat-toc end -->

## Introduction

This is the modification of the fork-choice accompanying the PQ upgrade.

The fork choice of Gloas is replaced by that of EIP-8453. The store follows the
finality gadget (FG) through the beacon state and runs the available chain (AC)
on head votes.

Blocks no longer carry payload attestations, so the votes of the payload
timeliness committee reach fork choice only from the wire. Head votes in a block
carry no signature. Gossip validation checks the signature of a head vote
message from the wire, and `process_stark` proves the signatures of the head
votes in a block.

At the fork, a node converts its EIP-8483 store with `upgrade_store_to_pq`. The
store keeps the blocks and post-states it holds, and the post-states of blocks
before the fork stay EIP-8483 states. PQ fork choice reads every stored state
through `get_block_state`, which upgrades an EIP-8483 state with
`get_upgraded_state`. `on_block` applies the first block after the fork to the
upgraded parent state, and imports a block from before the fork that arrives
late with the EIP-8483 state transition.

## Constants

### Time

| Name               | Value        |
| ------------------ | ------------ |
| `INFINITE_TIME_MS` | `UINT64_MAX` |

## Configs

### Time parameters

| Name                 | Value          | Duration                  |
| -------------------- | -------------- | ------------------------- |
| `HEAD_VOTE_DUE_BPS`  | `Uint64(2500)` | 25% of `SLOT_DURATION_MS` |
| `SUPPORT_CUTOFF_BPS` | `Uint64(5000)` | 50% of `SLOT_DURATION_MS` |
| `VIEW_FREEZE_BPS`    | `Uint64(7500)` | 75% of `SLOT_DURATION_MS` |

### Misc

| Name                  | Value        | Description                                              |
| --------------------- | ------------ | -------------------------------------------------------- |
| `SLOW_LOCK_WINDOW`    | `Slot(2**5)` | Slow-confirmation window and max lock duration, in slots |
| `FAST_LOCK_EXTENSION` | `Slot(2)`    | Slots added to the latest live fast expiry               |

Both `SLOW_LOCK_WINDOW` and `FAST_LOCK_EXTENSION` must be at least two.

## Helpers

### New `ACLock`

*Note*: A lock records its node, confirmation slot, whether it is fast, and its
last live slot. It expires at the start of `expiry_slot + 1`. Moving the lock to
an ancestor preserves its other fields. Fast and slow locks remain separate,
even when they lock the same node or have the same expiry.

```python
@dataclass(eq=True, frozen=True)
class ACLock:
    node: ForkChoiceNode
    slot: Slot
    fast: bool
    expiry_slot: Slot
```

### Modified `Store`

```python
@dataclass
class Store:
    time_ms: Uint64
    genesis_time_ms: Uint64
    # [Modified in PQ:EIP8453]
    justified_checkpoint: HeightCheckpoint
    finalized_checkpoint: HeightCheckpoint
    # [Modified in PQ:EIP8453]
    # Removed `unrealized_justified_checkpoint`
    # [Modified in PQ:EIP8453]
    # Removed `unrealized_finalized_checkpoint`
    proposer_boost_root: Root
    # [Modified in PQ:EIP8453]
    # Removed `equivocating_indices`
    # [Modified in PQ:EIP8453]
    # Blocks before the fork keep their EIP-8483 blocks and post-states
    blocks: dict[Root, BeaconBlock | eip8483.BeaconBlock]
    block_states: dict[Root, BeaconState | eip8483.BeaconState]
    # [Modified in PQ:EIP8453]
    # Removed `block_timeliness`
    # [Modified in PQ:EIP8453]
    # Removed `checkpoint_states`
    latest_messages: dict[ValidatorIndex, LatestMessage]
    # [Modified in PQ:EIP8453]
    # Removed `unrealized_justifications`
    # [Modified in PQ:EIP8453]
    # Payloads of blocks before the fork keep their EIP-8483 envelopes
    payloads: dict[Root, ExecutionPayloadEnvelope | eip8483.ExecutionPayloadEnvelope]
    payload_timeliness_vote: dict[Root, list[Boolean | None]]
    payload_data_availability_vote: dict[Root, list[Boolean | None]]
    # [New in PQ:EIP8453]
    max_height: Height
    block_receipt_times: dict[Root, Uint64]
    payload_receipt_times: dict[Root, Uint64]
    latest_confirmed: ForkChoiceNode
    saved_confirmations: dict[Slot, ForkChoiceNode]
    locks: set[ACLock]
    head_vote_messages: dict[Slot, list[HeadVoteMessage]]
    head_vote_message_receipt_times: dict[Root, Uint64]
    head_vote_committees: dict[Slot, HeadVoteCommittee]
    prepared_head_vote: tuple[Slot, ForkChoiceNode] | None = None
    restart_time_ms: Uint64 | None = None
    pending_head_votes: list[tuple[HeadVoteMessage, HeadVoteCommittee]] = field(
        default_factory=list
    )
```

### Modified `get_forkchoice_store`

*Note*: The caller trusts the anchor block as justified and finalized at its
post-state’s target height. A node observing from genesis may omit `time_ms`. A
node bootstrapping from a weak-subjectivity anchor supplies its current wall
clock time and waits for the joining condition before performing AC duties.

```python
def get_forkchoice_store(
    anchor_state: BeaconState, anchor_block: BeaconBlock, time_ms: Uint64 | None = None
) -> Store:
    assert anchor_block.state_root == hash_tree_root(anchor_state)
    anchor_root = hash_tree_root(anchor_block)
    # [New in PQ:EIP8453]
    advanced_anchor_state = anchor_state.copy()
    process_slot(advanced_anchor_state)
    assert advanced_anchor_state.target_checkpoint.root == anchor_root
    # [Modified in PQ:EIP8453]
    anchor_height = anchor_state.target_checkpoint.height
    justified_checkpoint = HeightCheckpoint(height=anchor_height, root=anchor_root)
    finalized_checkpoint = HeightCheckpoint(height=anchor_height, root=anchor_root)
    genesis_time_ms = seconds_to_milliseconds(anchor_state.genesis_time)
    anchor_time_ms = compute_time_at_slot_ms(genesis_time_ms, anchor_state.slot)
    if time_ms is None:
        assert anchor_state.slot == GENESIS_SLOT
        time_ms = anchor_time_ms
        restart_time_ms = None
    else:
        assert time_ms >= anchor_time_ms
        restart_time_ms = time_ms
    return Store(
        time_ms=time_ms,
        genesis_time_ms=genesis_time_ms,
        # [Modified in PQ:EIP8453]
        justified_checkpoint=justified_checkpoint,
        finalized_checkpoint=finalized_checkpoint,
        proposer_boost_root=Root(),
        blocks={anchor_root: anchor_block.copy()},
        block_states={anchor_root: anchor_state.copy()},
        latest_messages={},
        payloads={},
        payload_timeliness_vote={anchor_root: [None] * PTC_SIZE},
        payload_data_availability_vote={anchor_root: [None] * PTC_SIZE},
        # [New in PQ:EIP8453]
        max_height=anchor_height,
        block_receipt_times={anchor_root: time_ms},
        payload_receipt_times={},
        latest_confirmed=ForkChoiceNode(
            root=finalized_checkpoint.root, payload_status=PAYLOAD_STATUS_PENDING
        ),
        saved_confirmations={},
        locks=set(),
        head_vote_messages={},
        head_vote_message_receipt_times={},
        head_vote_committees={},
        restart_time_ms=restart_time_ms,
    )
```

### New `upgrade_store_to_pq`

*Note*: The finality gadget starts at height 0 from the last finalized Casper
FFG checkpoint, as in `upgrade_to_pq`, so the store's justified and finalized
checkpoints are that block at height 0. Every block before the fork is the
target of height 1 on its own branch. Blocks before the fork count as received
at the start of their slot. The AC starts with no locks, confirmations or head
votes.

```python
def upgrade_store_to_pq(pre: eip8483.Store) -> Store:
    """
    Return the PQ fork choice store converted from the EIP-8483 store ``pre``
    at the fork.
    """
    finalized_checkpoint = HeightCheckpoint(height=Height(0), root=pre.finalized_checkpoint.root)
    return Store(
        time_ms=pre.time_ms,
        genesis_time_ms=pre.genesis_time_ms,
        justified_checkpoint=finalized_checkpoint,
        finalized_checkpoint=finalized_checkpoint,
        proposer_boost_root=Root(),
        blocks=dict(pre.blocks),
        block_states=dict(pre.block_states),
        latest_messages={},
        payloads=dict(pre.payloads),
        payload_timeliness_vote=dict(pre.payload_timeliness_vote),
        payload_data_availability_vote=dict(pre.payload_data_availability_vote),
        # [Modified in PQ]
        # Removed `payload_inclusion_list_satisfaction`
        max_height=Height(1),
        block_receipt_times={
            root: compute_time_at_slot_ms(pre.genesis_time_ms, block.slot)
            for root, block in pre.blocks.items()
        },
        payload_receipt_times={
            root: compute_time_at_slot_ms(pre.genesis_time_ms, pre.blocks[root].slot)
            for root in pre.payloads
        },
        latest_confirmed=ForkChoiceNode(
            root=finalized_checkpoint.root, payload_status=PAYLOAD_STATUS_PENDING
        ),
        saved_confirmations={},
        locks=set(),
        head_vote_messages={},
        head_vote_message_receipt_times={},
        head_vote_committees={},
    )
```

### New `is_ac_joined`

```python
def is_ac_joined(store: Store) -> bool:
    """
    Return whether the node has observed continuously since the previous slot.
    """
    if store.restart_time_ms is None:
        return True
    slot = get_current_slot(store)
    return slot > GENESIS_SLOT and store.restart_time_ms <= compute_time_at_slot_ms(
        store.genesis_time_ms, slot - 1
    )
```

### New `on_ac_restart`

*Note*: The validated block/state/payload database, FG state, AC locks and
`latest_confirmed` survive restart. Persistent validator signing records also
survive, including records preventing duplicate head votes. Committee duties are
rederived from retained states. The transient AC views are reconstructed from
retained blocks in parent order; all reconstructed receipts use restart time,
not their pre-restart times. Sibling order is deterministic by root. No
proposing, vote preparation, confirmation or FG-source publication runs during
replay or until the joining condition holds.

```python
def on_ac_restart(store: Store, time_ms: Uint64) -> None:
    assert time_ms >= store.time_ms
    store.time_ms = time_ms
    store.restart_time_ms = time_ms
    store.prepared_head_vote = None
    store.pending_head_votes = []
    store.saved_confirmations = {}
    store.head_vote_messages = {}
    store.head_vote_message_receipt_times = {}
    store.head_vote_committees = {}
    store.block_receipt_times = {}
    store.payload_receipt_times = dict.fromkeys(store.payloads, time_ms)
    for root in sorted(store.blocks, key=lambda root: (store.blocks[root].slot, root)):
        store.block_receipt_times[root] = time_ms
        block = store.blocks[root]
        # Blocks before the PQ fork carry no head votes
        if isinstance(block, eip8483.BeaconBlock):
            continue
        for vote in block.body.head_votes:
            record_head_vote_committee(store, get_block_state(store, root), vote.data)
```

### New `get_head_vote_due_ms`

```python
def get_head_vote_due_ms() -> Uint64:
    return get_slot_component_duration_ms(HEAD_VOTE_DUE_BPS)
```

### New `get_support_cutoff_ms`

```python
def get_support_cutoff_ms() -> Uint64:
    return get_slot_component_duration_ms(SUPPORT_CUTOFF_BPS)
```

### New `get_view_freeze_ms`

```python
def get_view_freeze_ms() -> Uint64:
    return get_slot_component_duration_ms(VIEW_FREEZE_BPS)
```

### New `is_ancestor_root`

```python
def is_ancestor_root(store: Store, root: Root, ancestor: Root) -> bool:
    """
    Return ``True`` if ``ancestor`` is an ancestor of ``root``
    in the tree of beacon blocks ignoring payload status.
    """
    node = ForkChoiceNode(root=root, payload_status=PAYLOAD_STATUS_PENDING)
    ancestor_node = ForkChoiceNode(root=ancestor, payload_status=PAYLOAD_STATUS_PENDING)
    return is_ancestor(store, node, ancestor_node)
```

### New `is_strict_ancestor_root`

```python
def is_strict_ancestor_root(store: Store, root: Root, ancestor: Root) -> bool:
    """
    Return ``True`` if ``ancestor`` is a strict ancestor of ``root``.
    """
    return root != ancestor and is_ancestor_root(store, root, ancestor)
```

### New `get_deepest_node`

*Note*: This helper has no root tie-break. Use it to select a node only from a
chain or a compatible set. Callers comparing conflicting nodes must be
independent of which tied node is returned, as in `is_compatible`.

```python
def get_deepest_node(store: Store, nodes: set[ForkChoiceNode]) -> ForkChoiceNode:
    """
    Return the node in ``nodes`` with the highest slot and payload status.
    """
    assert len(nodes) > 0
    return max(
        nodes,
        key=lambda node: (
            store.blocks[node.root].slot,
            # Precedence of full/empty over pending
            0 if node.payload_status == PAYLOAD_STATUS_PENDING else 1,
        ),
    )
```

### New `is_compatible`

```python
def is_compatible(store: Store, node_1: ForkChoiceNode, node_2: ForkChoiceNode) -> bool:
    """
    Return ``True`` if ``node_1`` and ``node_2`` belong to the same chain.
    """
    if get_deepest_node(store, {node_1, node_2}) == node_1:
        return is_ancestor(store, node_1, node_2)
    else:
        return is_ancestor(store, node_2, node_1)
```

### New `get_subtree`

```python
def get_subtree(store: Store, subtree_root: ForkChoiceNode) -> Sequence[ForkChoiceNode]:
    """
    Return the nodes in a subtree rooted at ``subtree_root``, including ``subtree_root``.
    """
    subtree = [subtree_root]
    for child in get_node_children(store, subtree_root):
        subtree.extend(get_subtree(store, child))
    return subtree
```

### Modified `get_parent_payload_status`

```python
def get_parent_payload_status(
    store: Store,
    # [Modified in PQ:EIP8453]
    block: BeaconBlock | eip8483.BeaconBlock,
) -> PayloadStatus:
    parent = store.blocks[block.parent_root]
    parent_block_hash = block.body.signed_execution_payload_bid.message.parent_block_hash
    message_block_hash = parent.body.signed_execution_payload_bid.message.block_hash
    return PAYLOAD_STATUS_FULL if parent_block_hash == message_block_hash else PAYLOAD_STATUS_EMPTY
```

### Modified `is_parent_node_full`

```python
def is_parent_node_full(
    store: Store,
    # [Modified in PQ:EIP8453]
    block: BeaconBlock | eip8483.BeaconBlock,
) -> bool:
    return get_parent_payload_status(store, block) == PAYLOAD_STATUS_FULL
```

### New `get_upgraded_state`

*Note*: The upgrade replays the slots from the state's slot to the fork, up to
an epoch near the fork. Readers such as `is_fg_contest` upgrade every stored
block before the fork on each call, so implementations should cache the upgraded
state of each stored block.

```python
def get_upgraded_state(state: eip8483.BeaconState | BeaconState) -> BeaconState:
    """
    Return ``state``, advanced to the PQ fork and upgraded if it is an EIP-8483
    state.
    """
    if not isinstance(state, eip8483.BeaconState):
        return state
    pre = state.copy()
    fork_slot = compute_start_slot_at_epoch(Epoch(PQ_FORK_EPOCH))
    if pre.slot < fork_slot:
        eip8483.process_slots(pre, fork_slot)
    return upgrade_to_pq(pre)
```

### New `get_block_state`

*Note*: The returned state can be the stored state itself. Callers must not
mutate it; a caller that changes it works on a copy.

```python
def get_block_state(store: Store, root: Root) -> BeaconState:
    """
    Return the post-state of the block at ``root``, upgraded at the EIP-8453
    fork.
    """
    return get_upgraded_state(store.block_states[root])
```

### New `get_block_pre_state`

```python
def get_block_pre_state(store: Store, block: BeaconBlock) -> BeaconState:
    """
    Return the post-state of the parent of ``block``, upgraded at the EIP-8453
    fork and advanced to the slot of ``block``.
    """
    state = get_block_state(store, block.parent_root).copy()
    if state.slot < block.slot:
        process_slots(state, block.slot)
    return state
```

### New `get_pulled_up_state`

```python
def get_pulled_up_state(store: Store, block_root: Root) -> BeaconState:
    """
    Return the state of the block pulled up to the current epoch if needed.
    """
    block_state = get_block_state(store, block_root)
    if get_current_epoch(block_state) < get_current_store_epoch(store):
        pulled_up_state = block_state.copy()
        process_slots(pulled_up_state, compute_start_slot_at_epoch(get_current_store_epoch(store)))
        return pulled_up_state
    else:
        return block_state
```

### Finality gadget

#### New `FGFrame`

*Note*: Available Chain uses the Finality Gadget frame to constrain its decision
walks.

```python
@dataclass
class FGFrame:
    finalized_node: ForkChoiceNode
    forkchoice_root: ForkChoiceNode
    tree: Sequence[ForkChoiceNode]
    viable_heads: set[ForkChoiceNode]
```

#### New `get_fg_frame`

```python
def get_fg_frame(store: Store) -> FGFrame:
    finalized_node = ForkChoiceNode(
        root=store.finalized_checkpoint.root,
        payload_status=PAYLOAD_STATUS_PENDING,
    )

    # Root the subtree at the finalized node
    tree = get_subtree(store, finalized_node)

    # Compute the forkchoice_root based on the justification height and FG contest
    if store.max_height == store.justified_checkpoint.height + 1 and not is_fg_contest(store):
        forkchoice_block_root = store.justified_checkpoint.root
    else:
        forkchoice_block_root = store.finalized_checkpoint.root
    forkchoice_root = ForkChoiceNode(
        root=forkchoice_block_root,
        payload_status=PAYLOAD_STATUS_PENDING,
    )

    # Viable nodes must be descendants of forkchoice_root and pass the FG viability test
    viable_heads = {
        node
        for node in tree
        if is_ancestor(store, node, forkchoice_root) and is_fg_viable_block(store, node.root)
    }

    return FGFrame(
        finalized_node=finalized_node,
        forkchoice_root=forkchoice_root,
        tree=tree,
        viable_heads=viable_heads,
    )
```

#### New `get_viable_subtree`

```python
def get_viable_subtree(
    store: Store, fg_frame: FGFrame, tree: Sequence[ForkChoiceNode]
) -> Sequence[ForkChoiceNode]:
    """
    Return a subtree of ``tree`` that passes the viability test.
    """
    viable_heads_in_tree = set(tree) & fg_frame.viable_heads
    return [
        node
        for node in tree
        # Nodes must be descendants of forkchoice_root
        # and ancestors of at least one viable head belonging to the tree
        if is_ancestor(store, node, fg_frame.forkchoice_root)
        and any(is_ancestor(store, viable_head, node) for viable_head in viable_heads_in_tree)
    ]
```

#### New `is_fg_contest`

*Note*: FG contest occurs when the maximum known height is exactly one above the
justified checkpoint height, and a block at that maximum height extends the
finalized checkpoint but conflicts with the justified checkpoint.

```python
def is_fg_contest(store: Store) -> bool:
    """
    Return ``True`` if ``store`` is in an FG contest.
    """
    if store.max_height > store.justified_checkpoint.height + 1:
        return False
    max_height_blocks = [
        root
        for root in store.blocks
        if get_block_state(store, root).target_checkpoint.height == store.max_height
        and is_ancestor_root(store, root, store.finalized_checkpoint.root)
    ]
    return any(
        not is_ancestor_root(store, b, store.justified_checkpoint.root) for b in max_height_blocks
    )
```

#### New `is_fg_viable_block`

*Note*: The height floor depends on whether there is FG contest or not.

```python
def is_fg_viable_block(store: Store, block_root: Root) -> bool:
    """
    Return ``True`` if block passes the height floor check.
    """
    block_target = get_block_state(store, block_root).target_checkpoint
    if is_fg_contest(store):
        return block_target.height >= store.max_height
    else:
        return block_target.height + 1 >= store.max_height
```

#### New `has_viable_descendant`

```python
def has_viable_descendant(store: Store, block_root: Root) -> bool:
    """
    Return ``True`` if the block or any of its descendants passes the FG viability check.
    """
    return any(
        is_fg_viable_block(store, root)
        for root in store.blocks
        if is_ancestor_root(store, root, block_root)
    )
```

### Available chain

#### New `ACVote`

*Note*: Represents an individual AC vote in a form suitable for set operations,
including deduplication and merging votes from messages and blocks.

```python
@dataclass(eq=True, frozen=True)
class ACVote:
    slot: Slot
    validator_index: ValidatorIndex
    supported_node: ForkChoiceNode
```

#### New `get_ac_vote`

```python
def get_ac_vote(validator_index: ValidatorIndex, data: HeadVoteData) -> ACVote:
    """
    Create an AC vote for ``validator_index`` from the head vote ``data``.
    """
    supported_node = ForkChoiceNode(
        root=data.beacon_block_root,
        payload_status=data.payload_status,
    )
    return ACVote(
        slot=data.slot,
        validator_index=validator_index,
        supported_node=supported_node,
    )
```

#### New `get_head_vote_committee_seats_count`

```python
def get_head_vote_committee_seats_count() -> Uint64:
    """
    Return size of the head vote committee.
    """
    return HEAD_VOTE_COMMITTEE_SIZE
```

#### New `get_validator_seats_count`

*Note*: The head vote committee selection may assign multiple seats to the same
validator.

```python
def get_validator_seats_count(store: Store, slot: Slot, validator_index: ValidatorIndex) -> Uint64:
    """
    Return the number of seats assigned to ``validator_index`` in the head vote committee for ``slot``.
    """
    assert slot in store.head_vote_committees
    return Uint64(store.head_vote_committees[slot].count(validator_index))
```

#### New `get_block_and_payload_receipt_time`

*Note*: An *empty* or *pending* node uses the beacon block’s receipt time. A
*full* node uses the later of the beacon block and payload receipt times.

```python
def get_block_and_payload_receipt_time(store: Store, node: ForkChoiceNode) -> Uint64:
    """
    Return ``node`` receipt time.
    """
    if node.payload_status == PAYLOAD_STATUS_FULL:
        return max(store.block_receipt_times[node.root], store.payload_receipt_times[node.root])
    else:
        return store.block_receipt_times[node.root]
```

#### New `get_vote_resolution_time`

*Note*: For unresolved votes `INFINITE_TIME_MS` is returned.

```python
def get_vote_resolution_time(
    store: Store, supported_node: ForkChoiceNode, vote_slot: Slot, vote_receipt_time: Uint64
) -> Uint64:
    """
    Return the resolution time of the vote.
    """
    block_root = supported_node.root
    payload_status = supported_node.payload_status

    # Votes must be for a known block
    if block_root not in store.blocks:
        return INFINITE_TIME_MS

    # The supported block must not be later than the vote's slot
    block_slot = store.blocks[block_root].slot
    if block_slot > vote_slot:
        return INFINITE_TIME_MS

    # Votes for a block in the vote's own slot must support PENDING
    if block_slot == vote_slot and payload_status != PAYLOAD_STATUS_PENDING:
        return INFINITE_TIME_MS

    # Full votes require a verified payload
    if payload_status == PAYLOAD_STATUS_FULL and not is_payload_verified(store, block_root):
        return INFINITE_TIME_MS

    # Votes must support blocks belonging to the FG frame
    if not is_ancestor_root(store, supported_node.root, store.finalized_checkpoint.root):
        return INFINITE_TIME_MS

    return max(vote_receipt_time, get_block_and_payload_receipt_time(store, supported_node))
```

#### New `get_local_view_from_p2p_messages`

*Note*: Builds an AC view from P2P messages using locally observed receipt and
resolution times.

```python
def get_local_view_from_p2p_messages(
    store: Store, vote_slot: Slot, receipt_threshold_ms: Uint64, resolution_threshold_ms: Uint64
) -> tuple[list[HeadVoteMessage], list[int]]:
    """
    Return messages for ``vote_slot`` received before ``receipt_threshold_ms``,
    and indices of those votes that are resolved before ``resolution_threshold_ms``.
    """
    vote_messages: list[HeadVoteMessage] = []
    support_indices: list[int] = []

    for index, message in enumerate(store.head_vote_messages.get(vote_slot, [])):
        data = message.data
        message_root = hash_tree_root(message)
        message_receipt_ms = store.head_vote_message_receipt_times[message_root]
        # Include messages received before the receipt threshold
        if message_receipt_ms < receipt_threshold_ms:
            vote_messages.append(message)
            supported_node = ForkChoiceNode(
                root=data.beacon_block_root, payload_status=data.payload_status
            )
            # Record the indices of included messages whose votes resolve before the support threshold
            if (
                get_vote_resolution_time(store, supported_node, data.slot, message_receipt_ms)
                < resolution_threshold_ms
            ):
                support_indices.append(index)

    return vote_messages, support_indices
```

#### New `get_view_from_blocks`

*Note*: A general function to build AC view from votes included in blocks.
Clients should cache head-vote committees by slot and dependent root, reusing
them across block votes while keeping branch-dependent committees separate.

```python
def get_view_from_blocks(
    store: Store,
    block_slot: Slot,
    vote_slot: Slot,
    block_predicate: Callable[[Root], bool],
    is_supported: Callable[[Root, HeadVote, bool], bool],
) -> tuple[list[HeadVote], list[bool]]:
    """
    Return head votes for ``vote_slot`` included in blocks at ``block_slot``
    that pass ``block_predicate``, and whether each of them is support
    as decided by ``is_supported``.
    """
    vote_messages: list[HeadVote] = []
    support: list[bool] = []

    for block_root in store.blocks:
        block = store.blocks[block_root]
        # Filter by block slot and block test predicate
        # (blocks before the PQ fork carry no head votes)
        if isinstance(block, eip8483.BeaconBlock):
            continue
        if block.slot == block_slot and block_predicate(block_root):
            for vote_index, head_vote in enumerate(block.body.head_votes):
                data = head_vote.data
                # Only votes matching the slot's recorded committee enter AC views.
                if (
                    data.slot == vote_slot
                    and data.slot in store.head_vote_committees
                    and get_head_vote_committee(get_block_state(store, block_root), data.slot)
                    == store.head_vote_committees[data.slot]
                ):
                    vote_messages.append(head_vote)
                    proposer_support = bool(block.body.head_vote_support[vote_index])
                    support.append(is_supported(block_root, head_vote, proposer_support))

    return vote_messages, support
```

#### New `get_local_view_from_blocks`

*Note*: Builds an AC view from block votes using locally observed receipt and
resolution times.

```python
def get_local_view_from_blocks(
    store: Store, vote_slot: Slot, receipt_threshold_ms: Uint64, resolution_threshold_ms: Uint64
) -> tuple[list[HeadVote], list[bool]]:
    """
    Return votes for ``vote_slot`` indluded in blocks received before ``receipt_threshold_ms``,
    and whether each of those votes is resolved before ``resolution_threshold_ms``.
    """

    def is_supported(block_root: Root, head_vote: HeadVote, _proposer_support: bool) -> bool:
        data = head_vote.data
        block_receipt_time = store.block_receipt_times[block_root]
        supported_node = ForkChoiceNode(
            root=data.beacon_block_root, payload_status=data.payload_status
        )
        # All voters in this vote support the locally resolved node
        return (
            get_vote_resolution_time(store, supported_node, data.slot, block_receipt_time)
            < resolution_threshold_ms
        )

    # Restrict to blocks that are from the slot immediately after the vote slot
    return get_view_from_blocks(
        store,
        vote_slot + 1,
        vote_slot,
        block_predicate=lambda block_root: (
            store.block_receipt_times[block_root] < receipt_threshold_ms
        ),
        is_supported=is_supported,
    )
```

#### New `is_usable_proposer_support`

```python
def is_usable_proposer_support(
    store: Store, tree: Sequence[ForkChoiceNode], data: HeadVoteData
) -> bool:
    node = ForkChoiceNode(root=data.beacon_block_root, payload_status=data.payload_status)
    return (
        node in tree
        and store.blocks[node.root].slot <= data.slot
        and (
            store.blocks[node.root].slot < data.slot
            or data.payload_status == PAYLOAD_STATUS_PENDING
        )
    )
```

#### New `get_proposer_view`

*Note*: Builds an AC proposer view. Supporting votes must reference locally
known blocks. *Full* block support additionally requires a verified payload.

```python
def get_proposer_view(
    store: Store, block_slot: Slot, vote_slot: Slot
) -> tuple[list[HeadVote], list[bool]]:
    """
    Return the proposer view for ``vote_slot`` from proposals made in ``block_slot``.
    """

    tree = get_fg_frame(store).tree

    def is_supported(_block_root: Root, head_vote: HeadVote, proposer_support: bool) -> bool:
        return proposer_support and is_usable_proposer_support(store, tree, head_vote.data)

    return get_view_from_blocks(
        store,
        block_slot,
        vote_slot,
        block_predicate=lambda block_root: is_ancestor_root(
            store, block_root, store.finalized_checkpoint.root
        ),
        is_supported=is_supported,
    )
```

#### New `compute_merged_view`

*Note*: Merges views from P2P messages and blocks into sets of single AC votes,
deduplicating votes and combining their support.

```python
def compute_merged_view(
    votes_from_messages: tuple[list[HeadVoteMessage], list[int]],
    votes_from_blocks: tuple[list[HeadVote], list[bool]],
) -> tuple[set[ACVote], set[ACVote]]:
    """
    Return the merged vote set and its supporting subset.
    """
    votes: set[ACVote] = set()
    support_votes: set[ACVote] = set()

    # Process p2p message votes
    for index, message_vote in enumerate(votes_from_messages[0]):
        vote = get_ac_vote(message_vote.validator_index, message_vote.data)
        votes.add(vote)
        if index in votes_from_messages[1]:
            support_votes.add(vote)

    # Update sets with block votes
    for vote_index, block_vote in enumerate(votes_from_blocks[0]):
        is_supported = votes_from_blocks[1][vote_index]
        for voter_index in block_vote.voter_indices:
            vote = get_ac_vote(voter_index, block_vote.data)
            votes.add(vote)
            if is_supported:
                support_votes.add(vote)

    return votes, support_votes
```

#### New `get_combined_local_view`

```python
def get_combined_local_view(
    store: Store, slot: Slot, receipt_threshold_ms: Uint64, resolution_threshold_ms: Uint64
) -> tuple[set[ACVote], set[ACVote]]:
    """
    Return the merged local vote set and supporting subset for ``slot``,
    using the receipt and resolution thresholds for both P2P and block votes.
    """
    votes_from_messages = get_local_view_from_p2p_messages(
        store, slot, receipt_threshold_ms, resolution_threshold_ms
    )
    votes_from_blocks = get_local_view_from_blocks(
        store, slot, receipt_threshold_ms, resolution_threshold_ms
    )
    return compute_merged_view(votes_from_messages, votes_from_blocks)
```

#### New `get_equivocating_indices`

```python
def get_equivocating_indices(votes: set[ACVote]) -> set[ValidatorIndex]:
    """
    Return indices of validators with multiple distinct votes.
    """
    equivocating_indices: set[ValidatorIndex] = set()
    for voter_index in {vote.validator_index for vote in votes}:
        votes_by_index = {vote for vote in votes if vote.validator_index == voter_index}
        if len(votes_by_index) > 1:
            equivocating_indices.add(voter_index)
    return equivocating_indices
```

#### New `get_viable_ancestor`

```python
def get_viable_ancestor(
    store: Store, fg_frame: FGFrame, viable_tree: Sequence[ForkChoiceNode], node: ForkChoiceNode
) -> ForkChoiceNode:
    """
    Return the deepest ancestor that is viable or an ancestor of the forkchoice root.
    """
    return get_deepest_node(
        store,
        {
            ancestor
            for ancestor in fg_frame.tree
            if is_ancestor(store, node, ancestor)
            and (ancestor in viable_tree or is_ancestor(store, fg_frame.forkchoice_root, ancestor))
        },
    )
```

#### New `get_live_locks`

*Note*: Every lock read uses its viable ancestor. Lock updates store this
ancestor so that a later change to the FG frame cannot restore the old node.

```python
def get_live_locks(store: Store, fg_frame: FGFrame, time_ms: Uint64) -> set[ACLock]:
    """
    Return unexpired locks in the frame, each moved to its viable ancestor.
    """
    viable_tree = get_viable_subtree(store, fg_frame, fg_frame.tree)
    return {
        ACLock(
            node=get_viable_ancestor(store, fg_frame, viable_tree, lock.node),
            slot=lock.slot,
            fast=lock.fast,
            expiry_slot=lock.expiry_slot,
        )
        for lock in store.locks
        if lock.node in fg_frame.tree
        and time_ms < compute_time_at_slot_ms(store.genesis_time_ms, lock.expiry_slot + 1)
    }
```

#### New `conflicts_with_lock`

```python
def conflicts_with_lock(store: Store, live_locks: set[ACLock], node: ForkChoiceNode) -> bool:
    return any(not is_compatible(store, lock.node, node) for lock in live_locks)
```

#### New `compute_fast_lock_expiry`

*Note*: Only live fast locks from slots before `slot` extend the expiry. Their
nodes need not be on the new lock's branch. A lock moved to the finalized node
still contributes. Locks from the same or a newer slot do not contribute.

```python
def compute_fast_lock_expiry(live_locks: set[ACLock], slot: Slot) -> Slot:
    expiries = {lock.expiry_slot for lock in live_locks if lock.fast and lock.slot < slot}
    if len(expiries) == 0:
        return slot + 2
    return min(slot + SLOW_LOCK_WINDOW, max(slot + 2, max(expiries) + FAST_LOCK_EXTENSION))
```

#### New `compute_ghost_head`

```python
def compute_ghost_head(
    store: Store,
    anchor: ForkChoiceNode,
    tree: Sequence[ForkChoiceNode],
    get_score: Callable[[ForkChoiceNode], Uint64],
    is_eligible: Callable[[ForkChoiceNode], bool],
) -> ForkChoiceNode:
    """
    Return the head reached by a GHOST walk from ``anchor``,
    using the supplied scoring and eligibility functions.
    """
    head = anchor
    while True:
        eligible_children = [
            child
            for child in get_node_children(store, head)
            if child in tree and is_eligible(child)
        ]
        if len(eligible_children) == 0:
            return head
        head = max(
            eligible_children,
            key=lambda child: (
                get_score(child),
                child.root,
                get_payload_status_tiebreaker(store, child),
            ),
        )
```

#### New `compute_head_walk_score`

*Note*: Equivocating validators contribute their support to every node. The
node’s supporting score counts the committee seats of non-equivocating
validators whose support vote is for the node or one of its descendants.

```python
def compute_head_walk_score(
    store: Store,
    votes: set[ACVote],
    support_votes: set[ACVote],
    slot: Slot,
    node: ForkChoiceNode,
) -> Uint64:
    """
    Return the sum of the equivocating score and the node's supporting score.
    """
    equivocating_indices = get_equivocating_indices(votes)
    # Votes for any descendant from the support set
    # cast by non-equivocating voters of a given slot
    supporting_indices = {
        vote.validator_index
        for vote in support_votes
        if vote.validator_index not in equivocating_indices
        and vote.slot == slot
        and is_ancestor(store, vote.supported_node, node)
    }
    equivocating_score = Uint64(
        sum(
            get_validator_seats_count(store, slot, validator_index)
            for validator_index in equivocating_indices
        )
    )
    supporting_score = Uint64(
        sum(
            get_validator_seats_count(store, slot, validator_index)
            for validator_index in supporting_indices
        )
    )
    # Equivocating score counts for every block
    return equivocating_score + supporting_score
```

#### New `is_eligible_for_head_walk`

*Note*: A node is eligible for the head walk if it is a full or empty node from
the previous slot, its parent block is not yet a viable head, its block is from
the current slot, or its head-walk score exceeds half the participating
committee seats.

```python
def is_eligible_for_head_walk(
    store: Store,
    fg_frame: FGFrame,
    votes: set[ACVote],
    support_votes: set[ACVote],
    slot: Slot,
    node: ForkChoiceNode,
) -> bool:
    """
    Return ``True`` if the head walk may advance into ``node``.
    """
    block = store.blocks[node.root]

    # Full or empty nodes from the previous slot are always eligible
    if is_previous_slot_payload_decision(store, node):
        return True

    parent = ForkChoiceNode(root=block.parent_root, payload_status=PAYLOAD_STATUS_PENDING)
    if parent not in fg_frame.viable_heads:
        return True

    if block.slot == get_current_slot(store):
        return True

    # Total seats of all voters
    voting_indices = {vote.validator_index for vote in votes}
    voting_seats_count = Uint64(
        sum(
            get_validator_seats_count(store, slot, validator_index)
            for validator_index in voting_indices
        )
    )
    score = compute_head_walk_score(store, votes, support_votes, slot, node)

    # Require a strict majority of participating committee seats
    return 2 * score > voting_seats_count
```

#### New `get_head_walk_anchor`

*Note*: Use the full FG frame even when the caller selects votes and blocks from
a restricted view.

```python
def get_head_walk_anchor(store: Store, fg_frame: FGFrame) -> ForkChoiceNode:
    """
    Return the deepest live lock node or the forkchoice root.
    """
    return get_deepest_node(
        store,
        {lock.node for lock in get_live_locks(store, fg_frame, store.time_ms)}
        | {fg_frame.forkchoice_root},
    )
```

#### New `get_head_in_tree`

*Note*: Walks the viable subtree of tree from the head-walk anchor, using the
head-walk scoring and eligibility rules. The anchor is selected from the full FG
frame independently of tree.

```python
def get_head_in_tree(
    store: Store,
    fg_frame: FGFrame,
    tree: Sequence[ForkChoiceNode],
    votes: set[ACVote],
    support_votes: set[ACVote],
    slot: Slot,
) -> ForkChoiceNode:
    """
    Return the head of the tree.
    """
    anchor = get_head_walk_anchor(store, fg_frame)
    viable_subtree = get_viable_subtree(store, fg_frame, tree)
    return compute_ghost_head(
        store=store,
        anchor=anchor,
        tree=viable_subtree,
        get_score=lambda node: compute_head_walk_score(store, votes, support_votes, slot, node),
        is_eligible=lambda node: is_eligible_for_head_walk(
            store, fg_frame, votes, support_votes, slot, node
        ),
    )
```

#### New `get_voter_subtree`

*Note*: Return a subtree of nodes received before the previous slot's
view-freeze deadline, together with ancestors of proposals from the voting slot,
including the proposals themselves.

```python
def get_voter_subtree(
    store: Store, tree: Sequence[ForkChoiceNode], slot: Slot
) -> Sequence[ForkChoiceNode]:
    """
    Return the subtree available to the voter in ``slot``.
    """
    view_freeze_ms = compute_time_at_slot_ms(store.genesis_time_ms, slot - 1) + get_view_freeze_ms()
    slot_proposals = {node for node in tree if store.blocks[node.root].slot == slot}
    return [
        node
        for node in tree
        if get_block_and_payload_receipt_time(store, node) < view_freeze_ms
        or any(is_ancestor(store, proposal, node) for proposal in slot_proposals)
    ]
```

#### New `compute_confirmation_score`

*Note*: The confirmation score counts the committee seats of non-equivocating
validators whose votes are in support votes set and support the node or one of
its descendants. Equivocating validators contribute no support.

```python
def compute_confirmation_score(
    store: Store,
    votes: set[ACVote],
    support_votes: set[ACVote],
    slot: Slot,
    node: ForkChoiceNode,
) -> Uint64:
    """
    Return confirmation score of the ``node``.
    """
    equivocating_indices = get_equivocating_indices(votes)
    supporting_indices = {
        vote.validator_index
        for vote in support_votes
        if vote.validator_index not in equivocating_indices
        and is_ancestor(store, vote.supported_node, node)
    }
    return Uint64(
        sum(
            get_validator_seats_count(store, slot, validator_index)
            for validator_index in supporting_indices
        )
    )
```

#### New `get_confirmed_head`

*Note*: Runs a confirmation walk using the confirmation score, requiring
eligible nodes to score more than half the participating committee seats.
Returns `None` if the resulting head is ineligible, including when the walk
stops at the finalized node.

```python
def get_confirmed_head(
    store: Store, fg_frame: FGFrame, votes: set[ACVote], support_votes: set[ACVote], slot: Slot
) -> ForkChoiceNode | None:
    """
    Return the confirmation candidate, or ``None`` if no node has sufficient support.
    """
    voting_indices = {vote.validator_index for vote in votes}
    voting_seats_count = Uint64(
        sum(
            get_validator_seats_count(store, slot, validator_index)
            for validator_index in voting_indices
        )
    )

    def is_eligible(node: ForkChoiceNode) -> bool:
        return (
            2 * compute_confirmation_score(store, votes, support_votes, slot, node)
            > voting_seats_count
        )

    head = compute_ghost_head(
        store=store,
        anchor=fg_frame.finalized_node,
        tree=fg_frame.tree,
        get_score=lambda node: compute_confirmation_score(store, votes, support_votes, slot, node),
        is_eligible=is_eligible,
    )

    if is_eligible(head):
        return head
    else:
        return None
```

#### New `compute_confirmed_lock`

*Note*: Computes the confirmed path and the lock as the deepest node in the
confirmed path. Candidate nodes are selected from the FG frame, excluding
genesis and nodes that conflict with a live lock.

```python
def compute_confirmed_lock(
    store: Store,
    fg_frame: FGFrame,
    live_locks: set[ACLock],
    confirmed: ForkChoiceNode,
    test_predicate: Callable[[ForkChoiceNode], bool],
) -> ForkChoiceNode | None:
    """
    Return the deepest selected path node, or ``None``.
    """
    path = {
        node
        for node in fg_frame.tree
        if is_ancestor(store, confirmed, node)
        and store.blocks[node.root].slot > GENESIS_SLOT
        and not conflicts_with_lock(store, live_locks, node)
        and test_predicate(node)
    }

    return get_deepest_node(store, path) if len(path) > 0 else None
```

#### New `compute_fast_lock`

*Note*: Selects non-genesis nodes on the path to `confirmed` within the FG frame
whose confirmation support accounts for at least half of all committee seats.
The deepest selected node is the fast lock.

```python
def compute_fast_lock(
    store: Store,
    fg_frame: FGFrame,
    live_locks: set[ACLock],
    votes: set[ACVote],
    support_votes: set[ACVote],
    slot: Slot,
    confirmed: ForkChoiceNode,
) -> ForkChoiceNode | None:
    """
    Return the fast lock, or ``None``.
    """
    return compute_confirmed_lock(
        store=store,
        fg_frame=fg_frame,
        live_locks=live_locks,
        confirmed=confirmed,
        test_predicate=lambda node: (
            2 * compute_confirmation_score(store, votes, support_votes, slot, node)
            >= get_head_vote_committee_seats_count()
        ),
    )
```

#### New `compute_slow_lock`

*Note*: The slow lock requires:

- Saved confirmations in the FG frame for each of the previous
  `SLOW_LOCK_WINDOW - 1` slots.
- A non-genesis node in the FG frame that is an ancestor of or equal to both the
  current candidate and every saved confirmation in that window.

The deepest such node is the slow lock.

```python
def compute_slow_lock(
    store: Store, fg_frame: FGFrame, live_locks: set[ACLock], slot: Slot, confirmed: ForkChoiceNode
) -> ForkChoiceNode | None:
    """
    Return the slow lock, or ``None`` if the window or common ancestor is missing.
    """
    if slot + 1 < SLOW_LOCK_WINDOW:
        return None

    previous_slots = range(slot + 1 - SLOW_LOCK_WINDOW, slot)
    if not all(
        Slot(j) in store.saved_confirmations and store.saved_confirmations[Slot(j)] in fg_frame.tree
        for j in previous_slots
    ):
        return None

    slow_lock = compute_confirmed_lock(
        store=store,
        fg_frame=fg_frame,
        live_locks=live_locks,
        confirmed=confirmed,
        test_predicate=lambda node: all(
            is_ancestor(store, store.saved_confirmations[Slot(j)], node) for j in previous_slots
        ),
    )
    return slow_lock
```

### Store mutators

#### New `update_finality`

*Notes*: First, update the store's maximum known height using the state's target
height.

Replace the store's justified checkpoint with the state's justified checkpoint
when both conditions hold:

- Its `(height, root)` tuple is lexicographically greater than the store's
  justified tuple.
- Its block descends from or equals the store's finalized block.

Then replace the store's finalized checkpoint with the state's finalized
checkpoint when all conditions hold:

- Its height is greater than the store's finalized height.
- Its block is a strict descendant of the store's finalized block.
- Its block is an ancestor of or equal to the store's justified block, including
  any justification update made above.
- Its block or one of its descendants passes the FG viability check.

```python
def update_finality(store: Store, state: BeaconState) -> None:
    """
    Update finality gadget information in store
    """
    # Update max_height
    store.max_height = max(store.max_height, state.target_checkpoint.height)

    # Update justification
    store_justification = (store.justified_checkpoint.height, store.justified_checkpoint.root)
    state_justification = (state.justified_checkpoint.height, state.justified_checkpoint.root)
    if state_justification > store_justification and is_ancestor_root(
        store, state.justified_checkpoint.root, store.finalized_checkpoint.root
    ):
        store.justified_checkpoint = state.justified_checkpoint

    # Update finality
    if (
        state.finalized_checkpoint.height > store.finalized_checkpoint.height
        and is_strict_ancestor_root(
            store, state.finalized_checkpoint.root, store.finalized_checkpoint.root
        )
        and is_ancestor_root(
            store, store.justified_checkpoint.root, state.finalized_checkpoint.root
        )
        and has_viable_descendant(store, state.finalized_checkpoint.root)
    ):
        store.finalized_checkpoint = state.finalized_checkpoint
```

#### New `add_locks`

```python
def add_locks(store: Store, fg_frame: FGFrame, locks: set[ACLock]) -> None:
    """
    Add locks, remove expired or out-of-frame locks, and store their viable ancestors.
    """
    store.locks |= locks
    store.locks = get_live_locks(store, fg_frame, store.time_ms)
```

#### New `update_locks_and_confirmation`

```python
def update_locks_and_confirmation(
    store: Store,
    slot: Slot,
    fg_frame: FGFrame,
    live_locks: set[ACLock],
    confirmed: ForkChoiceNode,
    fast_lock: ForkChoiceNode | None,
    slow_lock: ForkChoiceNode | None,
) -> None:
    """
    Record the candidate and separate fast and slow locks, even when confirmation is vetoed.
    """
    store.saved_confirmations[slot] = confirmed
    vetoed = conflicts_with_lock(store, live_locks, confirmed)

    locks = set()
    if fast_lock is not None:
        locks.add(
            ACLock(
                node=fast_lock,
                slot=slot,
                fast=True,
                expiry_slot=compute_fast_lock_expiry(live_locks, slot),
            )
        )
    if slow_lock is not None:
        locks.add(
            ACLock(node=slow_lock, slot=slot, fast=False, expiry_slot=slot + SLOW_LOCK_WINDOW)
        )

    # A veto stops the confirmation record, not locks on compatible ancestors.
    if not vetoed and not (
        store.latest_confirmed in fg_frame.tree
        and is_ancestor(store, store.latest_confirmed, confirmed)
    ):
        store.latest_confirmed = confirmed

    # Store viable ancestors even when neither test creates a new lock.
    add_locks(store, fg_frame, locks)
```

#### New `record_block_receipt_time`

```python
def record_block_receipt_time(store: Store, root: Root) -> None:
    """
    Store block receipt time.
    """
    store.block_receipt_times[root] = store.time_ms
```

#### New `record_payload_receipt_time`

```python
def record_payload_receipt_time(store: Store, root: Root) -> None:
    """
    Store payload receipt time.
    """
    store.payload_receipt_times[root] = store.time_ms
```

#### New `record_head_vote_committee`

*Note*: Store the head vote committee for a vote from the previous or current
slot. The first recorded committee supplies the slot's weights. Block and P2P
votes with another committee are excluded from AC views, while their blocks
remain available. Per-branch committee keying is an open protocol decision.

```python
def record_head_vote_committee(store: Store, state: BeaconState, data: HeadVoteData) -> None:
    """
    Store head vote committee.
    """
    if data.slot + 1 >= get_current_slot(store):
        store.head_vote_committees.setdefault(data.slot, get_head_vote_committee(state, data.slot))
```

#### New `record_head_vote_message`

```python
def record_head_vote_message(
    store: Store, committee: HeadVoteCommittee, message: HeadVoteMessage
) -> None:
    """
    Store head vote message in the pool, updates its receipt time and its slot committee.
    """
    stored_committee = store.head_vote_committees.get(message.data.slot)
    if stored_committee is not None and stored_committee != committee:
        return
    # Keep at most two distinct vote data values for each validator and slot.
    slot_pool = store.head_vote_messages.get(message.data.slot, [])
    previous = [vote for vote in slot_pool if vote.validator_index == message.validator_index]
    if any(vote.data == message.data for vote in previous) or len(previous) >= 2:
        return
    slot_pool.append(message)
    store.head_vote_messages[message.data.slot] = slot_pool

    # Add receipt time
    message_root = hash_tree_root(message)
    store.head_vote_message_receipt_times[message_root] = store.time_ms

    # The first validated view supplies the committee for this slot.
    store.head_vote_committees.setdefault(message.data.slot, committee)
```

### `on_tick` helpers

#### New `update_confirmation`

*Notes*: This function:

- Computes and records a confirmation candidate using all locally known votes
  for the slot and support resolved before the cutoff.
- Updates the confirmed head only when no live lock conflicts with the
  candidate.
- Adds separate fast and slow locks on qualifying ancestors that conflict with
  no live lock, even when the candidate itself is vetoed.

```python
def update_confirmation(store: Store, slot: Slot) -> None:
    if not is_ac_joined(store):
        return
    fg_frame = get_fg_frame(store)
    support_cutoff_ms = (
        compute_time_at_slot_ms(store.genesis_time_ms, slot) + get_support_cutoff_ms()
    )
    votes, support_votes = get_combined_local_view(store, slot, INFINITE_TIME_MS, support_cutoff_ms)
    confirmed = get_confirmed_head(store, fg_frame, votes, support_votes, slot)

    # Return if there is no confirmation
    if confirmed is None:
        store.saved_confirmations.pop(slot, None)
        return

    live_locks = get_live_locks(store, fg_frame, store.time_ms)
    fast_lock = compute_fast_lock(
        store=store,
        fg_frame=fg_frame,
        live_locks=live_locks,
        votes=votes,
        support_votes=support_votes,
        slot=slot,
        confirmed=confirmed,
    )
    slow_lock = compute_slow_lock(store, fg_frame, live_locks, slot, confirmed)

    # Write updates to store
    update_locks_and_confirmation(
        store,
        slot,
        fg_frame,
        live_locks,
        confirmed,
        fast_lock,
        slow_lock,
    )
```

#### New `update_optimistic_confirmation`

*Note*: Before the half-slot cutoff, a joined node confirms the deepest node
supported by resolved votes from at least three quarters of the current
committee seats and conflicting with no live lock. Equal-depth candidates prefer
a decided payload over PENDING, then the lowest root and payload status. Each
validator counts once per candidate, including an equivocator with a vote
extending that candidate. This writes a current-slot fast lock but does not
write a scheduled confirmation candidate or emit an FG attestation.

```python
def update_optimistic_confirmation(store: Store) -> None:
    slot = get_current_slot(store)
    if not is_ac_joined(store) or slot == GENESIS_SLOT:
        return
    if get_time_into_slot_ms(store) >= get_support_cutoff_ms():
        return
    fg_frame = get_fg_frame(store)
    _, support_votes = get_combined_local_view(store, slot, INFINITE_TIME_MS, INFINITE_TIME_MS)
    live_locks = get_live_locks(store, fg_frame, store.time_ms)
    candidates = set()
    for node in fg_frame.tree:
        voters = {
            vote.validator_index
            for vote in support_votes
            if vote.slot == slot
            and vote.supported_node in fg_frame.tree
            and is_ancestor(store, vote.supported_node, node)
        }
        seats = sum(get_validator_seats_count(store, slot, index) for index in voters)
        if 4 * seats >= 3 * get_head_vote_committee_seats_count() and not conflicts_with_lock(
            store, live_locks, node
        ):
            candidates.add(node)
    if len(candidates) == 0:
        return
    confirmed = min(
        candidates,
        key=lambda node: (
            -int(store.blocks[node.root].slot),
            node.payload_status == PAYLOAD_STATUS_PENDING,
            node.root,
            node.payload_status,
        ),
    )
    expiry = compute_fast_lock_expiry(live_locks, slot)
    add_locks(store, fg_frame, {ACLock(node=confirmed, slot=slot, fast=True, expiry_slot=expiry)})
    if not (
        store.latest_confirmed in fg_frame.tree
        and is_ancestor(store, store.latest_confirmed, confirmed)
    ):
        store.latest_confirmed = confirmed
```

#### New `unlock`

*Note*: Equivocators count as opposition to every node. Other validators count
when their resolved vote supports a conflicting node. Count each validator's
committee seats once. Only locks from slots before the vote slot can move.

```python
def unlock(store: Store, slot: Slot, votes: set[ACVote], support_votes: set[ACVote]) -> None:
    """
    Move older locks using the supplied vote and support view.
    """
    fg_frame = get_fg_frame(store)
    equivocating_indices = get_equivocating_indices(votes)

    def is_opposed_by_majority(node: ForkChoiceNode) -> bool:
        opposing_voters = equivocating_indices | {
            vote.validator_index
            for vote in support_votes
            if vote.slot == slot
            and vote.supported_node in fg_frame.tree
            and not is_compatible(store, vote.supported_node, node)
        }
        opposing_score = sum(
            get_validator_seats_count(store, slot, validator_index)
            for validator_index in opposing_voters
        )
        return 2 * opposing_score >= get_head_vote_committee_seats_count()

    locks = set()
    for lock in get_live_locks(store, fg_frame, store.time_ms):
        node = lock.node
        if lock.slot < slot:
            fallback_path = {
                ancestor
                for ancestor in fg_frame.tree
                if is_ancestor(store, node, ancestor) and not is_opposed_by_majority(ancestor)
            }
            node = (
                get_deepest_node(store, fallback_path)
                if len(fallback_path) > 0
                else fg_frame.finalized_node
            )
        locks.add(ACLock(node=node, slot=lock.slot, fast=lock.fast, expiry_slot=lock.expiry_slot))
    store.locks = locks
```

### `on_head_vote_message` helpers

#### New `is_valid_head_vote_message`

```python
def is_valid_head_vote_message(state: BeaconState, message: HeadVoteMessage) -> bool:
    """
    Return ``True`` if head vote message is valid.
    """
    # Vote must have correct payload_status
    if message.data.payload_status not in [
        PAYLOAD_STATUS_EMPTY,
        PAYLOAD_STATUS_FULL,
        PAYLOAD_STATUS_PENDING,
    ]:
        return False

    # Validator must belong to the selected committee
    if message.validator_index not in get_head_vote_committee(state, message.data.slot):
        return False

    # Vote must have a valid signature
    domain = get_domain(state, DOMAIN_HEAD_VOTE, compute_epoch_at_slot(message.data.slot))
    signing_root = compute_signing_root(message.data, domain)
    leaf_index = compute_xmss_leaf_index(message.data.slot, LEAF_OFFSET_HEAD_VOTE)
    pubkey = state.validators[message.validator_index].pubkey
    return xmss.Verify(pubkey, leaf_index, signing_root, message.signature)
```

## Handlers

### Modified `on_tick`

*Note*: Updates the store time, then prepares the head vote or runs confirmation
when scheduled at `time_ms`. Every node prepares the head vote, including nodes
without a validator on the committee. Callers must process this tick before
other events at the same timestamp. A delayed client timer processes every
crossed duty timestamp in order before advancing to its wall time: the first
physical tick at or after the deadline dispatches the deadline duty with that
scheduled timestamp. Queued early votes carry their validated committee and are
admitted without revalidation against a possibly changed head state.

```python
def on_tick(store: Store, time_ms: Uint64) -> None:
    # Lock expiry reads must use the time of this tick.
    store.time_ms = time_ms
    time_into_slot_ms = (time_ms - store.genesis_time_ms) % SLOT_DURATION_MS
    slot = compute_slot_at_time_ms(store.genesis_time_ms, time_ms)
    previous_slot = saturating_sub(slot, 1)
    store.head_vote_messages = {
        s: votes for s, votes in store.head_vote_messages.items() if s >= previous_slot
    }
    retained_roots = {
        hash_tree_root(vote) for votes in store.head_vote_messages.values() for vote in votes
    }
    store.head_vote_message_receipt_times = {
        root: time
        for root, time in store.head_vote_message_receipt_times.items()
        if root in retained_roots
    }
    store.head_vote_committees = {
        s: committee for s, committee in store.head_vote_committees.items() if s >= previous_slot
    }
    store.saved_confirmations = {
        s: node
        for s, node in store.saved_confirmations.items()
        if s >= saturating_sub(slot, SLOW_LOCK_WINDOW)
    }

    pending = store.pending_head_votes
    store.pending_head_votes = []
    for message, committee in pending:
        if message.data.slot > slot:
            store.pending_head_votes.append((message, committee))
        elif message.data.slot >= previous_slot:
            record_head_vote_message(store, committee, message)
            update_optimistic_confirmation(store)
            get_ac_vote_head(store)

    if not is_ac_joined(store):
        return

    if time_into_slot_ms == get_head_vote_due_ms():
        get_ac_vote_head(store)

    if slot > GENESIS_SLOT and time_into_slot_ms == get_support_cutoff_ms():
        update_confirmation(store, slot - 1)
```

### Modified `on_block`

*Note*: This function is modified to update finality with the new finality
gadget, record block receipt time and store head vote committees. Blocks no
longer carry payload attestations.

```python
def on_block(store: Store, signed_block: SignedBeaconBlock | eip8483.SignedBeaconBlock) -> None:
    """
    Run ``on_block`` upon receiving a new block.
    """
    block = signed_block.message
    block_root = hash_tree_root(block)

    # Return early if the block is already known
    if block_root in store.blocks:
        return

    # Parent block must be known
    assert block.parent_root in store.block_states

    # If this block builds on the parent's full payload, that payload must
    # have been verified by on_execution_payload_envelope
    if is_parent_node_full(store, block):
        assert is_payload_verified(store, block.parent_root)

    # Blocks cannot be in the future. If they are, their consideration must be delayed until they are in the past.
    current_slot = get_current_slot(store)
    assert current_slot >= block.slot

    # [Modified in PQ:EIP8453]
    # Run finalized check over the parent to avoid circular dependency.
    assert is_ancestor_root(store, block.parent_root, store.finalized_checkpoint.root)

    # [New in PQ:EIP8453]
    # A block from before the fork that arrives late is processed with the EIP-8483
    # state transition, and its EIP-8483 post-state is stored like those of the
    # blocks before the fork
    if compute_epoch_at_slot(block.slot) < PQ_FORK_EPOCH:
        assert isinstance(signed_block, eip8483.SignedBeaconBlock)
        pre_fork_state = store.block_states[block.parent_root].copy()
        assert isinstance(pre_fork_state, eip8483.BeaconState)
        eip8483.state_transition(pre_fork_state, signed_block, validate_result=True)
        store.blocks[block_root] = signed_block.message
        store.block_states[block_root] = pre_fork_state
        store.payload_timeliness_vote[block_root] = [None] * PTC_SIZE
        store.payload_data_availability_vote[block_root] = [None] * PTC_SIZE
        record_block_receipt_time(store, block_root)
        # Notify the store about the payload attestations in the block, read
        # with its EIP-8483 post-state
        notify_ptc_messages(store, pre_fork_state, signed_block.message.body.payload_attestations)
        return

    # A block at or after the fork is a PQ block
    assert isinstance(signed_block, SignedBeaconBlock)
    block = signed_block.message

    # [Modified in PQ:EIP8453]
    # Make a copy of the parent's state, upgraded at the PQ fork
    state = get_block_state(store, block.parent_root).copy()

    # Check the block is valid and compute the post-state
    state_transition(state, signed_block, validate_result=True)

    # Add new block to the store
    store.blocks[block_root] = block
    # Add new state for this block to the store
    store.block_states[block_root] = state
    # Add a new PTC voting for this block to the store
    store.payload_timeliness_vote[block_root] = [None] * PTC_SIZE
    store.payload_data_availability_vote[block_root] = [None] * PTC_SIZE

    # [Modified in PQ:EIP8453]
    update_finality(store, state)

    # [New in PQ:EIP8453]
    # Record block receipt time
    record_block_receipt_time(store, block_root)

    # [New in PQ:EIP8453]
    for vote in block.body.head_votes:
        record_head_vote_committee(store, state, vote.data)

    # [Modified in PQ]
    # Removed `notify_ptc_messages`
    update_optimistic_confirmation(store)
    get_ac_vote_head(store)
```

### Modified `on_execution_payload_envelope`

*Note*: This function is modified to record payload receipt time.

```python
def on_execution_payload_envelope(
    store: Store,
    # [Modified in PQ:EIP8453]
    signed_envelope: SignedExecutionPayloadEnvelope | eip8483.SignedExecutionPayloadEnvelope,
) -> None:
    """
    Run ``on_execution_payload_envelope`` upon receiving a new execution payload envelope.
    """
    envelope = signed_envelope.message
    # The corresponding beacon block root needs to be known
    assert envelope.beacon_block_root in store.block_states

    # Check if blob data is available
    # If not, this payload MAY be queued and subsequently considered when blob data becomes available
    assert is_data_available(envelope.beacon_block_root)

    state = store.block_states[envelope.beacon_block_root]

    # Verify the execution payload envelope
    # [Modified in PQ:EIP8453]
    # The payload of a block before the fork is verified with the EIP-8483 rules
    if isinstance(state, eip8483.BeaconState):
        assert isinstance(signed_envelope, eip8483.SignedExecutionPayloadEnvelope)
        eip8483.verify_execution_payload_envelope(state, signed_envelope, eip8483.EXECUTION_ENGINE)
    else:
        assert isinstance(signed_envelope, SignedExecutionPayloadEnvelope)
        verify_execution_payload_envelope(state, signed_envelope, EXECUTION_ENGINE)

    # [New in PQ:EIP8453]
    # Record payload receipt time
    record_payload_receipt_time(store, envelope.beacon_block_root)

    # Add execution payload envelope to the store
    store.payloads[envelope.beacon_block_root] = envelope
    update_optimistic_confirmation(store)
    get_ac_vote_head(store)
```

### Modified `notify_ptc_messages`

*Note*: PQ blocks carry no payload attestations. Only a block before the fork
that arrives after the store conversion passes its PTC votes to the store, read
with its EIP-8483 post-state.

```python
def notify_ptc_messages(
    store: Store,
    # [Modified in PQ:EIP8453]
    state: eip8483.BeaconState,
    payload_attestations: Sequence[eip8483.PayloadAttestation],
) -> None:
    """
    Extracts a list of ``PayloadAttestationMessage`` from ``payload_attestations`` and updates the store with them
    These Payload attestations are assumed to be in the beacon block hence signature verification is not needed
    """
    if state.slot == 0:
        return
    for payload_attestation in payload_attestations:
        # [Modified in PQ:EIP8453]
        # A block before the fork has the EIP-8483 PTC
        indexed_payload_attestation = eip8483.get_indexed_payload_attestation(
            state, payload_attestation
        )
        for idx in indexed_payload_attestation.attesting_indices:
            on_payload_attestation_message(
                store,
                PayloadAttestationMessage(
                    validator_index=idx,
                    data=payload_attestation.data,
                    # [Modified in PQ]
                    signature=XMSSSignature(),
                ),
                is_from_block=True,
            )
```

### Modified `on_payload_attestation_message`

*Note*: PQ blocks carry no payload attestations, so a message from a block is a
PTC vote of a block before the fork, passed on by `notify_ptc_messages`. A
message from the wire is for the current slot, so after the store conversion it
is for a PQ block, and its signature is checked with `xmss.Verify`, since
`IndexedPayloadAttestation` is deprecated.

```python
def on_payload_attestation_message(
    store: Store,
    ptc_message: PayloadAttestationMessage,
    # [Modified in PQ:EIP8453]
    is_from_block: bool = False,
) -> None:
    """
    Run ``on_payload_attestation_message`` upon receiving a new payload attestation message
    from either within a block before the fork or directly on the wire.
    """
    data = ptc_message.data

    # PTC attestation must be for a known block. If block is unknown, delay consideration until the block is found
    assert data.beacon_block_root in store.block_states
    state = store.block_states[data.beacon_block_root]

    # PTC votes can only change the vote for their assigned beacon block, return early otherwise
    if data.slot != state.slot:
        return

    # Get all positions of the attester in the PTC
    ptc_indices = []
    # [Modified in PQ:EIP8453]
    # A block before the fork has the EIP-8483 PTC
    if isinstance(state, eip8483.BeaconState):
        ptc = eip8483.get_ptc(state, data.slot)
    else:
        ptc = get_ptc(state, data.slot)
    for ptc_index, validator_index in enumerate(ptc):
        if validator_index == ptc_message.validator_index:
            ptc_indices.append(ptc_index)

    # Check that the attester is from the PTC
    assert len(ptc_indices) > 0

    # Verify the signature and check that its for the current slot if it is coming from the wire
    if not is_from_block:
        # [Modified in PQ]
        # Check that the attestation is for the current slot
        assert data.slot == get_current_slot(store)
        # A message from the wire is for the current slot, so for a block after the
        # store conversion
        assert isinstance(state, BeaconState)
        # Verify the signature
        domain = get_domain(state, DOMAIN_PTC_ATTESTER, compute_epoch_at_slot(data.slot))
        signing_root = compute_signing_root(data, domain)
        leaf_index = compute_xmss_leaf_index(data.slot, LEAF_OFFSET_PTC_ATTESTER)
        pubkey = state.validators[ptc_message.validator_index].pubkey
        assert xmss.Verify(pubkey, leaf_index, signing_root, ptc_message.signature)

    # Update the votes for the block
    payload_timeliness_vote = store.payload_timeliness_vote[data.beacon_block_root]
    payload_data_availability_vote = store.payload_data_availability_vote[data.beacon_block_root]
    for ptc_index in ptc_indices:
        payload_timeliness_vote[ptc_index] = data.payload_present
        payload_data_availability_vote[ptc_index] = data.blob_data_available
```

### New `on_head_vote_message`

*Note*: Validates and stores head vote P2P message.

```python
def on_head_vote_message(store: Store, message: HeadVoteMessage) -> None:
    current_slot = get_current_slot(store)
    previous_slot = saturating_sub(current_slot, 1)
    data = message.data
    if data.beacon_block_root in store.blocks:
        block_slot = store.blocks[data.beacon_block_root].slot
        assert block_slot <= data.slot
        if block_slot == data.slot:
            assert data.payload_status == PAYLOAD_STATUS_PENDING
        else:
            assert data.payload_status in (PAYLOAD_STATUS_EMPTY, PAYLOAD_STATUS_FULL)

    if message.data.slot == current_slot + 1:
        slot_start = compute_time_at_slot_ms(store.genesis_time_ms, message.data.slot)
        if store.time_ms + MAXIMUM_GOSSIP_CLOCK_DISPARITY < slot_start:
            return
        previous = [
            vote
            for vote, _ in store.pending_head_votes
            if vote.validator_index == message.validator_index
            and vote.data.slot == message.data.slot
        ]
        if any(vote.data == message.data for vote in previous) or len(previous) >= 2:
            return
        state = get_pulled_up_state(store, get_head(store).root)
        assert is_valid_head_vote_message(state, message)
        store.pending_head_votes.append((
            message,
            get_head_vote_committee(state, message.data.slot),
        ))
        return
    if message.data.slot not in [previous_slot, current_slot]:
        return
    previous = [
        vote
        for vote in store.head_vote_messages.get(message.data.slot, [])
        if vote.validator_index == message.validator_index
    ]
    if any(vote.data == message.data for vote in previous) or len(previous) >= 2:
        return

    # Use pulled up head state
    state = get_pulled_up_state(store, get_head(store).root)
    assert is_valid_head_vote_message(state, message)

    # Record the message
    record_head_vote_message(store, get_head_vote_committee(state, message.data.slot), message)
    update_optimistic_confirmation(store)
    get_ac_vote_head(store)
```

## Internal API

### New `get_ac_proposal`

*Note*: At the start of a slot, selects the proposal head using received and
resolved P2P votes from the previous slot. Returns the head, vote messages, and
supporting message indices. The receipt and resolution thresholds are infinite,
so whether a vote is support depends only on its data and the store, not on when
the vote or its block was received. Votes with the same data are all support or
all not, which is why a block records one support bit per head vote.

```python
def get_ac_proposal(
    store: Store,
) -> tuple[ForkChoiceNode, list[HeadVoteMessage], list[int]] | None:
    if not is_ac_joined(store):
        return None
    assert get_time_into_slot_ms(store) == Uint64(0)

    current_slot = get_current_slot(store)
    assert current_slot > GENESIS_SLOT

    fg_frame = get_fg_frame(store)
    vote_messages, support_indices = get_local_view_from_p2p_messages(
        store,
        current_slot - 1,
        receipt_threshold_ms=INFINITE_TIME_MS,
        resolution_threshold_ms=INFINITE_TIME_MS,
    )

    # Build the view from P2P messages only
    votes, support_votes = compute_merged_view((vote_messages, support_indices), ([], []))
    unlock(store, current_slot - 1, votes, support_votes)
    head = get_head_in_tree(
        store=store,
        fg_frame=fg_frame,
        tree=fg_frame.tree,
        votes=votes,
        support_votes=support_votes,
        slot=current_slot - 1,
    )

    # Convert a pending head to empty for proposal construction
    if head.payload_status == PAYLOAD_STATUS_PENDING:
        head = ForkChoiceNode(root=head.root, payload_status=PAYLOAD_STATUS_EMPTY)

    return head, vote_messages, support_indices
```

### New `is_ac_vote_ready`

*Note*: Early readiness uses the single proposer expected by the node's head
chain for the current slot. Proposals by other branches' proposers do not
trigger an early vote. At least one proposal from that proposer must have all
marked support usable in the local FG tree.

```python
def is_ac_vote_ready(store: Store) -> bool:
    """
    Return whether a current proposal has all of its supporting heads available.
    """
    slot = get_current_slot(store)
    if slot == GENESIS_SLOT or not any(block.slot == slot for block in store.blocks.values()):
        return False
    tree = get_fg_frame(store).tree
    state = get_pulled_up_state(store, get_head(store).root).copy()
    # The pulled-up state's proposer lookahead covers every slot of this epoch.
    state.slot = slot
    proposer_index = get_beacon_proposer_index(state)
    for root, block in store.blocks.items():
        proposal = ForkChoiceNode(root=root, payload_status=PAYLOAD_STATUS_PENDING)
        if block.slot != slot or block.proposer_index != proposer_index or proposal not in tree:
            continue
        # Blocks before the PQ fork carry no head votes
        if isinstance(block, eip8483.BeaconBlock):
            continue
        ready = True
        for vote, support in zip(block.body.head_votes, block.body.head_vote_support, strict=True):
            if (
                vote.data.slot != slot - 1
                or not support
                or vote.data.slot not in store.head_vote_committees
                or get_head_vote_committee(get_block_state(store, root), vote.data.slot)
                != store.head_vote_committees[vote.data.slot]
            ):
                continue
            if not is_usable_proposer_support(store, tree, vote.data):
                ready = False
                break
        if ready:
            return True
    return False
```

### New `get_ac_vote_head`

*Note*: Prepares the head at the first ready proposal up to the head-vote
deadline, or at the deadline if no proposal is ready. Returns `None` before
readiness or after a missed deadline. The prepared result remains stable for the
slot. Merges the frozen local P2P view with views from current slot proposals,
then walks the voter's viable subtree, falling back to the full FG tree if that
subtree is empty.

```python
def get_ac_vote_head(store: Store) -> ForkChoiceNode | None:
    if not is_ac_joined(store):
        return None
    current_slot = get_current_slot(store)
    if store.prepared_head_vote is not None and store.prepared_head_vote[0] == current_slot:
        return store.prepared_head_vote[1]
    elapsed = get_time_into_slot_ms(store)
    if elapsed > get_head_vote_due_ms():
        return None
    if elapsed < get_head_vote_due_ms() and not is_ac_vote_ready(store):
        return None

    fg_frame = get_fg_frame(store)
    if current_slot == GENESIS_SLOT:
        store.prepared_head_vote = (current_slot, fg_frame.finalized_node)
        return fg_frame.finalized_node
    view_freeze_ms = (
        compute_time_at_slot_ms(store.genesis_time_ms, current_slot - 1) + get_view_freeze_ms()
    )
    # Local view
    local_view = get_local_view_from_p2p_messages(
        store,
        current_slot - 1,
        receipt_threshold_ms=view_freeze_ms,
        resolution_threshold_ms=view_freeze_ms,
    )
    # Proposer view
    proposer_view = get_proposer_view(store, current_slot, current_slot - 1)
    # Merge views
    votes, support_votes = compute_merged_view(local_view, proposer_view)
    unlock(store, current_slot - 1, votes, support_votes)

    # Run over voter viable subtree
    voter_subtree = get_voter_subtree(store, fg_frame.tree, current_slot)
    if len(get_viable_subtree(store, fg_frame, voter_subtree)) == 0:
        voter_subtree = fg_frame.tree
    head = get_head_in_tree(
        store=store,
        fg_frame=fg_frame,
        tree=voter_subtree,
        votes=votes,
        support_votes=support_votes,
        slot=current_slot - 1,
    )

    # Current-slot votes name the block without deciding its payload.
    if store.blocks[head.root].slot == current_slot:
        head = ForkChoiceNode(root=head.root, payload_status=PAYLOAD_STATUS_PENDING)
    elif head.payload_status == PAYLOAD_STATUS_PENDING:
        head = ForkChoiceNode(root=head.root, payload_status=PAYLOAD_STATUS_EMPTY)
    store.prepared_head_vote = (current_slot, head)
    return head
```

### New `get_ac_frame`

*Notes*: At or after the support cutoff, returns the FG confirmation node and
the head selected using the current slot's local vote view.

For a joined node, the FG confirmation node is the deepest viable effective live
fast-lock node whose confirmation slot is at least the current slot minus two,
or `None` if no such node exists. Slow locks do not provide FG sources.

The AC frame is used by validators at scheduled FG duties. Each duty reads the
currently eligible source; publication is deduplicated by each validator's
persistent signing record rather than a node-level source watermark. A later
duty may therefore read a source equal to or ancestral to an earlier source.

```python
def get_ac_frame(store: Store) -> tuple[ForkChoiceNode | None, ForkChoiceNode]:
    assert get_time_into_slot_ms(store) >= get_support_cutoff_ms()

    current_slot = get_current_slot(store)
    fg_frame = get_fg_frame(store)
    votes, support_votes = get_combined_local_view(
        store,
        current_slot,
        receipt_threshold_ms=INFINITE_TIME_MS,
        resolution_threshold_ms=INFINITE_TIME_MS,
    )
    head = get_head_in_tree(
        store=store,
        fg_frame=fg_frame,
        tree=fg_frame.tree,
        votes=votes,
        support_votes=support_votes,
        slot=current_slot,
    )

    if not is_ac_joined(store):
        return None, head

    viable_subtree = get_viable_subtree(store, fg_frame, fg_frame.tree)
    candidates = {
        lock.node
        for lock in get_live_locks(store, fg_frame, store.time_ms)
        if lock.fast and current_slot <= lock.slot + 2 and lock.node in viable_subtree
    }
    if len(candidates) > 0:
        fg_confirmed = get_deepest_node(store, candidates)
        return fg_confirmed, head
    else:
        return None, head
```

### New `get_confirmed_execution_block_hash`

*Note*: Returns the confirmed execution block hash for the Engine API. In the
case of an empty slot a payload from a past slot can still be confirmed.

```python
def get_confirmed_execution_block_hash(store: Store) -> Hash32:
    confirmed_node = get_confirmed_node(store)
    confirmed_block = store.blocks[confirmed_node.root]
    bid = confirmed_block.body.signed_execution_payload_bid.message
    if confirmed_node.payload_status == PAYLOAD_STATUS_FULL:
        return bid.block_hash
    else:
        return bid.parent_block_hash
```

## External API

### New `get_confirmed_node`

*Note*: Returns the deepest common ancestor of the current head and the latest
confirmed node, using the finalized node when the latter is outside the FG
frame. Ancestry includes payload status, so the result can be pending.

```python
def get_confirmed_node(store: Store) -> ForkChoiceNode:
    fg_frame = get_fg_frame(store)
    confirmed = (
        store.latest_confirmed
        if store.latest_confirmed in fg_frame.tree
        else fg_frame.finalized_node
    )
    head = get_head(store)
    return get_deepest_node(
        store,
        {
            node
            for node in fg_frame.tree
            if is_ancestor(store, confirmed, node) and is_ancestor(store, head, node)
        },
    )
```

### Modified `get_head`

*Note*: This function is modified to use the new fork-choice algorithm. It uses
current slot votes at or after the support cutoff, and previous slot votes
otherwise.

```python
def get_head(store: Store) -> ForkChoiceNode:
    current_slot = get_current_slot(store)
    if current_slot == GENESIS_SLOT:
        return ForkChoiceNode(
            root=store.finalized_checkpoint.root,
            payload_status=PAYLOAD_STATUS_EMPTY,
        )

    if get_time_into_slot_ms(store) >= get_support_cutoff_ms():
        slot = current_slot
    else:
        slot = current_slot - 1

    fg_frame = get_fg_frame(store)
    votes, support_votes = get_combined_local_view(
        store, slot, receipt_threshold_ms=INFINITE_TIME_MS, resolution_threshold_ms=INFINITE_TIME_MS
    )
    head = get_head_in_tree(
        store=store,
        fg_frame=fg_frame,
        tree=fg_frame.tree,
        votes=votes,
        support_votes=support_votes,
        slot=slot,
    )

    # Never return pending
    if head.payload_status == PAYLOAD_STATUS_PENDING:
        return ForkChoiceNode(root=head.root, payload_status=PAYLOAD_STATUS_EMPTY)
    else:
        return head
```
