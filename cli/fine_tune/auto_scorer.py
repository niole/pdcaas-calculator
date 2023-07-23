import traceback
from noop_cache import NoopCache

"""
match iterator returns predetermined scores in form of (match, 0 or 1)
"""
class AutoScorer:
    def __init__(self, cache, query, matches, out):
        self.cache = cache
        if cache is None:
            self.cache = NoopCache()
        self.query = query
        self.matches = matches
        self.out = out

    def run(self):
        for query in self.query():
            if not self.cache.contains(query):
                for match in self.matches(query):
                    try:
                        self.out((query, match[0], match[1]))
                    except Exception as e:
                        traceback.print_exc()
                        print(e)
                self.cache.add(query)
