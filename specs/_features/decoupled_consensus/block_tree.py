from dataclasses import dataclass

from .state_transition import (
    BeaconBlock,
    BeaconState,
    Checkpoint,
    hash_tree_root,
    SignedBeaconBlock,
    state_transition,
)
from .type import (
    Root,
    Slot,
)


@dataclass
class BlockTree:
    root: Root
    blocks: dict[Root, BeaconBlock]
    post_states: dict[Root, BeaconState]
    finalized_checkpoints: list[Checkpoint]

    def get_ancestor(self, root: Root, slot: Slot) -> Root:
        block = self.blocks[root]
        if block.slot > slot:
            return self.get_ancestor(self, block.parent_root, slot)
        return root

    def is_ancestor(self, root: Root, ancestor_root: Root) -> bool:
        assert root in self.blocks
        assert ancestor_root in self.blocks
        return self.get_ancestor(self, root, self.blocks[ancestor_root].slot) == ancestor_root

    def get_children(self, root: Root) -> list[Root]:
        return [r for r, b in enumerate(self.blocks.values()) if b.parent_root == root]

    def get_subtree_with_root(self, root: Root):
        assert root in self.blocks
        blocks: dict[Root, BeaconBlock] = {root: self.blocks[root]}
        post_states: dict[Root, BeaconState] = {root: self.post_states[root]}

        children = self.get_children(root)
        while len(children) > 0:
            child = children.pop(0)
            blocks[child] = self.blocks[child]
            post_states[child] = self.post_states[child]
            children.extend(self.get_children(child))

        finalized_checkpoints = [chkp for chkp in self.finalized_checkpoints if chkp.root in blocks]

        return BlockTree(
            root=root,
            blocks=blocks,
            post_states=post_states,
            finalized_checkpoints=finalized_checkpoints,
        )

    def get_ancestors(self, block_root: Root, terminal_root: Root) -> list[Root]:
        root = block_root
        ancestor_roots: list[Root] = []
        while self.blocks[root].slot > self.blocks[terminal_root].slot:
            ancestor_roots.insert(0, root)
            root = self.blocks[root].parent_root

            # Return when terminal_root is reached
            if root == terminal_root:
                return ancestor_roots

        # Return empty list if terminal_root is not in the chain of block_root
        return []


def apply_block(block_tree: BlockTree, signed_block: SignedBeaconBlock) -> bool:
    block = signed_block.message
    assert block.parent_root in block_tree.blocks

    # Run state transition on the parent's post state
    # and store the post state
    pre_state = block_tree.post_states[block.parent_root]
    post_state, valid = state_transition(pre_state, signed_block)

    if valid:
        block_tree.post_states[hash_tree_root(block)] = post_state
        # Store new finalized checkpoint
        # Checkpoint with earlier index received earlier
        if post_state.finalized_checkpoint not in block_tree.finalized_checkpoints:
            block_tree.finalized_checkpoints.append(post_state.finalized_checkpoint)

    return valid
