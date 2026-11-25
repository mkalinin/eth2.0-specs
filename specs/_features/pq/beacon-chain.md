# PQ -- The Beacon Chain

*Note*: This document is a work-in-progress for researchers and implementers.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `VRFProof`](#new-vrfproof)
  - [New `AttestationProof`](#new-attestationproof)
  - [New `XMSSPubkey`](#new-xmsspubkey)
  - [New `XMSSSignature`](#new-xmsssignature)
  - [New `ValidatorPreregistrationRequests`](#new-validatorpreregistrationrequests)
  - [New `BuilderPreregistrationRequests`](#new-builderpreregistrationrequests)
  - [New `ValidatorPreregistrations`](#new-validatorpreregistrations)
  - [New `BuilderPreregistrations`](#new-builderpreregistrations)
  - [New `VoluntaryExitRequests`](#new-voluntaryexitrequests)
  - [New `AttestationCommittee`](#new-attestationcommittee)
  - [New `AttestationCommitteeBits`](#new-attestationcommitteebits)
  - [New `Dynasty`](#new-dynasty)
  - [New `ACWeights`](#new-acweights)
  - [New `ACSnapshots`](#new-acsnapshots)
  - [New `HeadVoteCredentials`](#new-headvotecredentials)
  - [New `HeadVotePaymentVoters`](#new-headvotepaymentvoters)
  - [New `HeadVoteParticipation`](#new-headvoteparticipation)
  - [New `HeadVoteDeclarations`](#new-headvotedeclarations)
  - [New `HeadVoteSupportBits`](#new-headvotesupportbits)
  - [New `HeadVotes`](#new-headvotes)
  - [New `Height`](#new-height)
  - [New `HeightParticipation`](#new-heightparticipation)
  - [New `PendingFinalities`](#new-pendingfinalities)
  - [New `Round`](#new-round)
  - [New `RoundParticipation`](#new-roundparticipation)
- [Constants](#constants)
  - [Participation flag indices](#participation-flag-indices)
  - [Incentivization weights](#incentivization-weights)
  - [Domains](#domains)
  - [Misc](#misc)
  - [XMSS](#xmss)
  - [VRF](#vrf)
  - [XMSS leaf offsets](#xmss-leaf-offsets)
  - [Deposits](#deposits)
  - [Legacy domains](#legacy-domains)
  - [Execution-layer triggered requests](#execution-layer-triggered-requests)
- [Presets](#presets)
  - [Finality gadget](#finality-gadget)
  - [Rounds](#rounds)
  - [Head votes](#head-votes)
  - [Rewards](#rewards)
  - [Inactivity leak](#inactivity-leak)
  - [XMSS](#xmss-1)
  - [Max operations per block](#max-operations-per-block)
  - [Execution](#execution)
- [Configs](#configs)
  - [Time parameters](#time-parameters)
- [Containers](#containers)
  - [New `HeadVoteDeclaration`](#new-headvotedeclaration)
  - [Modified containers](#modified-containers)
    - [`Attestation`](#attestation)
    - [`AttestationData`](#attestationdata)
    - [`BeaconBlockBody`](#beaconblockbody)
    - [`BeaconState`](#beaconstate)
    - [`Builder`](#builder)
    - [`BuilderDepositRequest`](#builderdepositrequest)
    - [`BuilderExitRequest`](#builderexitrequest)
    - [`ConsolidationRequest`](#consolidationrequest)
    - [`DepositRequest`](#depositrequest)
    - [`ExecutionRequests`](#executionrequests)
    - [`IndexedAttestation`](#indexedattestation)
    - [`PayloadAttestationMessage`](#payloadattestationmessage)
    - [`PendingDeposit`](#pendingdeposit)
    - [`SignedBeaconBlock`](#signedbeaconblock)
    - [`SignedBeaconBlockHeader`](#signedbeaconblockheader)
    - [`SignedExecutionPayloadBid`](#signedexecutionpayloadbid)
    - [`SignedExecutionPayloadEnvelope`](#signedexecutionpayloadenvelope)
    - [`SingleAttestation`](#singleattestation)
    - [`Validator`](#validator)
    - [`WithdrawalRequest`](#withdrawalrequest)
  - [New containers](#new-containers)
    - [`HeightCheckpoint`](#heightcheckpoint)
    - [`PendingFinality`](#pendingfinality)
    - [`ACSnapshot`](#acsnapshot)
    - [`HeadVoteCredential`](#headvotecredential)
    - [`HeadVoteData`](#headvotedata)
    - [`HeadVote`](#headvote)
    - [`HeadVoteMessage`](#headvotemessage)
    - [`ValidatorPreregistrationRequest`](#validatorpreregistrationrequest)
    - [`ValidatorPreregistration`](#validatorpreregistration)
    - [`BuilderPreregistrationRequest`](#builderpreregistrationrequest)
    - [`BuilderPreregistration`](#builderpreregistration)
    - [`VoluntaryExitRequest`](#voluntaryexitrequest)
- [Dataclasses](#dataclasses)
  - [New dataclasses](#new-dataclasses)
    - [`XMSSAggregateStatement`](#xmssaggregatestatement)
- [Helpers](#helpers)
  - [Crypto](#crypto)
    - [New `keccak256`](#new-keccak256)
    - [New `xmss_sign`](#new-xmss_sign)
    - [New `xmss_verify`](#new-xmss_verify)
    - [New `xmss_get_leaf_index`](#new-xmss_get_leaf_index)
    - [New `stark_prove_aggregates`](#new-stark_prove_aggregates)
    - [New `stark_merge_proofs`](#new-stark_merge_proofs)
    - [New `stark_verify_aggregates`](#new-stark_verify_aggregates)
  - [Misc](#misc-1)
    - [New `compute_legacy_xmss_pubkey`](#new-compute_legacy_xmss_pubkey)
    - [New `compute_legacy_vrf_root`](#new-compute_legacy_vrf_root)
    - [New `compute_deposit_pubkey`](#new-compute_deposit_pubkey)
    - [New `compute_vrf_leaf`](#new-compute_vrf_leaf)
    - [New `compute_deposit_vrf_root`](#new-compute_deposit_vrf_root)
    - [New `compute_xmss_attestation_leaf_index`](#new-compute_xmss_attestation_leaf_index)
    - [New `compute_xmss_leaf_index`](#new-compute_xmss_leaf_index)
    - [New `compute_round_at_slot`](#new-compute_round_at_slot)
    - [New `compute_start_slot_at_round`](#new-compute_start_slot_at_round)
    - [New `compute_attestation_committee_slot`](#new-compute_attestation_committee_slot)
    - [Modified `compute_ptc`](#modified-compute_ptc)
    - [New `compute_ac_seat_indices`](#new-compute_ac_seat_indices)
  - [Predicates](#predicates)
    - [New `is_active_validator_preregistration`](#new-is_active_validator_preregistration)
    - [New `is_active_builder_preregistration`](#new-is_active_builder_preregistration)
    - [New `is_builder_bid_leaf_index`](#new-is_builder_bid_leaf_index)
    - [New `is_legacy_pubkey`](#new-is_legacy_pubkey)
    - [New `is_valid_vrf_proof`](#new-is_valid_vrf_proof)
    - [Modified `is_pending_validator`](#modified-is_pending_validator)
    - [Modified `is_valid_indexed_attestation`](#modified-is_valid_indexed_attestation)
    - [New `is_well_formed_attestation_data`](#new-is_well_formed_attestation_data)
    - [New `is_valid_attestation_data`](#new-is_valid_attestation_data)
    - [New `is_previous_target_attestation_data`](#new-is_previous_target_attestation_data)
    - [New `is_double_target_vote`](#new-is_double_target_vote)
    - [New `is_conflicting_with_finality_pair`](#new-is_conflicting_with_finality_pair)
    - [Modified `is_slashable_attestation_data`](#modified-is_slashable_attestation_data)
    - [Modified `is_eligible_for_activation`](#modified-is_eligible_for_activation)
    - [Modified `is_active_builder`](#modified-is_active_builder)
    - [New `is_valid_head_vote_declarations`](#new-is_valid_head_vote_declarations)
    - [New `is_head_vote_same_slot`](#new-is_head_vote_same_slot)
    - [New `is_head_vote_payload_status_valid`](#new-is_head_vote_payload_status_valid)
    - [New `has_builder_payment_quorum`](#new-has_builder_payment_quorum)
    - [New `has_quorum`](#new-has_quorum)
    - [Modified `is_in_inactivity_leak`](#modified-is_in_inactivity_leak)
    - [New `is_valid_aggregation_bits`](#new-is_valid_aggregation_bits)
  - [Beacon state accessors](#beacon-state-accessors)
    - [Modified `get_attesting_indices`](#modified-get_attesting_indices)
    - [Modified `get_indexed_attestation`](#modified-get_indexed_attestation)
    - [New `get_attestation_statements`](#new-get_attestation_statements)
    - [New `get_head_vote_statement`](#new-get_head_vote_statement)
    - [New `get_validator_preregistration_index`](#new-get_validator_preregistration_index)
    - [New `get_active_validator_preregistration`](#new-get_active_validator_preregistration)
    - [New `get_builder_preregistration_index`](#new-get_builder_preregistration_index)
    - [New `get_active_builder_preregistration`](#new-get_active_builder_preregistration)
    - [New `get_current_round`](#new-get_current_round)
    - [New `get_previous_round`](#new-get_previous_round)
    - [New `get_attestation_committee`](#new-get_attestation_committee)
    - [New `get_attestation_epoch`](#new-get_attestation_epoch)
    - [New `get_aggregate_participants`](#new-get_aggregate_participants)
    - [New `get_ac_seat_indices`](#new-get_ac_seat_indices)
    - [New `get_head_vote_weight`](#new-get_head_vote_weight)
    - [Modified `get_unslashed_participating_indices`](#modified-get_unslashed_participating_indices)
    - [New `get_validator_weight`](#new-get_validator_weight)
    - [New `get_total_weight`](#new-get_total_weight)
    - [New `get_participating_weight`](#new-get_participating_weight)
    - [Modified `get_finality_delay`](#modified-get_finality_delay)
    - [New `get_round_base_reward`](#new-get_round_base_reward)
    - [New `get_flag_index_rewards`](#new-get_flag_index_rewards)
  - [Beacon state mutators](#beacon-state-mutators)
    - [Modified `queue_excess_active_balance`](#modified-queue_excess_active_balance)
    - [New `remove_validator_preregistration`](#new-remove_validator_preregistration)
    - [New `remove_builder_preregistration`](#new-remove_builder_preregistration)
    - [New `add_participation_flag`](#new-add_participation_flag)
- [Beacon chain state transition function](#beacon-chain-state-transition-function)
  - [Modified `state_transition`](#modified-state_transition)
  - [Modified `verify_block_signature`](#modified-verify_block_signature)
  - [Modified `process_slots`](#modified-process_slots)
  - [Modified `process_slot`](#modified-process_slot)
  - [Round processing](#round-processing)
    - [New `process_round`](#new-process_round)
    - [Modified `process_inactivity_updates`](#modified-process_inactivity_updates)
    - [New `process_rewards`](#new-process_rewards)
    - [Modified `process_participation_flag_updates`](#modified-process_participation_flag_updates)
  - [Epoch processing](#epoch-processing)
    - [Modified `process_epoch`](#modified-process_epoch)
    - [Modified `process_builder_pending_payments`](#modified-process_builder_pending_payments)
    - [New `get_ac_weights`](#new-get_ac_weights)
    - [New `process_ac_snapshot_updates`](#new-process_ac_snapshot_updates)
    - [New `process_preregistration_expiry`](#new-process_preregistration_expiry)
    - [Modified `apply_pending_deposit`](#modified-apply_pending_deposit)
    - [Modified `process_pending_deposits`](#modified-process_pending_deposits)
  - [Block processing](#block-processing)
    - [Modified `process_block`](#modified-process_block)
    - [Modified `process_randao`](#modified-process_randao)
    - [Execution payload](#execution-payload)
      - [Modified `get_execution_requests_list`](#modified-get_execution_requests_list)
      - [Modified `verify_execution_payload_envelope_signature`](#modified-verify_execution_payload_envelope_signature)
    - [Execution payload bid](#execution-payload-bid)
      - [Modified `verify_execution_payload_bid_signature`](#modified-verify_execution_payload_bid_signature)
      - [Modified `process_execution_payload_bid`](#modified-process_execution_payload_bid)
    - [Operations](#operations)
      - [Modified `process_operations`](#modified-process_operations)
      - [New `process_stark`](#new-process_stark)
      - [Modified `process_proposer_slashing`](#modified-process_proposer_slashing)
      - [Attestations](#attestations)
        - [Modified `process_attestation`](#modified-process_attestation)
      - [Head votes](#head-votes-1)
        - [New `process_head_vote`](#new-process_head_vote)
      - [Deposit requests](#deposit-requests)
        - [Modified `process_deposit_request`](#modified-process_deposit_request)
        - [Modified `get_validator_from_deposit`](#modified-get_validator_from_deposit)
        - [Modified `add_validator_to_registry`](#modified-add_validator_to_registry)
      - [Builder deposit requests](#builder-deposit-requests)
        - [Modified `add_builder_to_registry`](#modified-add_builder_to_registry)
        - [Modified `process_builder_deposit_request`](#modified-process_builder_deposit_request)
      - [Builder exit requests](#builder-exit-requests)
        - [Modified `process_builder_exit_request`](#modified-process_builder_exit_request)
      - [Execution-layer withdrawal requests](#execution-layer-withdrawal-requests)
        - [Modified `process_withdrawal_request`](#modified-process_withdrawal_request)
      - [Execution-layer consolidation requests](#execution-layer-consolidation-requests)
        - [Modified `is_valid_switch_to_compounding_request`](#modified-is_valid_switch_to_compounding_request)
        - [Modified `process_consolidation_request`](#modified-process_consolidation_request)
      - [Validator preregistration requests](#validator-preregistration-requests)
        - [New `process_validator_preregistration_request`](#new-process_validator_preregistration_request)
      - [Builder preregistration requests](#builder-preregistration-requests)
        - [New `process_builder_preregistration_request`](#new-process_builder_preregistration_request)
      - [Voluntary exit requests](#voluntary-exit-requests)
        - [New `process_voluntary_exit_request`](#new-process_voluntary_exit_request)
    - [Parent execution payload](#parent-execution-payload)
      - [Modified `apply_parent_execution_payload`](#modified-apply_parent_execution_payload)
    - [Height events](#height-events)
      - [New `is_previous_height_justified`](#new-is_previous_height_justified)
      - [New `process_height_events`](#new-process_height_events)
      - [New `advance_dynasty`](#new-advance_dynasty)
      - [New `update_ac_snapshots`](#new-update_ac_snapshots)
      - [New `advance_height`](#new-advance_height)

<!-- mdformat-toc end -->

## Introduction

This upgrade replaces the BLS signatures used by validators and builders with
leanXMSS, a hash-based signature scheme believed to be secure against a quantum
adversary. It also replaces the combined LMD-GHOST and Casper FFG attestation
with EIP-8453 ("Decoupled Consensus"), which separates head votes from finality
attestations.

This upgrade is meant as an emergency fork for when elliptic curve cryptography
can no longer be trusted, so it keeps only what consensus needs. It removes sync
committees, whose hundreds of signatures per slot serve only light clients, and
with them the light client protocol.

Decoupled consensus has two parts. The finality gadget (FG) replaces Casper FFG
and finalizes blocks. The available chain (AC) follows the head with head votes.

The FG advances through heights, and the block that opens a height is its
target. An attestation is a target vote or a timeout for a height, with an
optional finality pair naming a justification below that height. A quorum of
target votes justifies the target and opens the next height. A quorum of target
votes and timeouts also opens the next height, but only `TIMEOUT_DELAY_SLOTS`
slots after the target. A target quorum justifies only if the previous height is
not justified or is already finalized. Validators take the finality pair from
the state in which the chain entered the height: the justified predecessor, or a
pending justification of that state. A finality pair counts only while the
justification it names is still pending on the chain that includes it. A quorum
of finality pairs finalizes a pending justification, before the same block
checks the target quorum.

AC draws fresh balance-proportional tickets every slot from two frozen balance
snapshots. Each new dynasty switches one seat index to the newer snapshot. A
block declares the previous slot's votes that its proposer holds, with one
support bit per declaration. Fork choice merges those declarations with signed
votes. For epoch settlement of pending builder payments, blocks also carry head
vote aggregates with a credential for each distinct voter.

Validators cast FG attestations in rounds of `SLOTS_PER_ROUND` slots. Each
validator sits on the attestation committee given by its index modulo
`ATTESTATION_COMMITTEES_PER_ROUND`, and committees are spread evenly over the
slots of a round, moving by at most one slot from round to round. In every
round, an active validator casts its FG attestation in its committee's slot. A
block includes attestations for the chain's current target, and for its previous
target, which count only toward pending justifications. Their bits are laid out
in the committees of the target's epoch, so an aggregate keeps one encoding for
as long as it can be included. Rewards and inactivity are settled at the end of
each round, in `process_round`.

A validator earns the progress flag for a target vote or a timeout at the
current height, and the finality flag for a finality pair of a pending
justification. There are no penalties. Inactivity instead lowers a validator's
weight in FG quorums, and a validator whose weight reaches zero is exited and
keeps its stake.

*Note*: A quorum is two thirds of the total weight of the active validators.
Slashed validators count toward the total but not toward a quorum.

*Note*: This upgrade does not yet specify rewards for head votes.

XMSS is a stateful scheme. A key covers a fixed number of one-time leaves, and
signing two different messages at the same leaf breaks the key. This upgrade
therefore assigns every validator message a leaf derived from its slot and its
type, see `compute_xmss_leaf_index`. An attestation instead uses the leaf of its
round, see `compute_xmss_attestation_leaf_index`. A message without a leaf of
its own, such as a voluntary exit, instead uses any reserved leaf, one of the
first `XMSS_RESERVED_LEAVES` leaves. A bid instead uses any leaf reserved for
bids, see `is_builder_bid_leaf_index`. An honest signer never equivocates and
uses each leaf it chooses at most once, so it never reuses a leaf. Each
signature carries its leaf index, and verification checks that the message may
use it.

XMSS has no native aggregation. A STARK instead proves many XMSS signatures at
once, such as those of attestations and head votes in an `AttestationProof`.

XMSS signatures are not unique, so a proposer could grind a signature-based
RANDAO reveal. Each validator instead has a secret random value for each slot,
and registers as its VRF root the root of a Merkle tree whose leaf for a slot
commits to the slot's secret. Its RANDAO reveal is the secret for the slot with
the leaf's Merkle branch, a `VRFProof`, which the proposer committed to before
the fork. The branch holds only commitments, so it reveals no other secret.

A validator's record carries the XMSS public key and VRF root it registered with
EIP-8483 before the fork in place of its BLS public key, and a builder's record
the XMSS public key it registered. Validators that did not register are exited
at the fork and become withdrawable
`UNREGISTERED_VALIDATOR_WITHDRAWABILITY_DELAY` epochs later, and builders that
did not register are withdrawn at the fork. See [the fork document](./fork.md)
for details.

Execution layer requests keep their formats. A request's 48-byte public key
field is 16 zero bytes followed by an XMSS public key. Deposits no longer carry
a signature. Instead, the first 32 bytes of a deposit's 96-byte signature field
are the VRF root of the validator it creates. A legacy request made before the
fork names a BLS public key instead, whose first byte always has its top bit
set. A legacy deposit's validator takes the XMSS public key and VRF root that a
validator that did not register takes at the fork, and it is exited at once, so
the validator sweep refunds its balance after the withdrawability delay. A
legacy builder deposit's builder is keyed the same way and initiates its exit at
once. A legacy withdrawal or consolidation request is ignored.

Without deposit signatures, anyone who sees the first deposit for a new XMSS
public key could get in first with a deposit of their own withdrawal
credentials. As in [EIP-8205](../eip8205/beacon-chain.md), the holder of a key
can first bind the key to its withdrawal credentials, and for a validator its
VRF root, with a preregistration signed by the key. Validators and builders
preregister separately, each with a request type of its own. The system contract
verifies the signature, so the preregistration request it emits carries none.
While the binding is active, a deposit of the same kind for the key is discarded
unless it matches the binding.

Voluntary exits are execution layer requests. A validator signs its exit, and
the system contract verifies the signature, so the voluntary exit request it
emits carries none. Anyone can submit a signed exit, not only the validator's
withdrawal address. The block body no longer has `voluntary_exits`.

`BLSToExecutionChange` is disabled, because its BLS signature could be forged.

Blocks no longer carry payload attestations, which spares proposers from
aggregating them. The payload timeliness committee still broadcasts its votes,
which fork choice uses as before.

Attestations and head votes in a block carry no signature. A block instead
carries one `proof` of the signatures of all its attestations and head votes,
which replaces verifying each aggregate signature in turn. Head vote
declarations and their support bits are not signed and add no statements to the
`proof`; they feed only fork choice, which accepts a declaration only if it
holds the signed vote.

*TODO*: Specify how the signatures of head votes are proven. For now, the
block's `proof` covers them together with the attestations.

*TODO*: Specify how `AttestationProof` fits attestations aggregated over
multiple slots. For now, an aggregate covers one round, since its signers must
share an XMSS leaf, and its statements are per attestation committee.

*TODO*: Specify aggregator selection for head votes and attestations.

*Note*: This specification is built upon [EIP-8483](../eip8483/beacon-chain.md),
which is built upon [Gloas](../../gloas/beacon-chain.md).

## Types

### New `VRFProof`

```python
class VRFProof(Vector[Bytes32]):
    """
    A secret committed to by a leaf of the tree under a validator's VRF root,
    followed by the leaf's Merkle branch.
    """

    LENGTH = VRF_TREE_DEPTH + 1
```

### New `AttestationProof`

```python
class AttestationProof(ByteList):
    """
    A STARK proof of the XMSS signatures of attestations and head votes.
    """

    LIMIT = MAX_STARK_PROOF_SIZE
```

### New `XMSSPubkey`

```python
class XMSSPubkey(Bytes32):
    """
    A leanXMSS public key, the Merkle root followed by the public parameter.
    """
```

### New `XMSSSignature`

```python
class XMSSSignature(ByteVector):
    """
    A leanXMSS signature, the leaf index followed by one signature per layer.
    """

    LENGTH = XMSS_SIGNATURE_SIZE
```

### New `ValidatorPreregistrationRequests`

```python
class ValidatorPreregistrationRequests(ProgressiveList[ValidatorPreregistrationRequest]):
    """
    The validator preregistration requests pertaining to a single execution
    payload.
    """
```

### New `BuilderPreregistrationRequests`

```python
class BuilderPreregistrationRequests(ProgressiveList[BuilderPreregistrationRequest]):
    """
    The builder preregistration requests pertaining to a single execution
    payload.
    """
```

### New `ValidatorPreregistrations`

```python
class ValidatorPreregistrations(ProgressiveList[ValidatorPreregistration]):
    """
    The validator preregistrations stored in the beacon state, including
    expired records not yet garbage-collected.
    """
```

### New `BuilderPreregistrations`

```python
class BuilderPreregistrations(ProgressiveList[BuilderPreregistration]):
    """
    The builder preregistrations stored in the beacon state, including expired
    records not yet garbage-collected.
    """
```

### New `VoluntaryExitRequests`

```python
class VoluntaryExitRequests(ProgressiveList[VoluntaryExitRequest]):
    """
    The voluntary exit requests pertaining to a single execution payload.
    """
```

### New `AttestationCommittee`

```python
class AttestationCommittee(ProgressiveList[ValidatorIndex]):
    """
    An attestation committee of an epoch.
    """
```

### New `AttestationCommitteeBits`

```python
class AttestationCommitteeBits(BitVector):
    """
    Bits marking which attestation committees of an epoch participate in an
    attestation.
    """

    LENGTH = ATTESTATION_COMMITTEES_PER_ROUND
```

### New `Dynasty`

```python
class Dynasty(Uint64):
    """
    A chain counter that advances when a block of the current dynasty is finalized.
    """
```

### New `ACWeights`

Each entry counts effective-balance increments. The maximum effective balance is
2048 increments, which fits in `Uint16`.

```python
class ACWeights(List[Uint16]):
    LIMIT = VALIDATOR_REGISTRY_LIMIT
```

### New `ACSnapshots`

```python
class ACSnapshots(Vector[ACSnapshot]):
    LENGTH = 3
```

### New `HeadVoteCredentials`

```python
class HeadVoteCredentials(List[HeadVoteCredential]):
    LIMIT = 2 * HEAD_VOTE_COMMITTEE_SIZE
```

### New `HeadVotePaymentVoters`

```python
class HeadVotePaymentVoters(List[ValidatorIndex]):
    LIMIT = HEAD_VOTE_PAYMENT_TARGET
```

### New `HeadVoteParticipation`

```python
class HeadVoteParticipation(Vector[HeadVotePaymentVoters]):
    """
    Distinct voters credited per slot, for the previous and current epochs.
    """

    LENGTH = 2 * SLOTS_PER_EPOCH
```

### New `HeadVoteDeclarations`

```python
class HeadVoteDeclarations(ProgressiveList[HeadVoteDeclaration]):
    """
    The proposer's declarations for the previous slot.
    """
```

### New `HeadVoteSupportBits`

```python
class HeadVoteSupportBits(ProgressiveBitList):
    """
    One support bit per declaration, in declaration order.
    """
```

### New `HeadVotes`

```python
class HeadVotes(ProgressiveList[HeadVote]):
    """
    The head votes included in a beacon block.
    """
```

### New `Height`

```python
class Height(Uint64):
    """
    A height of the finality gadget. The chain moves to the next height when it
    justifies the target of the current height, or after a delay when target
    votes and timeouts together reach a quorum.
    """
```

### New `HeightParticipation`

```python
class HeightParticipation(ProgressiveList[Boolean]):
    """
    Whether each validator in the registry voted at a height, in validator index
    order.
    """
```

### New `PendingFinalities`

```python
class PendingFinalities(List[PendingFinality]):
    """
    The justifications on the chain that are not yet finalized, in increasing
    order of height.
    """

    LIMIT = PENDING_FINALITY_WINDOW
```

### New `Round`

```python
class Round(Uint64):
    """
    A round number. A round spans ``SLOTS_PER_ROUND`` slots, in which each
    active validator casts one FG attestation and after which the FG settles
    rewards and inactivity.
    """
```

### New `RoundParticipation`

```python
class RoundParticipation(ProgressiveList[ParticipationFlags]):
    """
    The participation flags of each validator for a round.
    """
```

## Constants

### Participation flag indices

| Name                  | Value       |
| --------------------- | ----------- |
| `PROGRESS_FLAG_INDEX` | `Uint64(0)` |
| `FINALITY_FLAG_INDEX` | `Uint64(1)` |

### Incentivization weights

| Name              | Value        |
| ----------------- | ------------ |
| `PROGRESS_WEIGHT` | `Uint64(40)` |
| `FINALITY_WEIGHT` | `Uint64(14)` |

*Note*: The progress flag takes the Altair weights of the source and target
flags, and the finality flag takes the weight of the head flag, so the sum of
the weights still equals `WEIGHT_DENOMINATOR`.

### Domains

| Name                         | Value                      |
| ---------------------------- | -------------------------- |
| `DOMAIN_HEAD_VOTE`           | `DomainType("0x12000000")` |
| `DOMAIN_HEAD_VOTE_COMMITTEE` | `DomainType("0x13000000")` |
| `DOMAIN_FINALITY_ATTESTER`   | `DomainType("0x14000000")` |

### Misc

| Name                            | Value                                |
| ------------------------------- | ------------------------------------ |
| `GENESIS_ROUND`                 | `Round(0)`                           |
| `TIMEOUT_DELAY_SLOTS`           | `SLOTS_PER_ROUND`                    |
| `PARTICIPATION_FLAG_WEIGHTS_PQ` | `[PROGRESS_WEIGHT, FINALITY_WEIGHT]` |

### XMSS

| Name                      | Value                             |
| ------------------------- | --------------------------------- |
| `XMSS_SIGNATURE_SIZE`     | `Uint64(2404)`                    |
| `XMSS_RESERVED_LEAVES`    | `Uint64(2**15)` (= 32,768)        |
| `XMSS_ATTESTATION_LEAVES` | `Uint64(2**29)` (= 536,870,912)   |
| `XMSS_BUILDER_BID_LEAVES` | `Uint64(2**30)` (= 1,073,741,824) |
| `XMSS_LEAVES_PER_SLOT`    | `Uint64(2**3)` (= 8)              |

### VRF

| Name              | Value         |
| ----------------- | ------------- |
| `VRF_TREE_DEPTH`  | `Uint64(31)`  |
| `VRF_LEAF_DOMAIN` | `b"VRF_LEAF"` |

### XMSS leaf offsets

| Name                                     | Value       |
| ---------------------------------------- | ----------- |
| `LEAF_OFFSET_BEACON_PROPOSER`            | `Uint64(0)` |
| `LEAF_OFFSET_AGGREGATE_AND_PROOF`        | `Uint64(1)` |
| `LEAF_OFFSET_PTC_ATTESTER`               | `Uint64(2)` |
| `LEAF_OFFSET_PROPOSER_PREFERENCES`       | `Uint64(3)` |
| `LEAF_OFFSET_EXECUTION_PAYLOAD_ENVELOPE` | `Uint64(4)` |
| `LEAF_OFFSET_HEAD_VOTE`                  | `Uint64(5)` |

### Deposits

| Name                  | Value       |
| --------------------- | ----------- |
| `XMSS_DEPOSIT_PREFIX` | `Bytes16()` |

### Legacy domains

| Name                        | Value            |
| --------------------------- | ---------------- |
| `LEGACY_XMSS_PUBKEY_DOMAIN` | `Bytes1("0x00")` |
| `LEGACY_VRF_ROOT_DOMAIN`    | `Bytes1("0x01")` |

### Execution-layer triggered requests

| Name                                     | Value            |
| ---------------------------------------- | ---------------- |
| `VALIDATOR_PREREGISTRATION_REQUEST_TYPE` | `Bytes1("0x07")` |
| `BUILDER_PREREGISTRATION_REQUEST_TYPE`   | `Bytes1("0x08")` |
| `VOLUNTARY_EXIT_REQUEST_TYPE`            | `Bytes1("0x09")` |

## Presets

### Finality gadget

| Name                      | Value                |
| ------------------------- | -------------------- |
| `PENDING_FINALITY_WINDOW` | `Uint64(2**1)` (= 2) |

*Note*: `PENDING_FINALITY_WINDOW` must be at least 2. The FG client reads its
finality pair from the pending justifications of the state in which its source
entered the height. When the previous height is not justified, it offers the
newest pending justification its signing record permits, and an older one when
the record rules out the newest, so the state keeps the older one too.

### Rounds

| Name                               | Value                       |
| ---------------------------------- | --------------------------- |
| `SLOTS_PER_ROUND`                  | `Slot(2**3)` (= 8)          |
| `ATTESTATION_COMMITTEES_PER_ROUND` | `Uint64(2**11)` (= 2,048)   |
| `MAX_VALIDATORS_PER_AGGREGATE`     | `Uint64(2**17)` (= 131,072) |

*Note*: `SLOTS_PER_EPOCH` must be a multiple of `SLOTS_PER_ROUND`, and
`ATTESTATION_COMMITTEES_PER_ROUND` must be a multiple of `SLOTS_PER_ROUND`.

### Head votes

| Name                            | Value                  |
| ------------------------------- | ---------------------- |
| `HEAD_VOTE_COMMITTEE_SIZE`      | `Uint64(2**9)` (= 512) |
| `HEAD_VOTE_FAST_LOCK_THRESHOLD` | `Uint64(327)`          |
| `HEAD_VOTE_UNLOCK_THRESHOLD`    | `Uint64(277)`          |
| `HEAD_VOTE_PAYMENT_TARGET`      | `Uint64(2**8)` (= 256) |

The committee size is an expectation, not a bound. The fast-lock threshold is
sized against the upper tail of the total ticket count to make disjoint fast
quorums unlikely. The lower unlock threshold is sized against adversarial ticket
weight while allowing honest voters to move older locks with less support. The
mainnet lock thresholds use a 10× seed-grinding buffer in their per-slot risk
budget; they do not imply deterministic quorum intersection. Under a Poisson
model, two thirds of stake voting reaches the mainnet fast-lock threshold in
about 79% of slots; recent fast locks provide sources for finality-gadget
duties.

The builder payment target is half the expected committee size, sized to limit
payments backed by adversarial voters alone while remaining reachable by honest
voters. Settlement counts distinct voters across all seats, not tickets. Minimal
scales each threshold by its committee size relative to mainnet and rounds up to
a whole number; it does not target the same tail probabilities.

The block credential limit is twice the expected committee size so a block can
carry a slot's full set of votes, with slack for variation in the number of
distinct voters. The builder payment target only limits payment accounting.

Presets must set `HEAD_VOTE_COMMITTEE_SIZE` to a power of two so seat assignment
by reduction modulo the committee size is uniform. It must also be at least
`SLOTS_PER_EPOCH + 2` so the third descriptor can seal before the penultimate
dynasty of each cycle.

The active snapshots retain their frozen stake as the committee interpolates
between them. Through a finality stall, the ticket draws remain fresh each slot
but their weights remain fixed. Validators that exit or are slashed keep the
tickets their frozen weights earn. New validators become eligible when a later
snapshot captures their stake.

Eligibility uses the frozen weights, so nodes do not change a vote's weight
based on locally seen slashing evidence or another branch's exit state. Budget
the frozen weight of exited or slashed validators as potentially adversarial.
Honest exits that stop voting make the absolute fast-lock and unlock ticket
thresholds harder to reach, but their absent votes do not enter the relative
quorum. In particular, honest votes still need to outweigh participating
adversarial votes.

### Rewards

| Name                  | Value                 |
| --------------------- | --------------------- |
| `ROUND_REWARD_FACTOR` | `Uint64(2**4)` (= 16) |

### Inactivity leak

| Name                            | Value                      |
| ------------------------------- | -------------------------- |
| `MIN_ROUNDS_TO_INACTIVITY_LEAK` | `Round(2**4)` (= 16)       |
| `EJECTION_INACTIVITY_SCORE`     | `Uint64(2**16)` (= 65,536) |

### XMSS

| Name                   | Value                         |
| ---------------------- | ----------------------------- |
| `MAX_STARK_PROOF_SIZE` | `Uint64(2**20)` (= 1,048,576) |

*Note*: `MAX_STARK_PROOF_SIZE` is a placeholder for the size of a STARK proof.
The reference concatenation fits at most
`MAX_STARK_PROOF_SIZE // XMSS_SIGNATURE_SIZE` signatures in a proof.

### Max operations per block

| Name                  | Value                 |
| --------------------- | --------------------- |
| `MAX_ATTESTATIONS_PQ` | `Uint64(2**4)` (= 16) |
| `MAX_HEAD_VOTES`      | `Uint64(2**3)` (= 8)  |

### Execution

| Name                                                 | Value                       |
| ---------------------------------------------------- | --------------------------- |
| `MAX_VALIDATOR_PREREGISTRATION_REQUESTS_PER_PAYLOAD` | `Uint64(2**6)` (= 64)       |
| `MAX_BUILDER_PREREGISTRATION_REQUESTS_PER_PAYLOAD`   | `Uint64(2**2)` (= 4)        |
| `PREREGISTRATIONS_LIMIT`                             | `Uint64(2**19)` (= 524,288) |
| `PREREGISTRATION_EXPIRY_SLOTS`                       | `Slot(2**18)` (= 262,144)   |
| `MAX_VOLUNTARY_EXIT_REQUESTS_PER_PAYLOAD`            | `Uint64(2**4)` (= 16)       |

## Configs

### Time parameters

| Name                                           | Value                     |
| ---------------------------------------------- | ------------------------- |
| `UNREGISTERED_VALIDATOR_WITHDRAWABILITY_DELAY` | `Epoch(2**14)` (= 16,384) |

## Containers

### New `HeadVoteDeclaration`

*Note*: Each declaration occupies 41 SSZ bytes. At one declaration per seat for
1,024 distinct mainnet participants, the declarations occupy 41,984 bytes (about
42 kB before Snappy), excluding the support bits. Two declarations per
participant double that budget.

```python
class HeadVoteDeclaration(Container):
    validator_index: ValidatorIndex
    beacon_block_root: Root
    payload_status: PayloadStatus
```

### Modified containers

#### `Attestation`

*Note*: The committees and signature domain of an attestation are those of the
epoch of the target slot of the state that includes it (see
`get_attestation_epoch`). `round` is not signed. It only selects the XMSS leaf
at which the attesters signed, so an attestation holds the signatures of one
round.

```python
class Attestation(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=5, gaps=(2,))

    aggregation_bits: AggregationBits
    data: AttestationData
    # [Modified in PQ]
    # Removed `signature`
    # [Modified in PQ:EIP8453]
    committee_bits: AttestationCommitteeBits
    # [New in PQ:EIP8453]
    round: Round
```

#### `AttestationData`

*Note*: The height pair is (`target`, `timeout`): a target vote when `timeout`
is false, and a timeout when it is true. The finality pair is `finality`.

```python
class AttestationData(Container):
    # [Modified in PQ:EIP8453]
    # Removed `slot`
    # [Modified in PQ:EIP8453]
    # Removed `index`
    # [Modified in PQ:EIP8453]
    # Removed `beacon_block_root`
    # [Modified in PQ:EIP8453]
    # Removed `source`
    # [Modified in PQ:EIP8453]
    target: HeightCheckpoint
    # [New in PQ:EIP8453]
    timeout: Boolean
    # [New in PQ:EIP8453]
    finality: HeightCheckpoint
```

#### `BeaconBlockBody`

```python
class BeaconBlockBody(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=17, gaps=(7, 8, 9, 11))

    # [Modified in PQ]
    randao_reveal: VRFProof
    eth1_data: Eth1Data
    graffiti: Bytes32
    proposer_slashings: ProposerSlashings
    attester_slashings: AttesterSlashings
    attestations: Attestations
    deposits: Deposits
    # [Modified in PQ]
    # Removed `voluntary_exits`
    # [Modified in PQ]
    # Removed `sync_aggregate`
    # [Modified in PQ]
    # Removed `bls_to_execution_changes`
    signed_execution_payload_bid: SignedExecutionPayloadBid
    # [Modified in PQ]
    # Removed `payload_attestations`
    parent_execution_requests: ExecutionRequests
    # [New in PQ]
    proof: AttestationProof
    # [New in PQ:EIP8453]
    head_votes: HeadVotes
    # [New in PQ:EIP8453]
    head_vote_support_bits: HeadVoteSupportBits
    # [New in PQ:EIP8453]
    head_vote_declarations: HeadVoteDeclarations
```

#### `BeaconState`

*Note*: The positions of the epoch participation and Casper FFG fields are left
as gaps, so their generalized indices are never reused. `finalized_checkpoint`
keeps its name but moves to a new position.

```python
class BeaconState(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=66, gaps=(15, 16, 17, 18, 19, 20, 22, 23, 46, 47))

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
    # [Modified in PQ:EIP8453]
    # Removed `previous_epoch_participation`
    # [Modified in PQ:EIP8453]
    # Removed `current_epoch_participation`
    # [Modified in PQ:EIP8453]
    # Removed `justification_bits`
    # [Modified in PQ:EIP8453]
    # Removed `previous_justified_checkpoint`
    # [Modified in PQ:EIP8453]
    # Removed `current_justified_checkpoint`
    # [Modified in PQ:EIP8453]
    # Removed `finalized_checkpoint`
    inactivity_scores: InactivityScores
    # [Modified in PQ]
    # Removed `current_sync_committee`
    # [Modified in PQ]
    # Removed `next_sync_committee`
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
    # [Modified in PQ]
    # Removed `validator_pq_registrations`
    # [Modified in PQ]
    # Removed `builder_pq_registrations`
    # [New in PQ:EIP8205]
    validator_preregistrations: ValidatorPreregistrations
    # [New in PQ:EIP8205]
    builder_preregistrations: BuilderPreregistrations
    # [New in PQ:EIP8453]
    previous_target_checkpoint: HeightCheckpoint
    # [New in PQ:EIP8453]
    target_checkpoint: HeightCheckpoint
    # [New in PQ:EIP8453]
    justified_checkpoint: HeightCheckpoint
    # [New in PQ:EIP8453]
    finalized_checkpoint: HeightCheckpoint
    # [New in PQ:EIP8453]
    previous_target_slot: Slot
    # [New in PQ:EIP8453]
    target_slot: Slot
    # [New in PQ:EIP8453]
    finalized_slot: Slot
    # [New in PQ:EIP8453]
    target_participation: HeightParticipation
    # [New in PQ:EIP8453]
    progress_participation: HeightParticipation
    # [New in PQ:EIP8453]
    round_participation: RoundParticipation
    # [New in PQ:EIP8453]
    pending_finality: PendingFinalities
    # [New in PQ:EIP8453]
    head_vote_participation: HeadVoteParticipation
    # [New in PQ:EIP8453]
    dynasty: Dynasty
    dynasty_start_slot: Slot
    previous_dynasty_start_slot: Slot
    ac_snapshots: ACSnapshots
```

#### `Builder`

```python
class Builder(Container):
    # [Modified in PQ]
    pubkey: XMSSPubkey
    version: Uint8
    execution_address: ExecutionAddress
    balance: Gwei
    deposit_epoch: Epoch
    withdrawable_epoch: Epoch
```

#### `BuilderDepositRequest`

```python
class BuilderDepositRequest(Container):
    # [Modified in PQ]
    pubkey: Bytes48
    withdrawal_credentials: Bytes32
    amount: Gwei
    # [Modified in PQ]
    signature: Bytes96
```

#### `BuilderExitRequest`

```python
class BuilderExitRequest(Container):
    source_address: ExecutionAddress
    # [Modified in PQ]
    pubkey: Bytes48
```

#### `ConsolidationRequest`

```python
class ConsolidationRequest(Container):
    source_address: ExecutionAddress
    # [Modified in PQ]
    source_pubkey: Bytes48
    # [Modified in PQ]
    target_pubkey: Bytes48
```

#### `DepositRequest`

```python
class DepositRequest(Container):
    # [Modified in PQ]
    pubkey: Bytes48
    withdrawal_credentials: Bytes32
    amount: Gwei
    # [Modified in PQ]
    signature: Bytes96
    index: Uint64
```

#### `ExecutionRequests`

```python
class ExecutionRequests(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=10, gaps=(5, 6))

    deposits: DepositRequests
    withdrawals: WithdrawalRequests
    consolidations: ConsolidationRequests
    builder_deposits: BuilderDepositRequests
    builder_exits: BuilderExitRequests
    # [Modified in PQ]
    # Removed `validator_pq_registrations`
    # [Modified in PQ]
    # Removed `builder_pq_registrations`
    # [New in PQ:EIP8205]
    validator_preregistrations: ValidatorPreregistrationRequests
    # [New in PQ:EIP8205]
    builder_preregistrations: BuilderPreregistrationRequests
    # [New in PQ]
    voluntary_exits: VoluntaryExitRequests
```

#### `IndexedAttestation`

*Note*: `epoch` selects the signature domain and `round` the XMSS leaf, so that
slashing evidence can be verified in any later state. Both are outside the
signed data, and a wrong value makes the proof invalid.

```python
class IndexedAttestation(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=5)

    attesting_indices: AttestingIndices
    data: AttestationData
    # [Modified in PQ]
    # Removed `signature`
    # [New in PQ]
    proof: AttestationProof
    # [New in PQ:EIP8453]
    epoch: Epoch
    # [New in PQ]
    round: Round
```

#### `PayloadAttestationMessage`

```python
class PayloadAttestationMessage(Container):
    validator_index: ValidatorIndex
    data: PayloadAttestationData
    # [Modified in PQ]
    signature: XMSSSignature
```

#### `PendingDeposit`

```python
class PendingDeposit(Container):
    # [Modified in PQ]
    pubkey: Bytes48
    withdrawal_credentials: Bytes32
    amount: Gwei
    # [Modified in PQ]
    signature: Bytes96
    slot: Slot
```

#### `SignedBeaconBlock`

```python
class SignedBeaconBlock(Container):
    message: BeaconBlock
    # [Modified in PQ]
    signature: XMSSSignature
```

#### `SignedBeaconBlockHeader`

```python
class SignedBeaconBlockHeader(Container):
    message: BeaconBlockHeader
    # [Modified in PQ]
    signature: XMSSSignature
```

#### `SignedExecutionPayloadBid`

```python
class SignedExecutionPayloadBid(Container):
    message: ExecutionPayloadBid
    # [Modified in PQ]
    signature: XMSSSignature
```

#### `SignedExecutionPayloadEnvelope`

```python
class SignedExecutionPayloadEnvelope(Container):
    message: ExecutionPayloadEnvelope
    # [Modified in PQ]
    signature: XMSSSignature
```

#### `SingleAttestation`

```python
class SingleAttestation(Container):
    committee_index: CommitteeIndex
    attester_index: ValidatorIndex
    data: AttestationData
    # [Modified in PQ]
    signature: XMSSSignature
    # [New in PQ:EIP8453]
    round: Round
```

#### `Validator`

```python
class Validator(Container):
    # [Modified in PQ]
    pubkey: XMSSPubkey
    # [New in PQ]
    vrf_root: Root
    withdrawal_credentials: Bytes32
    effective_balance: Gwei
    slashed: Boolean
    activation_eligibility_epoch: Epoch
    activation_epoch: Epoch
    exit_epoch: Epoch
    withdrawable_epoch: Epoch
```

#### `WithdrawalRequest`

```python
class WithdrawalRequest(Container):
    source_address: ExecutionAddress
    # [Modified in PQ]
    validator_pubkey: Bytes48
    amount: Gwei
```

### New containers

#### `HeightCheckpoint`

*Note*: The empty checkpoint, `HeightCheckpoint.empty()`, stands for an absent
finality pair.

```python
class HeightCheckpoint(Container):
    height: Height
    root: Root
```

#### `PendingFinality`

```python
class PendingFinality(Container):
    checkpoint: HeightCheckpoint
    slot: Slot
    participation: HeightParticipation
```

#### `ACSnapshot`

```python
class ACSnapshot(Container):
    weights: ACWeights
    seed: Bytes32
    capture_epoch: Epoch
```

#### `HeadVoteCredential`

```python
class HeadVoteCredential(Container):
    validator_index: ValidatorIndex
    proof: VRFProof
```

#### `HeadVoteData`

```python
class HeadVoteData(Container):
    slot: Slot
    beacon_block_root: Root
    payload_status: PayloadStatus
```

#### `HeadVote`

*Note*: A head vote in a block carries no signature. The block's `proof` proves
the signatures of its voters.

```python
class HeadVote(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=2)

    credentials: HeadVoteCredentials
    data: HeadVoteData
```

#### `HeadVoteMessage`

```python
class HeadVoteMessage(Container):
    validator_index: ValidatorIndex
    data: HeadVoteData
    signature: XMSSSignature
    proof: VRFProof
```

#### `ValidatorPreregistrationRequest`

*Note*: Before it emits a request, the system contract verifies that the binding
is signed by `pubkey` at a reserved leaf. The request therefore carries no
signature.

```python
class ValidatorPreregistrationRequest(Container):
    pubkey: XMSSPubkey
    withdrawal_credentials: Bytes32
    vrf_root: Root
```

#### `ValidatorPreregistration`

*Note*: `expiry_slot` is the absolute deadline computed when the preregistration
is stored. A later change to `PREREGISTRATION_EXPIRY_SLOTS` therefore affects
only newly stored records.

```python
class ValidatorPreregistration(Container):
    pubkey: XMSSPubkey
    withdrawal_credentials: Bytes32
    vrf_root: Root
    expiry_slot: Slot
```

#### `BuilderPreregistrationRequest`

*Note*: Before it emits a request, the system contract verifies that the binding
is signed by `pubkey` at a reserved leaf. A builder has no VRF root, so the
binding has none.

```python
class BuilderPreregistrationRequest(Container):
    pubkey: XMSSPubkey
    withdrawal_credentials: Bytes32
```

#### `BuilderPreregistration`

```python
class BuilderPreregistration(Container):
    pubkey: XMSSPubkey
    withdrawal_credentials: Bytes32
    expiry_slot: Slot
```

#### `VoluntaryExitRequest`

*Note*: Before it emits a request, the system contract verifies that the exit is
signed by `pubkey` at a reserved leaf. The request therefore carries no
signature.

```python
class VoluntaryExitRequest(Container):
    pubkey: XMSSPubkey
```

## Dataclasses

### New dataclasses

#### `XMSSAggregateStatement`

```python
@dataclass
class XMSSAggregateStatement:
    pubkeys: Sequence[XMSSPubkey]
    leaf_index: Uint64
    message: Bytes32
```

## Helpers

### Crypto

#### New `keccak256`

```python
def keccak256(data: bytes) -> Bytes32:
    """
    Return the Keccak-256 hash of ``data``.
    """
    return Bytes32(keccak256_hash(data))
```

#### New `xmss_sign`

```python
def xmss_sign(privkey: Bytes32, leaf_index: Uint64, message: Bytes32) -> XMSSSignature:
    """
    Return the signature of ``message`` at ``leaf_index``.
    """
    return XMSSSignature(xmss.Sign(privkey, leaf_index, message))
```

#### New `xmss_verify`

```python
def xmss_verify(
    pubkey: XMSSPubkey,
    leaf_index: Uint64,
    message: Bytes32,
    signature: XMSSSignature,
) -> bool:
    """
    Return ``True`` only if ``signature`` was produced at ``leaf_index``.
    """
    return xmss.Verify(pubkey, leaf_index, message, signature)
```

#### New `xmss_get_leaf_index`

```python
def xmss_get_leaf_index(signature: XMSSSignature) -> Uint64:
    """
    Return the leaf index that ``signature`` carries.
    """
    return Uint64(xmss.GetLeafIndex(signature))
```

#### New `stark_prove_aggregates`

```python
def stark_prove_aggregates(
    statements: Sequence[XMSSAggregateStatement],
    signatures: Sequence[Sequence[XMSSSignature]],
) -> AttestationProof:
    """
    Return a proof of ``signatures``, which holds the signatures for each of
    ``statements`` in order, and within a statement in the order of its public
    keys.
    """
    return AttestationProof(data=stark.ProveAggregates(statements, signatures))
```

#### New `stark_merge_proofs`

```python
def stark_merge_proofs(proofs: Sequence[AttestationProof]) -> AttestationProof:
    """
    Return one proof of the concatenation, in order, of the lists of statements
    that ``proofs`` prove.
    """
    return AttestationProof(data=stark.MergeProofs(proofs))
```

#### New `stark_verify_aggregates`

```python
def stark_verify_aggregates(
    statements: Sequence[XMSSAggregateStatement],
    proof: AttestationProof,
) -> bool:
    """
    Return ``True`` only if ``proof`` proves, for each of ``statements`` and
    each of its public keys, a signature that
    ``xmss_verify(pubkey, statement.leaf_index, statement.message, signature)``
    accepts.
    """
    return stark.VerifyAggregates(statements, proof)
```

### Misc

#### New `compute_legacy_xmss_pubkey`

```python
def compute_legacy_xmss_pubkey(pubkey: Bytes48) -> XMSSPubkey:
    """
    Return the XMSS public key derived from the BLS public key ``pubkey``.
    """
    return XMSSPubkey(keccak256(pubkey + LEGACY_XMSS_PUBKEY_DOMAIN))
```

#### New `compute_legacy_vrf_root`

```python
def compute_legacy_vrf_root(pubkey: Bytes48) -> Root:
    """
    Return the VRF root derived from the BLS public key ``pubkey``.
    """
    return Root(keccak256(pubkey + LEGACY_VRF_ROOT_DOMAIN))
```

#### New `compute_deposit_pubkey`

```python
def compute_deposit_pubkey(pubkey: Bytes48) -> XMSSPubkey:
    """
    Return the XMSS public key that a deposit naming ``pubkey`` is for.
    """
    if is_legacy_pubkey(pubkey):
        return compute_legacy_xmss_pubkey(pubkey)
    return XMSSPubkey(pubkey[16:])
```

#### New `compute_vrf_leaf`

*Note*: A leaf commits to its index as well as its secret, so no two leaves of a
tree are the same, even if its secrets repeat. A validator cannot save work by
repeating a small subtree in place of computing the whole tree.

```python
def compute_vrf_leaf(secret: Bytes32, index: Uint64) -> Bytes32:
    """
    Return the leaf at ``index`` of a VRF tree, which commits to ``secret``.
    """
    return keccak256(VRF_LEAF_DOMAIN + secret + uint_to_bytes(index))
```

#### New `compute_deposit_vrf_root`

```python
def compute_deposit_vrf_root(deposit: PendingDeposit) -> Root:
    """
    Return the VRF root of the validator that ``deposit`` creates.
    """
    if is_legacy_pubkey(deposit.pubkey):
        return compute_legacy_vrf_root(deposit.pubkey)
    return Root(deposit.signature[:32])
```

#### New `compute_xmss_attestation_leaf_index`

*Note*: The attestation leaves follow the `XMSS_RESERVED_LEAVES` reserved
leaves. They hold one attestation per round, since a validator attests at most
once per round, in the slot of its attestation committee.

```python
def compute_xmss_attestation_leaf_index(round: Round) -> Uint64:
    """
    Return the XMSS leaf at which an attestation is signed in ``round``.
    """
    return Uint64(XMSS_RESERVED_LEAVES + round)
```

#### New `compute_xmss_leaf_index`

```python
def compute_xmss_leaf_index(slot: Slot, leaf_offset: Uint64) -> Uint64:
    """
    Return the XMSS leaf at which a message of the type given by ``leaf_offset``
    is signed for ``slot``.
    """
    return Uint64(
        XMSS_RESERVED_LEAVES
        + XMSS_ATTESTATION_LEAVES
        + XMSS_BUILDER_BID_LEAVES
        + slot * XMSS_LEAVES_PER_SLOT
        + leaf_offset
    )
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

#### New `compute_attestation_committee_slot`

*Note*: The committees are split in index order into blocks of
`ATTESTATION_COMMITTEES_PER_ROUND // SLOTS_PER_ROUND` committees, one block per
slot of a round. From one round to the next, neighbouring blocks swap slots: the
blocks in slots `(0, 1), (2, 3), ...` after an even round and in slots
`(1, 2), (3, 4), ...` after an odd round. Each block moves towards one end of
the round, stays there for one round and moves back, so it votes in every slot
twice every `2 * SLOTS_PER_ROUND` rounds. Consecutive votes of a committee are
`SLOTS_PER_ROUND - 1`, `SLOTS_PER_ROUND` or `SLOTS_PER_ROUND + 1` slots apart.

```python
def compute_attestation_committee_slot(round: Round, index: CommitteeIndex) -> Slot:
    """
    Return the slot of ``round`` assigned to the committee at ``index``.
    """
    committees_per_slot = ATTESTATION_COMMITTEES_PER_ROUND // Uint64(SLOTS_PER_ROUND)
    block = Uint64(index) // committees_per_slot
    period = 2 * Uint64(SLOTS_PER_ROUND)
    # Even blocks move towards the last slot first, odd blocks towards the first
    if block % 2 == 0:
        position = (block + Uint64(round)) % period
    else:
        position = (block + period - Uint64(round) % period) % period
    # Positions past the last slot walk back from it
    if position >= SLOTS_PER_ROUND:
        position = period - 1 - position
    return compute_start_slot_at_round(round) + Slot(position)
```

#### Modified `compute_ptc`

```python
def compute_ptc(state: BeaconState, slot: Slot) -> PayloadTimelinessCommittee:
    """
    Get the payload timeliness committee for ``slot``, with possible duplicates.
    """
    epoch = compute_epoch_at_slot(slot)
    seed = sha256(get_seed(state, epoch, DOMAIN_PTC_ATTESTER) + uint_to_bytes(slot))
    # [Modified in PQ:EIP8453]
    indices = get_active_validator_indices(state, epoch)
    # [Modified in PQ:EIP8453]
    return PayloadTimelinessCommittee(
        data=compute_balance_weighted_selection(
            state,
            indices,
            seed,
            size=PTC_SIZE,
            shuffle_indices=True,
        )
    )
```

#### New `compute_ac_seat_indices`

For a validator of weight `w`, the target expected ticket count is `w * T / W`,
where `T` is the seat count and `W` is the frozen total weight. The validator
receives the integer part plus one ticket with probability rounded up from the
fractional part to the nearest multiple of `2**-64`. A single comparison with
128-bit products implements this rounding, with bias less than `2**-64`. Each
ticket independently chooses a seat index uniformly, with replacement. Repeated
seat indices count as separate tickets. A validator with zero weight receives no
seats, including when an upgraded historical head has no eligible validators.
Clients may cache the total weight for each snapshot.

```python
def compute_ac_seat_indices(
    snapshot: ACSnapshot,
    snapshot_number: Uint64,
    slot: Slot,
    validator_index: ValidatorIndex,
    secret: Bytes32,
) -> Sequence[Uint64]:
    if validator_index >= len(snapshot.weights):
        return []
    weight = snapshot.weights[validator_index]
    if weight == 0:
        return []
    total = sum(int(weight) for weight in snapshot.weights)
    count, remainder = divmod(int(weight) * int(HEAD_VOTE_COMMITTEE_SIZE), total)
    seed = sha256(
        DOMAIN_HEAD_VOTE_COMMITTEE
        + snapshot.seed
        + uint_to_bytes(snapshot_number)
        + uint_to_bytes(slot)
        + uint_to_bytes(validator_index)
        + secret
    )
    if int(bytes_to_uint64(seed[:8])) * total < remainder * 2**64:
        count += 1
    return [
        Uint64(
            bytes_to_uint64(sha256(seed + b"\x01" + uint_to_bytes(Uint64(ticket)))[:8])
            % HEAD_VOTE_COMMITTEE_SIZE
        )
        for ticket in range(count)
    ]
```

### Predicates

#### New `is_active_validator_preregistration`

*Note*: Activity is evaluated against the slot of the outstanding parent
payload, whose execution requests are the ones being applied during block
processing.

```python
def is_active_validator_preregistration(
    state: BeaconState,
    preregistration: ValidatorPreregistration,
) -> bool:
    """
    Check if ``preregistration`` has not expired.
    """
    parent_slot = state.latest_execution_payload_bid.slot
    return parent_slot < preregistration.expiry_slot
```

#### New `is_active_builder_preregistration`

```python
def is_active_builder_preregistration(
    state: BeaconState,
    preregistration: BuilderPreregistration,
) -> bool:
    """
    Check if ``preregistration`` has not expired.
    """
    parent_slot = state.latest_execution_payload_bid.slot
    return parent_slot < preregistration.expiry_slot
```

#### New `is_builder_bid_leaf_index`

```python
def is_builder_bid_leaf_index(leaf_index: Uint64) -> bool:
    """
    Check if ``leaf_index`` is one of the leaves reserved for builder bids.
    """
    start = XMSS_RESERVED_LEAVES + XMSS_ATTESTATION_LEAVES
    return start <= leaf_index < start + XMSS_BUILDER_BID_LEAVES
```

#### New `is_legacy_pubkey`

*Note*: A request made after the upgrade names 16 zero bytes followed by an XMSS
public key. A request made before it names a compressed BLS public key, whose
first byte always has its top bit set as the compression flag.

```python
def is_legacy_pubkey(pubkey: Bytes48) -> bool:
    """
    Check if ``pubkey`` is a BLS public key rather than an XMSS public key.
    """
    return pubkey[:16] != XMSS_DEPOSIT_PREFIX
```

#### New `is_valid_vrf_proof`

```python
def is_valid_vrf_proof(
    state: BeaconState,
    validator_index: ValidatorIndex,
    slot: Slot,
    proof: VRFProof,
) -> bool:
    """
    Check that ``proof`` reveals the secret that the leaf at index ``slot`` of
    the tree under the VRF root of the validator at ``validator_index`` commits
    to.
    """
    if slot >= 2**VRF_TREE_DEPTH:
        return False
    value = compute_vrf_leaf(proof[0], Uint64(slot))
    for height in range(VRF_TREE_DEPTH):
        if slot // (2**height) % 2:
            value = keccak256(proof[height + 1] + value)
        else:
            value = keccak256(value + proof[height + 1])
    return value == state.validators[validator_index].vrf_root
```

#### Modified `is_pending_validator`

*Note*: Deposits carry no signature, so any pending deposit for the key counts.

```python
def is_pending_validator(
    pending_deposits: Sequence[PendingDeposit],
    # [Modified in PQ]
    pubkey: XMSSPubkey,
) -> bool:
    """
    Check if a pending deposit is in the queue for the given pubkey.
    """
    for pending_deposit in pending_deposits:
        # [Modified in PQ]
        if compute_deposit_pubkey(pending_deposit.pubkey) == pubkey:
            return True
    return False
```

#### Modified `is_valid_indexed_attestation`

*Note*: The `proof` of an indexed attestation proves one statement, over the
public keys of its attesting indices in order.

```python
def is_valid_indexed_attestation(
    state: BeaconState,
    indexed_attestation: IndexedAttestation,
) -> bool:
    """
    Check if ``indexed_attestation`` is not empty, has sorted and unique
    indices and has a valid stark proof.
    """
    # Verify indices are sorted and unique
    indices = indexed_attestation.attesting_indices
    if (
        len(indices) == 0
        # [Modified in PQ:EIP8453]
        or len(indices) > MAX_VALIDATORS_PER_AGGREGATE
        or list(indices) != sorted(set(indices))
    ):
        return False
    # [Modified in PQ]
    # Verify the proof of the attesters' signatures
    pubkeys = [state.validators[index].pubkey for index in indices]
    # [Modified in PQ:EIP8453]
    domain = get_domain(state, DOMAIN_FINALITY_ATTESTER, indexed_attestation.epoch)
    signing_root = compute_signing_root(indexed_attestation.data, domain)
    leaf_index = compute_xmss_attestation_leaf_index(indexed_attestation.round)
    statement = XMSSAggregateStatement(pubkeys=pubkeys, leaf_index=leaf_index, message=signing_root)
    return stark_verify_aggregates([statement], indexed_attestation.proof)
```

#### New `is_well_formed_attestation_data`

```python
def is_well_formed_attestation_data(data: AttestationData) -> bool:
    """
    Check if the height pair and the finality pair of ``data`` have valid
    forms.
    """
    if data.target.height == 0 or data.target.root == Root():
        return False
    if data.finality == HeightCheckpoint.empty():
        return True
    return data.finality.root != Root() and data.finality.height < data.target.height
```

#### New `is_valid_attestation_data`

```python
def is_valid_attestation_data(state: BeaconState, data: AttestationData) -> bool:
    """
    Check if ``data`` names the current or the previous target checkpoint of
    ``state``.
    """
    # [Modified in PQ:EIP8453]
    # Only votes for the current or the previous target are included
    return data.target == state.target_checkpoint or is_previous_target_attestation_data(
        state, data
    )
```

#### New `is_previous_target_attestation_data`

```python
def is_previous_target_attestation_data(state: BeaconState, data: AttestationData) -> bool:
    """
    Check if ``data`` names the previous target checkpoint of ``state``.
    """
    previous_target = state.previous_target_checkpoint
    return previous_target.height > 0 and data.target == previous_target
```

#### New `is_double_target_vote`

```python
def is_double_target_vote(data_1: AttestationData, data_2: AttestationData) -> bool:
    """
    Check if ``data_1`` and ``data_2`` are target votes for different roots
    at the same height.
    """
    if data_1.timeout:
        return False
    if data_2.timeout:
        return False
    if data_1.target.height != data_2.target.height:
        return False
    if data_1.target.root == data_2.target.root:
        return False
    return True
```

#### New `is_conflicting_with_finality_pair`

*Note*: A timeout that names the root of the finality pair does not conflict
with it.

```python
def is_conflicting_with_finality_pair(data: AttestationData, finality: HeightCheckpoint) -> bool:
    """
    Check if ``data`` votes at the height of the non-empty ``finality`` pair
    for another root, as a target vote or a timeout.
    """
    if finality == HeightCheckpoint.empty():
        return False
    if data.target.height != finality.height:
        return False
    if data.target.root != finality.root:
        return True
    return False
```

#### Modified `is_slashable_attestation_data`

*Note*: The function `is_slashable_attestation_data` is rewritten for the
finality gadget.

```python
def is_slashable_attestation_data(data_1: AttestationData, data_2: AttestationData) -> bool:
    """
    Check if ``data_1`` and ``data_2`` are slashable according to the finality
    gadget rules.
    """
    if is_double_target_vote(data_1, data_2):
        return True
    if is_conflicting_with_finality_pair(data_1, data_2.finality):
        return True
    if is_conflicting_with_finality_pair(data_2, data_1.finality):
        return True
    return False
```

#### Modified `is_eligible_for_activation`

```python
def is_eligible_for_activation(state: BeaconState, validator: Validator) -> bool:
    """
    Check if ``validator`` is eligible for activation.
    """
    return (
        # [Modified in PQ:EIP8453]
        # Placement in queue is finalized
        validator.activation_eligibility_epoch <= compute_epoch_at_slot(state.finalized_slot)
        # Has not yet been activated
        and validator.activation_epoch == FAR_FUTURE_EPOCH
    )
```

#### Modified `is_active_builder`

```python
def is_active_builder(state: BeaconState, builder_index: BuilderIndex) -> bool:
    """
    Check if the builder at ``builder_index`` is active for the given ``state``.
    """
    builder = state.builders[builder_index]
    return (
        # [Modified in PQ:EIP8453]
        # Placement in builder list is finalized
        builder.deposit_epoch < compute_epoch_at_slot(state.finalized_slot)
        # Has not initiated exit
        and builder.withdrawable_epoch == FAR_FUTURE_EPOCH
    )
```

#### New `is_valid_head_vote_declarations`

```python
def is_valid_head_vote_declarations(body: BeaconBlockBody, slot: Slot) -> bool:
    declarations = body.head_vote_declarations
    if len(declarations) != len(body.head_vote_support_bits):
        return False
    if len(declarations) > 4 * HEAD_VOTE_COMMITTEE_SIZE:
        return False
    if declarations and (slot == GENESIS_SLOT or compute_epoch_at_slot(slot - 1) < PQ_FORK_EPOCH):
        return False
    heads: dict[ValidatorIndex, set[tuple[Root, PayloadStatus]]] = {}
    for declaration in declarations:
        status = declaration.payload_status
        if status not in (PAYLOAD_STATUS_PENDING, PAYLOAD_STATUS_EMPTY, PAYLOAD_STATUS_FULL):
            return False
        if declaration.validator_index not in heads:
            heads[declaration.validator_index] = set()
        previous = heads[declaration.validator_index]
        head = (declaration.beacon_block_root, status)
        if head in previous:
            return False
        previous.add(head)
    return True
```

#### New `is_head_vote_same_slot`

```python
def is_head_vote_same_slot(state: BeaconState, data: HeadVoteData) -> bool:
    """
    Check if ``data`` votes for the block proposed at its slot.
    """
    if data.beacon_block_root != get_block_root_at_slot(state, data.slot):
        return False
    if data.slot == GENESIS_SLOT:
        return True
    if data.beacon_block_root == get_block_root_at_slot(state, data.slot - 1):
        return False
    return True
```

#### New `is_head_vote_payload_status_valid`

*Note*: The beacon state checks payload status against its retained canonical
block roots. A canonical block from the vote's own slot requires PENDING; a root
recorded at an earlier slot requires EMPTY or FULL. Non-canonical roots may name
same-slot siblings, so their slot is checked by store-aware paths when the block
is available. Clients should index retained roots by root, recording the
earliest retained slot for each root, to avoid scanning the history for each
vote.

```python
def is_head_vote_payload_status_valid(state: BeaconState, data: HeadVoteData) -> bool:
    if data.payload_status not in (
        PAYLOAD_STATUS_EMPTY,
        PAYLOAD_STATUS_FULL,
        PAYLOAD_STATUS_PENDING,
    ):
        return False

    oldest_slot = Slot(max(state.slot, SLOTS_PER_HISTORICAL_ROOT) - SLOTS_PER_HISTORICAL_ROOT)
    if (
        data.slot < state.slot
        and (data.slot > oldest_slot or (data.slot == GENESIS_SLOT and oldest_slot == GENESIS_SLOT))
        and is_head_vote_same_slot(state, data)
    ):
        return data.payload_status == PAYLOAD_STATUS_PENDING
    if data.payload_status == PAYLOAD_STATUS_PENDING:
        for slot in range(oldest_slot, min(data.slot, state.slot)):
            if get_block_root_at_slot(state, Slot(slot)) == data.beacon_block_root:
                return False
    return True
```

#### New `has_builder_payment_quorum`

```python
def has_builder_payment_quorum(participation: HeadVotePaymentVoters) -> bool:
    """
    Check whether the distinct voters reach the payment target.
    """
    return len(participation) == HEAD_VOTE_PAYMENT_TARGET
```

#### New `has_quorum`

```python
def has_quorum(state: BeaconState, participation: HeightParticipation) -> bool:
    """
    Check if the validators marked in ``participation`` hold at least two
    thirds of the total weight of the active validators.
    """
    active_indices = set(get_active_validator_indices(state, get_current_epoch(state)))
    participating_weight = get_participating_weight(state, participation)
    total_weight = get_total_weight(state, active_indices)
    return participating_weight > 0 and participating_weight * 3 >= total_weight * 2
```

#### Modified `is_in_inactivity_leak`

```python
def is_in_inactivity_leak(state: BeaconState) -> bool:
    # [Modified in PQ:EIP8453]
    return get_finality_delay(state) > MIN_ROUNDS_TO_INACTIVITY_LEAK
```

#### New `is_valid_aggregation_bits`

```python
def is_valid_aggregation_bits(state: BeaconState, epoch: Epoch, aggregate: Attestation) -> bool:
    """
    Check if the ``aggregation_bits`` of ``aggregate`` has one bit for each
    member of the attestation committees marked in its ``committee_bits``,
    within the aggregate limit.
    """
    committees_size = 0
    for committee_index in get_committee_indices(aggregate.committee_bits):
        committees_size += len(get_attestation_committee(state, epoch, committee_index))
    if committees_size > MAX_VALIDATORS_PER_AGGREGATE:
        return False
    return len(aggregate.aggregation_bits) == committees_size
```

### Beacon state accessors

#### Modified `get_attesting_indices`

```python
def get_attesting_indices(state: BeaconState, attestation: Attestation) -> set[ValidatorIndex]:
    """
    Return the set of attesting indices corresponding to ``aggregation_bits``
    and ``committee_bits``.
    """
    # [Modified in PQ:EIP8453]
    return get_aggregate_participants(
        state, get_attestation_epoch(state, attestation.data), attestation
    )
```

#### Modified `get_indexed_attestation`

```python
def get_indexed_attestation(
    state: BeaconState,
    attestation: Attestation,
    # [New in PQ]
    proof: AttestationProof,
) -> IndexedAttestation:
    """
    Return the indexed attestation corresponding to ``attestation`` and the
    ``proof`` of its attesters' signatures.
    """
    attesting_indices = get_attesting_indices(state, attestation)

    return IndexedAttestation(
        attesting_indices=AttestingIndices(data=sorted(attesting_indices)),
        data=attestation.data,
        # [Modified in PQ]
        proof=proof,
        # [New in PQ:EIP8453]
        epoch=get_attestation_epoch(state, attestation.data),
        # [New in PQ]
        round=attestation.round,
    )
```

#### New `get_attestation_statements`

*Note*: Statements are per attestation committee so that the proposer can merge
the proofs of aggregates that cover different committees into the block's
`proof`. All attesters of an attestation signed at the leaf of its `round`.

*TODO*: Revisit the statements once the aggregation of attestations over
multiple slots is specified.

```python
def get_attestation_statements(
    state: BeaconState,
    attestation: Attestation,
) -> Sequence[XMSSAggregateStatement]:
    """
    Return, for each committee of ``attestation`` in order, the statement that the
    signatures of its attesters in that committee prove.
    """
    # [Modified in PQ:EIP8453]
    epoch = get_attestation_epoch(state, attestation.data)
    domain = get_domain(state, DOMAIN_FINALITY_ATTESTER, epoch)
    message = compute_signing_root(attestation.data, domain)
    leaf_index = compute_xmss_attestation_leaf_index(attestation.round)
    statements = []
    committee_offset = 0
    for committee_index in get_committee_indices(attestation.committee_bits):
        committee = get_attestation_committee(state, epoch, committee_index)
        pubkeys = [
            state.validators[validator_index].pubkey
            for i, validator_index in enumerate(committee)
            if attestation.aggregation_bits[committee_offset + i]
        ]
        statements.append(
            XMSSAggregateStatement(pubkeys=pubkeys, leaf_index=leaf_index, message=message)
        )
        committee_offset += len(committee)
    return statements
```

#### New `get_head_vote_statement`

*TODO*: Revisit once the proof of head vote signatures is specified.

```python
def get_head_vote_statement(state: BeaconState, vote: HeadVote) -> XMSSAggregateStatement:
    """
    Return the statement that the signatures of the voters of ``vote`` prove.
    """
    data = vote.data
    domain = get_domain(state, DOMAIN_HEAD_VOTE, compute_epoch_at_slot(data.slot))
    message = compute_signing_root(data, domain)
    leaf_index = compute_xmss_leaf_index(data.slot, LEAF_OFFSET_HEAD_VOTE)
    pubkeys = [
        state.validators[credential.validator_index].pubkey for credential in vote.credentials
    ]
    return XMSSAggregateStatement(pubkeys=pubkeys, leaf_index=leaf_index, message=message)
```

#### New `get_validator_preregistration_index`

```python
def get_validator_preregistration_index(state: BeaconState, pubkey: XMSSPubkey) -> Uint64 | None:
    """
    Return the index of the validator preregistration of ``pubkey``, if any.
    """
    for index, preregistration in enumerate(state.validator_preregistrations):
        if preregistration.pubkey == pubkey:
            return Uint64(index)
    return None
```

#### New `get_active_validator_preregistration`

```python
def get_active_validator_preregistration(
    state: BeaconState,
    pubkey: XMSSPubkey,
) -> ValidatorPreregistration | None:
    """
    Return the active validator preregistration of ``pubkey``, if any.
    """
    index = get_validator_preregistration_index(state, pubkey)
    if index is None:
        return None
    preregistration = state.validator_preregistrations[index]
    if not is_active_validator_preregistration(state, preregistration):
        return None
    return preregistration
```

#### New `get_builder_preregistration_index`

```python
def get_builder_preregistration_index(state: BeaconState, pubkey: XMSSPubkey) -> Uint64 | None:
    """
    Return the index of the builder preregistration of ``pubkey``, if any.
    """
    for index, preregistration in enumerate(state.builder_preregistrations):
        if preregistration.pubkey == pubkey:
            return Uint64(index)
    return None
```

#### New `get_active_builder_preregistration`

```python
def get_active_builder_preregistration(
    state: BeaconState,
    pubkey: XMSSPubkey,
) -> BuilderPreregistration | None:
    """
    Return the active builder preregistration of ``pubkey``, if any.
    """
    index = get_builder_preregistration_index(state, pubkey)
    if index is None:
        return None
    preregistration = state.builder_preregistrations[index]
    if not is_active_builder_preregistration(state, preregistration):
        return None
    return preregistration
```

#### New `get_current_round`

```python
def get_current_round(state: BeaconState) -> Round:
    """
    Return the current round.
    """
    return compute_round_at_slot(state.slot)
```

#### New `get_previous_round`

```python
def get_previous_round(state: BeaconState) -> Round:
    """
    Return the previous round, or ``GENESIS_ROUND`` if that is
    the current round.
    """
    current_round = get_current_round(state)
    if current_round == GENESIS_ROUND:
        return GENESIS_ROUND
    return current_round - 1
```

#### New `get_attestation_committee`

*Note*: The committee at `index` holds the validators whose index is `index`
modulo `ATTESTATION_COMMITTEES_PER_ROUND`, in index order, that are eligible for
activation by `epoch` and have not exited by `epoch`. A validator's committee
index is fixed by its validator index. The committees include validators that
are not yet active, and validators that exit later; their signatures verify but
do not count.

*Note*: `process_registry_updates` sets `activation_eligibility_epoch` once, to
the epoch after the one being processed, and an exit epoch is set at least
`1 + MAX_SEED_LOOKAHEAD` epochs ahead. The committees of `epoch` are therefore
fixed before the start of `epoch`: two chains that share a block of `epoch` or
of a later epoch have the same committees of `epoch`. Every validator that is
active in a state whose target is in `epoch` is eligible for activation by
`epoch`, since its activation required its eligibility to be finalized.

```python
def get_attestation_committee(
    state: BeaconState, epoch: Epoch, index: CommitteeIndex
) -> AttestationCommittee:
    """
    Return the attestation committee at ``index`` for ``epoch``.
    """
    return AttestationCommittee(
        data=[
            ValidatorIndex(validator_index)
            for validator_index in range(
                index, len(state.validators), ATTESTATION_COMMITTEES_PER_ROUND
            )
            if state.validators[validator_index].activation_eligibility_epoch
            <= epoch
            < state.validators[validator_index].exit_epoch
        ]
    )
```

#### New `get_attestation_epoch`

*Note*: Attestations are included only while their target is the current or the
previous target of the chain, and every chain on which that holds contains the
target block. So the committees of the target's epoch, and the signature domain,
are the same on every chain that can include an attestation, and an aggregate
has one encoding on all of them. The committees of an earlier epoch read from a
later state are the same, since eligibility and exit epochs are only ever set to
later epochs.

```python
def get_attestation_epoch(state: BeaconState, data: AttestationData) -> Epoch:
    """
    Return the epoch of the committees and the signature domain of an
    attestation with ``data`` included in ``state``, the epoch of its target.
    """
    if is_previous_target_attestation_data(state, data):
        return compute_epoch_at_slot(state.previous_target_slot)
    return compute_epoch_at_slot(state.target_slot)
```

#### New `get_aggregate_participants`

```python
def get_aggregate_participants(
    state: BeaconState, epoch: Epoch, aggregate: Attestation
) -> set[ValidatorIndex]:
    """
    Return the validators marked in the ``aggregation_bits`` of ``aggregate``,
    which concatenates the attestation committees marked in its
    ``committee_bits`` for ``epoch``.
    """
    participants: set[ValidatorIndex] = set()
    committee_offset = 0
    for committee_index in get_committee_indices(aggregate.committee_bits):
        committee = get_attestation_committee(state, epoch, committee_index)
        for i, validator_index in enumerate(committee):
            if aggregate.aggregation_bits[committee_offset + i]:
                participants.add(validator_index)
        committee_offset += len(committee)
    return participants
```

#### New `get_ac_seat_indices`

For dynasty `d`, the snapshot boundary index is `d % T`. Seat indices below it
use the newer snapshot numbered `d // T + 1`; seat indices at or above it use
the older snapshot numbered `d // T`. The next snapshot has number `d // T + 2`.
Storage uses the snapshot number modulo three. Draws use the full number, so
seats staying with a snapshot retain their draws for the same slot across a
rollover. The returned sequence retains one entry per winning ticket, including
repeated seat indices.

```python
def get_ac_seat_indices(
    state: BeaconState,
    dynasty: Dynasty,
    slot: Slot,
    validator_index: ValidatorIndex,
    secret: Bytes32,
) -> Sequence[Uint64]:
    snapshot_number = Uint64(dynasty // HEAD_VOTE_COMMITTEE_SIZE)
    snapshot_boundary_index = dynasty % HEAD_VOTE_COMMITTEE_SIZE
    snapshots = state.ac_snapshots
    old_seat_indices = compute_ac_seat_indices(
        snapshots[snapshot_number % len(snapshots)],
        snapshot_number,
        slot,
        validator_index,
        secret,
    )
    seat_indices = [
        seat_index for seat_index in old_seat_indices if seat_index >= snapshot_boundary_index
    ]
    if snapshot_boundary_index > 0:
        snapshot_number += 1
        new_seat_indices = compute_ac_seat_indices(
            snapshots[snapshot_number % len(snapshots)],
            snapshot_number,
            slot,
            validator_index,
            secret,
        )
        seat_indices.extend(
            seat_index for seat_index in new_seat_indices if seat_index < snapshot_boundary_index
        )
    return seat_indices
```

#### New `get_head_vote_weight`

Fork choice uses the voting head's post-state and the full duty slot, including
when the head is older than the duty. Block inclusion uses the including chain's
dynasty at the end of the duty slot, carried forward over empty slots. A duty
before the previous dynasty has no weight for inclusion.

The draft uses the registered RANDAO tree. A proposer reveal also reveals the
proposer's AC opening for that slot, and an AC vote reveals the voter's RANDAO
secret for that slot. The sampler uses the authenticated secret, whose leaf
commitment is checked by `is_valid_vrf_proof`. The commitment itself can appear
in another slot's proof and is not the lottery input.

```python
def get_head_vote_weight(
    state: BeaconState, slot: Slot, validator_index: ValidatorIndex, proof: VRFProof
) -> Uint64:
    if compute_epoch_at_slot(slot) < PQ_FORK_EPOCH:
        return Uint64(0)
    if validator_index >= len(state.validators):
        return Uint64(0)
    if not is_valid_vrf_proof(state, validator_index, slot, proof):
        return Uint64(0)

    dynasty = state.dynasty
    if slot < state.dynasty_start_slot:
        if slot < state.previous_dynasty_start_slot:
            return Uint64(0)
        dynasty -= 1
    return Uint64(len(get_ac_seat_indices(state, dynasty, slot, validator_index, proof[0])))
```

#### Modified `get_unslashed_participating_indices`

*Note*: The function `get_unslashed_participating_indices` is rewritten to use
round participation.

```python
def get_unslashed_participating_indices(state: BeaconState, flag_index: int) -> set[ValidatorIndex]:
    """
    Return the set of validator indices that are both active and unslashed for
    the given ``flag_index`` in the current round.
    """
    participating_indices: set[ValidatorIndex] = set()
    for index in get_active_validator_indices(state, get_current_epoch(state)):
        flags = state.round_participation[index]
        if has_flag(flags, flag_index) and not state.validators[index].slashed:
            participating_indices.add(index)
    return participating_indices
```

#### New `get_validator_weight`

*Note*: A validator's weight is its current effective balance in increments,
multiplied by `EJECTION_INACTIVITY_SCORE**2 - inactivity_score**2`. The weight
reaches zero at `EJECTION_INACTIVITY_SCORE`. Weight calculations use `Uint256`
to avoid overflow when summing weights and checking quorums.

```python
def get_validator_weight(state: BeaconState, index: ValidatorIndex) -> Uint256:
    """
    Return the weight of the validator at ``index`` in finality gadget quorums.
    """
    increments = Uint256(state.validators[index].effective_balance // EFFECTIVE_BALANCE_INCREMENT)
    inactivity_score = min(state.inactivity_scores[index], EJECTION_INACTIVITY_SCORE)
    inactivity_weight = (EJECTION_INACTIVITY_SCORE - inactivity_score) * (
        EJECTION_INACTIVITY_SCORE + inactivity_score
    )
    return increments * Uint256(inactivity_weight)
```

#### New `get_total_weight`

```python
def get_total_weight(state: BeaconState, indices: set[ValidatorIndex]) -> Uint256:
    """
    Return the combined weight of the ``indices``.
    """
    total_weight = Uint256(0)
    for index in indices:
        total_weight += get_validator_weight(state, index)
    return total_weight
```

#### New `get_participating_weight`

```python
def get_participating_weight(state: BeaconState, participation: HeightParticipation) -> Uint256:
    """
    Return the combined weight of the active and unslashed validators marked in
    ``participation``.
    """
    participating_indices: set[ValidatorIndex] = set()
    for index in get_active_validator_indices(state, get_current_epoch(state)):
        if participation[index] and not state.validators[index].slashed:
            participating_indices.add(index)
    return get_total_weight(state, participating_indices)
```

#### Modified `get_finality_delay`

*Note*: The function `get_finality_delay` is rewritten to measure the delay in
rounds. The finality gadget can finalize a block of the current round, so the
delay stops at zero rather than going negative.

```python
def get_finality_delay(state: BeaconState) -> Round:
    previous_round = get_previous_round(state)
    finalized_round = compute_round_at_slot(state.finalized_slot)
    if finalized_round > previous_round:
        return Round(0)
    return previous_round - finalized_round
```

#### New `get_round_base_reward`

```python
def get_round_base_reward(state: BeaconState, index: ValidatorIndex) -> Gwei:
    """
    Return the base reward for one round of the validator at ``index``.
    """
    increments = state.validators[index].effective_balance // EFFECTIVE_BALANCE_INCREMENT
    total_balance_root = integer_squareroot(get_total_active_balance(state))
    reward_per_increment = EFFECTIVE_BALANCE_INCREMENT * ROUND_REWARD_FACTOR // total_balance_root
    return increments * reward_per_increment
```

#### New `get_flag_index_rewards`

*Note*: This replaces `get_flag_index_deltas`. A validator without the flag
forfeits the reward and is not penalized, and no rewards are paid during an
inactivity leak. Rewards are settled at the end of each round.

```python
def get_flag_index_rewards(state: BeaconState, flag_index: int) -> Sequence[Gwei]:
    """
    Return the rewards for a given ``flag_index`` by scanning through the
    participation flags.
    """
    rewards = [Gwei(0)] * len(state.validators)
    if is_in_inactivity_leak(state):
        return rewards

    unslashed_participating_indices = get_unslashed_participating_indices(state, flag_index)
    weight = PARTICIPATION_FLAG_WEIGHTS_PQ[flag_index]
    unslashed_participating_balance = get_total_balance(state, unslashed_participating_indices)
    unslashed_participating_increments = (
        unslashed_participating_balance // EFFECTIVE_BALANCE_INCREMENT
    )
    active_increments = get_total_active_balance(state) // EFFECTIVE_BALANCE_INCREMENT
    for index in unslashed_participating_indices:
        base_reward = get_round_base_reward(state, index)
        reward_numerator = base_reward * weight * unslashed_participating_increments
        reward_denominator = active_increments * WEIGHT_DENOMINATOR
        rewards[index] += reward_numerator // reward_denominator
    return rewards
```

### Beacon state mutators

#### Modified `queue_excess_active_balance`

```python
def queue_excess_active_balance(state: BeaconState, index: ValidatorIndex) -> None:
    balance = state.balances[index]
    if balance > MIN_ACTIVATION_BALANCE:
        excess_balance = balance - MIN_ACTIVATION_BALANCE
        state.balances[index] = MIN_ACTIVATION_BALANCE
        validator = state.validators[index]
        # Use an empty signature field as a placeholder
        # and GENESIS_SLOT to distinguish from a pending deposit request
        state.pending_deposits.append(
            PendingDeposit(
                # [Modified in PQ]
                pubkey=Bytes48(XMSS_DEPOSIT_PREFIX + validator.pubkey),
                withdrawal_credentials=validator.withdrawal_credentials,
                amount=excess_balance,
                # [Modified in PQ]
                signature=Bytes96(),
                slot=GENESIS_SLOT,
            )
        )
```

#### New `remove_validator_preregistration`

*Note*: Removal preserves the order of the remaining records, which the state
root commits to.

```python
def remove_validator_preregistration(state: BeaconState, pubkey: XMSSPubkey) -> None:
    """
    Remove the validator preregistration of ``pubkey``.
    """
    state.validator_preregistrations = ValidatorPreregistrations(
        data=[
            preregistration
            for preregistration in state.validator_preregistrations
            if preregistration.pubkey != pubkey
        ]
    )
```

#### New `remove_builder_preregistration`

```python
def remove_builder_preregistration(state: BeaconState, pubkey: XMSSPubkey) -> None:
    """
    Remove the builder preregistration of ``pubkey``.
    """
    state.builder_preregistrations = BuilderPreregistrations(
        data=[
            preregistration
            for preregistration in state.builder_preregistrations
            if preregistration.pubkey != pubkey
        ]
    )
```

#### New `add_participation_flag`

```python
def add_participation_flag(state: BeaconState, index: ValidatorIndex, flag_index: int) -> None:
    """
    Add the flag at ``flag_index`` to the participation of the validator at
    ``index`` in the current round.
    """
    state.round_participation[index] = add_flag(state.round_participation[index], flag_index)
```

## Beacon chain state transition function

### Modified `state_transition`

*Note*: The upgraded state of the last block before the PQ fork is already at
the fork slot, where the first block after the fork can be. Slots are processed
only up to the block's slot.

```python
def state_transition(
    state: BeaconState, signed_block: SignedBeaconBlock, validate_result: bool = True
) -> None:
    block = signed_block.message
    # [Modified in PQ:EIP8453]
    # Process slots (including those with no blocks) since block
    if state.slot < block.slot:
        process_slots(state, block.slot)
    # Verify signature
    if validate_result:
        assert verify_block_signature(state, signed_block)
    # Process block
    process_block(state, block)
    # Verify state root
    if validate_result:
        assert block.state_root == hash_tree_root(state)
```

### Modified `verify_block_signature`

```python
def verify_block_signature(state: BeaconState, signed_block: SignedBeaconBlock) -> bool:
    proposer = state.validators[signed_block.message.proposer_index]
    signing_root = compute_signing_root(
        signed_block.message, get_domain(state, DOMAIN_BEACON_PROPOSER)
    )
    # [Modified in PQ]
    leaf_index = compute_xmss_leaf_index(signed_block.message.slot, LEAF_OFFSET_BEACON_PROPOSER)
    return xmss_verify(proposer.pubkey, leaf_index, signing_root, signed_block.signature)
```

### Modified `process_slots`

*Note*: At an epoch boundary, the round is processed before the epoch.

```python
def process_slots(state: BeaconState, slot: Slot) -> None:
    assert state.slot < slot
    while state.slot < slot:
        process_slot(state)
        # [New in PQ:EIP8453]
        # Process round on the start slot of the next round
        if (state.slot + 1) % SLOTS_PER_ROUND == 0:
            process_round(state)
        # Process epoch on the start slot of the next epoch
        if (state.slot + 1) % SLOTS_PER_EPOCH == 0:
            process_epoch(state)
        state.slot = state.slot + 1
```

### Modified `process_slot`

*Note*: The block that moves the chain to a new height is the target of that
height, and a post-state cannot contain the root of its own block. So
`advance_height` leaves the root of `target_checkpoint` empty, and the next
`process_slot` fills it in, as it does for the state root of
`latest_block_header`.

```python
def process_slot(state: BeaconState) -> None:
    slot_index = state.slot % SLOTS_PER_HISTORICAL_ROOT
    # Cache state root
    previous_state_root = hash_tree_root(state)
    state.state_roots[slot_index] = previous_state_root
    # Cache latest block header state root
    if state.latest_block_header.state_root == Bytes32():
        state.latest_block_header.state_root = previous_state_root
    # Cache block root
    previous_block_root = hash_tree_root(state.latest_block_header)
    state.block_roots[slot_index] = previous_block_root
    # [New in PQ:EIP8453]
    # Cache target checkpoint root
    if state.target_checkpoint.root == Root():
        state.target_checkpoint.root = previous_block_root
    # Unset the next payload availability
    next_slot_index = (state.slot + 1) % SLOTS_PER_HISTORICAL_ROOT
    state.execution_payload_availability[next_slot_index] = Boolean(False)
```

### Round processing

#### New `process_round`

```python
def process_round(state: BeaconState) -> None:
    process_inactivity_updates(state)
    process_rewards(state)
    process_participation_flag_updates(state)
```

#### Modified `process_inactivity_updates`

*Note*: The function `process_inactivity_updates` is rewritten to use a virtual
penalty system. Inactivity scores are updated in every round, not only during an
inactivity leak.

```python
def process_inactivity_updates(state: BeaconState) -> None:
    participating_indices = get_unslashed_participating_indices(state, PROGRESS_FLAG_INDEX)
    for index in get_active_validator_indices(state, get_current_epoch(state)):
        if index in participating_indices:
            state.inactivity_scores[index] = saturating_sub(
                state.inactivity_scores[index], INACTIVITY_SCORE_RECOVERY_RATE
            )
        else:
            state.inactivity_scores[index] += INACTIVITY_SCORE_BIAS
            if state.inactivity_scores[index] >= EJECTION_INACTIVITY_SCORE:
                initiate_validator_exit(state, index)
```

*Note*: A validator gains `INACTIVITY_SCORE_BIAS` points for each round it is
offline, and its weight falls with the square of its score. The table below
shows the weight of a validator that was fully active and then stays offline.
Weights are shown as a percentage of full weight. Inactivity does not reduce a
validator's balance. When the weight reaches zero, the validator is force-exited
and keeps its stake.

| Rounds offline | Inactivity score | Voting weight |
| -------------: | ---------------: | ------------: |
|              0 |                0 |       100.00% |
|          1,024 |            4,096 |        99.61% |
|          2,048 |            8,192 |        98.44% |
|          3,072 |           12,288 |        96.48% |
|          4,096 |           16,384 |        93.75% |
|          5,120 |           20,480 |        90.23% |
|          6,144 |           24,576 |        85.94% |
|          7,168 |           28,672 |        80.86% |
|          8,192 |           32,768 |        75.00% |
|          9,216 |           36,864 |        68.36% |
|         10,240 |           40,960 |        60.94% |
|         11,264 |           45,056 |        52.73% |
|         12,288 |           49,152 |        43.75% |
|         13,312 |           53,248 |        33.98% |
|         14,336 |           57,344 |        23.44% |
|         15,360 |           61,440 |        12.11% |
|         16,384 |           65,536 |         0.00% |

#### New `process_rewards`

*Note*: This replaces `process_rewards_and_penalties`, since inactivity is no
longer penalized.

```python
def process_rewards(state: BeaconState) -> None:
    for flag_index in range(len(PARTICIPATION_FLAG_WEIGHTS_PQ)):
        rewards = get_flag_index_rewards(state, flag_index)
        for index in range(len(state.validators)):
            increase_balance(state, ValidatorIndex(index), rewards[index])
```

#### Modified `process_participation_flag_updates`

*Note*: A validator sends at most one target vote per height and names each
entry at most once, so it cannot vote again while a height lasts across rounds.
Progress already made at the current height therefore carries into the new
round.

```python
def process_participation_flag_updates(state: BeaconState) -> None:
    # [Modified in PQ:EIP8453]
    state.round_participation = RoundParticipation(
        data=[ParticipationFlags(0b0000_0000)] * len(state.validators)
    )
    # [New in PQ:EIP8453]
    for index in range(len(state.validators)):
        if state.progress_participation[index]:
            add_participation_flag(state, ValidatorIndex(index), PROGRESS_FLAG_INDEX)
```

### Epoch processing

#### Modified `process_epoch`

*Note*: Inactivity updates, rewards, and participation flag updates run in
`process_round` instead.

```python
def process_epoch(state: BeaconState) -> None:
    # [Modified in PQ:EIP8453]
    # Removed `process_justification_and_finalization`
    # [Modified in PQ:EIP8453]
    # Removed `process_inactivity_updates`
    # [Modified in PQ:EIP8453]
    # Removed `process_rewards_and_penalties`
    process_registry_updates(state)
    process_slashings(state)
    process_eth1_data_reset(state)
    process_pending_deposits(state)
    process_pending_consolidations(state)
    process_builder_pending_payments(state)
    process_effective_balance_updates(state)
    process_slashings_reset(state)
    process_randao_mixes_reset(state)
    process_historical_summaries_update(state)
    # [Modified in PQ:EIP8453]
    # Removed `process_participation_flag_updates`
    # [Modified in PQ]
    # Removed `process_sync_committee_updates`
    process_proposer_lookahead(state)
    process_ptc_window(state)
    # [New in PQ:EIP8453]
    process_ac_snapshot_updates(state)
    # [New in PQ:EIP8205]
    process_preregistration_expiry(state)
```

#### Modified `process_builder_pending_payments`

*Note*: The function `process_builder_pending_payments` is rewritten to weigh
payments by the head votes recorded in `head_vote_participation`.

```python
def process_builder_pending_payments(state: BeaconState) -> None:
    """
    Processes the builder pending payments from the previous epoch.
    """
    for index in range(SLOTS_PER_EPOCH):
        payment = state.builder_pending_payments[index]
        if payment.withdrawal.amount == 0:
            continue
        if has_builder_payment_quorum(state.head_vote_participation[index]):
            state.builder_pending_withdrawals.append(payment.withdrawal)

    old_payments = state.builder_pending_payments[SLOTS_PER_EPOCH:]
    state.builder_pending_payments[:SLOTS_PER_EPOCH] = old_payments
    new_payments = [BuilderPendingPayment.empty() for _ in range(SLOTS_PER_EPOCH)]
    state.builder_pending_payments[SLOTS_PER_EPOCH:] = new_payments

    old_participation = state.head_vote_participation[SLOTS_PER_EPOCH:]
    state.head_vote_participation[:SLOTS_PER_EPOCH] = old_participation
    new_participation = [HeadVotePaymentVoters() for _ in range(SLOTS_PER_EPOCH)]
    state.head_vote_participation[SLOTS_PER_EPOCH:] = new_participation
```

#### New `get_ac_weights`

```python
def get_ac_weights(state: BeaconState, epoch: Epoch) -> ACWeights:
    return ACWeights(
        data=[
            Uint16(v.effective_balance // EFFECTIVE_BALANCE_INCREMENT)
            if is_active_validator(v, epoch) and not v.slashed
            else Uint16(0)
            for v in state.validators
        ]
    )
```

#### New `process_ac_snapshot_updates`

Seal at the end of the first full epoch after capture, using that epoch's
completed RANDAO mix. A slashing before capture can change which weights are
recorded. In the last slot of the capture epoch, the block's RANDAO reveal runs
before capture, so that epoch's completed mix may already be known when the
weights are fixed.

```python
def process_ac_snapshot_updates(state: BeaconState) -> None:
    if state.dynasty % HEAD_VOTE_COMMITTEE_SIZE == 0:
        return
    epoch = get_current_epoch(state)
    snapshot_number = state.dynasty // HEAD_VOTE_COMMITTEE_SIZE + 2
    snapshot = state.ac_snapshots[snapshot_number % len(state.ac_snapshots)]
    if epoch > GENESIS_EPOCH and epoch - 1 == snapshot.capture_epoch:
        snapshot.seed = get_randao_mix(state, epoch)
```

#### New `process_preregistration_expiry`

*Note*: The sweep is garbage collection only. Bindings are enforced through
`is_active_validator_preregistration` and `is_active_builder_preregistration`,
so the timing of the sweep has no effect on whether a binding is enforced or a
request is admitted.

```python
def process_preregistration_expiry(state: BeaconState) -> None:
    state.validator_preregistrations = ValidatorPreregistrations(
        data=[
            preregistration
            for preregistration in state.validator_preregistrations
            if is_active_validator_preregistration(state, preregistration)
        ]
    )
    state.builder_preregistrations = BuilderPreregistrations(
        data=[
            preregistration
            for preregistration in state.builder_preregistrations
            if is_active_builder_preregistration(state, preregistration)
        ]
    )
```

#### Modified `apply_pending_deposit`

*Note*: Deposits carry no signature, so a deposit for a new validator is not
verified. The validator of a legacy deposit is exited at once without consuming
exit churn, since it was never active, and becomes withdrawable after
`MIN_VALIDATOR_WITHDRAWABILITY_DELAY` epochs, as after any exit.

```python
def apply_pending_deposit(state: BeaconState, deposit: PendingDeposit) -> None:
    """
    Applies ``deposit`` to the ``state``.
    """
    # [Modified in PQ]
    pubkey = compute_deposit_pubkey(deposit.pubkey)
    validator_pubkeys = [validator.pubkey for validator in state.validators]
    if pubkey not in validator_pubkeys:
        # [New in PQ]
        index = get_index_for_new_validator(state)
        add_validator_to_registry(
            state,
            pubkey,
            # [New in PQ]
            compute_deposit_vrf_root(deposit),
            deposit.withdrawal_credentials,
            deposit.amount,
        )
        # [New in PQ]
        if is_legacy_pubkey(deposit.pubkey):
            epoch = get_current_epoch(state)
            validator = state.validators[index]
            validator.exit_epoch = epoch
            validator.withdrawable_epoch = epoch + MIN_VALIDATOR_WITHDRAWABILITY_DELAY
    else:
        validator_index = ValidatorIndex(validator_pubkeys.index(pubkey))
        increase_balance(state, validator_index, deposit.amount)
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
        # [Modified in PQ:EIP8453]
        # Check if deposit has been finalized, otherwise, stop processing.
        if deposit.slot > state.finalized_slot:
            break

        # Check if number of processed deposits has not reached the limit, otherwise, stop processing.
        if next_deposit_index >= MAX_PENDING_DEPOSITS_PER_EPOCH:
            break

        # Read validator state
        is_validator_exited = False
        is_validator_withdrawn = False
        # [Modified in PQ]
        pubkey = compute_deposit_pubkey(deposit.pubkey)
        validator_pubkeys = [validator.pubkey for validator in state.validators]
        if pubkey in validator_pubkeys:
            validator = state.validators[ValidatorIndex(validator_pubkeys.index(pubkey))]
            is_validator_exited = validator.exit_epoch < FAR_FUTURE_EPOCH
            is_validator_withdrawn = validator.withdrawable_epoch < next_epoch

        # [Modified in PQ]
        if is_validator_withdrawn or is_legacy_pubkey(deposit.pubkey):
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

### Block processing

#### Modified `process_block`

*Note*: Without sync aggregates, the sync committee rewards are no longer
issued, which lowers issuance by `SYNC_REWARD_WEIGHT / WEIGHT_DENOMINATOR`. The
height events of a block are processed once, after all of its attestations.

```python
def process_block(state: BeaconState, block: BeaconBlock) -> None:
    process_parent_execution_payload(state, block)
    process_block_header(state, block)
    process_withdrawals(state)
    process_execution_payload_bid(state, block.body.signed_execution_payload_bid)
    process_randao(state, block.body)
    process_eth1_data(state, block.body)
    # [Modified in PQ:EIP8453]
    process_operations(state, block.body)
    # [Modified in PQ]
    # Removed `process_sync_aggregate`
    # [New in PQ:EIP8453]
    height = state.target_checkpoint.height
    process_height_events(state)
    if state.target_checkpoint.height > height:
        # Dynasties are monotone along the chain, so finalizing a block at or
        # after the current dynasty's start slot finalizes a block of that dynasty.
        if (
            state.finalized_checkpoint.height > 0
            and state.finalized_slot >= state.dynasty_start_slot
        ):
            advance_dynasty(state)
            if state.dynasty % HEAD_VOTE_COMMITTEE_SIZE == 1:
                update_ac_snapshots(state)
```

#### Modified `process_randao`

*Note*: The reveal is the proposer's VRF proof for the slot, and the secret it
reveals is mixed in. The proposer committed to its secrets when it registered
its VRF root, so it cannot grind the reveal and can only withhold its block, as
with BLS.

```python
def process_randao(state: BeaconState, body: BeaconBlockBody) -> None:
    epoch = get_current_epoch(state)
    # [Modified in PQ]
    # Verify RANDAO reveal
    assert is_valid_vrf_proof(
        state,
        get_beacon_proposer_index(state),
        state.slot,
        body.randao_reveal,
    )
    # [Modified in PQ]
    # Mix in RANDAO reveal
    prev_randao = get_randao_mix(state, epoch)
    mix = sha256(prev_randao + body.randao_reveal[0] + DOMAIN_RANDAO)
    state.randao_mixes[epoch % EPOCHS_PER_HISTORICAL_VECTOR] = mix
```

#### Execution payload

##### Modified `get_execution_requests_list`

*Note*: Encodes execution requests as defined by
[EIP-7685](https://eips.ethereum.org/EIPS/eip-7685).

```python
def get_execution_requests_list(execution_requests: ExecutionRequests) -> Sequence[bytes]:
    requests: Sequence[tuple[Bytes1, ProgressiveList]] = [
        (DEPOSIT_REQUEST_TYPE, execution_requests.deposits),
        (WITHDRAWAL_REQUEST_TYPE, execution_requests.withdrawals),
        (CONSOLIDATION_REQUEST_TYPE, execution_requests.consolidations),
        (BUILDER_DEPOSIT_REQUEST_TYPE, execution_requests.builder_deposits),
        (BUILDER_EXIT_REQUEST_TYPE, execution_requests.builder_exits),
        # [Modified in PQ]
        # Removed `VALIDATOR_PQ_REGISTRATION_REQUEST_TYPE`
        # [Modified in PQ]
        # Removed `BUILDER_PQ_REGISTRATION_REQUEST_TYPE`
        # [New in PQ:EIP8205]
        (VALIDATOR_PREREGISTRATION_REQUEST_TYPE, execution_requests.validator_preregistrations),
        # [New in PQ:EIP8205]
        (BUILDER_PREREGISTRATION_REQUEST_TYPE, execution_requests.builder_preregistrations),
        # [New in PQ]
        (VOLUNTARY_EXIT_REQUEST_TYPE, execution_requests.voluntary_exits),
    ]

    return [
        request_type + ssz_serialize(request_data)
        for request_type, request_data in requests
        if len(request_data) != 0
    ]
```

##### Modified `verify_execution_payload_envelope_signature`

```python
def verify_execution_payload_envelope_signature(
    state: BeaconState,
    signed_envelope: SignedExecutionPayloadEnvelope,
) -> bool:
    builder_index = signed_envelope.message.builder_index
    if builder_index == BUILDER_INDEX_SELF_BUILD:
        validator_index = state.latest_block_header.proposer_index
        pubkey = state.validators[validator_index].pubkey
    else:
        pubkey = state.builders[builder_index].pubkey

    signing_root = compute_signing_root(
        signed_envelope.message, get_domain(state, DOMAIN_BEACON_BUILDER)
    )
    # [Modified in PQ]
    leaf_index = compute_xmss_leaf_index(
        state.latest_block_header.slot, LEAF_OFFSET_EXECUTION_PAYLOAD_ENVELOPE
    )
    return xmss_verify(pubkey, leaf_index, signing_root, signed_envelope.signature)
```

#### Execution payload bid

##### Modified `verify_execution_payload_bid_signature`

```python
def verify_execution_payload_bid_signature(
    state: BeaconState,
    signed_bid: SignedExecutionPayloadBid,
) -> bool:
    builder = state.builders[signed_bid.message.builder_index]
    signing_root = compute_signing_root(
        signed_bid.message, get_domain(state, DOMAIN_BEACON_BUILDER)
    )
    # [Modified in PQ]
    leaf_index = xmss_get_leaf_index(signed_bid.signature)
    if not is_builder_bid_leaf_index(leaf_index):
        return False
    return xmss_verify(builder.pubkey, leaf_index, signing_root, signed_bid.signature)
```

##### Modified `process_execution_payload_bid`

```python
def process_execution_payload_bid(
    state: BeaconState,
    signed_bid: SignedExecutionPayloadBid,
) -> None:
    bid = signed_bid.message
    builder_index = bid.builder_index
    amount = bid.value

    # For self-builds, amount must be zero regardless of withdrawal credential prefix
    if builder_index == BUILDER_INDEX_SELF_BUILD:
        assert amount == 0
        # [Modified in PQ]
        assert signed_bid.signature == XMSSSignature()
    else:
        # Verify that the builder is active
        assert is_active_builder(state, builder_index)
        # Verify that the builder is a payload builder
        assert state.builders[builder_index].version == PAYLOAD_BUILDER_VERSION
        # Verify that the builder has funds to cover the bid
        assert can_builder_cover_bid(state, builder_index, amount)
        # Verify that the bid signature is valid
        assert verify_execution_payload_bid_signature(state, signed_bid)

    # Verify commitments are under limit
    assert (
        len(bid.blob_kzg_commitments)
        <= get_blob_parameters(get_current_epoch(state)).max_blobs_per_block
    )

    # Verify that the bid is for the current slot
    assert bid.slot == state.slot
    assert state.slot > GENESIS_SLOT
    # Verify that the bid is for the right parent block
    assert bid.parent_block_hash == state.latest_block_hash
    # Verify that the bid's block hash differs from its parent block hash
    assert bid.block_hash != bid.parent_block_hash
    assert bid.parent_block_root == get_block_root_at_slot(state, state.slot - 1)
    assert bid.prev_randao == get_randao_mix(state, get_current_epoch(state))

    # Record the pending payment if there is some payment
    if amount > 0:
        pending_payment = BuilderPendingPayment(
            weight=Gwei(0),
            withdrawal=BuilderPendingWithdrawal(
                fee_recipient=bid.fee_recipient,
                amount=amount,
                builder_index=builder_index,
            ),
            proposer_index=get_beacon_proposer_index(state),
        )
        state.builder_pending_payments[SLOTS_PER_EPOCH + bid.slot % SLOTS_PER_EPOCH] = (
            pending_payment
        )

    # Cache the signed execution payload bid
    state.latest_execution_payload_bid = bid
```

#### Operations

##### Modified `process_operations`

```python
def process_operations(
    state: BeaconState,
    body: BeaconBlockBody,
    # [Modified in PQ:EIP8453]
    # Removed `parent_slot`
) -> None:
    assert len(body.deposits) == 0

    def for_ops(operations: Sequence[Any], fn: Callable[..., None], *args: Any) -> None:
        for operation in operations:
            fn(state, operation, *args)

    assert len(body.proposer_slashings) <= MAX_PROPOSER_SLASHINGS
    assert len(body.attester_slashings) <= MAX_ATTESTER_SLASHINGS_ELECTRA
    # [Modified in PQ]
    assert len(body.attestations) <= MAX_ATTESTATIONS_PQ
    # [Modified in PQ]
    # Removed the voluntary exit limit
    # [Modified in PQ]
    # Removed the BLS to execution change limit
    # [Modified in PQ]
    # Removed the payload attestation limit
    # [New in PQ:EIP8453]
    assert len(body.head_votes) <= MAX_HEAD_VOTES
    assert sum(len(vote.credentials) for vote in body.head_votes) <= 2 * HEAD_VOTE_COMMITTEE_SIZE
    # [New in PQ:EIP8453]
    assert is_valid_head_vote_declarations(body, state.slot)

    for_ops(body.proposer_slashings, process_proposer_slashing)
    for_ops(body.attester_slashings, process_attester_slashing)
    # [Modified in PQ:EIP8453]
    for_ops(body.attestations, process_attestation)
    # [Modified in PQ]
    # Removed `process_voluntary_exit`
    # [Modified in PQ]
    # Removed `process_bls_to_execution_change`
    # [Modified in PQ]
    # Removed `process_payload_attestation`
    # [New in PQ:EIP8453]
    for_ops(body.head_votes, process_head_vote)
    # [New in PQ]
    process_stark(state, body)
```

##### New `process_stark`

*Note*: The block's `proof` proves the XMSS statements of its attestations,
followed by those of its head votes. Head vote VRF openings are verified in
`process_head_vote`; aggregating them requires LeanVM support for the Keccak-256
opening statement.

```python
def process_stark(state: BeaconState, body: BeaconBlockBody) -> None:
    statements = []
    for attestation in body.attestations:
        statements.extend(get_attestation_statements(state, attestation))
    for vote in body.head_votes:
        statements.append(get_head_vote_statement(state, vote))
    assert stark_verify_aggregates(statements, body.proof)
```

##### Modified `process_proposer_slashing`

*Note*: Both headers are signed at the same leaf, which exposes that leaf of the
proposer's key. The leaf belongs to a past slot and the proposer is slashed.

```python
def process_proposer_slashing(state: BeaconState, proposer_slashing: ProposerSlashing) -> None:
    header_1 = proposer_slashing.signed_header_1.message
    header_2 = proposer_slashing.signed_header_2.message

    # Verify header slots match
    assert header_1.slot == header_2.slot
    # Verify header proposer indices match
    assert header_1.proposer_index == header_2.proposer_index
    # Verify the headers are different
    assert header_1 != header_2
    # Verify the proposer is slashable
    proposer = state.validators[header_1.proposer_index]
    assert is_slashable_validator(proposer, get_current_epoch(state))
    # Verify signatures
    for signed_header in (proposer_slashing.signed_header_1, proposer_slashing.signed_header_2):
        domain = get_domain(
            state, DOMAIN_BEACON_PROPOSER, compute_epoch_at_slot(signed_header.message.slot)
        )
        signing_root = compute_signing_root(signed_header.message, domain)
        # [Modified in PQ]
        leaf_index = compute_xmss_leaf_index(
            signed_header.message.slot, LEAF_OFFSET_BEACON_PROPOSER
        )
        assert xmss_verify(proposer.pubkey, leaf_index, signing_root, signed_header.signature)

    slash_validator(state, header_1.proposer_index)
```

##### Attestations

###### Modified `process_attestation`

*Note*: The function `process_attestation` is rewritten for the finality gadget.
The progress flag is credited the first time a validator's progress is recorded
at the height, and the finality flag whenever a finality pair counts for a
pending justification and the validator does not yet have it in the round. Both
count toward the round in which the attestation is included. Only attestations
for the current or the previous target are included, and only signers that are
active are counted. An attestation for the previous target counts only toward
the participation of the pending justification its finality pair names, and
credits no flag or reward. An attestation carries no signature, so
`process_stark` verifies the signatures of all attestations in the block
instead. Its `round` only selects the XMSS leaf of those signatures, which
cannot be of a future round.

```python
def process_attestation(state: BeaconState, attestation: Attestation) -> None:
    data = attestation.data

    assert is_well_formed_attestation_data(data)
    assert is_valid_attestation_data(state, data)
    # [New in PQ]
    # The XMSS leaf is not of a future round
    assert attestation.round <= get_current_round(state)
    assert is_valid_aggregation_bits(state, get_attestation_epoch(state, data), attestation)

    proposer_reward_numerator = 0
    for index in get_attesting_indices(state, attestation):
        # Signers that are not active are verified but not counted
        if not is_active_validator(state.validators[index], get_current_epoch(state)):
            continue
        # A vote for the previous target counts only for a pending
        # justification, without flags or rewards. It writes the participation
        # unconditionally because it carries no reward; a reward for it would
        # need its own once-only check
        if is_previous_target_attestation_data(state, data):
            for pending in state.pending_finality:
                if pending.checkpoint == data.finality:
                    pending.participation[index] = Boolean(True)
            continue
        base_reward = get_round_base_reward(state, index)
        for pending in state.pending_finality:
            if pending.checkpoint == data.finality:
                pending.participation[index] = Boolean(True)
                # The flag does not depend on whether a vote for the previous
                # target already counted the pair
                if not has_flag(state.round_participation[index], FINALITY_FLAG_INDEX):
                    add_participation_flag(state, index, FINALITY_FLAG_INDEX)
                    proposer_reward_numerator += base_reward * FINALITY_WEIGHT
        if not state.progress_participation[index]:
            state.progress_participation[index] = Boolean(True)
            add_participation_flag(state, index, PROGRESS_FLAG_INDEX)
            proposer_reward_numerator += base_reward * PROGRESS_WEIGHT
        if not data.timeout:
            state.target_participation[index] = Boolean(True)

    reward_divisor = (WEIGHT_DENOMINATOR - PROPOSER_WEIGHT) * WEIGHT_DENOMINATOR // PROPOSER_WEIGHT
    proposer_reward = Gwei(proposer_reward_numerator // reward_divisor)
    increase_balance(state, get_beacon_proposer_index(state), proposer_reward)
```

##### Head votes

###### New `process_head_vote`

*Note*: The beacon state credits a distinct voter for the canonical block of the
duty slot until the payment reaches its target. The epoch window matches the two
epochs of payment participation kept in state. A vote must also belong to the
current or previous dynasty of the including block's entering state. Operations
run before dynasty advancement, so an entry block may include a duty from the
dynasty it makes ineligible for subsequent blocks. With a dynasty advance every
two slots, this gives votes three or four slots for inclusion, depending on the
duty slot. `process_stark` verifies the XMSS signatures; this operation checks
the raw VRF Merkle openings. Every eligible voter can count once toward payment
regardless of which seat indices they hold.

```python
def process_head_vote(state: BeaconState, vote: HeadVote) -> None:
    data = vote.data
    assert data.slot + MIN_ATTESTATION_INCLUSION_DELAY <= state.slot
    assert data.slot >= state.previous_dynasty_start_slot
    assert compute_epoch_at_slot(data.slot) in (get_previous_epoch(state), get_current_epoch(state))
    assert is_head_vote_payload_status_valid(state, data)

    indices = [credential.validator_index for credential in vote.credentials]
    assert len(indices) > 0
    assert indices == sorted(set(indices))
    for credential in vote.credentials:
        assert (
            get_head_vote_weight(state, data.slot, credential.validator_index, credential.proof) > 0
        )

    if is_head_vote_same_slot(state, data):
        if compute_epoch_at_slot(data.slot) == get_current_epoch(state):
            participation_index = SLOTS_PER_EPOCH + data.slot % SLOTS_PER_EPOCH
        else:
            participation_index = data.slot % SLOTS_PER_EPOCH
        participation = state.head_vote_participation[participation_index]
        for index in indices:
            if has_builder_payment_quorum(participation):
                break
            if index not in participation:
                participation.append(index)
```

##### Deposit requests

###### Modified `process_deposit_request`

```python
def process_deposit_request(state: BeaconState, deposit_request: DepositRequest) -> None:
    # [New in PQ:EIP8205]
    pubkey = compute_deposit_pubkey(deposit_request.pubkey)
    preregistration = get_active_validator_preregistration(state, pubkey)
    if preregistration is not None:
        if deposit_request.withdrawal_credentials != preregistration.withdrawal_credentials:
            return
        if Root(deposit_request.signature[:32]) != preregistration.vrf_root:
            return
        remove_validator_preregistration(state, pubkey)

    state.pending_deposits.append(
        PendingDeposit(
            pubkey=deposit_request.pubkey,
            withdrawal_credentials=deposit_request.withdrawal_credentials,
            amount=deposit_request.amount,
            signature=deposit_request.signature,
            slot=state.slot,
        )
    )
```

###### Modified `get_validator_from_deposit`

```python
def get_validator_from_deposit(
    # [Modified in PQ]
    pubkey: XMSSPubkey,
    # [New in PQ]
    vrf_root: Root,
    withdrawal_credentials: Bytes32,
    amount: Gwei,
) -> Validator:
    validator = Validator(
        pubkey=pubkey,
        # [New in PQ]
        vrf_root=vrf_root,
        withdrawal_credentials=withdrawal_credentials,
        effective_balance=Gwei(0),
        slashed=Boolean(False),
        activation_eligibility_epoch=FAR_FUTURE_EPOCH,
        activation_epoch=FAR_FUTURE_EPOCH,
        exit_epoch=FAR_FUTURE_EPOCH,
        withdrawable_epoch=FAR_FUTURE_EPOCH,
    )

    max_effective_balance = get_max_effective_balance(validator)
    validator.effective_balance = min(
        amount - amount % EFFECTIVE_BALANCE_INCREMENT, max_effective_balance
    )

    return validator
```

###### Modified `add_validator_to_registry`

```python
def add_validator_to_registry(
    state: BeaconState,
    # [Modified in PQ]
    pubkey: XMSSPubkey,
    # [New in PQ]
    vrf_root: Root,
    withdrawal_credentials: Bytes32,
    amount: Gwei,
) -> None:
    index = get_index_for_new_validator(state)
    # [Modified in PQ]
    validator = get_validator_from_deposit(pubkey, vrf_root, withdrawal_credentials, amount)
    set_or_append_list(state.validators, index, validator)
    set_or_append_list(state.balances, index, amount)
    set_or_append_list(state.inactivity_scores, index, Uint64(0))
    # [New in PQ:EIP8453]
    set_or_append_list(state.round_participation, index, ParticipationFlags(0b0000_0000))
    # [New in PQ:EIP8453]
    set_or_append_list(state.target_participation, index, Boolean(False))
    # [New in PQ:EIP8453]
    set_or_append_list(state.progress_participation, index, Boolean(False))
    # [New in PQ:EIP8453]
    for pending in state.pending_finality:
        set_or_append_list(pending.participation, index, Boolean(False))
```

##### Builder deposit requests

###### Modified `add_builder_to_registry`

```python
def add_builder_to_registry(
    state: BeaconState,
    # [Modified in PQ]
    pubkey: XMSSPubkey,
    version: Uint8,
    execution_address: ExecutionAddress,
    amount: Gwei,
    slot: Slot,
) -> None:
    set_or_append_list(
        state.builders,
        get_index_for_new_builder(state),
        Builder(
            pubkey=pubkey,
            version=version,
            execution_address=execution_address,
            balance=amount,
            deposit_epoch=compute_epoch_at_slot(slot),
            withdrawable_epoch=FAR_FUTURE_EPOCH,
        ),
    )
```

###### Modified `process_builder_deposit_request`

*Note*: Builder deposits carry no signature, so a deposit for a new builder is
not verified. A builder has no VRF root, so `request.signature` is ignored. The
builder of a legacy deposit initiates its exit at once, so the builder sweep
refunds its balance.

```python
def process_builder_deposit_request(state: BeaconState, request: BuilderDepositRequest) -> None:
    # Ignore deposits with unexpected withdrawal credential prefixes
    if not is_builder_withdrawal_credential(request.withdrawal_credentials):
        return

    # [Modified in PQ]
    pubkey = compute_deposit_pubkey(request.pubkey)
    # [New in PQ:EIP8205]
    preregistration = get_active_builder_preregistration(state, pubkey)
    if preregistration is not None:
        if request.withdrawal_credentials != preregistration.withdrawal_credentials:
            return
        remove_builder_preregistration(state, pubkey)

    builder_pubkeys = [builder.pubkey for builder in state.builders]
    if pubkey not in builder_pubkeys:
        # [New in PQ]
        builder_index = get_index_for_new_builder(state)
        add_builder_to_registry(
            state,
            pubkey,
            PAYLOAD_BUILDER_VERSION,
            ExecutionAddress(request.withdrawal_credentials[12:]),
            request.amount,
            state.slot,
        )
        # [New in PQ]
        if is_legacy_pubkey(request.pubkey):
            initiate_builder_exit(state, builder_index)
    else:
        builder_index = BuilderIndex(builder_pubkeys.index(pubkey))
        builder = state.builders[builder_index]

        # If exited and swept, reset the withdrawable epoch
        if builder.withdrawable_epoch != FAR_FUTURE_EPOCH and builder.balance == 0:
            epoch = get_current_epoch(state)
            builder.withdrawable_epoch = epoch + MIN_BUILDER_WITHDRAWABILITY_DELAY

        # Increase balance by deposit amount
        builder.balance += request.amount
```

##### Builder exit requests

###### Modified `process_builder_exit_request`

```python
def process_builder_exit_request(state: BeaconState, request: BuilderExitRequest) -> None:
    # [Modified in PQ]
    pubkey = XMSSPubkey(request.pubkey[16:])
    builder_pubkeys = [builder.pubkey for builder in state.builders]
    if pubkey not in builder_pubkeys:
        return

    builder_index = BuilderIndex(builder_pubkeys.index(pubkey))
    builder = state.builders[builder_index]

    if not is_active_builder(state, builder_index):
        return
    if builder.execution_address != request.source_address:
        return
    if get_pending_balance_to_withdraw_for_builder(state, builder_index) != 0:
        return

    initiate_builder_exit(state, builder_index)
```

##### Execution-layer withdrawal requests

###### Modified `process_withdrawal_request`

```python
def process_withdrawal_request(state: BeaconState, withdrawal_request: WithdrawalRequest) -> None:
    # [New in PQ]
    # Ignore requests that name a BLS public key
    if is_legacy_pubkey(withdrawal_request.validator_pubkey):
        return

    amount = withdrawal_request.amount
    is_full_exit_request = amount == FULL_EXIT_REQUEST_AMOUNT

    # If partial withdrawal queue is full, only full exits are processed
    if (
        len(state.pending_partial_withdrawals) == PENDING_PARTIAL_WITHDRAWALS_LIMIT
        and not is_full_exit_request
    ):
        return

    validator_pubkeys = [validator.pubkey for validator in state.validators]
    # [Modified in PQ]
    # Verify pubkey exists
    request_pubkey = XMSSPubkey(withdrawal_request.validator_pubkey[16:])
    if request_pubkey not in validator_pubkeys:
        return
    index = ValidatorIndex(validator_pubkeys.index(request_pubkey))
    validator = state.validators[index]

    # Verify withdrawal credentials
    has_correct_credential = has_execution_withdrawal_credential(validator)
    is_correct_source_address = (
        validator.withdrawal_credentials[12:] == withdrawal_request.source_address
    )
    if not (has_correct_credential and is_correct_source_address):
        return
    # Verify the validator is active
    if not is_active_validator(validator, get_current_epoch(state)):
        return
    # Verify exit has not been initiated
    if validator.exit_epoch != FAR_FUTURE_EPOCH:
        return
    # Verify the validator has been active long enough
    if get_current_epoch(state) < validator.activation_epoch + SHARD_COMMITTEE_PERIOD:
        return

    pending_balance_to_withdraw = get_pending_balance_to_withdraw(state, index)

    if is_full_exit_request:
        # Only exit validator if it has no pending withdrawals in the queue
        if pending_balance_to_withdraw == 0:
            initiate_validator_exit(state, index)
        return

    has_sufficient_effective_balance = validator.effective_balance >= MIN_ACTIVATION_BALANCE
    has_excess_balance = (
        state.balances[index] > MIN_ACTIVATION_BALANCE + pending_balance_to_withdraw
    )

    # Only allow partial withdrawals with compounding withdrawal credentials
    if (
        has_compounding_withdrawal_credential(validator)
        and has_sufficient_effective_balance
        and has_excess_balance
    ):
        to_withdraw = min(
            state.balances[index] - MIN_ACTIVATION_BALANCE - pending_balance_to_withdraw, amount
        )
        exit_queue_epoch = compute_exit_epoch_and_update_churn(state, to_withdraw)
        withdrawable_epoch = exit_queue_epoch + MIN_VALIDATOR_WITHDRAWABILITY_DELAY
        state.pending_partial_withdrawals.append(
            PendingPartialWithdrawal(
                validator_index=index,
                amount=to_withdraw,
                withdrawable_epoch=withdrawable_epoch,
            )
        )
```

##### Execution-layer consolidation requests

###### Modified `is_valid_switch_to_compounding_request`

```python
def is_valid_switch_to_compounding_request(
    state: BeaconState,
    consolidation_request: ConsolidationRequest,
) -> bool:
    # Switch to compounding requires source and target be equal
    if consolidation_request.source_pubkey != consolidation_request.target_pubkey:
        return False

    # [Modified in PQ]
    # Verify pubkey exists
    source_pubkey = XMSSPubkey(consolidation_request.source_pubkey[16:])
    validator_pubkeys = [validator.pubkey for validator in state.validators]
    if source_pubkey not in validator_pubkeys:
        return False

    source_validator = state.validators[ValidatorIndex(validator_pubkeys.index(source_pubkey))]

    # Verify request has been authorized
    if source_validator.withdrawal_credentials[12:] != consolidation_request.source_address:
        return False

    # Verify source withdrawal credentials
    if not has_eth1_withdrawal_credential(source_validator):
        return False

    # Verify the source is active
    current_epoch = get_current_epoch(state)
    if not is_active_validator(source_validator, current_epoch):
        return False

    # Verify exit for source has not been initiated
    if source_validator.exit_epoch != FAR_FUTURE_EPOCH:
        return False

    return True
```

###### Modified `process_consolidation_request`

```python
def process_consolidation_request(
    state: BeaconState,
    consolidation_request: ConsolidationRequest,
) -> None:
    # [New in PQ]
    # Ignore requests that name a BLS public key
    if is_legacy_pubkey(consolidation_request.source_pubkey):
        return
    if is_legacy_pubkey(consolidation_request.target_pubkey):
        return

    if is_valid_switch_to_compounding_request(state, consolidation_request):
        validator_pubkeys = [validator.pubkey for validator in state.validators]
        # [Modified in PQ]
        request_source_pubkey = XMSSPubkey(consolidation_request.source_pubkey[16:])
        source_index = ValidatorIndex(validator_pubkeys.index(request_source_pubkey))
        switch_to_compounding_validator(state, source_index)
        return

    # Verify that source != target, so a consolidation cannot be used as an exit
    if consolidation_request.source_pubkey == consolidation_request.target_pubkey:
        return
    # If the pending consolidations queue is full, consolidation requests are ignored
    if len(state.pending_consolidations) == PENDING_CONSOLIDATIONS_LIMIT:
        return
    # If there is too little available consolidation churn limit, consolidation requests are ignored
    if get_consolidation_churn_limit(state) <= MIN_ACTIVATION_BALANCE:
        return

    validator_pubkeys = [validator.pubkey for validator in state.validators]
    # [Modified in PQ]
    # Verify pubkeys exists
    request_source_pubkey = XMSSPubkey(consolidation_request.source_pubkey[16:])
    request_target_pubkey = XMSSPubkey(consolidation_request.target_pubkey[16:])
    if request_source_pubkey not in validator_pubkeys:
        return
    if request_target_pubkey not in validator_pubkeys:
        return
    source_index = ValidatorIndex(validator_pubkeys.index(request_source_pubkey))
    target_index = ValidatorIndex(validator_pubkeys.index(request_target_pubkey))
    source_validator = state.validators[source_index]
    target_validator = state.validators[target_index]

    # Verify source withdrawal credentials
    has_correct_credential = has_execution_withdrawal_credential(source_validator)
    is_correct_source_address = (
        source_validator.withdrawal_credentials[12:] == consolidation_request.source_address
    )
    if not (has_correct_credential and is_correct_source_address):
        return

    # Verify that target has compounding withdrawal credentials
    if not has_compounding_withdrawal_credential(target_validator):
        return

    # Verify the source and the target are active
    current_epoch = get_current_epoch(state)
    if not is_active_validator(source_validator, current_epoch):
        return
    if not is_active_validator(target_validator, current_epoch):
        return
    # Verify exits for source and target have not been initiated
    if source_validator.exit_epoch != FAR_FUTURE_EPOCH:
        return
    if target_validator.exit_epoch != FAR_FUTURE_EPOCH:
        return
    # Verify the source has been active long enough
    if current_epoch < source_validator.activation_epoch + SHARD_COMMITTEE_PERIOD:
        return
    # Verify the source has no pending withdrawals in the queue
    if get_pending_balance_to_withdraw(state, source_index) > 0:
        return

    # Initiate source validator exit and append pending consolidation
    source_validator.exit_epoch = compute_consolidation_epoch_and_update_churn(
        state, source_validator.effective_balance
    )
    source_validator.withdrawable_epoch = (
        source_validator.exit_epoch + MIN_VALIDATOR_WITHDRAWABILITY_DELAY
    )
    state.pending_consolidations.append(
        PendingConsolidation(source_index=source_index, target_index=target_index)
    )
```

##### Validator preregistration requests

###### New `process_validator_preregistration_request`

```python
def process_validator_preregistration_request(
    state: BeaconState,
    request: ValidatorPreregistrationRequest,
) -> None:
    pubkey = request.pubkey

    # An active binding for this pubkey makes the new request a no-op
    if get_active_validator_preregistration(state, pubkey) is not None:
        return

    # A pubkey with an existing validator cannot be preregistered
    if pubkey in [validator.pubkey for validator in state.validators]:
        return

    # A pubkey with a pending deposit cannot be preregistered
    if is_pending_validator(state.pending_deposits, pubkey):
        return

    # The capacity check counts only active records, so the timing of the
    # garbage-collection sweep does not affect admission
    active_preregistrations = [
        preregistration
        for preregistration in state.validator_preregistrations
        if is_active_validator_preregistration(state, preregistration)
    ]
    if len(active_preregistrations) >= PREREGISTRATIONS_LIMIT:
        return

    preregistration = ValidatorPreregistration(
        pubkey=pubkey,
        withdrawal_credentials=request.withdrawal_credentials,
        vrf_root=request.vrf_root,
        expiry_slot=state.slot + PREREGISTRATION_EXPIRY_SLOTS,
    )
    index = get_validator_preregistration_index(state, pubkey)
    if index is not None:
        # Replace the expired record in place
        state.validator_preregistrations[index] = preregistration
    else:
        state.validator_preregistrations.append(preregistration)
```

##### Builder preregistration requests

###### New `process_builder_preregistration_request`

```python
def process_builder_preregistration_request(
    state: BeaconState,
    request: BuilderPreregistrationRequest,
) -> None:
    pubkey = request.pubkey

    # An active binding for this pubkey makes the new request a no-op
    if get_active_builder_preregistration(state, pubkey) is not None:
        return

    # A pubkey with an existing builder cannot be preregistered
    if pubkey in [builder.pubkey for builder in state.builders]:
        return

    # The capacity check counts only active records, so the timing of the
    # garbage-collection sweep does not affect admission
    active_preregistrations = [
        preregistration
        for preregistration in state.builder_preregistrations
        if is_active_builder_preregistration(state, preregistration)
    ]
    if len(active_preregistrations) >= PREREGISTRATIONS_LIMIT:
        return

    preregistration = BuilderPreregistration(
        pubkey=pubkey,
        withdrawal_credentials=request.withdrawal_credentials,
        expiry_slot=state.slot + PREREGISTRATION_EXPIRY_SLOTS,
    )
    index = get_builder_preregistration_index(state, pubkey)
    if index is not None:
        # Replace the expired record in place
        state.builder_preregistrations[index] = preregistration
    else:
        state.builder_preregistrations.append(preregistration)
```

##### Voluntary exit requests

###### New `process_voluntary_exit_request`

```python
def process_voluntary_exit_request(state: BeaconState, request: VoluntaryExitRequest) -> None:
    validator_pubkeys = [validator.pubkey for validator in state.validators]
    if request.pubkey not in validator_pubkeys:
        return
    index = ValidatorIndex(validator_pubkeys.index(request.pubkey))
    validator = state.validators[index]

    if not is_active_validator(validator, get_current_epoch(state)):
        return
    if validator.exit_epoch != FAR_FUTURE_EPOCH:
        return
    if get_current_epoch(state) < validator.activation_epoch + SHARD_COMMITTEE_PERIOD:
        return
    if get_pending_balance_to_withdraw(state, index) != 0:
        return

    initiate_validator_exit(state, index)
```

#### Parent execution payload

##### Modified `apply_parent_execution_payload`

*Note*: This function queues the builder payment, processes the parent's
execution requests, updates payload availability, and updates the latest block
hash. It is called by `process_parent_execution_payload` during block processing
and by the validator during block production before computing withdrawals.

```python
def apply_parent_execution_payload(
    state: BeaconState,
    requests: ExecutionRequests,
) -> None:
    parent_bid = state.latest_execution_payload_bid
    parent_slot = state.latest_block_header.slot
    parent_epoch = compute_epoch_at_slot(parent_slot)

    assert len(requests.withdrawals) <= MAX_WITHDRAWAL_REQUESTS_PER_PAYLOAD
    assert len(requests.consolidations) <= MAX_CONSOLIDATION_REQUESTS_PER_PAYLOAD
    assert len(requests.builder_deposits) <= MAX_BUILDER_DEPOSIT_REQUESTS_PER_PAYLOAD
    assert len(requests.builder_exits) <= MAX_BUILDER_EXIT_REQUESTS_PER_PAYLOAD
    # [Modified in PQ]
    # Removed the validator and builder PQ registration request limits
    # [New in PQ:EIP8205]
    assert (
        len(requests.validator_preregistrations)
        <= MAX_VALIDATOR_PREREGISTRATION_REQUESTS_PER_PAYLOAD
    )
    # [New in PQ:EIP8205]
    assert (
        len(requests.builder_preregistrations) <= MAX_BUILDER_PREREGISTRATION_REQUESTS_PER_PAYLOAD
    )
    # [New in PQ]
    assert len(requests.voluntary_exits) <= MAX_VOLUNTARY_EXIT_REQUESTS_PER_PAYLOAD

    # Settle the builder payment before the requests so that a builder exit
    # request is rejected while the payment is pending
    if parent_epoch == get_current_epoch(state):
        payment_index = SLOTS_PER_EPOCH + parent_slot % SLOTS_PER_EPOCH
        settle_builder_payment(state, payment_index)
    elif parent_epoch == get_previous_epoch(state):
        payment_index = parent_slot % SLOTS_PER_EPOCH
        settle_builder_payment(state, payment_index)
    elif parent_bid.value > 0:
        # Parent is older than the previous epoch, its payment entry has been
        # evicted from builder_pending_payments. Append the withdrawal directly.
        state.builder_pending_withdrawals.append(
            BuilderPendingWithdrawal(
                fee_recipient=parent_bid.fee_recipient,
                amount=parent_bid.value,
                builder_index=parent_bid.builder_index,
            )
        )

    # Process execution requests from parent's payload. The execution
    # requests are processed at state.slot (child's slot), not the parent's slot.
    def for_ops(operations: Sequence[Any], fn: Callable[[BeaconState, Any], None]) -> None:
        for operation in operations:
            fn(state, operation)

    for_ops(requests.deposits, process_deposit_request)
    for_ops(requests.withdrawals, process_withdrawal_request)
    for_ops(requests.consolidations, process_consolidation_request)
    for_ops(requests.builder_deposits, process_builder_deposit_request)
    for_ops(requests.builder_exits, process_builder_exit_request)
    # [Modified in PQ]
    # Removed `process_validator_pq_registration_request`
    # [Modified in PQ]
    # Removed `process_builder_pq_registration_request`
    # [New in PQ:EIP8205]
    for_ops(requests.validator_preregistrations, process_validator_preregistration_request)
    # [New in PQ:EIP8205]
    for_ops(requests.builder_preregistrations, process_builder_preregistration_request)
    # [New in PQ]
    for_ops(requests.voluntary_exits, process_voluntary_exit_request)

    # Update parent payload availability and latest block hash
    state.execution_payload_availability[parent_slot % SLOTS_PER_HISTORICAL_ROOT] = Boolean(True)
    state.latest_block_hash = parent_bid.block_hash
```

#### Height events

##### New `is_previous_height_justified`

```python
def is_previous_height_justified(state: BeaconState) -> bool:
    """
    Check if the chain entered the current height by justifying the previous one.
    """
    justified_height = state.justified_checkpoint.height
    return justified_height > 0 and justified_height + 1 == state.target_checkpoint.height
```

##### New `process_height_events`

*Note*: A target quorum justifies the current height only if the previous height
is not justified or is already finalized. Otherwise the height waits for its
predecessor, and a quorum of progress flags can still advance it after the
timeout delay.

```python
def process_height_events(state: BeaconState) -> None:
    # Finalize the highest pending justification with a quorum
    for pending in state.pending_finality:
        if has_quorum(state, pending.participation):
            state.finalized_checkpoint = pending.checkpoint
            state.finalized_slot = pending.slot
    state.pending_finality = PendingFinalities(
        data=[
            pending
            for pending in state.pending_finality
            if pending.checkpoint.height > state.finalized_checkpoint.height
        ]
    )

    if has_quorum(state, state.target_participation) and (
        not is_previous_height_justified(state)
        or state.finalized_checkpoint.height == state.justified_checkpoint.height
    ):
        state.justified_checkpoint = state.target_checkpoint
        # Keep only the newest pending justifications
        if len(state.pending_finality) == PENDING_FINALITY_WINDOW:
            state.pending_finality = state.pending_finality[1:]
        state.pending_finality.append(
            PendingFinality(
                checkpoint=state.target_checkpoint,
                slot=state.target_slot,
                participation=HeightParticipation(data=[Boolean(False)] * len(state.validators)),
            )
        )
        advance_height(state)
    elif (
        has_quorum(state, state.progress_participation)
        # Timeouts count only after the delay
        and state.slot >= state.target_slot + TIMEOUT_DELAY_SLOTS
    ):
        advance_height(state)
```

##### New `advance_dynasty`

```python
def advance_dynasty(state: BeaconState) -> None:
    state.dynasty += 1
    state.previous_dynasty_start_slot = state.dynasty_start_slot
    state.dynasty_start_slot = state.slot
```

##### New `update_ac_snapshots`

At rollover, the third ring entry becomes the newest descriptor and the old
entry is retained for votes from the previous dynasty. The next dynasty frees
that retired entry, which can then capture weights for the next rollover.

The fastest dynasty advance takes two slots: the height opened by the dynasty's
entry block can be justified only by a later block, and the resulting pending
justification can only be finalized by another block. As the snapshot boundary
index goes from 1 at capture to `T - 1`, at least `2 * (T - 2)` slots elapse:
1020 on mainnet and 28 on minimal. Sealing takes at most two epochs (64 or 16
slots, respectively), so every block of the penultimate dynasty already carries
the sealed snapshot. A chain entering the rollover dynasty must finalize one of
those blocks. Registry indices are append-only on descendants of the capture
block.

```python
def update_ac_snapshots(state: BeaconState) -> None:
    epoch = get_current_epoch(state)
    snapshot_number = state.dynasty // HEAD_VOTE_COMMITTEE_SIZE + 2
    snapshots = state.ac_snapshots
    snapshots[snapshot_number % len(snapshots)] = ACSnapshot(
        weights=get_ac_weights(state, epoch), seed=Bytes32(), capture_epoch=epoch
    )
```

##### New `advance_height`

```python
def advance_height(state: BeaconState) -> None:
    state.previous_target_checkpoint = state.target_checkpoint
    state.previous_target_slot = state.target_slot
    state.target_checkpoint = HeightCheckpoint(
        height=state.target_checkpoint.height + 1,
        # Filled in by the next ``process_slot``
        root=Root(),
    )
    state.target_slot = state.latest_block_header.slot
    state.target_participation = HeightParticipation(data=[Boolean(False)] * len(state.validators))
    state.progress_participation = HeightParticipation(
        data=[Boolean(False)] * len(state.validators)
    )
```
