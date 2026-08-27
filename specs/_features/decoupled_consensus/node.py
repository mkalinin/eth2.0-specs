from dataclasses import dataclass

from .available_chain import AvailableChainStore
from .block_tree import apply_block, BlockTree
from .stabilization_gadget import StabilizationStore
from .state_transition import SignedBeaconBlock
from .time import get_current_slot, get_current_time, Millis
from .vote import AvailableChainVote, StabilizationVote


@dataclass
class BlockEvent:
    signed_block: SignedBeaconBlock
    receipt_time: Millis


@dataclass
class Node:
    time: Millis
    genesis_time: Millis
    block_tree: BlockTree
    block_queue: list[BlockEvent]
    available_chain_store: AvailableChainStore
    stabilization_store: StabilizationStore


def can_apply_block(node: Node, signed_block: SignedBeaconBlock) -> bool:
    # Apply a block if its parent was processed and the block isn't from the future
    block = signed_block.message
    return block.parent_root in node.block_tree.blocks and block.slot <= get_current_slot(
        node.time, node.genesis_time
    )


def process_block(node: Node, signed_block: SignedBeaconBlock) -> None:
    valid = apply_block(node.block_tree, signed_block)
    if valid:
        node.available_chain_store.process_block(signed_block.message)
        node.stabilization_store.process_block(signed_block.message)


def process_block_queue(node: Node) -> None:
    queue = sorted(node.block_queue, key=lambda e: (e.signed_block.message.slot, e.receipt_time))
    unprocessed = []
    for event in queue:
        if can_apply_block(node, event.signed_block):
            process_block(node, event.signed_block)
        else:
            unprocessed.append(event)
    node.block_queue = unprocessed


def on_slot_start(node: Node) -> None:
    process_block_queue(node)


def on_tick(node: Node, time: Millis) -> None:
    previous_slot = get_current_slot(node.time, node.genesis_time)
    node.time = time
    current_slot = get_current_slot(node.time, node.genesis_time)
    if current_slot > previous_slot:
        on_slot_start(node)

    node.available_chain_store.process_tick(time)
    node.stabilization_store.process_tick(time)


def on_block(node: Node, signed_block: SignedBeaconBlock) -> None:
    if can_apply_block(node, signed_block):
        # Apply a block and then process blocks
        # that are potentially in causal dependency
        process_block(node, signed_block)
        process_block_queue(node)
    else:
        # Otherwise, queue block for later processing
        node.event_queue.append(
            BlockEvent(signed_block=signed_block, receipt_time=get_current_time())
        )


def on_available_chain_vote(node: Node, vote: AvailableChainVote) -> None:
    node.available_chain_store.process_vote(vote)


def on_stabilization_vote(node: Node, vote: StabilizationVote) -> None:
    node.stabilization_store.process_vote(vote)
