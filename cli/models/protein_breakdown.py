from essential_amino_acid_utils import EAA_PROPORTIONS


class ProteinBreakdown:
    def __init__(self, ingredients):
        self.total_complete_digestible_protein_g = None
        self.total_protein_g = None
        self.total_eaa_g = None
        self.limiting_amino_acid_name = None
        self.limiting_amino_acid_g = None
        self.essential_amino_acid_g = []
        self.ingredient_summaries = None

        self._build_breakdown(ingredients)

    def _build_breakdown(self, ingredients):
        total_achievable_protein_g = 0
        protein_g = 0
        ingredient_summaries = []
        total_eaa_g = 0
        eaa_gs = dict([(eaa, 0) for eaa in EAA_PROPORTIONS.keys()])

        for ingredient in ingredients:
            protein_summary = IngredientProteinSummary(ingredient)
            ingredient_summaries.append(protein_summary)

            protein_g += protein_summary.total_protein_g
            total_eaa_g += protein_summary.total_eaa_g

            for aa in ingredient.aas:
                # add in td score now, only add to the amino acid data, because
                # that will be used to calculate real protein
                eaa_gs[aa.name] += aa.total_protein_g * protein_summary.td

        total_eaa_g = sum(eaa_gs.values())
        # get the limiting amino acid and total digestible protein

        lowest_aa = None
        lowest_aa_frac_of_expected = None
        if total_eaa_g > 0:
            for (name, gs) in eaa_gs.items():
                frac = gs/total_eaa_g
                if lowest_aa_frac_of_expected is None or frac < lowest_aa_frac_of_expected:
                    lowest_aa = name
                    lowest_aa_frac_of_expected = frac

        if lowest_aa is not None:
            self.limiting_amino_acid_name = lowest_aa
            self.limiting_amino_acid_g = eaa_gs[lowest_aa]
            self.total_complete_digestible_protein_g = eaa_gs[lowest_aa]/EAA_PROPORTIONS[lowest_aa]

        self.ingredient_summaries = ingredient_summaries
        self.total_protein_g = protein_g
        self.total_eaa_g = total_eaa_g
        self.essential_amino_acid_g = eaa_gs

    def is_scored(self):
        unscored_summaries = [s for s in self.ingredient_summaries if not s.is_scored()]
        return len(unscored_summaries) == 0

    def to_json(self):
        result = {
            "total_complete_digestible_protein_g": self.total_complete_digestible_protein_g,
            "total_protein_g": self.total_protein_g,
            "total_eaa_g": self.total_eaa_g,
            "limiting_amino_acid_name": self.limiting_amino_acid_name,
            "limiting_amino_acid_g": self.limiting_amino_acid_g,
            "ingredient_summaries": [i.to_json() for i in self.ingredient_summaries],
        }

        for (name, g) in self.essential_amino_acid_g.items():
            result[f"digestible_eaa_{name}_g"] = g

        return result

class IngredientProteinSummary:
    def __init__(self, ingredient):
        self.ingredient_name = ingredient.name
        self.food_match = ingredient.food_match()
        self.total_eaa_g = self._get_total_eaa_g(ingredient)
        self.limiting_aa_details = self._get_limiting_aa(ingredient)
        self.total_protein_g = ingredient.total_protein_g
        self.total_achievable_protein_food_g = None
        self.td = ingredient.td_score
        self.aas = ingredient.aas

        self._build(ingredient)

    def is_scored(self):
        if self.total_protein_g > 0:
            return self.limiting_aa_details is not None

        return True

    def to_json(self):
        limiting_aa_details = None
        if self.limiting_aa_details is not None:
            limiting_aa_details = self.limiting_aa_details.to_json()

        return {
            "name": self.ingredient_name,
            "food_match": self.food_match,
            "is_scored": self.is_scored(),
            "limiting_aa_details": limiting_aa_details,
            "total_protein_g": self.total_protein_g,
            "total_achievable_protein_food_g": self.total_achievable_protein_food_g,
            "total_eaa_g": self.total_eaa_g,
            "td": self.td,
            "aas": [a.to_json() for a in self.aas],
        }

    def _build(self, ingredient):
        if self.limiting_aa_details is not None:
            limiting_aa = self.limiting_aa_details.name
            total_limiting_aa_g = self.limiting_aa_details.total_protein_g

            self.total_achievable_protein_food_g = ingredient.td_score * total_limiting_aa_g / EAA_PROPORTIONS[limiting_aa]
        elif self.total_protein_g > 0:
            self.total_achievable_protein_food_g = ingredient.td_score * self.total_protein_g

    """
    verifies that all essential amino acid data exists
    """
    def _verify_eaa_data(self, ingredient) -> bool:
        aa_names = [a.name for a in ingredient.aas]
        return all([key in aa_names for key in EAA_PROPORTIONS.keys()])

    def _get_total_eaa_g(self, ingredient):
        eaas = [aa for aa in ingredient.aas if aa.name in EAA_PROPORTIONS.keys()]
        return sum([aa.total_protein_g for aa in eaas])

    """
    finds the amino acid whose proportional amount is lower that it should be in comparison
    to the amounts of all essential amino acids
    """
    def _get_limiting_aa(self, ingredient):
        lowest_aa = None
        if self._verify_eaa_data(ingredient) and self.total_eaa_g > 0:
            eaas = [aa for aa in ingredient.aas if aa.name in EAA_PROPORTIONS.keys()]

            lowest_aa = None
            lowest_aa_frac_of_expected = None
            for aa in eaas:
                frac = aa.total_protein_g/self.total_eaa_g
                if lowest_aa_frac_of_expected is None or frac < lowest_aa_frac_of_expected:
                    lowest_aa = aa
                    lowest_aa_frac_of_expected = frac
        return lowest_aa
