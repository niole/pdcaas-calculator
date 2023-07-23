import traceback
from fine_tune.noop_cache import NoopCache

"""
choose where unprocessed data lives, how to save state of what has already been processed
- you might want it to be in a database, you might have it in a file
- maybe we save a set somewhere, it can be in memory or in a database. if in a database, you have to write the connector

everything's a yield/iterator

Provides an interactive cli where a user is prompted with a pair of a query and a match
and then they respond with custom inputs, enter or the letter d in order to move on to the next query

cache - previously seen queries are added to. This cache is checked in order to ensure that
the same queries aren't score twice.
query - a function, which returns an iterator of queries, which must be human readable.
matches - a function, which takes a query and returns an iterator of matches, which must be human readable.
scores - a list of valid scores
score_parser - a function that takes a string, which is a score that the user provided via the command line and parses it correctly
out - a function that takes a (query, match, score) triplet and saves it somewhere
max_input_failures - the maximum number of unexpected failures in a row, defaults to 10
"""
class InteractiveDataPairScorer:
    def __init__(self, cache, query, matches, scores, score_parser, out, max_input_failures = 10):
        self.cache = cache
        if cache is None:
            self.cache = NoopCache()

        self.query = query
        self.matches = matches
        self.scores = scores
        self.score_parser = score_parser
        self.out = out
        self.max_input_failures = max_input_failures

    def run(self):
        for query in self.query():
            try:
                if not self.cache.contains(query):
                    for match in self.matches(query):
                        should_move_on = False

                        score = ""
                        failure_count = 0

                        while score not in self.scores:
                            if failure_count == self.max_input_failures:
                                print(f"Failed the max amount of times for {query} : {match}. Moving on.")
                                break

                            try:
                                raw_score = input(f"{query} : {match} ?")

                                if raw_score == "d":
                                    should_move_on = True
                                    break
                                else:
                                    score = self.score_parser(raw_score)
                            except Exception as e:
                                traceback.print_exc()
                                print(f"Something went wrong when accepting input: {e}")
                                failure_count += 1

                        if should_move_on:
                            break

                        self.out((query, match, score))
                    self.cache.add(query)
                    self.cache.maybe_backup()
            except Exception as e:
                traceback.print_exc()
                print(f"Something went wrong while generating data for {query}: {e}")

        self.cache.backup()
