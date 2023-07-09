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
- try the open ai functions API to do parsing into JSON repsonse
- try different sentence embedding library to see if we get better food item matching
- put food items into db: cassava flour, nutritional yeast
- create new vector index namespace called 'recipes' and embed the json and save the json as metadata in the db
- update the web app to get the recipes that best match the openai generated meal names and render them in the UI

# Bugs
- olive oil and mayonaise with olive oil match with higher likely hood than just olive oil
- couldn't find "cheese" or "cheddar" as the food item for good sharp aged white Cheddar, such as Cabot
- search for bacon turns up Bacon, mealess as most likely food item, milk is mapped to Milk, human, mature, fluid
- no entry for almond flour
- no entry for almond milk there is "milk imitation non-soy": 43543
- sunflower seeds maps to lotus seeds, maybe remove the lotus seed entry? 12205 
- entry for brown rice syrup?
- hazelnuts -> hazel nut oil
- salt and peper to raw banana pepper, maybe could remove extraneous words like "good" and "raw", maybe could map any nut milk to the imitation milk...or add own entries
- non-dary milk confuses cli
- matches coconut oil instead of coconut milk


id = recipename + origin
embedding
metadata = original recipe JSON, parsed ingredients JSON, protein information?
