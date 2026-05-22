# Gloas -- Fast Confirmation

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [Modified `get_block_root_node`](#modified-get_block_root_node)

<!-- mdformat-toc end -->

## Introduction

This is the modification of the fast confirmation rule specification
accompanying Gloas.

## Helpers

### Modified `get_block_root_node`

*Note:* This function is modified to return an extended `ForkChoiceNode`
structure with `PAYLOAD_STATUS_PENDING` payload status as a common ancestor of
all nodes referring to a given `block_root`.

```python
def get_block_root_node(block_root: Root) -> ForkChoiceNode:
    # [Modified in Gloas:EIP7732]
    return ForkChoiceNode(root=block_root, payload_status=PAYLOAD_STATUS_PENDING)
```
