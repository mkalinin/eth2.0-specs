from collections.abc import Callable
from dataclasses import dataclass

from .block_tree import BlockTree
from .type import Root, Slot, UInt64


@dataclass
class WeighedNode:
    root: Root
    slot: Slot
    parent_root: Root
    weight: UInt64


@dataclass
class WeighedTree:
    root: Root
    nodes: dict[Root, WeighedNode]
    is_node_eligible: Callable[[WeighedNode], bool]

    def get_eligible_children(self, root: Root) -> list[WeighedNode]:
        return [c for c in self.nodes if c.parent_root == root and self.is_node_eligible(c)]

    def get_head(self) -> Root:
        head = self.root
        children = self.get_eligible_children(head)
        while any(children):
            head = max(children, key=lambda n: (n.weight, n.root)).root
            children = self.get_eligible_children(head)
        return head

    def get_or_create_node(self, parent_root: Root, root: Root) -> WeighedNode:
        if root in self.nodes:
            return self.nodes[root]
        else:
            return WeighedNode(parent_root=parent_root, root=root, weight=UInt64(0))

    def add_score(self, root: Root, score: UInt64) -> None:
        block_root = root
        # Add score to each node in the branch denoted by the `root`
        while block_root in self.nodes:
            node = self.nodes[block_root]
            self.nodes[root] = WeighedNode(
                root=node.root, parent_root=node.parent_root, weight=(node.weight + score)
            )
            block_root = node.parent_root


def initialize_weighed_tree(
    block_tree: BlockTree,
    initial_node_weight: UInt64,
    is_node_eligible: Callable[[WeighedNode], bool],
) -> WeighedTree:
    nodes: dict[Root, WeighedNode] = []
    for root, block in block_tree.blocks.items():
        nodes[root] = WeighedNode(
            root=root,
            slot=block.slot,
            parent_root=block.parent_root,
            weight=initial_node_weight,
        )
    return WeighedTree(
        root=block_tree.root,
        nodes=nodes,
        is_node_eligible=is_node_eligible,
    )
