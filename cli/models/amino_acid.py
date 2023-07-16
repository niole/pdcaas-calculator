class AminoAcid:
    def __init__(self, name, total_protein_g):
        self.name = name
        self.total_protein_g = total_protein_g

    def to_json(self):
        return {
            'name': self.name,
            'total_protein_g': self.total_protein_g
        }
