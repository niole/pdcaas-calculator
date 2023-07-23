import json
import click
from auto_scorer import AutoScorer
from embed_cache import EmbedArrayCache
from conversions_map import TBSP_GROUP, TSP_GROUP, CUP_GROUP, LB_GROUP, OUNCE_GROUP, GRAMS_GROUP
from pinecone_client import find_limit_vector_query
from interactive_data_pair_membership_scorer import InteractiveDataPairMembershipScorer


class UnitsScorer(AutoScorer):
    def __init__(self, outpath):
        super().__init__(None, self._query, self._matches, self._out)
        self.outpath = outpath

    def _query(self):
        return TBSP_GROUP + TSP_GROUP + CUP_GROUP + LB_GROUP + OUNCE_GROUP + GRAMS_GROUP

    def _all_units(self, without = []):
        return [u for u in TBSP_GROUP + TSP_GROUP + CUP_GROUP + LB_GROUP + OUNCE_GROUP + GRAMS_GROUP if u not in without]

    def _matches(self, query):
        if query in TBSP_GROUP:
            return [(u, 1) for u in TBSP_GROUP] + [(u, 0) for u in self._all_units(TBSP_GROUP)]
        if query in TSP_GROUP:
            return [(u, 1) for u in TSP_GROUP] + [(u, 0) for u in self._all_units(TSP_GROUP)]
        if query in CUP_GROUP:
            return [(u, 1) for u in CUP_GROUP] + [(u, 0) for u in self._all_units(CUP_GROUP)]
        if query in LB_GROUP:
            return [(u, 1) for u in LB_GROUP] + [(u, 0) for u in self._all_units(LB_GROUP)]
        if query in OUNCE_GROUP:
            return [(u, 1) for u in OUNCE_GROUP] + [(u, 0) for u in self._all_units(OUNCE_GROUP)]
        if query in GRAMS_GROUP:
            return [(u, 1) for u in GRAMS_GROUP] + [(u, 0) for u in self._all_units(GRAMS_GROUP)]
        return []

    def _out(self, datum):
        (query, match, score) = datum
        with open(self.outpath, 'a') as file:
            file.write(json.dumps({ "query": query, "match": match, "score": score }) + "\n")

class VectorUnitsScorer(InteractiveDataPairMembershipScorer):
    def __init__(self, outpath):
        super().__init__(None, self._query, self._matches, self._out)
        self.outpath = outpath

    def _query(self):
        return TBSP_GROUP + TSP_GROUP + CUP_GROUP + LB_GROUP + OUNCE_GROUP + GRAMS_GROUP

    def _matches(self, query):
        matches = find_limit_vector_query(query, 15, 'measures')
        return [match['id'] for match in matches]

    def _out(self, datum):
        (query, match, score) = datum
        with open(self.outpath, 'a') as file:
            file.write(json.dumps({ "query": query, "match": match, "score": score }) + "\n")

@click.command()
@click.option("--vector", is_flag=True, default=False)
@click.option("--auto", is_flag=True, default=False)
@click.option('--outpath', '-o', type=str, required=True)
def main(vector, auto, outpath):
    if auto:
        UnitsScorer(outpath).run()

    if vector:
        VectorUnitsScorer(outpath).run()

if __name__ == "__main__":
    main()
