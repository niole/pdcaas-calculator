from interactive_data_pair_scorer import InteractiveDataPairScorer

"""
Provides an interaction command line program that lets the user score pairs of queries and matches as 0 or 1

cache - previously seen queries are added to. This cache is checked in order to ensure that
the same queries aren't score twice.
query - a function, which returns an iterator of queries, which must be human readable.
matches - a function, which takes a query and returns an iterator of matches, which must be human readable.
out - a function that takes a (query, match, score) triplet and saves it somewhere
"""
class InteractiveDataPairMembershipScorer(InteractiveDataPairScorer):
    def __init__(self, cache, query, matches, out):
        super().__init__(cache, query, matches, [0, 1], self._score_parser, out)

    def _score_parser(self, score):
        if score == "":
            return 0
        return int(score)

    def run(self):
        super().run()

