essential_amino_acids = ["Tryptophan","Threonine","Isoleucine","Leucine","Lysine","Methionine","Phenylalanine","Valine","Histidine"]
EAAS_QUERY_STRING = ','.join(["'" + a + "'" for a in essential_amino_acids])
total_eas_mg_per_kg = 95.5

"""
the essential amino acid proportions are for adults only, https://www.ncbi.nlm.nih.gov/books/NBK234922/table/ttt00008/?report=objectonly
Based on highest estimate of requirement to achieve nitrogen balance. Data from several investigators (reviewed in FAO/WHO, 1973).

maps from amino acid name to the proportion of the amino acid that should be present among all other essential amino acids
for nitrogen balance for an adult to be acheived. It is not clear if this is only for maintaining muscle mass.
"""
EAA_PROPORTIONS = {
    "Tryptophan": 3.5/total_eas_mg_per_kg,
    "Threonine": 7/total_eas_mg_per_kg,
    "Isoleucine": 10/total_eas_mg_per_kg,
    "Leucine": 14/total_eas_mg_per_kg,
    "Lysine": 12/total_eas_mg_per_kg,
    "Methionine": 13/total_eas_mg_per_kg,
    "Phenylalanine": 14/total_eas_mg_per_kg,
    "Valine": 10/total_eas_mg_per_kg,
    "Histidine": 12/total_eas_mg_per_kg
}
