from dataclasses import dataclass

from .block_tree import BlockTree
from .state_transition import Checkpoint
from .type import Height, Root


@dataclass
class FinalityView:
    finalized_checkpoint: Checkpoint
    justified_checkpoint: Checkpoint
    finality_gadget_root: Root


def compute_finalized_checkpoint(block_tree: BlockTree) -> Checkpoint:
    finalized_checkpoint = block_tree.finalized_checkpoints[0]
    # Find most recent finalized checkpoint on the first seen branch,
    # never switch to a conflicting one
    for checkpoint in block_tree.finalized_checkpoints:
        if checkpoint.height > finalized_checkpoint.height and block_tree.is_ancestor(
            checkpoint.root, finalized_checkpoint.root
        ):
            finalized_checkpoint = checkpoint
    return finalized_checkpoint


def compute_justified_checkpoint(block_tree: BlockTree) -> Checkpoint:
    return max(
        (s.justified_checkpoint for s in block_tree.post_states),
        # by height and then by root lexicographically
        key=lambda j: (j.height, j.root),
    )


def compute_max_height(block_tree: BlockTree) -> Height:
    return max(s.target.height for s in block_tree.post_states)


def get_finality_view(block_tree: BlockTree) -> FinalityView:
    # Compute finalized checkpoint and viable block tree
    finalized_checkpoint = compute_finalized_checkpoint(block_tree)
    subtree_below_finalized_block = block_tree.get_subtree_with_root(finalized_checkpoint.root)

    # Compute justified checkpoint and finality gadget root
    justified_checkpoint = compute_justified_checkpoint(subtree_below_finalized_block)
    max_height = compute_max_height(subtree_below_finalized_block)
    if justified_checkpoint.height + 1 == max_height:
        finality_gadget_root = justified_checkpoint.root
    else:
        finality_gadget_root = finalized_checkpoint.root

    return FinalityView(
        finalized_checkpoint=finalized_checkpoint,
        justified_checkpoint=justified_checkpoint,
        finality_gadget_root=finality_gadget_root,
    )
