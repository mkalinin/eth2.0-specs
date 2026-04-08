# Fork Choice -- Safe Block

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [`get_optimistic_store`](#get_optimistic_store)
- [`get_safe_beacon_block_root`](#get_safe_beacon_block_root)
- [`get_safe_execution_block_hash`](#get_safe_execution_block_hash)

<!-- mdformat-toc end -->

## Introduction

Under honest majority and certain network synchronicity assumptions there exists
a block that is safe from re-orgs. Normally this block is pretty close to the
head of canonical chain which makes it valuable to expose a safe block to users.

This section describes an algorithm to find a safe block.

## `get_optimistic_store`

*Note*: Abstract function that returns an instance of `OptimisticStore` defined
in [Optimistic Sync](../sync/optimistic.md).

```python
def get_optimistic_store() -> OptimisticStore:
    pass
```

## `get_safe_beacon_block_root`

*Notes*:

`NOT_VALIDATED`, `INVALIDATED`, `VALID` block statuses and
`latest_verified_ancestor` function used down below are defined in
[Optimistic Sync](../sync/optimistic.md) specification.

If `store.confirmed_root` is `NOT_VALIDATED` or `INVALIDATED` it **MUST NOT** be
served as a safe block as its validity either hasn't yet been verified or proven
to not hold by the local Execution engine.

Depending on the case, the following actions **SHOULD** be taken:

- if `store.confirmed_root` is `NOT_VALIDATED`, return the latest verified
  ancestor of `store.confirmed_root`,
- if `store.confirmed_root` is `INVALIDATED`, return the
  `store.finalized_checkpoint.root`.

The `INVALIDATED` status check is implemented by checking whether
`store.confirmed_root` is canonical or not at the time of the call of this
function as `INVALIDATED` block must not remain canonical as per the Optimistic
sync specification.

Note, if `store.finalized_checkpoint.root` is `NOT_VALIDATED` it may eventually
become `INVALIDATED`. In this case security of the safe block can be
compromised. Resolving the situation when an invalid block is finalized requires
manual intervention and left outside of the scope of this specification.

Implementations **MAY** satisfy the above requirements by returning from
`find_latest_confirmed_descendant` function when a block that have either
`NOT_VALIDATED` or `INVALIDATED` status is encountered.

```python
def get_safe_beacon_block_root(store: Store) -> Root:
    # Return finalized root if confirmed block is not canonical anymore
    if not is_ancestor(store, get_head(store), store.confirmed_root):
        return store.finalized_checkpoint.root

    # Return confirmed root or its most recent verified ancestor
    valid_confirmed_ancestor = latest_verified_ancestor(
        get_optimistic_store(), store.blocks[store.confirmed_root]
    )
    return valid_confirmed_ancestor.root
```

## `get_safe_execution_block_hash`

```python
def get_safe_execution_block_hash(store: Store) -> Hash32:
    safe_block_root = get_safe_beacon_block_root(store)
    safe_block = store.blocks[safe_block_root]

    # Return Hash32() if no payload is yet justified
    if compute_epoch_at_slot(safe_block.slot) >= BELLATRIX_FORK_EPOCH:
        return safe_block.body.execution_payload.block_hash
    else:
        return Hash32()
```

*Note*: This helper uses beacon block container extended in
[Bellatrix](../specs/bellatrix/beacon-chain.md).
