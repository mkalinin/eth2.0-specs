from dataclasses import dataclass

from .block_tree import BlockTree
from .preset import ROUNDS_IN_EXPIRY_WINDOW
from .round import EMPTY_ROUND, get_current_round
from .type import Millis, Root, Round, UInt64, ValidatorIndex
from .validator_set import ValidatorSet
from .vote import StabilizationVote
from .weighed_tree import initialize_weighed_tree, WeighedTree
from .state_transition import BeaconBlock


@dataclass
class StabilizationView:
    anchor_root: Root


@dataclass
class VoteAndTimestamp:
    vote: StabilizationVote
    time: Millis


@dataclass
class StabilizationStore:
    time: Millis
    genesis_time: Millis
    votes: list[set[VoteAndTimestamp]]

    def process_tick(self, time: Millis) -> None:
        self.time = time

    def process_vote(self, vote: StabilizationVote) -> None:
        if vote.round >= len(self.votes):
            self.votes.append(set())
        self.votes[vote.round].add(VoteAndTimestamp(vote, self.time))

    def process_block(self, block: BeaconBlock) -> None:
        pass

    def get_latest_round(self, validator_index: ValidatorIndex) -> Round:
        current_round = get_current_round(self.time, self.genesis_time)
        earliest_round = (
            Round(0)
            if current_round < ROUNDS_IN_EXPIRY_WINDOW
            else current_round - ROUNDS_IN_EXPIRY_WINDOW
        )
        latest_round = EMPTY_ROUND
        for r in range(earliest_round, current_round):
            if any(vt.vote.validator_index == validator_index for vt in self.votes[r]):
                latest_round = r

        return latest_round

    def get_validator_votes_in_round(
        self, validator_index: ValidatorIndex, round: Round
    ) -> list[StabilizationVote]:
        return [vt.vote for vt in self.votes[round] if vt.vote.validator_index == validator_index]

    def compute_weighed_tree(
        self,
        block_tree: BlockTree,
        validator_set: ValidatorSet,
    ) -> WeighedTree:
        # Validators submitted at least one vote during eligible rounds
        voters = {
            idx
            for idx in validator_set.get_active_validators()
            if self.get_latest_round(idx) != EMPTY_ROUND
        }

        # Total balance of the voters
        total_weight = UInt64(sum(validator_set.get_balance(idx) for idx in voters))

        # Initialize the tree
        tree = initialize_weighed_tree(
            block_tree=block_tree,
            initial_node_weight=UInt64(0),
            # weight > total / 2
            is_node_eligible=lambda node: 2 * node.weight > total_weight,
        )

        # Update tree branches with the balance of validators
        # supporting a block during their latest round
        # and hasn't equivocated in that round
        for index in voters:
            latest_round = self.get_latest_round(index)
            votes = self.get_validator_votes_in_round(index, latest_round)
            # Submitted more than one distinct vote
            is_equivocating = len(votes) > 1
            if not is_equivocating:
                vote = votes[0]
                tree.add_score(vote.root, validator_set.get_balance(index))

        return tree

    def get_stabilization_view(
        self,
        block_tree: BlockTree,
        validator_set: ValidatorSet,
    ) -> StabilizationView:
        weighed_tree = self.compute_weighed_tree(block_tree, validator_set)
        head_root = weighed_tree.get_head()
        return StabilizationView(anchor_root=head_root)
