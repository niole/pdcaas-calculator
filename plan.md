# UX

User says "give me this kind of meal" and we generate a recipe that fits that description and then we tell you the protein content.

- user input: Make me a balanced <kind> meal for <meal-time>. My bodyweight in kg is <count>.
- Text input data goes to chatgpt, which is prompted to generate meal names and then from the meal name, a couple recipes are generated

what stats?
- total grams of digestible balanced protein
- percent of protein that was digestible and balanced
- report of what amino acids they were deficient in
- recommendation on what foods to eat

# feedback
- no entry for nutritional yeast in food_info_types
- no entry for cashew milk
- we're missing some food items that would be good to have

# TODO
- redo scraping
  - inlcude tags and if we know the site is vegan, we add a vegan tag DONE
  - include descriptions, or a description of the site and add it to every recipe DONE
  - include the recipe's name and replace any identifying text DONE
- parse out ingredient quantities using openai and save on the ingredient json DONE
- get protein analysis and save onto the json
- create new vector index namespace called 'recipes' and embed the json and save the json as metadata in the db
- update the web app to get the recipes that best match the openai generated meal names and render them in the UI
- BUG: olive oil and mayonaise with olive oil match with higher likely hood than just olive oil
- BUG: couldn't find "cheese" or "cheddar" as the food item for good sharp aged white Cheddar, such as Cabot
- BUG: no good units on eggs { "units": "extra-large", "name": "eggs", "total": 5} or bacon  {"units": "slices": "name": "bacon", "total": 3} DONE, fixed with 1 off mappings
- BUG: search for bacon turns up Bacon, mealess as most likely food item, milk is mapped to Milk, human, mature, fluid


id = recipename + origin
embedding
metadata = original recipe JSON, parsed ingredients JSON, protein information?
