# PQ -- Honest Validator

*Note*: This document is a work-in-progress for researchers and implementers.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Constants](#constants)
  - [Misc](#misc)
- [Containers](#containers)
- [Helpers](#helpers)
  - [New `FinalitySigningRecord`](#new-finalitysigningrecord)
- [Becoming a validator](#becoming-a-validator)
  - [Initialization](#initialization)
    - [VRF tree](#vrf-tree)
      - [New `compute_vrf_secret`](#new-compute_vrf_secret)
      - [New `compute_vrf_node`](#new-compute_vrf_node)
      - [New `compute_vrf_root`](#new-compute_vrf_root)
      - [New `compute_vrf_proof`](#new-compute_vrf_proof)
    - [XMSS public key](#xmss-public-key)
  - [Preregister](#preregister)
  - [Submit deposit](#submit-deposit)
- [Validator assignments](#validator-assignments)
  - [Attestation committees](#attestation-committees)
  - [Head vote committees](#head-vote-committees)
  - [Lookahead](#lookahead)
- [Beacon chain responsibilities](#beacon-chain-responsibilities)
  - [Block and sidecar proposal](#block-and-sidecar-proposal)
    - [Broadcasting `SignedProposerPreferences`](#broadcasting-signedproposerpreferences)
    - [Preparing for a `BeaconBlock`](#preparing-for-a-beaconblock)
      - [Modified `prepare_execution_payload`](#modified-prepare_execution_payload)
    - [Constructing the `BeaconBlockBody`](#constructing-the-beaconblockbody)
      - [Randao reveal](#randao-reveal)
      - [Head votes](#head-votes)
      - [Attestations](#attestations)
      - [Attester slashings](#attester-slashings)
      - [Proof](#proof)
      - [Voluntary exits](#voluntary-exits)
      - [Sync committee](#sync-committee)
      - [BLS to execution changes](#bls-to-execution-changes)
      - [Payload attestations](#payload-attestations)
      - [Signed execution payload bid](#signed-execution-payload-bid)
      - [Execution requests](#execution-requests)
    - [Packaging into a `SignedBeaconBlock`](#packaging-into-a-signedbeaconblock)
      - [State root](#state-root)
      - [Signature](#signature)
  - [Head voting](#head-voting)
    - [Head vote data](#head-vote-data)
    - [Construct head vote](#construct-head-vote)
    - [Broadcast head vote](#broadcast-head-vote)
  - [Attesting](#attesting)
    - [Attestation data](#attestation-data)
      - [Finality pair](#finality-pair)
      - [Height pair](#height-pair)
      - [Construct data](#construct-data)
      - [Record attestation](#record-attestation)
    - [Construct attestation](#construct-attestation)
    - [Broadcast attestation](#broadcast-attestation)
  - [Attestation aggregation](#attestation-aggregation)
    - [Aggregation selection](#aggregation-selection)
    - [Construct aggregate](#construct-aggregate)
      - [Head votes](#head-votes-1)
      - [FG attestations](#fg-attestations)
      - [Aggregation bits](#aggregation-bits)
    - [Broadcast aggregate](#broadcast-aggregate)
  - [Sync committees](#sync-committees)
  - [Payload timeliness attestation](#payload-timeliness-attestation)
    - [Constructing the `PayloadAttestationMessage`](#constructing-the-payloadattestationmessage)
- [Protection best practices](#protection-best-practices)

<!-- mdformat-toc end -->

## Introduction

This document represents the changes to be made in the code of an "honest
validator" to implement PQ.

Validators sign with leanXMSS instead of BLS. Every message is signed at the
leaf that `compute_xmss_leaf_index` assigns to its slot and type, except an
attestation, which is signed at the leaf that
`compute_xmss_attestation_leaf_index` assigns to its round, and a message
without a leaf of its own, such as a voluntary exit, which is signed at a
reserved leaf, see [Protection best practices](#protection-best-practices).

## Constants

### Misc

*[New in PQ]*

| Name                | Value           |
| ------------------- | --------------- |
| `VRF_SECRET_DOMAIN` | `b"VRF_SECRET"` |

PQ replaces the combined LMD-GHOST and Casper FFG attestation with separate head
votes for the available chain (AC) and attestations for the finality gadget
(FG). Every validator sits on the attestation committee given by its index, and
an active validator casts its FG attestation in that committee's slot in every
round. In every slot, a head vote committee casts head votes.

*TODO*: Specify the fork-choice interfaces and duty deadlines referenced below.

## Containers

*TODO*: Specify the containers that carry an aggregate and the proof of its
signatures on the wire. `AggregateAndProof` and `SignedAggregateAndProof` are
deprecated, and the leaf offset `LEAF_OFFSET_AGGREGATE_AND_PROOF` stays reserved
for their replacement.

## Helpers

### New `FinalitySigningRecord`

The `FinalitySigningRecord` tracks a validator's FG signing history. A separate
record is maintained for each validator key, independently of whether its
attestations are included on chain.

```python
@dataclass
class FinalitySigningRecord:
    targets: dict[Height, Root]
    timeouts: dict[Height, set[Root]]
    finality_locks: dict[Height, Root]
    entries: dict[Height, set[Root]]
    # [New in PQ]
    rounds: set[Round]
```

The fields are initialized empty for a validator with no prior FG signing
history:

- `targets[h]`: the first target voted for at height `h`.
- `timeouts[h]`: the targets named by timeouts signed at height `h`.
- `finality_locks[h]`: the block named by a finality vote at height `h`.
- `entries[h]`: entries named by any height vote at height `h`.
- `rounds`: rounds in which an attestation was signed. An attestation is signed
  at the XMSS leaf of its round, so a second attestation in a round would reuse
  the leaf.

*Note*: Finality signing locks do not expire and are distinct from the temporary
AC locks maintained by fork choice.

## Becoming a validator

### Initialization

#### VRF tree

A validator's VRF seed, `vrf_seed`, is a secret 32-byte value from which its VRF
tree is derived. It must be securely generated and kept secret, since anyone who
learns it can compute the validator's future RANDAO reveals.

The VRF seed is independent of the validator's XMSS private key. A validator's
VRF root cannot be changed, so the validator must keep its VRF seed for as long
as it validates and take it along when it moves to another client. A tree
derived from any other seed has a different root, so its proofs fail
verification and the validator's blocks are invalid.

The VRF tree is a Merkle tree of depth `VRF_TREE_DEPTH`, hashed with
`keccak256`, with one leaf for each slot. The leaf at index `slot` commits to
the validator's secret for the slot, `compute_vrf_secret(vrf_seed, slot)`. A
validator's VRF root is the root of its VRF tree, `compute_vrf_root(vrf_seed)`.
Its VRF proof for a slot, `compute_vrf_proof(vrf_seed, slot)`, is the secret for
the slot followed by the leaf's Merkle branch. It reveals the proof as its
RANDAO reveal when it proposes. The branch holds only commitments, so it reveals
no other secret. The tree is fixed in advance, so a validator cannot grind its
proofs, and nobody can predict them before they are revealed.

##### New `compute_vrf_secret`

```python
def compute_vrf_secret(vrf_seed: Bytes32, index: Uint64) -> Bytes32:
    """
    Return the secret for ``index`` of the VRF tree derived from ``vrf_seed``.
    """
    return keccak256(VRF_SECRET_DOMAIN + vrf_seed + uint_to_bytes(index))
```

##### New `compute_vrf_node`

```python
def compute_vrf_node(vrf_seed: Bytes32, height: Uint64, index: Uint64) -> Bytes32:
    """
    Return the node at ``index`` among the nodes ``height`` levels above the
    leaves of the VRF tree derived from ``vrf_seed``.
    """
    if height == 0:
        return compute_vrf_leaf(compute_vrf_secret(vrf_seed, index), index)
    left = compute_vrf_node(vrf_seed, height - 1, 2 * index)
    right = compute_vrf_node(vrf_seed, height - 1, 2 * index + 1)
    return keccak256(left + right)
```

##### New `compute_vrf_root`

```python
def compute_vrf_root(vrf_seed: Bytes32) -> Root:
    """
    Return the root of the VRF tree derived from ``vrf_seed``.
    """
    return Root(compute_vrf_node(vrf_seed, VRF_TREE_DEPTH, Uint64(0)))
```

##### New `compute_vrf_proof`

```python
def compute_vrf_proof(vrf_seed: Bytes32, slot: Slot) -> VRFProof:
    """
    Return the secret for ``slot`` of the VRF tree derived from ``vrf_seed``,
    followed by the Merkle branch of the leaf at index ``slot``.
    """
    branch = [
        compute_vrf_node(vrf_seed, Uint64(height), Uint64((slot // 2**height) ^ 1))
        for height in range(VRF_TREE_DEPTH)
    ]
    return VRFProof(data=[compute_vrf_secret(vrf_seed, Uint64(slot))] + branch)
```

#### XMSS public key

A validator's XMSS private key, `privkey`, is a 32-byte seed from which its
leanXMSS key is derived. It must be securely generated along with the resultant
XMSS public key. This `privkey` must be "hot", that is, constantly available to
sign data throughout the lifetime of the validator.

### Preregister

A deposit carries no signature, so anyone who sees the first deposit for a new
XMSS public key before it is included could get in first with a deposit of their
own withdrawal credentials and VRF root. To prevent this, a validator first
preregisters, binding its XMSS public key to its withdrawal credentials and VRF
root. It signs the binding at a reserved leaf and submits it with the signature
to the system contract, which verifies the signature and emits a
`ValidatorPreregistrationRequest` without it.

The validator waits until its binding is in `state.validator_preregistrations`,
then submits its deposit before the binding's `expiry_slot`. If the binding is
not stored, a deposit for the key may already be pending, so the validator
generates a new key and preregisters that one instead.

To renew an expired binding, the validator resubmits the same request. To change
its binding, it generates a new key, since anyone can resubmit the old binding
once it expires.

### Submit deposit

After the upgrade, a deposit carries no signature. Its `pubkey` is
`XMSS_DEPOSIT_PREFIX`, 16 zero bytes, followed by the validator's XMSS public
key, and its `signature` holds the validator's VRF root followed by 64 zero
bytes. A deposit whose XMSS public key is already in `state.validators` tops up
that validator. While the key has an active validator preregistration, a deposit
for it is discarded unless its withdrawal credentials and VRF root match the
binding.

*Note*: A deposit whose `pubkey` does not start with 16 zero bytes is treated as
a legacy deposit, so the validator it creates is exited at once.

## Validator assignments

### Attestation committees

To determine its attestation committee for `epoch`, a validator calls
`get_attestation_committee_assignment(state, epoch, validator_index)`.

```python
def get_attestation_committee_assignment(
    state: BeaconState, epoch: Epoch, validator_index: ValidatorIndex
) -> CommitteeIndex | None:
    """
    Return the index of the validator's attestation committee in ``epoch``, if
    it is active in ``epoch``.
    """
    # [Modified in PQ:EIP8453]
    # The committee index is fixed by the validator index
    if not is_active_validator(state.validators[validator_index], epoch):
        return None
    return CommitteeIndex(validator_index % ATTESTATION_COMMITTEES_PER_ROUND)
```

A validator's committee index is fixed by its validator index, and so is its
subnet. An active validator attests in each round, in the slot
`compute_attestation_committee_slot(round, committee_index)`, which moves by at
most one slot from round to round. Round numbering is defined by
`compute_round_at_slot` and does not restart at the PQ fork.

*Note*: The committees of an epoch also contain validators that are eligible for
activation but not yet active, and validators that exit after that epoch. A
validator that is not active has no attestation duty.

### Head vote committees

For each slot, a validator evaluates its Merkle opening against the voted head's
post-state with `get_head_vote_weight`. It casts one head vote if it wins any
tickets, regardless of the number it wins.

### Lookahead

A validator can evaluate its own openings in advance for a given pair of
snapshots and committee interpolation index. A validator's attestation committee
index is fixed by its validator index, and the chain state determines whether it
is active.

*TODO*: Specify assignment lookahead and the dependent root in the PQ
fork-choice and networking specifications.

## Beacon chain responsibilities

All validator responsibilities remain unchanged other than those noted below.

### Block and sidecar proposal

#### Broadcasting `SignedProposerPreferences`

*Note*: Preferences for a proposal slot are always signed at the same leaf. A
validator MUST NOT sign two different preferences for the same proposal slot,
even if the dependent root changes.

```python
def get_signed_proposer_preferences(
    store: Store,
    state: BeaconState,
    head_root: Root,
    proposal_slot: Slot,
    validator_index: ValidatorIndex,
    fee_recipient: ExecutionAddress,
    target_gas_limit: Uint64,
    # [Modified in PQ]
    privkey: Bytes32,
) -> SignedProposerPreferences:
    proposal_epoch = compute_epoch_at_slot(proposal_slot)
    dependent_root = get_shuffling_dependent_root(store, head_root, proposal_epoch)
    preferences = ProposerPreferences(
        dependent_root=dependent_root,
        proposal_slot=proposal_slot,
        validator_index=validator_index,
        fee_recipient=fee_recipient,
        target_gas_limit=target_gas_limit,
    )
    domain = compute_domain(
        DOMAIN_PROPOSER_PREFERENCES,
        compute_fork_version(proposal_epoch),
        state.genesis_validators_root,
    )
    signing_root = compute_signing_root(preferences, domain)
    # [Modified in PQ]
    leaf_index = compute_xmss_leaf_index(proposal_slot, LEAF_OFFSET_PROPOSER_PREFERENCES)
    signature = xmss_sign(privkey, leaf_index, signing_root)
    return SignedProposerPreferences(message=preferences, signature=signature)
```

#### Preparing for a `BeaconBlock`

Let `parent` be the block returned by the AC proposal procedure, together with
its previous slot head-vote view.

*TODO*: Specify the PQ proposal helper, including full or empty execution
payload selection.

##### Modified `prepare_execution_payload`

*Note*: The fork choice store keeps the EIP-8483 payloads of blocks before the
fork. Their execution requests have the EIP-8483 type, whose root differs from
the commitment that a PQ block can carry (see
[the fork document](./fork.md#upgrading-the-state)), so the proposer builds on
the full payload of its parent only if it is a PQ payload.

*TODO*: Specify how the first block after the fork builds on the full payload of
the last block before the fork.

```python
def prepare_execution_payload(
    # [New in Gloas:EIP7732]
    store: Store,
    # [New in Gloas:EIP7732]
    head: ForkChoiceNode,
    state: BeaconState,
    safe_block_hash: Hash32,
    finalized_block_hash: Hash32,
    suggested_fee_recipient: ExecutionAddress,
    # [New in Gloas]
    target_gas_limit: Uint64,
    execution_engine: ExecutionEngine,
) -> PayloadId | None:
    # [New in Gloas:EIP7732]
    parent_bid = state.latest_execution_payload_bid
    if should_build_on_full(store, head, state.slot):
        envelope = store.payloads[head.root]
        # [New in PQ:EIP8453]
        # The full payload of the parent is a PQ payload
        assert isinstance(envelope, ExecutionPayloadEnvelope)
        # Make a copy of the state to avoid mutability issues
        state = state.copy()
        # Apply parent payload before computing withdrawals
        apply_parent_execution_payload(state, envelope.execution_requests)
        withdrawals = get_expected_withdrawals(state).withdrawals
        head_block_hash = parent_bid.block_hash
    else:
        withdrawals = state.payload_expected_withdrawals
        head_block_hash = parent_bid.parent_block_hash

    # Set the forkchoice head and initiate the payload build process
    payload_attributes = PayloadAttributes(
        timestamp=compute_time_at_slot(state.genesis_time, state.slot),
        prev_randao=get_randao_mix(state, get_current_epoch(state)),
        suggested_fee_recipient=suggested_fee_recipient,
        # [Modified in Gloas:EIP7732]
        withdrawals=withdrawals,
        parent_beacon_block_root=hash_tree_root(state.latest_block_header),
        # [New in Gloas:EIP7843]
        slot_number=state.slot,
        # [New in Gloas]
        target_gas_limit=target_gas_limit,
    )
    return execution_engine.notify_forkchoice_updated(
        # [Modified in Gloas:EIP7732]
        head_block_hash=head_block_hash,
        safe_block_hash=safe_block_hash,
        finalized_block_hash=finalized_block_hash,
        payload_attributes=payload_attributes,
        # [New in Gloas:EIP8070]
        custody_columns=None,
    )
```

#### Constructing the `BeaconBlockBody`

##### Randao reveal

Set `block.body.randao_reveal` to `compute_vrf_proof(vrf_seed, block.slot)`, the
proposer's VRF proof for `block.slot`.

##### Head votes

Set `block.body.head_vote_declarations` and `block.body.head_vote_support_bits`
to the declarations and support bits returned by
[`get_ac_proposal`](./fork-choice.md#new-get_ac_proposal). The vote slot is
`block.slot - 1`.

Independently select up to `MAX_HEAD_VOTES` signed aggregates that satisfy
[`process_head_vote`](./beacon-chain.md#new-process_head_vote). Include votes
that add uncredited voters for the canonical block of their slot. The duty slot
must be in the entering state's current or previous dynasty and in the current
or previous epoch for payment accounting. Under fast finality, the dynasty rule
can end eligibility after just a few slots, well before the epoch window closes.
Proposers may retain these aggregates beyond the lifetime of the fork-choice
message pool. They need not match any declaration.

Include at most `2 * HEAD_VOTE_PAYMENT_TARGET` credentials across all aggregates
in the block, enough to meet the full payment target for two duty slots. Recheck
each credential against the including chain's duty-slot dynasty and lotteries. A
vote with positive weight on its voted head can have zero weight for inclusion
when the two chains have different duty-slot dynasties.

##### Attestations

Set `block.body.attestations` to aggregates selected from the FG attestation
pool, up to `MAX_ATTESTATIONS_PQ`. Each aggregate must satisfy the verification
conditions in
[`process_attestation`](./beacon-chain.md#modified-process_attestation),
including its round and committee encoding. Only attestations for the current or
the previous target of `state` are valid. An attestation for the previous target
adds only pending-finality participation and pays the proposer nothing; a
proposer should include such aggregates when places are left after the
aggregates that add target, progress or pending-finality participation for the
current target. Attestations with the same data signed in different rounds are
in different aggregates, since an aggregate holds the signatures of one round.
`compute_on_chain_aggregate` is deprecated.

A proposer should prefer aggregates that add target, progress or
pending-finality participation.

##### Attester slashings

Set `block.body.attester_slashings` to valid attester slashing evidence, up to
`MAX_ATTESTER_SLASHINGS_ELECTRA` items.

The evidence must satisfy `process_attester_slashing` against the state at its
position in block processing.

##### Proof

The proposer sets `body.proof` to `stark_merge_proofs(proofs)`, where `proofs`
holds the proofs of the aggregates behind `body.attestations`, ordered as the
attestations are and, within each, by committee index, followed by the proofs of
the aggregates behind `body.head_votes`, ordered as the head votes are. The
merged proof then proves the statements that `process_stark` checks.

##### Voluntary exits

The block body no longer has `voluntary_exits`. To exit, a validator signs its
exit at a reserved leaf and submits it with the signature to the system
contract, which verifies the signature and emits a `VoluntaryExitRequest`
without it. Anyone can submit a signed exit, not only the validator's withdrawal
address.

##### Sync committee

Sync committees are removed in PQ, so the block body no longer has a
`sync_aggregate`.

##### BLS to execution changes

`BLSToExecutionChange` is disabled in PQ, so the block body no longer has
`bls_to_execution_changes`.

##### Payload attestations

The block body no longer has `payload_attestations`, so the proposer does not
aggregate payload attestation messages.

##### Signed execution payload bid

For self-builds, the signature MUST be the empty `XMSSSignature()`, which is all
zero bytes, and the `bid.value` MUST be zero. All other conditions on
`signed_execution_payload_bid` are unchanged.

##### Execution requests

*Note*: The function `get_execution_requests` is modified to no longer parse PQ
registration requests and to parse validator preregistration, builder
preregistration, and voluntary exit requests.

```python
def get_execution_requests(execution_requests_list: Sequence[bytes]) -> ExecutionRequests:
    deposits = DepositRequests()
    withdrawals = WithdrawalRequests()
    consolidations = ConsolidationRequests()
    builder_deposits = BuilderDepositRequests()
    builder_exits = BuilderExitRequests()
    # [New in PQ:EIP8205]
    validator_preregistrations = ValidatorPreregistrationRequests()
    # [New in PQ:EIP8205]
    builder_preregistrations = BuilderPreregistrationRequests()
    # [New in PQ]
    voluntary_exits = VoluntaryExitRequests()

    request_types = [
        DEPOSIT_REQUEST_TYPE,
        WITHDRAWAL_REQUEST_TYPE,
        CONSOLIDATION_REQUEST_TYPE,
        BUILDER_DEPOSIT_REQUEST_TYPE,
        BUILDER_EXIT_REQUEST_TYPE,
        # [Modified in PQ]
        # Removed `VALIDATOR_PQ_REGISTRATION_REQUEST_TYPE`
        # [Modified in PQ]
        # Removed `BUILDER_PQ_REGISTRATION_REQUEST_TYPE`
        # [New in PQ:EIP8205]
        VALIDATOR_PREREGISTRATION_REQUEST_TYPE,
        # [New in PQ:EIP8205]
        BUILDER_PREREGISTRATION_REQUEST_TYPE,
        # [New in PQ]
        VOLUNTARY_EXIT_REQUEST_TYPE,
    ]

    prev_request_type = None
    for request in execution_requests_list:
        request_type, request_data = request[0:1], request[1:]

        # Check that the request type is valid
        assert request_type in request_types
        # Check that the request data is not empty
        assert len(request_data) != 0
        # Check that requests are in strictly ascending order
        # Each successive type must be greater than the last with no duplicates
        assert prev_request_type is None or prev_request_type < request_type
        prev_request_type = request_type

        if request_type == DEPOSIT_REQUEST_TYPE:
            deposits = ssz_deserialize(DepositRequests, request_data)
        elif request_type == WITHDRAWAL_REQUEST_TYPE:
            withdrawals = ssz_deserialize(WithdrawalRequests, request_data)
        elif request_type == CONSOLIDATION_REQUEST_TYPE:
            consolidations = ssz_deserialize(ConsolidationRequests, request_data)
        elif request_type == BUILDER_DEPOSIT_REQUEST_TYPE:
            builder_deposits = ssz_deserialize(BuilderDepositRequests, request_data)
        elif request_type == BUILDER_EXIT_REQUEST_TYPE:
            builder_exits = ssz_deserialize(BuilderExitRequests, request_data)
        # [New in PQ:EIP8205]
        elif request_type == VALIDATOR_PREREGISTRATION_REQUEST_TYPE:
            validator_preregistrations = ssz_deserialize(
                ValidatorPreregistrationRequests, request_data
            )
        # [New in PQ:EIP8205]
        elif request_type == BUILDER_PREREGISTRATION_REQUEST_TYPE:
            builder_preregistrations = ssz_deserialize(BuilderPreregistrationRequests, request_data)
        # [New in PQ]
        elif request_type == VOLUNTARY_EXIT_REQUEST_TYPE:
            voluntary_exits = ssz_deserialize(VoluntaryExitRequests, request_data)

    return ExecutionRequests(
        deposits=deposits,
        withdrawals=withdrawals,
        consolidations=consolidations,
        builder_deposits=builder_deposits,
        builder_exits=builder_exits,
        # [Modified in PQ]
        # Removed `validator_pq_registrations`
        # [Modified in PQ]
        # Removed `builder_pq_registrations`
        # [New in PQ:EIP8205]
        validator_preregistrations=validator_preregistrations,
        # [New in PQ:EIP8205]
        builder_preregistrations=builder_preregistrations,
        # [New in PQ]
        voluntary_exits=voluntary_exits,
    )
```

#### Packaging into a `SignedBeaconBlock`

##### State root

```python
def compute_new_state_root(state: BeaconState, block: BeaconBlock) -> Root:
    temp_state: BeaconState = state.copy()
    # [Modified in PQ]
    signed_block = SignedBeaconBlock(message=block, signature=XMSSSignature())
    state_transition(temp_state, signed_block, validate_result=False)
    return hash_tree_root(temp_state)
```

##### Signature

`signed_block = SignedBeaconBlock(message=block, signature=block_signature)`,
where `block_signature` is obtained from:

```python
def get_block_signature(
    state: BeaconState,
    block: BeaconBlock,
    # [Modified in PQ]
    privkey: Bytes32,
) -> XMSSSignature:
    domain = get_domain(state, DOMAIN_BEACON_PROPOSER, compute_epoch_at_slot(block.slot))
    signing_root = compute_signing_root(block, domain)
    # [Modified in PQ]
    leaf_index = compute_xmss_leaf_index(block.slot, LEAF_OFFSET_BEACON_PROPOSER)
    return xmss_sign(privkey, leaf_index, signing_root)
```

### Head voting

A validator on the head vote committee of `slot` creates, signs and broadcasts a
`HeadVoteMessage` for that slot.

Every node attempts `get_ac_vote_head(store)` after block, payload and head-vote
receipts and at `get_head_vote_due_ms()` into the slot, even if none of its
validators belongs to the head vote committee. Early preparation requires all
eligible declarations across current-slot proposals in the FG tree to be held,
and all marked eligible heads of at least one such proposal to be usable (see
[`is_ac_vote_ready`](./fork-choice.md#new-is_ac_vote_ready)). At the deadline
the node prepares with the held declarations, omitting the rest. Preparation
caches one head per slot and unlocks using the frozen local view merged with
current proposals. When a new prepared head becomes available, assigned
validators immediately sign, process locally and broadcast their vote once.
Unselected validators do not sign, self-admit or emit a vote. Repeated requests
in the same slot return the prepared head without unlocking again. A `None`
result means preparation is not ready yet or the deadline was missed. A
validator must never sign two different head votes for one slot.

#### Head vote data

First, the validator constructs `head_vote_data`, a
[`HeadVoteData`](./beacon-chain.md#headvotedata) object:

- Let `head` be the head selected by the AC voting procedure for `slot`.
- Set `head_vote_data.slot = slot`.
- Set `head_vote_data.beacon_block_root = head.root`.
- Set `head_vote_data.payload_status = head.payload_status`. The prepared node
  uses `PAYLOAD_STATUS_PENDING` for a current-slot block, and
  `PAYLOAD_STATUS_FULL` or `PAYLOAD_STATUS_EMPTY` for an earlier block.

The AC voting procedure applies view merge, AC locks and FG restrictions using
its voting view.

#### Construct head vote

The validator creates `head_vote_message` as a
[`HeadVoteMessage`](./beacon-chain.md#headvotemessage):

- Set `head_vote_message.proof` to `compute_vrf_proof(vrf_seed, slot)` for the
  registered VRF tree. Check for positive weight against the voted head before
  signing.
- Set `head_vote_message.validator_index = validator_index`.
- Set `head_vote_message.data = head_vote_data`.
- Set `head_vote_message.signature` to
  `get_head_vote_signature(state, head_vote_data, privkey)`.

```python
def get_head_vote_signature(
    state: BeaconState, data: HeadVoteData, privkey: Bytes32
) -> XMSSSignature:
    domain = get_domain(state, DOMAIN_HEAD_VOTE, compute_epoch_at_slot(data.slot))
    signing_root = compute_signing_root(data, domain)
    leaf_index = compute_xmss_leaf_index(data.slot, LEAF_OFFSET_HEAD_VOTE)
    return xmss_sign(privkey, leaf_index, signing_root)
```

The validator must record the selected root before signing and must not sign
another head for the same slot.

#### Broadcast head vote

The validator broadcasts `head_vote_message` on the global `head_vote`
[topic](./p2p-interface.md#new-head_vote) and processes it locally.

### Attesting

A validator attempts to create an FG attestation in the slot of its attestation
committee using the rules below. It sends no new attestation if there is no FG
source or if its signing history suppresses the vote.

*TODO*: Specify the FG attestation deadline and source observation for each
assigned slot and staggered committee schedule.

#### Attestation data

First, obtain `source` from `get_ac_frame(store)` at or after the support
cutoff. The `source` is the deepest viable effective live fast-lock node whose
confirmation slot is at least the current slot minus two. Slow locks do not
provide FG sources. If `source` is `None`, the validator does not attest.

Let `source_state` be the state after processing `source`:

- Let `target` be a copy of `source_state.target_checkpoint`.

If `target.root == Root()` because `source` advanced the height, set
`target.root = source.root`.

Let `entry_state = get_block_state(store, target.root)`, the state after
processing the block `target.root`, in which the chain of `source` entered the
height of `target`. At height 1 the target is the last block before the fork,
whose stored state is an EIP-8483 state that `get_block_state` reads through the
upgrade.

*Note*: Both the height pair and the finality pair come from the chain of the
source. The candidate finality pairs are read from `entry_state`, so they do not
change while the source stays at the same height; which candidate is offered
still depends on the signing record.

##### Finality pair

The validator selects the finality pair using `get_finality_vote`. When the
previous height is justified, it offers that justification, also when a later
state has finalized it. Otherwise it offers the newest pending justification of
`entry_state` that its record permits.

```python
def is_finality_pair_permitted(record: FinalitySigningRecord, checkpoint: HeightCheckpoint) -> bool:
    height, root = checkpoint.height, checkpoint.root
    previous_target = record.targets.get(height)
    if previous_target is not None and previous_target != root:
        return False
    if not record.timeouts.get(height, set()) <= {root}:
        return False
    lock = record.finality_locks.get(height)
    return lock is None or lock == root
```

```python
def get_finality_vote(record: FinalitySigningRecord, entry_state: BeaconState) -> HeightCheckpoint:
    if is_previous_height_justified(entry_state):
        justified = entry_state.justified_checkpoint
        if is_finality_pair_permitted(record, justified):
            return justified.copy()
        return HeightCheckpoint.empty()
    for pending in reversed(entry_state.pending_finality):
        if is_finality_pair_permitted(record, pending.checkpoint):
            return pending.checkpoint.copy()
    return HeightCheckpoint.empty()
```

*Note*: Every pending justification of `entry_state` and its justified
checkpoint are below the height of `target`.

##### Height pair

The validator selects the height pair using `get_height_vote`:

```python
def get_height_vote(
    record: FinalitySigningRecord, target: HeightCheckpoint
) -> tuple[HeightCheckpoint, bool] | None:
    height, root = target.height, target.root
    if height == 0 or root == Root():
        return None
    lock = record.finality_locks.get(height)
    if lock is not None and lock != root:
        return None
    if height in record.timeouts:
        return target.copy(), True
    previous_target = record.targets.get(height)
    if previous_target is not None and previous_target != root:
        return target.copy(), True
    return target.copy(), False
```

##### Construct data

Set `attestation_data` to
`get_finality_attestation_data(record, target, entry_state)`. If it returns
`None`, the validator sends no new attestation.

*Note*: The duplicate-vote checks suppress the entire attestation, including any
new finality pair.

```python
def get_finality_attestation_data(
    record: FinalitySigningRecord, target: HeightCheckpoint, entry_state: BeaconState
) -> AttestationData | None:
    assert entry_state.target_checkpoint.height == target.height
    vote = get_height_vote(record, target)
    if vote is None:
        return None
    target, timeout = vote

    entries = record.entries.get(target.height, set())
    if (not timeout and len(entries) > 0) or target.root in entries:
        return None

    finality = get_finality_vote(record, entry_state)
    return AttestationData(target=target, timeout=Boolean(timeout), finality=finality)
```

##### Record attestation

Before signing, the validator records the selected `attestation_data` and the
round of its assigned slot. If it has already signed an attestation in that
round, it sends no new attestation:

```python
def record_finality_attestation(
    record: FinalitySigningRecord,
    data: AttestationData,
    # [New in PQ]
    round: Round,
) -> None:
    # [New in PQ]
    assert round not in record.rounds
    record.rounds.add(round)
    height, root = data.target.height, data.target.root
    if height not in record.entries:
        record.entries[height] = set()
    record.entries[height].add(root)
    if data.finality != HeightCheckpoint.empty():
        record.finality_locks[data.finality.height] = data.finality.root
    if data.timeout:
        if height not in record.timeouts:
            record.timeouts[height] = set()
        record.timeouts[height].add(root)
    elif height not in record.targets:
        record.targets[height] = root
```

Selecting and recording the data must be serialized per validator key. The
record and selected data must be persisted before signing. See
[Protection best practices](#protection-best-practices) for interrupted duties.

#### Construct attestation

The validator creates `attestation` as a
[`SingleAttestation`](./beacon-chain.md#singleattestation) with the following
fields:

- Set `attestation.committee_index` to the assigned committee index.
- Set `attestation.attester_index = validator_index`.
- Set `attestation.data = attestation_data`.
- Set `attestation.round` to the round of the assigned slot.
- Set `attestation.signature` to
  `get_attestation_signature(source_state, attestation_data, epoch, attestation.round, privkey)`,
  where `epoch = get_attestation_epoch(source_state, attestation_data)`, the
  epoch of the target.

```python
def get_attestation_signature(
    state: BeaconState,
    attestation_data: AttestationData,
    # [New in PQ:EIP8453]
    epoch: Epoch,
    # [New in PQ]
    round: Round,
    # [Modified in PQ]
    privkey: Bytes32,
) -> XMSSSignature:
    # [Modified in PQ:EIP8453]
    domain = get_domain(state, DOMAIN_FINALITY_ATTESTER, epoch)
    signing_root = compute_signing_root(attestation_data, domain)
    # [Modified in PQ]
    leaf_index = compute_xmss_attestation_leaf_index(round)
    return xmss_sign(privkey, leaf_index, signing_root)
```

The signature covers `attestation.data`, but not `attestation.round` or
`attestation.committee_index`. It is signed at the leaf of `attestation.round`,
so a validator MUST NOT sign two different attestations in the same round (see
`FinalitySigningRecord.rounds`).

*Note*: `source_state.target_slot` is the slot of the target block, so every
validator signing for the same target uses the same epoch. The target is current
in the state of every chain that can include the attestation, and that state has
the same target slot.

#### Broadcast attestation

The validator broadcasts `attestation` on the `attestation_{subnet_id}`
[topic](./p2p-interface.md#new-attestation_subnet_id) and processes it locally,
where `subnet_id = compute_subnet_for_attestation(attestation.committee_index)`.

```python
def compute_subnet_for_attestation(
    # [Modified in PQ:EIP8453]
    # Removed `committees_per_slot`
    # [Modified in PQ:EIP8453]
    # Removed `slot`
    committee_index: CommitteeIndex,
) -> SubnetID:
    """
    Return the subnet of the attestation committee at ``committee_index``.
    """
    # [Modified in PQ:EIP8453]
    return SubnetID(committee_index % ATTESTATION_SUBNET_COUNT_PQ)
```

### Attestation aggregation

Validators aggregate head votes and FG attestations separately. The messages
passed to the helpers below must have valid signatures under the same domain and
leaf, and valid committee assignments for `state`.

*Note*: The helpers aggregate individual messages, and prove their signatures
with an `AttestationProof` in place of an aggregate signature.

#### Aggregation selection

*TODO*: Specify aggregator selection for head votes and FG attestations.
`get_slot_signature` and `is_aggregator` are deprecated.

#### Construct aggregate

##### Head votes

Construct `aggregate_vote` using `get_aggregate_head_vote` with head vote
messages for the same slot, block root and payload status. A validator holding
several seats in the committee contributes one signature and one voter toward
the builder payment target.

```python
def get_aggregate_head_vote(state: BeaconState, messages: Sequence[HeadVoteMessage]) -> HeadVote:
    """
    Aggregate head vote messages with identical data and distinct signers.
    """
    assert len(messages) > 0
    data = messages[0].data
    assert all(message.data == data for message in messages)
    ordered = sorted(messages, key=lambda message: message.validator_index)
    assert len({message.validator_index for message in ordered}) == len(ordered)
    for message in ordered:
        assert get_head_vote_weight(state, data.slot, message.validator_index, message.proof) > 0
    return HeadVote(
        credentials=HeadVoteCredentials(
            data=[
                HeadVoteCredential(validator_index=message.validator_index, proof=message.proof)
                for message in ordered
            ]
        ),
        data=data,
    )
```

The aggregator proves the signatures of the messages it aggregates, in the order
of the aggregate's `credentials`:

*TODO*: Revisit once the proof of head vote signatures is specified.

```python
def get_aggregate_head_vote_stark(
    state: BeaconState, aggregate_vote: HeadVote, signatures: Sequence[XMSSSignature]
) -> AttestationProof:
    statement = get_head_vote_statement(state, aggregate_vote)
    return stark_prove_aggregates([statement], [signatures])
```

##### FG attestations

Construct `aggregate_attestation` using `get_aggregate_attestation` with
individual attestations for the same data and round, where `state` is a state
whose target is the target of that data, such as the aggregator's source state.
Attestations cast in different epochs can be aggregated together, but
attestations cast in different rounds cannot, since their signers sign at
different XMSS leaves. They are aggregated per round.

```python
def get_aggregate_attestation(
    state: BeaconState, attestations: Sequence[SingleAttestation]
) -> Attestation:
    """
    Aggregate attestations with identical data and round, and distinct signers.
    """
    assert len(attestations) > 0
    data = attestations[0].data
    round = attestations[0].round
    assert all(a.data == data and a.round == round for a in attestations)
    participants = {a.attester_index for a in attestations}
    assert len(participants) == len(attestations)

    # [Modified in PQ:EIP8453]
    # Each signer's committee is fixed by its index
    committee_bits = AttestationCommitteeBits()
    for validator_index in participants:
        committee_bits[validator_index % ATTESTATION_COMMITTEES_PER_ROUND] = Boolean(True)

    epoch = get_attestation_epoch(state, data)
    aggregation_bits = get_attestation_aggregation_bits(state, epoch, committee_bits, participants)
    return Attestation(
        aggregation_bits=aggregation_bits,
        data=data,
        committee_bits=committee_bits,
        round=round,
    )
```

The aggregator proves the signatures of the attestations it aggregates. It
passes, for each committee of the aggregate in order, the signatures of that
committee's attesters in the order of the committee:

```python
def get_aggregate_stark(
    state: BeaconState, aggregate: Attestation, signatures: Sequence[Sequence[XMSSSignature]]
) -> AttestationProof:
    statements = get_attestation_statements(state, aggregate)
    return stark_prove_aggregates(statements, signatures)
```

##### Aggregation bits

`get_attestation_aggregation_bits` encodes signers in committee-index order,
matching `get_aggregate_participants` in the beacon-chain specification. The
size bound applies to all members of the represented committees, not only the
signers. Split messages into separate aggregates when the bound would be
exceeded.

```python
def get_attestation_aggregation_bits(
    state: BeaconState,
    epoch: Epoch,
    committee_bits: AttestationCommitteeBits,
    participants: set[ValidatorIndex],
) -> AggregationBits:
    """
    Encode participants in the concatenation of the selected attestation
    committees.
    """
    aggregation_bits = AggregationBits()
    represented_participants: set[ValidatorIndex] = set()
    for committee_index in get_committee_indices(committee_bits):
        committee = get_attestation_committee(state, epoch, committee_index)
        assert len(aggregation_bits) + len(committee) <= MAX_VALIDATORS_PER_AGGREGATE
        for validator_index in committee:
            is_participant = validator_index in participants
            aggregation_bits.append(Boolean(is_participant))
            if is_participant:
                represented_participants.add(validator_index)
    assert represented_participants == participants
    return aggregation_bits
```

#### Broadcast aggregate

The validator broadcasts the aggregate and its proof for block inclusion.

*TODO*: Specify aggregate gossip messages, their proof wrappers and broadcast
deadlines. Gossip deduplication must use the data, round and signers.

*Note*: A block can include an FG aggregate only while its target is the current
or the previous target of the inclusion state, and only if its round is no later
than `get_current_round(state)`. Its encoding stays valid for that whole time,
since the committees depend only on the epoch of the target.

### Sync committees

Sync committees are removed in PQ, so validators have no sync committee duties.

### Payload timeliness attestation

#### Constructing the `PayloadAttestationMessage`

```python
def get_payload_attestation_message_signature(
    state: BeaconState,
    attestation: PayloadAttestationMessage,
    # [Modified in PQ]
    privkey: Bytes32,
) -> XMSSSignature:
    domain = get_domain(state, DOMAIN_PTC_ATTESTER, compute_epoch_at_slot(attestation.data.slot))
    signing_root = compute_signing_root(attestation.data, domain)
    # [Modified in PQ]
    leaf_index = compute_xmss_leaf_index(attestation.data.slot, LEAF_OFFSET_PTC_ATTESTER)
    return xmss_sign(privkey, leaf_index, signing_root)
```

## Protection best practices

An XMSS key MUST NOT sign two different messages at the same leaf, because that
exposes the leaf and lets others forge signatures at it. A validator client
SHOULD therefore extend its slashing protection to every message it signs. It
keeps a local record of the signing root signed at each leaf, refuses to sign a
different signing root at a recorded leaf, and records each new signing root
before signing it. Like the slashing protection database, this record must
survive restarts and move with the key.

An attestation is signed at the leaf of its round, and a head vote at a leaf of
its slot. The finality signing record and the selected head must be persisted
before signing, so that an interrupted duty is not signed again with different
data.

A message without a leaf of its own, such as a voluntary exit, is signed at a
reserved leaf, one of the first `XMSS_RESERVED_LEAVES` leaves. The signer MUST
use each reserved leaf at most once, for example by allocating them in
increasing order. The record must include the leaf of the key's preregistration,
which is signed before the validator exists.
