# Phase 0 -- Fast Confirmation Rule

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Fast Confirmation Rule](#fast-confirmation-rule)
  - [Constants](#constants)
  - [Configuration](#configuration)
  - [Helpers](#helpers)
    - [Modified `Store`](#modified-store)
    - [Modified `get_forkchoice_store`](#modified-get_forkchoice_store)
    - [Misc helper functions](#misc-helper-functions)
      - [New `get_block_slot`](#new-get_block_slot)
      - [New `get_block_epoch`](#new-get_block_epoch)
      - [New `get_checkpoint_for_block`](#new-get_checkpoint_for_block)
      - [New `get_checkpoint_state`](#new-get_checkpoint_state)
      - [New `is_start_slot_at_epoch`](#new-is_start_slot_at_epoch)
      - [New `is_ancestor`](#new-is_ancestor)
      - [New `get_chain_roots`](#new-get_chain_roots)
    - [LMD-GHOST helpers](#lmd-ghost-helpers)
      - [New `get_slot_committee`](#new-get_slot_committee)
      - [New `get_block_support_between_slots`](#new-get_block_support_between_slots)
      - [New `is_full_validator_set_covered`](#new-is_full_validator_set_covered)
      - [New `adjust_committee_weight_estimate_to_ensure_safety`](#new-adjust_committee_weight_estimate_to_ensure_safety)
      - [New `estimate_committee_weight_between_slots`](#new-estimate_committee_weight_between_slots)
      - [New `get_equivocation_score`](#new-get_equivocation_score)
      - [New `compute_adversarial_weight`](#new-compute_adversarial_weight)
      - [New `get_adversarial_weight`](#new-get_adversarial_weight)
      - [New `compute_empty_slot_support_discount`](#new-compute_empty_slot_support_discount)
      - [New `get_support_discount`](#new-get_support_discount)
      - [New `is_one_lmd_ghost_safe`](#new-is_one_lmd_ghost_safe)
      - [New `is_confirmed_chain_safe`](#new-is_confirmed_chain_safe)
    - [FFG helpers](#ffg-helpers)
      - [New `get_checkpoint_score`](#new-get_checkpoint_score)
      - [New `compute_honest_ffg_support`](#new-compute_honest_ffg_support)
      - [New `will_no_conflicting_checkpoint_be_justified`](#new-will_no_conflicting_checkpoint_be_justified)
      - [New `will_checkpoint_be_justified`](#new-will_checkpoint_be_justified)
    - [New `find_latest_confirmed_descendant`](#new-find_latest_confirmed_descendant)
    - [New `get_latest_confirmed`](#new-get_latest_confirmed)
  - [Handlers](#handlers)
    - [New `on_tick_per_slot_after_attestations_applied`](#new-on_tick_per_slot_after_attestations_applied)

<!-- mdformat-toc end -->

## Introduction

This document specifies a fast block confirmation rule (a.k.a. FCR) for the Ethereum protocol.

*Note*: Confirmation is not a substitute for finality! The safety of confirmations is weaker than that of finality.

The research paper for this rule can be found [here](https://arxiv.org/abs/2405.00549).

This rule makes the following network synchrony assumption: starting from the current slot, attestations created by honest validators in any slot are received by the end of that slot.
Consequently, this rule provides confirmations to users who believe in the above assumption. If this assumption is broken, confirmed blocks can be reorged without any adversarial behavior and without slashing.

## Fast Confirmation Rule

### Constants

| Name                                            | Value    | Description                                                                                                                                                                                                                                                                                                                     |
| ----------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `COMMITTEE_WEIGHT_ESTIMATION_ADJUSTMENT_FACTOR` | `int(5)` | Per mille value to add to the estimation of the committee weight across a range of slots not covering a full epoch in order to ensure the safety of the confirmation rule with high probability. See [here](https://gist.github.com/saltiniroberto/9ee53d29c33878d79417abb2b4468c20) for an explanation about the value chosen. |

### Configuration

| Name                               | Value        | Max. Value                         | Description                                                                                             |
| ---------------------------------- | ------------ | ---------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `CONFIRMATION_BYZANTINE_THRESHOLD` | `uint64(25)` | `uint64(25)`                       | Assumed maximum percentage of Byzantine validators among the validator set.                             |
| `CONFIRMATION_SLASHING_THRESHOLD`  | `uint64(25)` | `CONFIRMATION_BYZANTINE_THRESHOLD` | Assumed maximum amount of stake that the adversary is willing to get slashed in order to reorg a block. |

### Helpers

#### Modified `Store`

*Note:* `Store` is extended with new fields required by the algorithm.
The `confirmed_root` field contains the root of the most recent confirmed block.

```python
@dataclass
class Store(object):
    time: uint64
    genesis_time: uint64
    justified_checkpoint: Checkpoint
    finalized_checkpoint: Checkpoint
    unrealized_justified_checkpoint: Checkpoint
    unrealized_finalized_checkpoint: Checkpoint
    proposer_boost_root: Root
    equivocating_indices: Set[ValidatorIndex]
    blocks: Dict[Root, BeaconBlock] = field(default_factory=dict)
    block_states: Dict[Root, BeaconState] = field(default_factory=dict)
    block_timeliness: Dict[Root, boolean] = field(default_factory=dict)
    checkpoint_states: Dict[Checkpoint, BeaconState] = field(default_factory=dict)
    latest_messages: Dict[ValidatorIndex, LatestMessage] = field(default_factory=dict)
    unrealized_justifications: Dict[Root, Checkpoint] = field(default_factory=dict)
    # New in [FCR]
    confirmed_root: Root
    prev_epoch_unrealized_justified_checkpoint: Checkpoint
    prev_slot_head: Root
```

#### Modified `get_forkchoice_store`

*Note*: The function is extended with initialization of the new fields added to the `Store`.

```python
def get_forkchoice_store(anchor_state: BeaconState, anchor_block: BeaconBlock) -> Store:
    assert anchor_block.state_root == hash_tree_root(anchor_state)
    anchor_root = hash_tree_root(anchor_block)
    anchor_epoch = get_current_epoch(anchor_state)
    justified_checkpoint = Checkpoint(epoch=anchor_epoch, root=anchor_root)
    finalized_checkpoint = Checkpoint(epoch=anchor_epoch, root=anchor_root)
    proposer_boost_root = Root()
    return Store(
        time=uint64(anchor_state.genesis_time + SECONDS_PER_SLOT * anchor_state.slot),
        genesis_time=anchor_state.genesis_time,
        justified_checkpoint=justified_checkpoint,
        finalized_checkpoint=finalized_checkpoint,
        unrealized_justified_checkpoint=justified_checkpoint,
        unrealized_finalized_checkpoint=finalized_checkpoint,
        proposer_boost_root=proposer_boost_root,
        equivocating_indices=set(),
        blocks={anchor_root: copy(anchor_block)},
        block_states={anchor_root: copy(anchor_state)},
        checkpoint_states={justified_checkpoint: copy(anchor_state)},
        unrealized_justifications={anchor_root: justified_checkpoint},
        # New in [FCR]
        confirmed_root=finalized_checkpoint.root,
        prev_epoch_unrealized_justified_checkpoint=justified_checkpoint,
        prev_slot_head=anchor_block,
    )
```

#### Misc helper functions

##### New `get_block_slot`

```python
def get_block_slot(store: Store, block_root: Root) -> Slot:
    """
    Return a slot of the block.
    """
    return store.blocks[block_root].slot
```

##### New `get_block_epoch`

```python
def get_block_epoch(store: Store, block_root: Root) -> Epoch:
    """
    Return an epoch of the block.
    """
    return compute_epoch_at_slot(store.blocks[block_root].slot)
```

##### New `get_checkpoint_for_block`

```python
def get_checkpoint_for_block(store: Store, block_root: Root, epoch: Epoch) -> Checkpoint:
    """
    Return a checkpoint in the chain of the block at the ``epoch``.
    """
    return Checkpoint(get_checkpoint_block(store, block_root, epoch), epoch)
```

##### New `get_checkpoint_state`

```python
def get_checkpoint_state(store: Store, checkpoint: Checkpoint) -> BeaconState:
    """
    Return the ``checkpoint`` state.
    """
    if checkpoint in store.checkpoint_states:
        return store.checkpoint_states[checkpoint]
    elif checkpoint.epoch == compute_epoch_at_slot(store.block_states[checkpoint.root].slot):
        return store.block_states[checkpoint.root]
    else:
        # Compute checkpoint state by applying process_slots to the post-state of the checkpoin block.
        checkpoint_state = copy(store.block_states[checkpoint.root])
        process_slots(checkpoint_state, compute_start_slot_at_epoch(target.epoch))
        return checkpoint_state
```

##### New `is_start_slot_at_epoch`

```python
def is_start_slot_at_epoch(slot: Slot) -> bool:
    """
    Return ``True`` if ``slot`` is the start slot of an epoch.
    """
    return compute_slots_since_epoch_start(slot) == 0
```

##### New `is_ancestor`

```python
def is_ancestor(store: Store, block_root: Root, ancestor_root: Root):
    """
    Return ``True`` if ``block_root`` is an ancestor of ``ancestor_root``.
    """
    return get_ancestor(store, block_root, store.blocks[ancestor_root].slot) == ancestor_root
```

##### New `get_chain_roots`

```python
def get_chain_roots(store: Store, ancestor_root: Root, block_root: Root) -> Sequence[Root]:
    """
    Return block roots between ``ancestor_root`` exclusive and ``block_root`` inclusive.
    """
    ancestor_slot = get_block_slot(store, ancestor_root)
    chain_roots = [block_root]
    while store.blocks[block_root].slot > ancestor_slot:
        block_root = store.blocks[block_root].parent_root
        chain_roots.insert(0, block_root)

    # Return list of roots if the ancestor_root is in the chain of block_root,
    # otherwise, return empty list.
    if ancestor_root == store.blocks[chain_roots[0]].parent_root:
        return chain_roots
    else:
        return []
```

#### LMD-GHOST helpers

##### New `get_slot_committee`

```python
def get_slot_committee(store: Store, slot: Slot) -> Sequence[ValidatorIndex]:
    """
    Return participants of all committees in ``slot``.
    Uses the checkpoint state of the head of the chain as a source of shuffling.
    """
    head = get_head(store)
    head_checkpoint = get_checkpoint_for_block(store, head, get_block_epoch(store, head))
    shuffling_source = get_checkpoint_state(store, head_checkpoint)
    participants = []
    committees_count = get_committee_count_per_slot(shuffling_source, compute_epoch_at_slot(slot))
    for i in range(committees_count):
        participants.append(get_beacon_committee(shuffling_source, slot, CommitteeIndex(i)))
    return participants
```

##### New `get_block_support_between_slots`

```python
def get_block_support_between_slots(
    store: Store, balance_source: BeaconState, block_root: Root, start_slot: Slot, end_slot: Slot
) -> Gwei:
    """
    Return support of the block between ``start_slot`` and ``end_slot`` (inclusive of both).
    """
    participants = []
    for slot in range(start_slot, end_slot + 1):
        participants.append(get_slot_committee(store, slot))
    unslashed_and_active_indices = [
        i
        for i in get_active_validator_indices(balance_source, get_current_epoch(balance_source))
        if (i in participants and not balance_source.validators[i].slashed)
    ]
    return Gwei(
        sum(
            balance_source.validators[i].effective_balance
            for i in unslashed_and_active_indices
            if (
                i in store.latest_messages
                and i not in store.equivocating_indices
                and store.latest_messages[i].root == block_root
            )
        )
    )
```

##### New `is_full_validator_set_covered`

```python
def is_full_validator_set_covered(start_slot: Slot, end_slot: Slot) -> bool:
    """
    Return ``True`` if the range between ``start_slot`` and ``end_slot`` (inclusive of both) includes an entire epoch.
    """
    start_full_epoch = compute_epoch_at_slot(start_slot + (SLOTS_PER_EPOCH - 1))
    end_full_epoch = compute_epoch_at_slot(end_slot + 1)

    return start_full_epoch < end_full_epoch
```

##### New `adjust_committee_weight_estimate_to_ensure_safety`

```python
def adjust_committee_weight_estimate_to_ensure_safety(estimate: Gwei) -> Gwei:
    """
    Adjust the ``estimate`` of the weight of a committee for a sequence of slots not covering a full epoch to
    ensure the safety of FCR with high probability.

    See https://gist.github.com/saltiniroberto/9ee53d29c33878d79417abb2b4468c20 for an explanation of why this is
    required.
    """
    return Gwei(estimate // 1000 * (1000 + COMMITTEE_WEIGHT_ESTIMATION_ADJUSTMENT_FACTOR))
```

##### New `estimate_committee_weight_between_slots`

```python
def estimate_committee_weight_between_slots(
    state: BeaconState, start_slot: Slot, end_slot: Slot
) -> Gwei:
    """
    Estimate the total weight of committees between ``start_slot`` and ``end_slot`` (inclusive of both).
    """
    total_active_balance = get_total_active_balance(state)

    start_epoch = compute_epoch_at_slot(start_slot)
    end_epoch = compute_epoch_at_slot(end_slot)

    # Sanity check
    if start_slot > end_slot:
        return Gwei(0)

    # If an entire epoch is covered by the range, return the total active balance
    if is_full_validator_set_covered(start_slot, end_slot):
        return total_active_balance

    if start_epoch == end_epoch:
        return total_active_balance // SLOTS_PER_EPOCH * (end_slot - start_slot + 1)
    else:
        # First, calculate the number of committees in the end epoch
        num_slots_in_end_epoch = compute_slots_since_epoch_start(end_slot) + 1
        # Next, calculate the number of slots remaining in the end epoch
        remaining_slots_in_end_epoch = SLOTS_PER_EPOCH - num_slots_in_end_epoch
        # Then, calculate the number of slots in the start epoch
        num_slots_in_start_epoch = SLOTS_PER_EPOCH - compute_slots_since_epoch_start(start_slot)

        end_epoch_weight_estimate = total_active_balance // SLOTS_PER_EPOCH * num_slots_in_end_epoch
        start_epoch_weight_estimate = (
            total_active_balance
            // SLOTS_PER_EPOCH
            // SLOTS_PER_EPOCH
            * num_slots_in_start_epoch
            * remaining_slots_in_end_epoch
        )

        # A range that spans an epoch boundary, but does not span any full epoch
        # needs pro-rata calculation
        return adjust_committee_weight_estimate_to_ensure_safety(
            Gwei(start_epoch_weight_estimate + end_epoch_weight_estimate)
        )
```

##### New `get_equivocation_score`

```python
def get_equivocation_score(
    store: Store, balance_source: BeaconState, start_slot: Slot, end_slot: Slot
) -> Gwei:
    """
    Return total weight of equivocating participants of all committees
    in the slots between ``start_slot`` and ``end_slot`` (inclusive of both).
    """
    committee_indices = set()
    for slot in range(start_slot, end_slot + 1):
        committee_indices.update(get_slot_committee(store, slot))

    equivocating_participants = committee_indices.intersection(store.equivocating_indices)
    return Gwei(
        sum(balance_source.validators[i].effective_balance for i in equivocating_participants)
    )
```

##### New `compute_adversarial_weight`

```python
def compute_adversarial_weight(
    store: Store, balance_source: BeaconState, start_slot: Slot, end_slot: Slot
) -> Gwei:
    """
    Compute maximum possible weight that can be adversarial in the committees of the slots
    between ``start_slot`` and ``end_slot`` (inclusive of both),
    assuming ``CONFIRMATION_BYZANTINE_THRESHOLD`` and discounting already equivocated validators.
    """
    maximum_weight = estimate_committee_weight_between_slots(balance_source, start_slot, end_slot)
    max_adversarial_weight = maximum_weight // 100 * CONFIRMATION_BYZANTINE_THRESHOLD

    # Discount total weight of equivocating validators.
    equivocation_score = get_equivocation_score(store, balance_source, start_slot, end_slot)
    if max_adversarial_weight > equivocation_score:
        return Gwei(max_adversarial_weight - equivocation_score)
    else:
        return Gwei(0)
```

##### New `get_adversarial_weight`

```python
def get_adversarial_weight(store: Store, balance_source: BeaconState, block_root: Root) -> Gwei:
    """
    Return maximum adversarial weight that can support the block.
    """
    current_slot = get_current_slot(store)
    block = store.blocks[block_root]
    if get_block_epoch(store, block_root) > get_block_epoch(store, block.parent_root):
        # Use the first epoch slot as the start slot when crossing epoch boundary.
        start_slot = compute_start_slot_at_epoch(get_block_epoch(store, block_root))
        return compute_adversarial_weight(store, balance_source, start_slot, current_slot - 1)
    else:
        return compute_adversarial_weight(store, balance_source, block.slot, current_slot - 1)
```

##### New `compute_empty_slot_support_discount`

```python
def compute_empty_slot_support_discount(
    store: Store, balance_source: BeaconState, block_root: Root
) -> Gwei:
    """
    Compute weight that can be discounted during the safety threshold computation
    if there are empty slots preceding the block.
    """
    block = store.blocks[block_root]
    parent_block = store.blocks[block.parent_root]
    # No empty slot.
    if parent_block.slot + 1 == block.slot:
        return Gwei(0)

    # Discount votes supporting the parent block if they are from the committees of empty slots.
    parent_support_in_empty_slots = get_block_support_between_slots(
        store, balance_source, block.parent_root, parent_block.slot + 1, block.slot - 1
    )
    # Adversarial weight is not discounted.
    adversarial_weight = compute_adversarial_weight(
        store, balance_source, parent_block.slot + 1, block.slot - 1
    )
    if parent_support_in_empty_slots > adversarial_weight:
        return parent_support_in_empty_slots - adversarial_weight
    else:
        return Gwei(0)
```

##### New `get_support_discount`

```python
def get_support_discount(store: Store, balance_source: BeaconState, block_root: Root) -> Gwei:
    """
    Return the weight that can ve discounted during the safety threshold computation for the block.
    """

    # Empty slot support discount
    return compute_empty_slot_support_discount(store, balance_source, block_root)
```

##### New `is_one_lmd_ghost_safe`

*Notes:*

This function checks if a single block is LMD-GHOST safe by computing LMD-GHOST safety indicator
and comparing its value to the safety threshold.

At a high level the computation checks whether the actual score of the block outweighs
potential score of any block conflicting with it cosidering total weight of the committees
and maximal adversarial weight.

If this check passes the block is deemed LMD-GHOST safe,
but it's not enough to say that the block will remain canonical.
To ensure the latter, each ancestor of the block would also have to pass this check.

More details on this check can be found in the [paper](https://arxiv.org/abs/2405.00549).

```python
def is_one_lmd_ghost_safe(store: Store, block_root: Root) -> bool:
    """
    Return ``True`` if and only if the block is LMD-GHOST safe.
    """
    current_slot = get_current_slot(store)
    block = store.blocks[block_root]
    parent_block = store.blocks[block.parent_root]
    balance_source = store.checkpoint_states[store.prev_epoch_unrealized_justified_checkpoint]

    support = get_attestation_score(store, block_root, balance_source)
    proposer_score = compute_proposer_score(balance_source)
    maximum_support = estimate_committee_weight_between_slots(
        balance_source, parent_block.slot + 1, current_slot - 1
    )
    support_discount = get_support_discount(store, balance_source, block_root)
    adversarial_weight = get_adversarial_weight(store, balance_source, block_root)

    # Returns whether the following condition is true using only integer arithmetic:
    # support / maximum_support >
    #   0.5 * (1 + (proposer_score - support_discount) / maximum_support) + adversarial_weight / maximum_support
    return (
        2 * support + support_discount > maximum_support + proposer_score + 2 * adversarial_weight
    )
```

##### New `is_confirmed_chain_safe`

*Notes*:

This function should be called at the start of each epoch to ensure that the confirmed chain
starting from `store.prev_epoch_unrealized_justified_checkpoint.root` remains LMD-GHOST safe.

This check relaxes synchrony assumption by allowing GST to start from the beginning of the previous slot
without violation of the confirmed chain safety. If such check was not run, GST start would have to be assumed
from the time of the first run of the algorithm which could happen a huge number of epochs ago.

```python
def is_confirmed_chain_safe(store: Store, confirmed_root: Root) -> bool:
    """
    Return ``True`` if and only if all blocks of the confirmed chain
    starting from prev_epoch_unrealized_justified_checkpoint are LMD-GHOST safe.
    """

    # Check if the confirmed_root is descendant of prev_epoch_unrealized_justified_checkpoint.
    if not is_ancestor(
        store, confirmed_root, store.prev_epoch_unrealized_justified_checkpoint.root
    ):
        return False

    current_epoch = get_current_store_epoch(store)
    if store.prev_epoch_unrealized_justified_checkpoint.epoch + 1 >= current_epoch:
        # Exclude unrealized checkpoint block if it is from the previous epoch
        # as the this block will always be canonical in this case.
        start_root = store.prev_epoch_unrealized_justified_checkpoint.root
    else:
        # Limit reconfirmation to the checkpoint block
        # as if it's successful, reconfirmation of the ancestors is implied.
        checkpoint = get_checkpoint_for_block(store, confirmed_root, current_epoch - 1)
        start_root = store.blocks[checkpoint.root].parent_root

    # Run is_one_lmd_ghost_safe for each block in the confirmed chain.
    chain_roots = get_chain_roots(store, start_root, confirmed_root)
    return all(is_one_lmd_ghost_safe(store, root) for root in chain_roots)
```

#### FFG helpers

##### New `get_checkpoint_score`

```python
def get_checkpoint_score(store: Store, target: Checkpoint) -> Gwei:
    """
    Estimate FFG support of the ``target`` by using LMD-GHOST votes.

    This function is supposed to be used only during the target's epoch
    and the start of the epoch next to it, otherwise, the estimation might not be correct.
    """
    # No attestation with a vote for the target has yet been processed
    if target not in store.checkpoint_states:
        return Gwei(0)

    state = store.checkpoint_states[checkpoint]
    unslashed_and_active_indices = [
        i
        for i in get_active_validator_indices(state, get_current_epoch(state))
        if not state.validators[i].slashed
    ]
    return Gwei(
        sum(
            state.validators[i].effective_balance
            for i in unslashed_and_active_indices
            if (
                i in store.latest_messages
                and i not in store.equivocating_indices
                and target
                == get_checkpoint_for_block(
                    store, store.latest_messages[i].root, store.latest_messages[i].epoch
                )
            )
        )
    )
```

##### New `compute_honest_ffg_support`

```python
def compute_honest_ffg_support(
    store: Store, checkpoint: Checkpoint, checkpoint_state: BeaconState
) -> Gwei:
    """
    Compute honest FFG support of the ``checkpoint``.

    Takes into account observed votes supporting the ``checkpoint`` and
    assumes ``CONFIRMATION_BYZANTINE_THRESHOLD`` and ``CONFIRMATION_SLASHING_THRESHOLD``.
    This function works correctly only till the beginning of the epoch next to the ``checkpoint``'s epoch.
    """
    current_slot = get_current_slot(store)
    current_epoch = compute_epoch_at_slot(current_slot)
    total_active_balance = get_total_active_balance(checkpoint_state)

    # Compute FFG support for checkpoint
    ffg_support_for_checkpoint = get_checkpoint_score(store, checkpoint)

    # Compute total FFG weight till current slot exclusive
    ffg_weight_till_now = estimate_committee_weight_between_slots(
        checkpoint_state, compute_start_slot_at_epoch(current_epoch), current_slot - 1
    )

    # Compute remaining honest FFG weight
    remaining_ffg_weight = total_active_balance - ffg_weight_till_now
    remaining_honest_ffg_weight = Gwei(
        remaining_ffg_weight // 100 * (100 - config.CONFIRMATION_BYZANTINE_THRESHOLD)
    )

    # Compute min honest FFG support
    min_honest_ffg_support = ffg_support_for_checkpoint - min(
        Gwei(ffg_weight_till_now // 100 * config.CONFIRMATION_BYZANTINE_THRESHOLD),
        Gwei(ffg_weight_till_now // 100 * config.CONFIRMATION_SLASHING_THRESHOLD),
        ffg_support_for_checkpoint,
    )

    return Gwei(min_honest_ffg_support + remaining_honest_ffg_weight)
```

##### New `will_no_conflicting_checkpoint_be_justified`

```python
def will_no_conflicting_checkpoint_be_justified(store: Store, checkpoint: Checkpoint) -> bool:
    """
    Return ``True`` if and only if no checkpoint conflicting with the ``checkpoint`` can ever be justified.
    """

    # If checkpoint is unrealized justified then no conflicting checkpoint can be justified.
    if checkpoint == store.unrealized_justified_checkpoint:
        return True

    state = get_checkpoint_state(store, checkpoint)
    total_active_balance = get_total_active_balance(state)
    honest_ffg_support = compute_honest_ffg_support(store, checkpoint, state)
    return 3 * honest_ffg_support >= 1 * total_active_balance
```

##### New `will_checkpoint_be_justified`

```python
def will_checkpoint_be_justified(store: Store, checkpoint: Checkpoint) -> bool:
    """
    Return ``True`` if and only if the ``checkpoint`` will eventually be justified.
    """
    state = get_checkpoint_state(store, checkpoint)
    total_active_balance = get_total_active_balance(state)
    honest_ffg_support = compute_honest_ffg_support(store, checkpoint, state)
    return 3 * honest_ffg_support >= 2 * total_active_balance
```

#### New `find_latest_confirmed_descendant`

*Notes*:

This function examines canonical chain blocks starting from `latest_confirmed_root`
and returns the most recent block that satisfies FCR conditions:

1. Each block in its chain is LMD-GHOST safe,
   i.e. will be the winner of the LMD-GHOST fork choice rule starting from the current moment in time.
2. The block will not be filtered out during the current and the next epochs.

Assuming synchrony and `CONFIRMATION_BYZANTINE_THRESHOLD` value, the above criteria
ensures that the block returned by this function will remain canonical in the view
of all honest validators starting from the current moment in time.

This function works correctly only if the `latest_confirmed_root` belongs to the canonical chain
and is either from the previous or from the current epoch.

```python
def find_latest_confirmed_descendant(store: Store, latest_confirmed_root: Root) -> Root:
    """
    Return the most recent confirmed block in the suffix of the canonical chain
    starting from ``latest_confirmed_root``.
    """
    head = get_head(store)
    current_epoch = get_current_store_epoch(store)
    confirmed_root = latest_confirmed_root

    if (
        get_block_epoch(store, confirmed_root) + 1 == current_epoch
        and get_voting_source(store, store.prev_slot_head).epoch + 2 >= current_epoch
        and (
            is_start_slot_at_epoch(get_current_slot(store))
            or (
                will_no_conflicting_checkpoint_be_justified(
                    store, get_checkpoint_for_block(store, head, current_epoch)
                )
                and (
                    store.unrealized_justifications[store.prev_slot_head].epoch + 1 >= current_epoch
                    or store.unrealized_justifications[head].epoch + 1 >= current_epoch
                )
            )
        )
    ):
        # Get suffix of the canonical chain
        canonical_roots = get_chain_roots(store, confirmed_root, head)

        # Starting with the child of the latest_confirmed_root
        # move towards the head in attempt to advance confirmed block
        # and stop when the first unconfirmed descendant is encountered
        for block_root in canonical_roots:
            block_epoch = get_block_epoch(store, block_root)

            # If the current epoch is reached, exit the loop
            # as this code is meant to confirm blocks from the previous epoch
            if block_epoch == current_epoch:
                break

            # The algorithm can only rely on the previous head
            # if it is a descendant of the block that is attempted to be confirmed
            if not is_ancestor(store, store.prev_slot_head, block_root):
                break

            if not is_one_lmd_ghost_safe(store, block_root):
                break

            confirmed_root = block_root

    if (
        is_start_slot_at_epoch(get_current_slot(store))
        or store.unrealized_justifications[head].epoch + 1 >= current_epoch
    ):
        # Get suffix of the canonical chain
        canonical_roots = get_chain_roots(store, confirmed_root, head)

        tentative_confirmed_root = confirmed_root

        for block_root in canonical_roots:
            block_epoch = get_block_epoch(store, block_root)
            tentative_confirmed_epoch = get_block_epoch(store, tentative_confirmed_root)

            # The following condition can only be true the first time
            # the algorithm advances to a block from the current epoch
            if block_epoch > tentative_confirmed_epoch:
                # To confirm blocks from the current epoch ensure that
                # current epoch checkpoint will be justified
                checkpoint = get_checkpoint_for_block(store, block_root, block_epoch)
                if not will_checkpoint_be_justified(store, checkpoint):
                    break

            if not is_one_lmd_ghost_safe(store, block_root):
                break

            tentative_confirmed_root = block_root

        # The tentative_confirmed_root can only be confirmed
        # if it is for sure not going to be reorged out in either the current or next epoch.
        if get_block_epoch(store, tentative_confirmed_root) == current_epoch or (
            get_voting_source(store, tentative_confirmed_root).epoch + 2 >= current_epoch
            and (
                is_start_slot_at_epoch(get_current_slot(store))
                or will_no_conflicting_checkpoint_be_justified(
                    store, get_checkpoint_for_block(store, head, current_epoch)
                )
            )
        ):
            confirmed_root = tentative_confirmed_root

    return confirmed_root
```

#### New `get_latest_confirmed`

*Notes:*

This function executes the FCR algorithm which takes the following sequence of actions:

1. Check if the `store.confirmed_root` belongs to the canonical chain and is not older than the previous epoch.
2. Check if the confirmed chain starting from the `store.prev_epoch_unrealized_justified_checkpoint`
   can be re-confirmed at the start of the current epoch which resets GST to the start of the current epoch.
3. If any of the above checks fail, set `store.confirmed_root` to the `store.finalized_checkpoint.root`.
   Either of the above conditions signify that FCR assumptions (at least synchrony) are broken and the confirmed block might not be safe.
4. Restart the confirmation chain by setting `store.confirmed_root` to `store.prev_epoch_unrealized_justified_checkpoint.root`
   if the restart conditions are met. Under synchrony, such a checkpoint is for sure now the greatest justified checkpoint in the view
   of any honest validator and, therefore, any honest validator will keep voting for it for the entire epoch.
5. Attempt to advance the `store.confirmed_root` by calling `find_latest_confirmed_descendant`.

```python
def get_latest_confirmed(store: Store) -> Root:
    """
    Return the most recent confirmed block by executing the FCR algorithm.
    """
    confirmed_root = store.confirmed_root
    current_epoch = get_current_store_epoch(store)

    # Revert to finalized block if either of the following is true:
    # 1) the latest confirmed block's epoch is older than the previous epoch,
    # 2) the latest confirmed block doesn't belong to the canonical chain,
    # 3) the confirmed chain starting from the previous epoch unrealized justified checkpoint
    #    cannot be re-confirmed at the start of the current epoch.
    head = get_head(store)
    if (
        get_block_epoch(store, confirmed_root) + 1 < current_epoch
        or not is_ancestor(store, head, confirmed_root)
        or (
            is_start_slot_at_epoch(get_current_slot(store))
            and not is_confirmed_chain_safe(store, confirmed_root)
        )
    ):
        confirmed_root = store.finalized_checkpoint.root

    # Restart the confirmation chain if each of the following conditions are true:
    # 1) it is the start of the current epoch,
    # 2) epoch of store.prev_epoch_unrealized_justified_checkpoint equals to the previous epoch,
    # 3) confirmed block is older than the block of store.prev_epoch_unrealized_justified_checkpoint.
    if (
        is_start_slot_at_epoch(get_current_slot(store))
        and store.prev_epoch_unrealized_justified_checkpoint.epoch + 1 == current_epoch
        and get_block_slot(confirmed_root)
        < get_block_slot(store.prev_epoch_unrealized_justified_checkpoint.root)
    ):
        confirmed_root = store.prev_epoch_unrealized_justified_checkpoint.root

    # Attempt to further advance the latest confirmed block.
    if get_block_epoch(store, confirmed_root) + 1 >= current_epoch:
        return find_latest_confirmed_descendant(store, confirmed_root)
    else:
        return confirmed_root
```

### Handlers

#### New `on_tick_per_slot_after_attestations_applied`

```python
def on_tick_per_slot_after_attestations_applied(store: Store):
    # call sequence must be:
    # 1) on_tick(store) handler
    # 2) attestations from the previous slot are apllied to the store
    # 3) on_tick_per_slot_after_attestations_applied(store) is called
    store.confirmed_root = get_latest_confirmed(store)
    if is_start_slot_at_epoch(get_current_slot(store) + 1):
        store.prev_epoch_unrealized_justified_checkpoint = store.unrealized_justified_checkpoint
    store.prev_slot_head = get_head(store)
```
