import logging
import re
import multiprocessing
from conversions_map import CONVERSIONS, UNIT_GROUPS

logger = multiprocessing.get_logger()
logger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.WARNING)

def clean_units(units):
    for ug in UNIT_GROUPS:
        for u in ug:
            same = have_same_units(units, u)
            if same:
                return u
    return units

def match_unit(unit, s):
    p = f"(\s+|^)({unit})(\s*|s)(\s*|$)"
    m = re.search(p, s)
    if m is not None:
        matches = m.groups()
        return matches[1]
    return None

"""
if the strings contain the same kind of units and don't contain any quanitfiers in front of the unit or any additional units (except 1), they are the same
"""
def have_same_units(input1, input2):
    s1 = input1.lower()
    s2 = input2.lower()
    no_additional_units = True
    no_quantifiers = True

    for ug in UNIT_GROUPS:
        s1_matches = False
        s2_matches = False
        for unit in ug:
            possible_s1_match = match_unit(unit, s1)
            possible_s2_match = match_unit(unit, s2)

            if possible_s1_match:
                s1_matches = True
            if possible_s2_match:
                s2_matches = True

        if s1_matches and s2_matches:
            return True

        elif not (not s1_matches and not s2_matches):
            # if 1 of them matches, but the other doesn't, we are also done: "not a match"
            return False

    return False

"""
This will see if the requested_units and units are the same by doing cosin similarity on them. If they are not the same,
then this will iterate through the conversions that exist for units to see if any of them match requested_units via cosin sim

requested_units - the units that are found in the recipe
units - units that we have a "to grams" conversion for with regards to the food item that corresponds to the ingredient

returns - a scalar, with which to multiply the ingredient's quantity in order to convert it from "requested_units" to "units"
"""
def get_measure_conversion(requested_units, units):
    cleaned_units = clean_units(units)
    same = have_same_units(requested_units, cleaned_units)
    if same:
        # requested_units is the same as units
        return 1
    else:
        # see if there's anything that units can convert to is simliar to requested_units
        if cleaned_units in CONVERSIONS:
            for possible_unit in CONVERSIONS[cleaned_units]:
                same = have_same_units(requested_units, possible_unit[0])
                if same:
                    return 1/possible_unit[1]
    return None

"""
Gets the weight in grams of the ingredient

ingredient_units  -  The units of the ingredient in the recipe
ingredient_amount - The amount of the ingredient in the recipe
possible_measure_unit - Units of a measure that we have a conversion to grams for this ingredient
possible_measure_weight - The weight of 1 unit of the possible measure in grams

returns - the weight in grams of this ingredient
"""
def get_gram_weight(food_name, ingredient_units, ingredient_amount, possible_measure_unit, possible_measure_weight):
    logger.warning(f"get_gram_weight {food_name}, {ingredient_units}, {ingredient_amount}, {possible_measure_unit}, {possible_measure_weight}")
    conversion = get_measure_conversion(ingredient_units, possible_measure_unit)
    if conversion is not None:
        return conversion * float(possible_measure_weight) * float(ingredient_amount)
    else:
        # 1 off checks against food_name
        is_bread = re.search(r'bread', food_name, re.IGNORECASE)
        is_bacon = re.search(r'bacon', food_name, re.IGNORECASE)
        is_egg = re.search(r'egg', food_name, re.IGNORECASE)
        is_yolk = re.search(r'yolk', food_name, re.IGNORECASE)
        is_white = re.search(r'white', food_name, re.IGNORECASE)
        is_slice = re.search(r'slice', ingredient_units, re.IGNORECASE)

        if is_bacon and is_slice:
            # a slice of bacon is 12 grams
            return 12 * ingredient_amount
        elif is_egg:
            if is_white:
                return 33 * ingredient_amount 
            elif is_yolk:
                return 17 * ingredient_amount 
            else:
                return 50 * ingredient_amount 
        elif is_bread and is_slice:
            return 30 * ingredient_amount 

    return None
