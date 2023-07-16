"""
the scored ingredient
"""
class Ingredient:
    def __init__(self, name, food_match_name, food_match_id, td_score, total_protein_g, amount, unit, aas = []):
        self.name = name
        self.food_match_id = food_match_id
        self.food_match_name = food_match_name
        self.aas = aas
        self.total_protein_g = total_protein_g
        self.td_score = td_score
        self.amount = amount
        self.unit = unit

    def food_match(self):
        return {
            'id': self.food_match_id,
            'name': self.food_match_name,
        }

    def to_json(self):
        return {
            'name': self.name,
            'food_match': self.food_match(),
            'total_protein_g': self.total_protein_g,
            'td': self.td_score,
            'amount': self.amount,
            'unit': self.unit,
            'aas': [a.to_json() for a in self.aas],
        }
