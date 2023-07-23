from get_gram_weight import get_gram_weight

def main():
    food_name = 'sugar'
    actual = get_gram_weight(food_name, ingredient_units='oz', ingredient_amount=8, possible_measure_unit='g', possible_measure_weight='10')
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

    actual9 = get_gram_weight('shredded coconut', 'cup, shredded', 0.5, 'cup', 93)
    assert(actual9 == 46.5)

    actual10 = get_gram_weight('peanut butter', 'cup (125 mL)', 0.5, 'cup', 258)
    assert(actual10 == 129)

    actual11 = get_gram_weight('peanut butter', 'cup', 0.5, 'tbsp', 32)
    assert(actual11 == 256)

if __name__ == "__main__":
    main()
