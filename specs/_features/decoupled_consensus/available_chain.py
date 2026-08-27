from dataclasses import dataclass

from .block_tree import BlockTree
from .preset import SLOTS_PER_SECOND
from .state_transition import BeaconBlock
from .time import get_current_slot, get_previous_slot, get_slot_start_time, Millis
from .type import (
    Root,
    Slot,
    UInt64,
    ValidatorIndex,
)
from .vote import AvailableChainVote
from .weighed_tree import initialize_weighed_tree, WeighedTree


@dataclass
class VoteAndTimestamp:
    vote: AvailableChainVote
    time: Millis


@dataclass
class BlockAndTimestamp:
    block: BeaconBlock
    time: Millis


@dataclass
class ConfirmedView:
    confirmed_root: Root


@dataclass
class ProposerView:
    head_root: Root
    votes: list[AvailableChainVote]


@dataclass
class AttesterView:
    head_root: Root


@dataclass
class AvailableChainStore:
    time: Millis
    genesis_time: Millis
    attester_votes: list[VoteAndTimestamp]
    blocks: list[BlockAndTimestamp]

    def process_tick(self, time: Millis) -> None:
        self.time = time

    def process_vote(self, vote: AvailableChainVote) -> None:
        if vote not in [vt.vote for vt in self.attester_votes]:
            self.attester_votes.append(VoteAndTimestamp(vote, self.time))

    def process_block(self, block: BeaconBlock) -> None:
        self.blocks.append(BlockAndTimestamp(block, self.time))

    def compute_freeze_deadline(self, slot: Slot) -> Millis:
        # 3/4 of a slot interval
        return get_slot_start_time(slot, self.genesis_time) + 3 * SLOTS_PER_SECOND * 1000 // 4

    def compute_confirmation_deadline(self, slot: Slot) -> Millis:
        # 2/4 of a slot interval
        return get_slot_start_time(slot, self.genesis_time) + 2 * SLOTS_PER_SECOND * 1000 // 4

    def get_attester_votes_before_deadline(
        self, slot: Slot, deadline: Millis
    ) -> set[AvailableChainVote]:
        return {
            vt.vote for vt in self.attester_votes if vt.vote.slot == slot and vt.time < deadline
        }

    def get_proposal_votes_before_deadline(
        self,
        block_slot: Slot,
        vote_slot: Slot,
        deadline: Millis,
    ) -> set[AvailableChainVote]:
        votes: set[AvailableChainVote] = set()
        # Votes targeting vote_slot from the blocks
        # proposed in the block_slot before the deadline
        for block in (
            bt.block for bt in self.blocks if bt.block == block_slot and bt.time < deadline
        ):
            votes.update([v for v in block.body.available_chain_votes if v.slot == vote_slot])
        return votes

    def get_proposer_view_votes(self) -> set[AvailableChainVote]:
        previous_slot = get_previous_slot(self.time, self.genesis_time)
        current_slot = get_current_slot(self.time, self.genesis_time)
        current_slot_start = get_slot_start_time(current_slot, self.genesis_time)

        # Previous slot votes received before the start of the current slot
        return self.get_attester_votes_before_deadline(previous_slot, current_slot_start)

    def get_attester_view_votes(self) -> set[AvailableChainVote]:
        current_slot = get_current_slot(self.time, self.genesis_time)
        previous_slot = get_previous_slot(self.time, self.genesis_time)
        freeze_deadline = self.compute_freeze_deadline(previous_slot)
        attester_votes = self.get_attester_votes_before_deadline(
            slot=previous_slot, deadline=freeze_deadline
        )
        proposal_votes = self.get_proposal_votes_before_deadline(
            block_slot=current_slot,
            vote_slot=previous_slot,
            deadline=self.time,
        )

        # Previous slot votes received before the confirmation deadline
        # merged with the proposal votes
        return attester_votes & proposal_votes

    def get_confirmed_view_votes(self, target_slot: Slot) -> set[AvailableChainVote]:
        current_slot = get_current_slot(self.time, self.genesis_time)
        confirmation_deadline = self.compute_confirmation_deadline(target_slot)

        # target_slot votes before the confirmation deadline
        attester_votes = self.get_attester_votes_before_deadline(
            slot=target_slot, deadline=confirmation_deadline
        )
        # target_slot votes from current_slot blocks received before the confirmation deadline
        proposal_votes = self.get_proposal_votes_before_deadline(
            block_slot=current_slot,
            vote_slot=target_slot,
            deadline=self.time,
        )
        return attester_votes & proposal_votes

    def compute_weighed_tree(
        self,
        block_tree: BlockTree,
        early_votes: set[AvailableChainVote],
        late_votes: set[AvailableChainVote],
        equivocating_indices: set[ValidatorIndex],
    ) -> WeighedTree:
        def get_vote_score() -> UInt64:
            # Each vote has a score of 1
            return UInt64(1)

        # Compute equivocating score
        equivocating_weight = sum(get_vote_score() for idx in equivocating_indices)
        non_equivocating_late_weight = sum(
            get_vote_score()
            for vote in late_votes
            if vote.validator_index not in equivocating_indices
        )
        # Equivocating weight plus total weight contributed
        # by non-equivocating validators from the late set
        total_weight = UInt64(equivocating_weight + non_equivocating_late_weight)

        # Initialize the tree
        current_slot = get_current_slot(self.time, self.genesis_time)
        tree = initialize_weighed_tree(
            block_tree=block_tree,
            # Equivocating weight is added to each node
            initial_node_weight=equivocating_weight,
            # Either weight > total / 2 or a block is from current slot
            is_node_eligible=lambda node: (
                2 * node.weight > total_weight or node.slot == current_slot
            ),
        )

        # Update tree branches with the score contributed
        # by non-equivocating validators from the early set
        non_equivocating_early_votes = {
            vote for vote in early_votes if vote.validator_index not in equivocating_indices
        }
        for vote in non_equivocating_early_votes:
            tree.add_score(vote.root, get_vote_score())

        return tree

    def get_equivocating_indices(self, slot: Slot) -> set[ValidatorIndex]:
        target_votes: set[AvailableChainVote] = set()
        # Votes for target slot came outside of blocks
        target_votes.update(vt.vote for vt in self.attester_votes if vt.vote.slot == slot)
        # And inside of a block
        for bt in self.blocks:
            target_votes.update(
                vote for vote in bt.block.body.available_chain_votes if vote.slot == slot
            )

        vote_count: dict[ValidatorIndex, int] = {}
        for vote in target_votes:
            vote_count[vote.validator_index] = vote_count.get(vote.validator_index, 0) + 1

        # Validators with more than two distinct votes for the target slot
        return {idx for idx, count in vote_count.items() if count > 1}

    def get_proposer_view(self, block_tree: BlockTree) -> ProposerView:
        previous_slot = get_previous_slot(self.time, self.genesis_time)
        equivocating_indices = self.get_equivocating_indices(previous_slot)
        votes = self.get_proposer_view_votes()
        weighed_tree = self.compute_weighed_tree(block_tree, votes, votes, equivocating_indices)
        head_root = weighed_tree.get_head()
        return ProposerView(head_root=head_root, votes=votes)

    def get_attester_view(self, block_tree: BlockTree) -> AttesterView:
        previous_slot = get_previous_slot(self.time, self.genesis_time)
        equivocating_indices = self.get_equivocating_indices(previous_slot)
        votes = self.get_attester_view_votes()
        weighed_tree = self.compute_weighed_tree(block_tree, votes, votes, equivocating_indices)
        head_root = weighed_tree.get_head()
        return AttesterView(head_root=head_root)

    def get_confirmed_view(self, block_tree: BlockTree) -> ConfirmedView:
        previous_slot = get_previous_slot(self.time, self.genesis_time)
        current_slot = get_current_slot(self.time, self.genesis_time)
        equivocating_indices = self.get_equivocating_indices(previous_slot)
        early_votes = self.get_confirmed_view_votes(previous_slot)
        late_votes = self.get_confirmed_view_votes(current_slot)
        weighed_tree = self.compute_weighed_tree(
            block_tree, early_votes, late_votes, equivocating_indices
        )
        return ConfirmedView(confirmed_root=weighed_tree.get_head())
