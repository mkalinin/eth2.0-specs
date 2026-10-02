# Decoupled consensus -- The Beacon Chain

*Note*: This document is a work-in-progress for researchers and implementers.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
  - [TODO](#todo)
  - [Design notes](#design-notes)
    - [Heights and rounds](#heights-and-rounds)
    - [Beacon committees](#beacon-committees)
    - [`AttestationData2`, `IndexedAttestation2`, `AttesterSlashing2`](#attestationdata2-indexedattestation2-attesterslashing2)
    - [Available chain committee and participation](#available-chain-committee-and-participation)
- [Types](#types)
  - [New `Height`](#new-height)
  - [New `Round`](#new-round)
  - [New `AvailableChainCommitteeIndices`](#new-availablechaincommitteeindices)
  - [New `AvailableChainCommittee`](#new-availablechaincommittee)
  - [New `AvailableChainParticipation`](#new-availablechainparticipation)
  - [Modified `CommitteeBits`](#modified-committeebits)
- [Constants](#constants)
  - [Misc](#misc)
  - [Domains](#domains)
  - [Participation flag indices](#participation-flag-indices)
- [Presets](#presets)
  - [Misc](#misc-1)
  - [Available chain](#available-chain)
  - [Time parameters](#time-parameters)
- [Configuration](#configuration)
- [Containers](#containers)
  - [New containers](#new-containers)
    - [`HeightPair`](#heightpair)
    - [`AttestationData2`](#attestationdata2)
    - [`IndexedAttestation2`](#indexedattestation2)
    - [`AttesterSlashing2`](#attesterslashing2)
    - [`AvailableChainAttestationData`](#availablechainattestationdata)
    - [`AvailableChainAttestation`](#availablechainattestation)
  - [Modified containers](#modified-containers)
    - [`Attestation`](#attestation)
    - [`BeaconBlockBody`](#beaconblockbody)
    - [`BeaconState`](#beaconstate)
- [Helpers](#helpers)
  - [Finality and participation](#finality-and-participation)
    - [New `has_quorum`](#new-has_quorum)
  - [Slashings](#slashings)
    - [New `is_slashable_attestation_data_2`](#new-is_slashable_attestation_data_2)
  - [Available chain attestations](#available-chain-attestations)
    - [New `is_available_chain_attestation_same_slot`](#new-is_available_chain_attestation_same_slot)
    - [New `compute_available_chain_committee`](#new-compute_available_chain_committee)
    - [New `is_eligible_available_chain_attester`](#new-is_eligible_available_chain_attester)
    - [New `is_valid_available_chain_attestation_data`](#new-is_valid_available_chain_attestation_data)
    - [New `is_valid_available_chain_attestation`](#new-is_valid_available_chain_attestation)
    - [New `is_matching_head_attestation`](#new-is_matching_head_attestation)
    - [New `update_builder_payment_participation`](#new-update_builder_payment_participation)
  - [Attestations](#attestations)
    - [New `is_valid_attestation_data`](#new-is_valid_attestation_data)
    - [New `is_valid_aggregation_bits`](#new-is_valid_aggregation_bits)
    - [New `get_height_participation_flag_indices`](#new-get_height_participation_flag_indices)
    - [New `get_indexed_attestation_2`](#new-get_indexed_attestation_2)
    - [New `is_valid_indexed_attestation_2`](#new-is_valid_indexed_attestation_2)
  - [Misc](#misc-2)
    - [New `remove_flag`](#new-remove_flag)
    - [New `compute_round_at_slot`](#new-compute_round_at_slot)
    - [New `compute_start_slot_at_round`](#new-compute_start_slot_at_round)
    - [New `compute_epoch_at_round`](#new-compute_epoch_at_round)
    - [Modified `compute_ptc`](#modified-compute_ptc)
  - [Beacon state accessors](#beacon-state-accessors)
    - [Modified `get_beacon_committee`](#modified-get_beacon_committee)
    - [Modified `get_attesting_indices`](#modified-get_attesting_indices)
    - [Modified `get_builder_payment_quorum_threshold`](#modified-get_builder_payment_quorum_threshold)
- [Beacon chain state transition function](#beacon-chain-state-transition-function)
  - [Process height events](#process-height-events)
  - [Round processing](#round-processing)
    - [New `process_round`](#new-process_round)
  - [Epoch processing](#epoch-processing)
    - [Modified `process_epoch`](#modified-process_epoch)
    - [Modified `process_participation_flag_updates`](#modified-process_participation_flag_updates)
    - [Modified `process_pending_deposits`](#modified-process_pending_deposits)
    - [Modified `process_builder_pending_payments`](#modified-process_builder_pending_payments)
    - [New `process_builder_payment_participation`](#new-process_builder_payment_participation)
  - [Block processing](#block-processing)
    - [Operations](#operations)
      - [Modified `process_operations`](#modified-process_operations)
      - [Attestations](#attestations-1)
        - [`process_attestation`](#process_attestation)
      - [Available chain votes](#available-chain-votes)
        - [`process_available_chain_attestation`](#process_available_chain_attestation)
      - [Deposits](#deposits)
        - [Modified `add_validator_to_registry`](#modified-add_validator_to_registry)
      - [Attester slashings](#attester-slashings)
        - [`process_attester_slashing2`](#process_attester_slashing2)

<!-- mdformat-toc end -->

## Introduction

### TODO

- [x] Finality gadget
- [x] Available chain
- [ ] Rewards and penalties
- [ ] Inactivity leak
- [ ] Fork transition
- [ ] Stabilization gadget and healing
- [ ] Ensure that attesting indices in `IndexedAttestation2` aren't going to
  blow up a block
- [ ] Figure out checkpoint sync
- [ ] Cleanup `BeaconState`

### Design notes

#### Heights and rounds

Height and finality advance as soon as the corresponding quorum is reached. When
validators observe the target and finality change, they immediately start voting
to support a new target. In the happy case, this reduces the time to finality to
2/3 of a round duration on average.

*Note*: a proposer can end up on a branch that does not yet contain enough votes
to advance the target, while some attesters are on a competing branch with a
more advanced target. In that case the proposer cannot include those attesters'
votes.

Under this approach, a round is responsible for getting the whole validator set
to vote and for tracking participation. Participation is set when a validator
has voted for the current or the previous target, so that validators are not
penalized for failing to catch up with the most advanced height before
submitting a vote.

Round participation is used to compute rewards, penalties, and inactivity
updates, much like epoch participation. If the height does not advance during a
round, height participation should be used instead, so that validators who
fulfilled their duties for the current height in previous rounds are not
penalized or leaked.

*Note*: the rewards and penalties system should be checked carefully.

For the height-advancement approach above to be efficient, a committee rotation
strategy should keep the overlap between the committees at the end of the
current round and the start of the next round reasonably small.

#### Beacon committees

Beacon committees are no longer a security unit as they once were. They now
serve to distribute network load and to split the on-chain attestation data used
for inclusion.

This makes it possible to drop shuffling in favor of a simple rotation strategy,
so that validators eventually vote at different points of the round.

The current rotation strategy simply shifts the validator set left by `1` every
round, which provides the low-overlap property described in the previous
section.

*Note*: investigate the potential security implications of the new "committee"
mechanism.

Another important design point is to reduce client complexity by making
committee selection depend on state that is stable across branches. The current
logic ties it to the most recent finalized epoch and to the set of validators
that have not exited by that epoch. Validators that exit after that epoch cease
to be permitted in the `aggregation_bits` once the state reaches their exit
epoch.

Since activations are gated by finality, no new validators are added until the
next finality advancement. Newly added validators are not activated earlier than
`1 + MAX_SEED_LOOKAHEAD` epochs into the future, which should be enough for all
nodes in the network to catch up with the most recent finalized pair and agree
on the active validator set before newly activated validators start attesting.

An alternative to the finalized epoch is `epoch(attestation.data.target)`.

#### `AttestationData2`, `IndexedAttestation2`, `AttesterSlashing2`

These new types are introduced to keep supporting old slashings after the fork
transition.

Alternatively, old attester slashings could be dropped after the fork
transition. In that case the network would rely on the fact that nodes never
revert a finalized checkpoint and that a majority of nodes stay online until a
block is finalized by the new finality gadget after the transition. Checkpoint
sync would then have to use a newly finalized block.

We will at least have to add `AttestationData2`, since `AttestationData` is not
a `ProgressiveContainer`. A new `DOMAIN_BEACON_ATTESTER_2` is introduced to sign
the new attestations.

*Note*: the `_2` and `2` suffixes are ugly; it is worth finding a better way to
distinguish the new and old types.

#### Available chain committee and participation

The committee can be replaced with VRF selection.

Available chain participation is introduced to compute builder payment weights
and preserve the guarantees introduced by Gloas.

*Note*: consider removing that complexity by computing the payment weight from
the next slot's proposal only.

## Types

### New `Height`

```python
class Height(Uint64):
    """
    Finality gadget height.
    """
```

### New `Round`

```python
class Round(Uint64):
    """
    Finality gadget round.
    """
```

### New `AvailableChainCommitteeIndices`

```python
class AvailableChainCommitteeIndices(List[ValidatorIndex]):
    LIMIT = AVAILABLE_CHAIN_COMMITTEE_SIZE
```

### New `AvailableChainCommittee`

```python
class AvailableChainCommittee(Vector[ValidatorIndex]):
    LENGTH = AVAILABLE_CHAIN_COMMITTEE_SIZE
```

### New `AvailableChainParticipation`

```python
class AvailableChainParticipation(Vector[AvailableChainCommitteeIndices]):
    LENGTH = 2 * SLOTS_PER_EPOCH
```

### Modified `CommitteeBits`

```python
class CommitteeBits(BitVector):
    """
    Bits marking which committees of a round participate in an attestation.
    """

    LENGTH = COMMITTEES_PER_ROUND
```

## Constants

### Misc

| Name           | Value               |
| -------------- | ------------------- |
| `EMPTY_HEIGHT` | `Uint64(2**64 - 1)` |

### Domains

| Name                              | Value                      |
| --------------------------------- | -------------------------- |
| `DOMAIN_BEACON_ATTESTER_2`        | `DomainType('0x11000000')` |
| `DOMAIN_AVAILABLE_CHAIN_ATTESTER` | `DomainType('0x12000000')` |

### Participation flag indices

| Name                  | Value       |
| --------------------- | ----------- |
| `FINALITY_FLAG_INDEX` | `Uint64(0)` |
| `TARGET_FLAG_INDEX`   | `Uint64(1)` |
| `PROGRESS_FLAG_INDEX` | `Uint64(2)` |

## Presets

### Misc

| Name                           | Value                       |
| ------------------------------ | --------------------------- |
| `COMMITTEES_PER_ROUND`         | `Uint64(2**11)` (= 2,048)   |
| `MAX_VALIDATORS_PER_AGGREGATE` | `Uint64(2**17)` (= 131,072) |

### Available chain

| Name                             | Value                     |
| -------------------------------- | ------------------------- |
| `AVAILABLE_CHAIN_COMMITTEE_SIZE` | `Uint64(2**10)` (= 1,024) |

### Time parameters

| Name              | Value                |
| ----------------- | -------------------- |
| `SLOTS_PER_ROUND` | `Uint64(2**3)` (= 8) |

## Configuration

## Containers

### New containers

#### `HeightPair`

```python
class HeightPair(Container):
    height: Height
    root: Root
```

#### `AttestationData2`

```python
class AttestationData2(Container):
    round: Round
    finalize_pair: HeightPair
    target_pair: HeightPair
```

#### `IndexedAttestation2`

```python
class IndexedAttestation2(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=3)

    attesting_indices: AttestingIndices
    data: AttestationData2
    signature: BLSSignature
```

#### `AttesterSlashing2`

```python
class AttesterSlashing2(Container):
    attestation_1: IndexedAttestation2
    attestation_2: IndexedAttestation2
```

#### `AvailableChainAttestationData`

```python
class AvailableChainAttestationData(Container):
    root: Root
    slot: Slot
    payload_status: PayloadStatus
```

#### `AvailableChainAttestation`

```python
class AvailableChainAttestation(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=3)

    attesting_indices: AvailableChainCommitteeIndices
    data: AvailableChainAttestationData
    signature: BLSSignature
```

### Modified containers

#### `Attestation`

```python
class Attestation(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=5, gaps=(1))

    aggregation_bits: AggregationBits
    # [Modified in DC]
    # data: AttestationData
    signature: BLSSignature
    # [Modified in DC]
    committee_bits: CommitteeBits
    # [New in DC]
    data: AttestationData2
```

#### `BeaconBlockBody`

```python
class BeaconBlockBody(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=15)

    randao_reveal: BLSSignature
    eth1_data: Eth1Data
    graffiti: Bytes32
    proposer_slashings: ProposerSlashings
    attester_slashings: AttesterSlashings
    # [Modified in DC]
    attestations: Attestations
    deposits: Deposits
    voluntary_exits: VoluntaryExits
    sync_aggregate: SyncAggregate
    bls_to_execution_changes: BLSToExecutionChanges
    signed_execution_payload_bid: SignedExecutionPayloadBid
    payload_attestations: PayloadAttestations
    parent_execution_requests: ExecutionRequests
    # [New in DC]
    available_chain_attestations: ProgressiveList[AvailableChainAttestation]
    attester_slashings_2: ProgressiveList[AttesterSlashing2]
```

#### `BeaconState`

```python
class BeaconState(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=56)

    genesis_time: Uint64
    genesis_validators_root: Root
    slot: Slot
    fork: Fork
    latest_block_header: BeaconBlockHeader
    block_roots: BlockRoots
    state_roots: StateRoots
    historical_roots: HistoricalRoots
    eth1_data: Eth1Data
    eth1_data_votes: Eth1DataVotes
    eth1_deposit_index: Uint64
    validators: Validators
    balances: Balances
    randao_mixes: RandaoMixes
    slashings: Slashings
    previous_epoch_participation: EpochParticipation
    current_epoch_participation: EpochParticipation
    justification_bits: JustificationBits
    previous_justified_checkpoint: Checkpoint
    current_justified_checkpoint: Checkpoint
    finalized_checkpoint: Checkpoint
    inactivity_scores: InactivityScores
    current_sync_committee: SyncCommittee
    next_sync_committee: SyncCommittee
    latest_block_hash: Hash32
    next_withdrawal_index: WithdrawalIndex
    next_withdrawal_validator_index: ValidatorIndex
    historical_summaries: HistoricalSummaries
    deposit_requests_start_index: Uint64
    deposit_balance_to_consume: Gwei
    exit_balance_to_consume: Gwei
    earliest_exit_epoch: Epoch
    consolidation_balance_to_consume: Gwei
    earliest_consolidation_epoch: Epoch
    pending_deposits: PendingDeposits
    pending_partial_withdrawals: PendingPartialWithdrawals
    pending_consolidations: PendingConsolidations
    proposer_lookahead: ProposerLookahead
    builders: Builders
    next_withdrawal_builder_index: BuilderIndex
    execution_payload_availability: ExecutionPayloadAvailability
    builder_pending_payments: BuilderPendingPayments
    builder_pending_withdrawals: BuilderPendingWithdrawals
    latest_execution_payload_bid: ExecutionPayloadBid
    payload_expected_withdrawals: Withdrawals
    ptc_window: PayloadTimelinessCommitteeWindow
    # [New in DC]
    builder_payment_participation: AvailableChainParticipation
    height_participation: EpochParticipation
    previous_round_participation: EpochParticipation
    current_round_participation: EpochParticipation
    finalized_pair: HeightPair
    justified_pair: HeightPair
    target_pair: HeightPair
    finalized_slot: Slot
    justified_slot: Slot
    target_slot: Slot
```

## Helpers

### Finality and participation

#### New `has_quorum`

```python
def has_quorum(state: BeaconState, flag_index: int) -> bool:
    epoch = get_current_epoch(state)
    active_validator_indices = get_active_validator_indices(state, epoch)
    unslashed_participating_indices = {
        index
        for index in active_validator_indices
        if has_flag(state.height_participation[index], flag_index)
        and not state.validators[index].slashed
    }
    support = get_total_balance(state, unslashed_participating_indices)
    total_active_balance = get_total_active_balance(state)
    return support * 3 >= total_active_balance * 2
```

### Slashings

#### New `is_slashable_attestation_data_2`

```python
def is_slashable_attestation_data_2(data_1: AttestationData2, data_2: AttestationData2) -> bool:
    """
    Check if ``data_1`` and ``data_2`` are slashable according to Finality gadget rules.
    """

    def is_target_conflicting_with_finality(finality: HeightPair, target: HeightPair) -> bool:
        # Target vote conflicts with non-empty finality vote
        return (
            finality.root != Root()
            and finality.height == target.height
            and finality.root != target.root
        )

    return (
        # Target vote conflicts with finality vote
        (
            is_target_conflicting_with_finality(data_1.finalize_pair, data_2.target_pair)
            or is_target_conflicting_with_finality(data_2.finalize_pair, data_1.target_pair)
        )
        or
        # Conflicting non-empty target votes
        (
            data_1.target_pair.root != Root()
            and data_2.target_pair.root != Root()
            and data_1.target_pair.height == data_2.target_pair.height
            and data_1.target_pair.root != data_2.target_pair.root
        )
    )
```

### Available chain attestations

#### New `is_available_chain_attestation_same_slot`

```python
def is_available_chain_attestation_same_slot(
    state: BeaconState, data: AvailableChainAttestationData
) -> bool:
    if data.slot == GENESIS_SLOT:
        return True

    slot_blockroot = get_block_root_at_slot(state, data.slot)
    prev_blockroot = get_block_root_at_slot(state, data.slot - 1)

    return data.root == slot_blockroot and data.root != prev_blockroot
```

#### New `compute_available_chain_committee`

```python
def compute_available_chain_committee(state: BeaconState, slot: Slot) -> AvailableChainCommittee:
    epoch = compute_epoch_at_slot(slot)
    seed = sha256(get_seed(state, epoch, DOMAIN_AVAILABLE_CHAIN_ATTESTER) + uint_to_bytes(slot))
    indices = get_active_validator_indices(state, epoch)
    return AvailableChainCommittee(
        data=compute_balance_weighted_selection(
            state, indices, seed, size=AVAILABLE_CHAIN_COMMITTEE_SIZE, shuffle_indices=True
        )
    )
```

#### New `is_eligible_available_chain_attester`

```python
def is_eligible_available_chain_attester(
    state: BeaconState, slot: Slot, index: ValidatorIndex
) -> bool:
    return index in compute_available_chain_committee(state, slot)
```

#### New `is_valid_available_chain_attestation_data`

```python
def is_valid_available_chain_attestation_data(
    state: BeaconState, data: AvailableChainAttestationData
) -> bool:
    # Slot
    epoch = compute_epoch_at_slot(data.slot)
    if data.slot + MIN_ATTESTATION_INCLUSION_DELAY > state.slot:
        return False

    if epoch not in (get_previous_epoch(state), get_current_epoch(state)):
        return False

    # Payload status
    if is_available_chain_attestation_same_slot(state, data):
        if data.payload_status != PAYLOAD_STATUS_EMPTY:
            return False
    elif data.payload_status not in (PAYLOAD_STATUS_EMPTY, PAYLOAD_STATUS_FULL):
        return False

    return True
```

#### New `is_valid_available_chain_attestation`

```python
def is_valid_available_chain_attestation(
    state: BeaconState, attestation: AvailableChainAttestation
) -> bool:
    # Verify indices are non-empty, sorted and has no duplicates
    data = attestation.data
    indices = attestation.attesting_indices
    if len(indices) == 0 or list(indices) != sorted(indices) or len(indices) > len(set(indices)):
        return False

    # Check attestation data
    if not is_valid_available_chain_attestation_data(state, data):
        return False

    # Check if all indices are eligible
    if any(not is_eligible_available_chain_attester(state, data.slot, index) for index in indices):
        return False

    # Verify aggregate signature
    pubkeys = [state.validators[i].pubkey for i in indices]
    domain = get_domain(state, DOMAIN_AVAILABLE_CHAIN_ATTESTER, compute_epoch_at_slot(data.slot))
    signing_root = compute_signing_root(data, domain)
    return bls.FastAggregateVerify(pubkeys, signing_root, attestation.signature)
```

#### New `is_matching_head_attestation`

```python
def is_matching_head_attestation(
    state: BeaconState, data: AvailableChainAttestationData, parent_slot: Slot
) -> bool:
    head_root_matches = data.root == get_block_root_at_slot(state, data.slot)
    if is_available_chain_attestation_same_slot(state, data):
        return head_root_matches
    else:
        slot_index = parent_slot % SLOTS_PER_HISTORICAL_ROOT
        payload_index = state.execution_payload_availability[slot_index]
        payload_matches = Uint64(data.payload_status) == Uint64(payload_index)
        return head_root_matches and payload_matches
```

#### New `update_builder_payment_participation`

```python
def update_builder_payment_participation(
    state: BeaconState, attestation: AvailableChainAttestation
) -> None:
    data = attestation.data
    epoch = compute_epoch_at_slot(data.slot)
    if epoch == get_current_epoch(state):
        payment_index = SLOTS_PER_EPOCH + data.slot % SLOTS_PER_EPOCH
    else:
        payment_index = data.slot % SLOTS_PER_EPOCH
    participation = state.builder_payment_participation[payment_index]
    for index in attestation.attesting_indices:
        if index not in participation and is_available_chain_attestation_same_slot(state, data):
            participation.append(index)
```

### Attestations

#### New `is_valid_attestation_data`

```python
def is_valid_attestation_data(
    state: BeaconState,
    data: AttestationData2,
) -> bool:
    # Current or a previous round
    current_round = compute_round_at_slot(state.slot)
    if data.round + 1 != current_round and data.round != current_round:
        return False

    # Empty target and finalize
    if data.target_pair == data.finalize_pair and data.target_pair == HeightPair(
        height=EMPTY_HEIGHT, root=Root()
    ):
        return False

    is_valid_target_root = data.target_pair.root in (
        Root(),
        state.target_pair.root,
        state.justified_pair.root,
    )
    is_valid_target_height = data.target_pair.height in (
        EMPTY_HEIGHT,
        state.target_pair.height,
        state.justified_pair.height,
    )
    is_valid_finalize_root = data.finalize_pair.root in (
        Root(),
        state.justified_pair.root,
        state.finalized_pair.root,
    )
    is_valid_finalize_height = data.finalize_pair.height in (
        EMPTY_HEIGHT,
        state.justified_pair.height,
        state.finalized_pair.height,
    )

    return (
        is_valid_target_root
        and is_valid_target_height
        and is_valid_finalize_root
        and is_valid_finalize_height
    )
```

#### New `is_valid_aggregation_bits`

```python
def is_valid_aggregation_bits(state: BeaconState, attestation: Attestation) -> bool:
    committee_indices = get_committee_indices(attestation.committee_bits)
    committee_offset = 0
    current_epoch = get_current_epoch(state)
    for committee_index in committee_indices:
        # [Modified in DC]
        committee = get_beacon_committee(state, attestation.data.round, committee_index)
        committee_attesters = {
            attester_index
            for i, attester_index in enumerate(committee)
            if attestation.aggregation_bits[committee_offset + i]
        }
        if len(committee_attesters) == 0:
            return False
        if any(
            not is_active_validator(state.validators[index], current_epoch)
            for index in committee_attesters
        ):
            return False
        committee_offset += len(committee)
    return True
```

#### New `get_height_participation_flag_indices`

```python
def get_height_participation_flag_indices(
    data: AttestationData2,
    target_pair: HeightPair,
    justified_pair: HeightPair,
) -> Sequence[Uint64]:
    participation_flag_indices = []
    has_finality_support = data.finalize_pair == HeightPair(
        root=justified_pair.root, height=justified_pair.height
    )
    has_target_support = data.target_pair == target_pair
    has_progress_support = data.target_pair == HeightPair(root=Root(), height=target_pair.height)

    # Finalization
    if has_finality_support:
        participation_flag_indices.append(FINALITY_FLAG_INDEX)
    # Justification
    if has_target_support:
        participation_flag_indices.append(TARGET_FLAG_INDEX)
    # Progress
    if has_target_support or has_progress_support:
        participation_flag_indices.append(PROGRESS_FLAG_INDEX)

    return participation_flag_indices
```

#### New `get_indexed_attestation_2`

```python
def get_indexed_attestation_2(state: BeaconState, attestation: Attestation) -> IndexedAttestation2:
    """
    Return the indexed attestation corresponding to ``attestation``.
    """
    attesting_indices = get_attesting_indices(state, attestation)

    return IndexedAttestation2(
        attesting_indices=AttestingIndices(data=sorted(attesting_indices)),
        data=attestation.data,
        signature=attestation.signature,
    )
```

#### New `is_valid_indexed_attestation_2`

```python
def is_valid_indexed_attestation_2(
    state: BeaconState, indexed_attestation: IndexedAttestation2
) -> bool:
    """
    Check if ``indexed_attestation`` is not empty, has sorted and unique indices and has a valid aggregate signature.
    """
    # Verify indices are sorted and unique
    indices = indexed_attestation.attesting_indices
    if (
        len(indices) == 0
        or len(indices) > MAX_VALIDATORS_PER_AGGREGATE
        or list(indices) != sorted(set(indices))
    ):
        return False
    # Verify aggregate signature
    pubkeys = [state.validators[i].pubkey for i in indices]
    epoch = compute_epoch_at_round(indexed_attestation.data.round)
    domain = get_domain(state, DOMAIN_BEACON_ATTESTER_2, epoch)
    signing_root = compute_signing_root(indexed_attestation.data, domain)
    return bls.FastAggregateVerify(pubkeys, signing_root, indexed_attestation.signature)
```

### Misc

#### New `remove_flag`

```python
def remove_flag(flags: ParticipationFlags, flag_index: int) -> ParticipationFlags:
    flag = ParticipationFlags(2**flag_index)
    return flags & ~flag
```

#### New `compute_round_at_slot`

```python
def compute_round_at_slot(slot: Slot) -> Round:
    """
    Return the round number at ``slot``.
    """
    return Round(slot // SLOTS_PER_ROUND)
```

#### New `compute_start_slot_at_round`

```python
def compute_start_slot_at_round(round: Round) -> Slot:
    """
    Return the start slot of ``round``.
    """
    return Slot(round) * SLOTS_PER_ROUND
```

#### New `compute_epoch_at_round`

```python
def compute_epoch_at_round(round: Round) -> Epoch:
    """
    Return the epoch number at ``round``.
    """
    start_slot = compute_start_slot_at_round(round)
    return compute_epoch_at_slot(start_slot)
```

#### Modified `compute_ptc`

```python
def compute_ptc(state: BeaconState, slot: Slot) -> PayloadTimelinessCommittee:
    """
    Get the payload timeliness committee, with possible duplicates, for the given ``slot``.
    """
    epoch = compute_epoch_at_slot(slot)
    seed = sha256(get_seed(state, epoch, DOMAIN_PTC_ATTESTER) + uint_to_bytes(slot))
    # [Modified in DC]
    indices = get_active_validator_indices(state, epoch)
    return PayloadTimelinessCommittee(
        data=compute_balance_weighted_selection(
            state, indices, seed, size=PTC_SIZE, shuffle_indices=True
        )
    )
```

### Beacon state accessors

#### Modified `get_beacon_committee`

```python
def get_beacon_committee(
    state: BeaconState, round: Round, committee_index: CommitteeIndex
) -> Sequence[ValidatorIndex]:
    """
    Return the beacon committee at ``round`` for ``committee_index``.
    """
    # Indices of validators that aren't exited at the finalized epoch
    finalized_epoch = compute_epoch_at_slot(state.finalized_slot)
    indices = [
        index
        for index in range(len(state.validators))
        if state.validators[index].exit_epoch > finalized_epoch
    ]

    start = (len(indices) * committee_index) // COMMITTEES_PER_ROUND
    end = (len(indices) * (committee_index + 1)) // COMMITTEES_PER_ROUND
    return [indices[(i + round) % len(indices)] for i in range(start, end)]
```

#### Modified `get_attesting_indices`

```python
def get_attesting_indices(state: BeaconState, attestation: Attestation) -> Set[ValidatorIndex]:
    """
    Return the set of attesting indices corresponding to ``aggregation_bits`` and ``committee_bits``.
    """
    output: Set[ValidatorIndex] = set()
    committee_indices = get_committee_indices(attestation.committee_bits)
    committee_offset = 0
    for committee_index in committee_indices:
        # [Modified in DC]
        committee = get_beacon_committee(state, attestation.data.round, committee_index)
        committee_attesters = {
            attester_index
            for i, attester_index in enumerate(committee)
            if attestation.aggregation_bits[committee_offset + i]
        }
        output = output.union(committee_attesters)

        committee_offset += len(committee)

    return output
```

#### Modified `get_builder_payment_quorum_threshold`

```python
def get_builder_payment_quorum_threshold(per_slot_balance: Uint64) -> Uint64:
    # [Modified in DC]
    quorum = per_slot_balance * BUILDER_PAYMENT_THRESHOLD_NUMERATOR
    return Uint64(quorum // BUILDER_PAYMENT_THRESHOLD_DENOMINATOR)
```

## Beacon chain state transition function

```python
def state_transition(
    state: BeaconState, signed_block: SignedBeaconBlock, validate_result: bool = True
) -> None:
    block = signed_block.message
    # Process slots (including those with no blocks) since block
    process_slots(state, block.slot)
    # Verify signature
    if validate_result:
        assert verify_block_signature(state, signed_block)
    # [Modified in DC]
    # Process block
    process_block(state, block)
    # [New in DC]
    # Process height events
    process_height_events(state)
    # Verify state root
    if validate_result:
        assert block.state_root == hash_tree_root(state)
```

```python
def process_slots(state: BeaconState, slot: Slot) -> None:
    assert state.slot < slot
    while state.slot < slot:
        process_slot(state)
        # [New in DC]
        if (state.slot + 1) % SLOTS_PER_ROUND == 0:
            process_round(state)
        # Process epoch on the start slot of the next epoch
        if (state.slot + 1) % SLOTS_PER_EPOCH == 0:
            # [Modified in DC]
            process_epoch(state)
        state.slot = state.slot + 1
```

### Process height events

```python
def advance_height(state: BeaconState, reset_finality_participation: bool) -> None:
    state.target_pair = HeightPair(
        height=state.target_pair.height + 1, root=hash_tree_root(state.latest_block_header)
    )
    state.target_slot = state.latest_block_header.slot

    # Reset participation
    if reset_finality_participation:
        # Reset all flags
        state.height_participation = EpochParticipation(
            data=[ParticipationFlags(0b0000_0000) for _ in range(len(state.validators))]
        )
    else:
        # Keep only finality flag
        finality_flag = ParticipationFlags(2**FINALITY_FLAG_INDEX)
        for index in range(len(state.height_participation)):
            state.height_participation[index] = state.height_participation[index] & finality_flag
```

```python
def process_height_events(state: BeaconState) -> None:
    # Process finalization
    if state.justified_pair.height > state.finalized_pair.height and has_quorum(
        state, FINALITY_FLAG_INDEX
    ):
        state.finalized_pair = state.justified_pair
        state.finalized_slot = state.justified_slot

    # Process justification
    if has_quorum(state, TARGET_FLAG_INDEX):
        state.justified_pair = state.target_pair
        state.justified_slot = state.target_slot
        advance_height(state, True)
        return

    # Process progress
    if has_quorum(state, PROGRESS_FLAG_INDEX):
        advance_height(state, False)
```

### Round processing

#### New `process_round`

```python
def process_round(state: BeaconState) -> None:
    # [TODO: process_inactivity_updates(state)]
    # [TODO: process_rewards_and_penalties(state)]
    process_participation_flag_updates(state)
```

### Epoch processing

#### Modified `process_epoch`

```python
def process_epoch(state: BeaconState) -> None:
    # [Modified in DC]
    # process_justification_and_finalization(state)
    # process_inactivity_updates(state)
    # process_rewards_and_penalties(state)
    process_registry_updates(state)
    process_slashings(state)
    process_eth1_data_reset(state)
    # [Modified in DC]
    process_pending_deposits(state)
    process_pending_consolidations(state)
    # [Modified in DC]
    process_builder_pending_payments(state)
    process_effective_balance_updates(state)
    process_slashings_reset(state)
    process_randao_mixes_reset(state)
    process_historical_summaries_update(state)
    # [Modified in DC]
    # process_participation_flag_updates(state)
    process_sync_committee_updates(state)
    process_proposer_lookahead(state)
    process_ptc_window(state)
    # [New in DC]
    process_builder_payment_participation(state)
```

#### Modified `process_participation_flag_updates`

```python
def process_participation_flag_updates(state: BeaconState) -> None:
    state.previous_epoch_participation = state.current_epoch_participation
    state.current_epoch_participation = EpochParticipation(
        data=[ParticipationFlags(0b0000_0000) for _ in range(len(state.validators))]
    )
    # [New in DC]
    state.previous_round_participation = state.current_round_participation
    state.current_round_participation = EpochParticipation(
        data=[ParticipationFlags(0b0000_0000) for _ in range(len(state.validators))]
    )
```

#### Modified `process_pending_deposits`

```python
def process_pending_deposits(state: BeaconState) -> None:
    next_epoch = get_current_epoch(state) + 1
    # Deposits still consume the activation-only churn budget in Gloas.
    available_for_processing = state.deposit_balance_to_consume + get_activation_churn_limit(state)
    processed_amount = 0
    next_deposit_index = 0
    deposits_to_postpone = []
    is_churn_limit_reached = False

    for deposit in state.pending_deposits:
        # Check if deposit has been finalized, otherwise, stop processing.
        # [Modified in DC]
        if deposit.slot > state.finalized_slot:
            break

        # Check if number of processed deposits has not reached the limit, otherwise, stop processing.
        if next_deposit_index >= MAX_PENDING_DEPOSITS_PER_EPOCH:
            break

        # Read validator state
        is_validator_exited = False
        is_validator_withdrawn = False
        validator_pubkeys = [v.pubkey for v in state.validators]
        if deposit.pubkey in validator_pubkeys:
            validator = state.validators[ValidatorIndex(validator_pubkeys.index(deposit.pubkey))]
            is_validator_exited = validator.exit_epoch < FAR_FUTURE_EPOCH
            is_validator_withdrawn = validator.withdrawable_epoch < next_epoch

        if is_validator_withdrawn:
            # Deposited balance will never become active. Increase balance but do not consume churn
            apply_pending_deposit(state, deposit)
        elif is_validator_exited:
            # Validator is exiting, postpone the deposit until after withdrawable epoch
            deposits_to_postpone.append(deposit)
        else:
            # Check if deposit fits in the churn, otherwise, do no more deposit processing in this epoch.
            is_churn_limit_reached = processed_amount + deposit.amount > available_for_processing
            if is_churn_limit_reached:
                break

            # Consume churn and apply deposit.
            processed_amount += deposit.amount
            apply_pending_deposit(state, deposit)

        # Regardless of how the deposit was handled, we move on in the queue.
        next_deposit_index += 1

    state.pending_deposits = state.pending_deposits[next_deposit_index:] + deposits_to_postpone

    # Accumulate churn only if the churn limit has been hit.
    if is_churn_limit_reached:
        state.deposit_balance_to_consume = available_for_processing - processed_amount
    else:
        state.deposit_balance_to_consume = Gwei(0)
```

#### Modified `process_builder_pending_payments`

```python
def process_builder_pending_payments(state: BeaconState) -> None:
    """
    Processes the builder pending payments from the previous epoch.
    """
    if get_previous_epoch(state) < DC_FORK_EPOCH:
        # [Modified in DC]
        per_slot_balance = get_total_active_balance(state) // Uint64(SLOTS_PER_EPOCH)
        quorum = get_builder_payment_quorum_threshold(per_slot_balance)
        for payment in state.builder_pending_payments[:SLOTS_PER_EPOCH]:
            if payment.weight >= quorum:
                state.builder_pending_withdrawals.append(payment.withdrawal)
    else:
        # [New in DC]
        quorum = get_builder_payment_quorum_threshold(AVAILABLE_CHAIN_COMMITTEE_SIZE)
        for index, payment in enumerate(state.builder_pending_payments[:SLOTS_PER_EPOCH]):
            weight = Uint64(len(state.builder_payment_participation[index]))
            if weight >= quorum:
                state.builder_pending_withdrawals.append(payment.withdrawal)

    old_payments = state.builder_pending_payments[SLOTS_PER_EPOCH:]
    state.builder_pending_payments[:SLOTS_PER_EPOCH] = old_payments
    new_payments = [BuilderPendingPayment.empty() for _ in range(SLOTS_PER_EPOCH)]
    state.builder_pending_payments[SLOTS_PER_EPOCH:] = new_payments
```

#### New `process_builder_payment_participation`

```python
def process_builder_payment_participation(state: BeaconState) -> None:
    current_epoch_participation = state.builder_payment_participation[SLOTS_PER_EPOCH:]
    next_epoch_participation = [AvailableChainCommitteeIndices() for _ in range(SLOTS_PER_EPOCH)]
    state.builder_payment_participation[:SLOTS_PER_EPOCH] = current_epoch_participation
    state.builder_payment_participation[SLOTS_PER_EPOCH:] = next_epoch_participation
```

### Block processing

#### Operations

##### Modified `process_operations`

```python
def process_operations(
    state: BeaconState,
    body: BeaconBlockBody,
    parent_slot: Slot,
) -> None:
    assert len(body.deposits) == 0

    def for_ops(operations: Sequence[Any], fn: Callable[..., None], *args: Any) -> None:
        for operation in operations:
            fn(state, operation, *args)

    assert len(body.proposer_slashings) <= MAX_PROPOSER_SLASHINGS
    assert len(body.attester_slashings) <= MAX_ATTESTER_SLASHINGS_ELECTRA
    assert len(body.attestations) <= MAX_ATTESTATIONS_ELECTRA
    assert len(body.voluntary_exits) <= MAX_VOLUNTARY_EXITS
    assert len(body.bls_to_execution_changes) <= MAX_BLS_TO_EXECUTION_CHANGES
    assert len(body.payload_attestations) <= MAX_PAYLOAD_ATTESTATIONS
    # [New in DC]
    assert len(body.attester_slashings_2) <= MAX_ATTESTER_SLASHINGS_ELECTRA

    for_ops(body.proposer_slashings, process_proposer_slashing)
    for_ops(body.attester_slashings, process_attester_slashing)
    # [Modified in DC]
    for_ops(body.attestations, process_attestation)
    for_ops(body.voluntary_exits, process_voluntary_exit)
    for_ops(body.bls_to_execution_changes, process_bls_to_execution_change)
    for_ops(body.payload_attestations, process_payload_attestation)
    # [New in DC]
    for_ops(body.available_chain_attestations, process_available_chain_attestation, parent_slot)
    for_ops(body.attester_slashings_2, process_attester_slashing_2)
```

##### Attestations

###### `process_attestation`

```python
def process_attestation(state: BeaconState, attestation: Attestation) -> None:
    assert is_valid_attestation_data(state, attestation.data)
    assert is_valid_aggregation_bits(state, attestation)
    assert is_valid_indexed_attestation_2(state, get_indexed_attestation_2(state, attestation))

    if attestation.data.round == compute_round_at_slot(state.slot):
        round_participation = state.current_round_participation
    else:
        round_participation = state.previous_round_participation

    # Participation flag indices
    current_participation_flag_indices = get_height_participation_flag_indices(
        attestation.data, state.target_pair, state.justified_pair
    )
    previous_participation_flag_indices = get_height_participation_flag_indices(
        attestation.data, state.justified_pair, state.finalized_pair
    )
    for index in get_attesting_indices(state, attestation):
        # Current height participation counts in height and round participation
        for flag_index in current_participation_flag_indices:
            state.height_participation[index] = add_flag(
                state.height_participation[index], flag_index
            )
            round_participation[index] = add_flag(round_participation[index], flag_index)
        # Previous height participation counts in round participation only
        for flag_index in previous_participation_flag_indices:
            round_participation[index] = add_flag(round_participation[index], flag_index)

    # [TODO: proposer reward]
```

##### Available chain votes

###### `process_available_chain_attestation`

```python
def process_available_chain_attestation(
    state: BeaconState,
    attestation: AvailableChainAttestation,
    parent_slot: Slot,
) -> None:
    assert is_valid_available_chain_attestation(state, attestation)
    # Update builder payment participation
    update_builder_payment_participation(state, attestation)

    if is_matching_head_attestation(state, attestation.data, parent_slot):
        # [TODO: timely head and proposer reward logic]
        pass
```

##### Deposits

###### Modified `add_validator_to_registry`

```python
def add_validator_to_registry(
    state: BeaconState, pubkey: BLSPubkey, withdrawal_credentials: Bytes32, amount: Gwei
) -> None:
    index = get_index_for_new_validator(state)
    # [Modified in Electra:EIP7251]
    validator = get_validator_from_deposit(pubkey, withdrawal_credentials, amount)
    set_or_append_list(state.validators, index, validator)
    set_or_append_list(state.balances, index, amount)
    set_or_append_list(state.previous_epoch_participation, index, ParticipationFlags(0b0000_0000))
    set_or_append_list(state.current_epoch_participation, index, ParticipationFlags(0b0000_0000))
    set_or_append_list(state.inactivity_scores, index, Uint64(0))
    # [New in DC]
    set_or_append_list(state.height_participation, index, ParticipationFlags(0b0000_0000))
    set_or_append_list(state.previous_round_participation, index, ParticipationFlags(0b0000_0000))
    set_or_append_list(state.current_round_participation, index, ParticipationFlags(0b0000_0000))
```

##### Attester slashings

###### `process_attester_slashing2`

```python
def process_attester_slashing_2(state: BeaconState, attester_slashing: AttesterSlashing2) -> None:
    attestation_1 = attester_slashing.attestation_1
    attestation_2 = attester_slashing.attestation_2
    assert is_slashable_attestation_data_2(attestation_1.data, attestation_2.data)
    assert is_valid_indexed_attestation_2(state, attestation_1)
    assert is_valid_indexed_attestation_2(state, attestation_2)

    slashed_any = False
    indices = set(attestation_1.attesting_indices).intersection(attestation_2.attesting_indices)
    for index in sorted(indices):
        if is_slashable_validator(state.validators[index], get_current_epoch(state)):
            slash_validator(state, index)
            slashed_any = True
    assert slashed_any
```
