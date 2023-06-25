# UX

User says "give me this kind of meal" and we generate a recipe that fits that description and then we tell you the protein content.

- user input: Make me a balanced <kind> meal for <meal-time>. My bodyweight in kg is <count>.
- Text input data goes to chatgpt, which is prompted to generate meal names and then from the meal name, a couple recipes are generated
- Each recipe is processed (maybe the recipe scorer is an aws function, so we can parallelize) and then the recipes are returned along with their protein stats.


how to provide meal info?
- user says "give me a meal (plan)" and then we give you one with good amino acid balance

what stats?
- total grams of digestible balanced protein
- percent of protein that was digestible and balanced
- report of what amino acids they were deficient in
- recommendation on what foods to eat

# feedback
- no entry for nutritional yeast in food_info_types
- no entry for cashew milk
- we're missing some food items that would be good to have
- chat gpt is bad at making up recipes
