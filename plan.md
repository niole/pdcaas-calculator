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
- 7/15: train a new sentence transformer that better matches the ingredients in the scraped recipes to the food in the nutritional database and then re-embed the food item vectors into the vector database
- for items that don't have an entry in the food info collection: we might have a recipe for it or find a recipe for it, that we can then calculate info for

the process might look more like
- go through recipe ingredients
- if there isn't an entry in food info types, then maybe there's a recipe for it (almond milk, cashew milk, vegan cream cheese, vegan butter)
- need a fast way to get the recipe for a food item, get the amino acid data for the recipe, then save that amino acid data on a fabricated vector embedding

TODO embed previously scored recipes as food items, ingredients are the results of recipes and good items
This would mean that we have to store some kind of weight data on the recipe, maybe the weight in grams, bc supposedly I would be able to calculate that, the TD score is the digestible protein/total protein, amino acid data could be calculated

when a recipe is successfully scored, it also goes into the "info" namespace,
then for recipes that aren't successfully scored, we could run the script again. Should store the recipes that are "WIP" in sqlite.

a recipe is successfullly scored when all ingredients were completely findable in the "info" namespace and we scored the recipe.

successfully scored recipes are embedded in the "info" namespace as food items

unsuccessfullly scored recipes live in a collection in sqlite called "recipes"....

in order to make sure that we can score things properly, we need to fine-tune the sentence transformer to match ingredients to food in food_info_types

1. fine tune sentence transformer. I think we want to choose a data representation that indicates that something does and does not match, maybe see what the sentence transformer currently scores the thing as and if it's too high and it's wrong, give it a low score. then manually go and find the right match
    - embed recipe names and food items in vector db with basic sentence transformer
    - make fine tuning data: iterate over ingredient names and match them against the top 10 matches in the vector db, manually accept or reject matches, save the accepted and rejected in triplets (ingredient name, food item, 0 | 1)
    - fine tune the model and then proceed to next step

2. re-embed all food_info_types Long_Desc entries into the info namespace with the new model
3. ingest all recipes into sqlite. The recipe data collections will have a notion of successful scoring
    - recipe table: recipe name, id, successfully scored
    - ingredient table: id, recipe id, ingredient name, ingredient unit, ingredient amount, total protein g, successfully scored
    - amino acid table: id, recipe id, amino acid name, total aa g

4. score the recipes, successfully scored recipes will be embedded in the "info" namespace, unsuccessfullly scored recipes will only exist in sqlite
5. run 2 rounds of scoring for the recipes in sqlite, by then you will have the recipes that were immediately scorable and the recipes that are not possible to complete given the state of the food db, the current recipes, the sentence transformer
6. manually evaluate the unsuccessfullly scored recipes


- try the open ai functions API to do parsing into JSON repsonse
- put food items into db: cassava flour, nutritional yeast
- create new vector index namespace called 'recipes' and embed the json and save the json as metadata in the db
- update the web app to get the recipes that best match the openai generated meal names and render them in the UI

# Bugs
- matches oats for rolled oats. Oats has a much higher protein content than rolled oats, so not quite
- fine tune units transformer


id = recipename + origin
embedding
metadata = original recipe JSON, parsed ingredients JSON, protein information?
