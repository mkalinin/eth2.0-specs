from dataclasses import dataclass

from .available_chain import AvailableChainStore
from .block_tree import BlockTree
from .finality_gadget import get_finality_view
from .type import Root


@dataclass
class ForkChoiceView:
    head_root: Root
    confirmed_root: Root
    finalized_root: Root


def get_fork_choice_view(
    block_tree: BlockTree, available_chain: AvailableChainStore
) -> ForkChoiceView:
    finality_view = get_finality_view(block_tree)
    viable_tree = block_tree.get_subtree_with_root(finality_state.finality_gadget_root)
    confirmed_view = available_chain.get_confirmed_view(viable_tree)
    return ForkChoiceView(
        head_root=confirmed_view.head_root,
        confirmed_root=confirmed_view.confirmed_root,
        finalized_root=finality_state.finalized_checkpoint.root,
    )
