import logging
import re
import multiprocessing
from pinecone_client import find_limit_vector_query
from conversions_map import CONVERSIONS, LB_GROUP, OUNCE_GROUP

logger = multiprocessing.get_logger()
logger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.WARNING)

def test_get_gram_weight():
    food_name = 'sugar'
    actual = get_gram_weight(food_name, 'oz', 8, 'g', 10)
    expected = 28.34 * 8 * 10
    assert(actual == expected)

    actual2 = get_gram_weight(food_name, 'tsps', 2.5, 'cups', 4)
    expected2 = 1/48 * 2.5 * 4
    assert(actual2 == expected2)

    actual3 = get_gram_weight(food_name, 'cup', 2.5, 'teaspoon', 4)
    expected3 = 48 * 2.5 * 4
    assert(actual3 == expected3)

    actual4 = get_gram_weight(food_name, 'tablespoon', 2.5, 'tsp', 4)
    expected4 = 3 * 2.5 * 4
    assert(actual4 == expected4)

    actual5 = get_gram_weight(food_name, 'g', 8, 'ounces', 10)
    expected5 = 1/28.34 * 8 * 10
    assert(actual5 == expected5)

    actual6 = get_gram_weight(food_name, 'pound', 8, 'ounce', 10)
    expected6 = 16 * 8 * 10
    assert(actual6 == expected6)

    actual7 = get_gram_weight(food_name, 'oz', 8, 'lb', 10)
    expected7 = 1/16 * 8 * 10
    assert(actual7 == expected7)

    actual8 = get_gram_weight('brocolini', 'pounds', 5.5, 'grams', 1)
    expected8 = 453.6 * 5.5
    assert(actual8 == expected8)

"""
requested_units - the units that are found in the recipe
units - units that we have a "to grams" conversion for with regards to the food item that corresponds to the ingredient

returns - a scalar, with which to multiply the ingredient's quantity in order to convert it from "requested_units" to "units"
"""
def get_measure_conversion(requested_units, units):
    # check to see if the requested units could be real
    likely_measures = find_limit_vector_query(requested_units, 5, 'measures')
    match = next((m for m in likely_measures if m['score'] >= 0.7), None)
    # check to see if the found
    # weight matches the known weights
    if match is not None:
        matched_unit = match['id']

        if matched_unit in CONVERSIONS:
            conversions = CONVERSIONS[matched_unit]
            conversion = next(
                (c for c in conversions if c[0] == units),
                None
            )
            if conversion is not None:
                return conversion[1]
            else:
                # convert straight to grames, even though might be inaccurate
                direct_grams_conversion = next((c for c in conversions if c[0] == 'g'), None)
                if direct_grams_conversion is not None:
                    return direct_grams_conversion[1]

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
        return conversion * possible_measure_weight * ingredient_amount
    else:
        # TODO do 1 off checks against food_name
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


if __name__ == '__main__':
    test_get_gram_weight()
