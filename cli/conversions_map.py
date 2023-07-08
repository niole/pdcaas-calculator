TBSP_GROUP = ['tbs', 'tbsp', 'tablespoons', 'tablespoon', 'tbsps']
TSP_GROUP = ['tsp', 'teaspoons', 'teaspoon', 'tsps']
CUP_GROUP = ['cup', 'cups', 'cs', 'c']
LB_GROUP = ['pound', 'lb', 'lbs', 'pounds']
OUNCE_GROUP = ['oz', 'ounce', 'ounces']
GRAMS_GROUP = ['g', 'gram', 'grams']

UNIT_GROUPS = [
    TBSP_GROUP,
    TSP_GROUP,
    CUP_GROUP,
    LB_GROUP,
    OUNCE_GROUP,
    GRAMS_GROUP,
]
GRAMS_IN_LB = 453.6
GRAMS_IN_OUNCE = 28.34
TSP_IN_OUNCE = 6
TBSP_IN_OUNCE = 2
OUNCE_IN_CUP = 8


"""
This map's keys are many units and their various spellings and the values are
lists of other units and their various likely spellings and scalars that you would
multiply by in order to convert from the units of the key, to the units of the entrie

map[unit string] = (unit string, scalar)[]
"""
CONVERSIONS = {}

for e in TBSP_GROUP:
    CONVERSIONS[e] = [(l, 3) for l in TSP_GROUP] + \
    [(l, 1/16) for l in CUP_GROUP] + \
    [(l, 1) for l in TBSP_GROUP] + \
    [(l, 1/TBSP_IN_OUNCE) for l in OUNCE_GROUP] + \
    [(l, 1/(TBSP_IN_OUNCE*16)) for l in LB_GROUP] + \
    [(l, GRAMS_IN_OUNCE/TBSP_IN_OUNCE) for l in GRAMS_GROUP]
for e in TSP_GROUP:
    CONVERSIONS[e] = [(l, 1/3) for l in TBSP_GROUP] + \
    [(l, 1/48) for l in CUP_GROUP] + \
    [(l, 1) for l in TSP_GROUP] + \
    [(l, 1/(3*TBSP_IN_OUNCE)) for l in OUNCE_GROUP] + \
    [(l, 1/(3*TBSP_IN_OUNCE*16)) for l in LB_GROUP] + \
    [(l, GRAMS_IN_OUNCE/6) for l in GRAMS_GROUP]
for e in CUP_GROUP:
    CONVERSIONS[e] = [(l, 16) for l in TBSP_GROUP] + \
    [(l, 48) for l in TSP_GROUP] + \
    [(l, 1) for l in CUP_GROUP] + \
    [(l, 8) for l in OUNCE_GROUP] + \
    [(l, 1/2) for l in LB_GROUP] + \
    [(l, 8*GRAMS_IN_OUNCE) for l in GRAMS_GROUP]
for e in LB_GROUP:
    CONVERSIONS[e] = [(l, 16) for l in OUNCE_GROUP] + \
    [(l, GRAMS_IN_LB) for l in GRAMS_GROUP] + \
    [(l, 1) for l in LB_GROUP] + \
    [(l, 2*3*16) for l in TSP_GROUP] + \
    [(l, 2) for l in CUP_GROUP] + \
    [(l, 32) for l in TBSP_GROUP]
for e in OUNCE_GROUP:
    CONVERSIONS[e] = [(l, 1/16) for l in LB_GROUP] + \
    [(l, GRAMS_IN_OUNCE) for l in GRAMS_GROUP] + \
    [(l, 1) for l in OUNCE_GROUP] + \
    [(l, 6) for l in TSP_GROUP] + \
    [(l, 1/8) for l in CUP_GROUP] + \
    [(l, 2) for l in TBSP_GROUP]

for e in GRAMS_GROUP:
    CONVERSIONS[e] = [(l, 1/GRAMS_IN_LB) for l in LB_GROUP] + \
    [(l, 1/GRAMS_IN_OUNCE) for l in OUNCE_GROUP] + \
    [(l, 1) for l in GRAMS_GROUP] + \
    [(l, 6/GRAMS_IN_OUNCE) for l in TSP_GROUP] + \
    [(l, 1/(8*GRAMS_IN_OUNCE)) for l in CUP_GROUP] + \
    [(l, 2/GRAMS_IN_OUNCE) for l in TBSP_GROUP]

