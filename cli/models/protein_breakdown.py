from essential_amino_acid_utils import EAA_PROPORTIONS


class ProteinBreakdown:
    def __init__(self, ingredients):
        self.percent_complete_digestible_protein = None
        self.total_complete_digestible_protein_g = None
        self.total_protein_g = None
        self.ingredient_summaries = None

        self._build_breakdown(ingredients)

    def _build_breakdown(self, ingredients):
        total_achievable_protein_g = 0
        protein_g = 0
        ingredient_summaries = []

        for ingredient in ingredients:
            total_achievable_protein_food_g = 0

            ingredient_summaries.append(IngredientProteinSummary(ingredient))

            total_achievable_protein_g += total_achievable_protein_food_g
            protein_g += ingredient.total_protein_g

        self.ingredient_summaries = ingredient_summaries
        self.percent_complete_digestible_protein = total_achievable_protein_g/protein_g
        self.total_complete_digestible_protein_g = total_achievable_protein_g
        self.total_protein_g = protein_g

    def is_scored(self):
        unscored_summaries = [s for s in self.ingredient_summaries if not s.is_scored()]
        return len(unscored_summaries) == 0

    def to_json(self):
        return {
            "percent_complete_digestible_protein": self.percent_complete_digestible_protein,
            "total_complete_digestible_protein_g": self.total_complete_digestible_protein_g,
            "total_protein_g": self.total_protein_g,
            "ingredient_summaries": [i.to_json() for i in self.ingredient_summaries],
        }

class IngredientProteinSummary:
    def __init__(self, ingredient):
        self.ingredient_name = ingredient.name
        self.food_match = ingredient.food_match()
        self.limiting_aa_details = self._get_limiting_aa(ingredient)
        self.total_protein_g = ingredient.total_protein_g
        self.total_balanced_protein_g = None
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
            "limiting_aa_details": limiting_aa_details,
            "total_protein_g": self.total_protein_g,
            "total_balanced_protein_g": self.total_balanced_protein_g,
            "aas": [a.to_json() for a in self.aas],
        }

    def _build(self, ingredient):
        if self.limiting_aa_details is not None:
            limiting_aa = self.limiting_aa_details.name
            total_limiting_aa_g = self.limiting_aa_details.total_protein_g
            self.total_achievable_protein_food_g = ingredient.td_score * min(total_limiting_aa_g / EAA_PROPORTIONS[limiting_aa], ingredient.total_protein_g)

    def _get_limiting_aa(self, ingredient):
        # calculating percentage complete protein
        # if an aa comes in low w/ respect to total protein, then it is a limiting factor
        # a limiting aa is one that when considered in proportion to the total amount of protein, has the lowest score

        total_protein_g = ingredient.total_protein_g
        percent_expected = []
        for aa in ingredient.aas:
            # the expected proportion of the ingredients protein in order for it to be complete
            expected = EAA_PROPORTIONS[aa.name]*total_protein_g
            actual = aa.total_protein_g
            if actual > 0 and expected > 0:
                percent_expected.append((aa.name, actual/expected))
            else:
                percent_expected.append((aa.name, 0))

        if len(percent_expected) > 0:
            limiting_aa = min(percent_expected, key = lambda k: k[1])[0]
            return next((a for a in ingredient.aas if a.name == limiting_aa), None)
        return None

