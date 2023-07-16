import logging
from models.protein_breakdown import ProteinBreakdown

"""
the scored recipe
"""
class Recipe:
    def __init__(self, id, title, ingredients = []):
        self.id = id
        self.title = title
        self.ingredients = ingredients
        self.protein_breakdown = None

        self._init_protein_breakdown()

    def _init_protein_breakdown(self):
        if self.ingredients is None:
            logging.warning("Ingredients have not been parsed. Can't create protein breakdown")
        else:
            self.protein_breakdown = ProteinBreakdown(self.ingredients)

    def is_scored(self):
        if self.protein_breakdown is not None:
            return self.protein_breakdown.is_scored()
        return False

    def set_ingredients(self, ingredients):
        self.ingredients = ingredients
        self._init_protein_breakdown()

    def to_json(self):
        return {
            "title": self.title,
            "id": self.id,
            "nutrient_breakdown": { "protein_breakdown": self.protein_breakdown.to_json() },
            "ingredients": [i.to_json() for i in self.ingredients],
        }
