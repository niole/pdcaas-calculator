import { OpenAIEmbeddings } from "langchain/embeddings/openai";
import { findLimitVectorQuery } from 'pineconeClient';

const embeddings = new OpenAIEmbeddings({
  openAIApiKey: process.env.OPENAI_API_KEY, // In Node.js defaults to process.env.OPENAI_API_KEY
});

const ESSENTIAL_AMINO_ACIDS = ["Tryptophan","Threonine","Isoleucine","Leucine","Lysine","Methionine","Phenylalanine","Valine","Histidine"];
const EAAS_QUERY_STRING = ESSENTIAL_AMINO_ACIDS.map(a => `'${a}`).join(',');
const EAA_PROPORTIONS: { [key: string]: number } = {
    "Tryptophan": 7/1000,
    "Threonine": 27/1000,
    "Isoleucine": 25/1000,
    "Leucine": 55/1000,
    "Lysine": 51/1000,
    "Methionine": 25/1000,
    "Phenylalanine": 47/1000,
    "Valine": 32/1000,
    "Histidine": 18/1000
}
type Recipe = {
  total_servings: number,
  ingredients: {units: string, "name": string, "total": number}[],
  instructions: string,
};
type DomainAA = { name: string, per100g: number };
type AA = { name: string, total_protein_g: number };
type Ingredient = {
  name: string,
  total_protein_g: number
  food_query: string,
  aas: AA[],
  td: number,
};

const createAa = (name: string, total_per100g: number, total_g_ing: number): AA => ({
        'name': name,
        'total_protein_g': total_g_ing*total_per100g/100
    });

const createIngredient = (food_query: string, name: string, total_protein: number, td: number = 1, aas: AA[] = []): Ingredient => ({
        'name': name,
        'food_query': food_query,
        'aas': aas,
        'total_protein_g': total_protein,
        'td': td
    });

const setTd = (ingredient: Ingredient, td_score: number): Ingredient => {
  // set TD score for ingredient
  ingredient['td'] = td_score;
  return ingredient;
};

const createInitialIngredient = (food_query: string, name: string, total_protein: number, total_g_ing: number, aas: DomainAA[]): Ingredient => {
  const aas_final = aas.map(f =>
    createAa(f.name, f.per100g, total_g_ing)
  );
  return createIngredient(food_query, name, total_protein, 1, aas_final);
};

const getLimitingAa = (ingredient: Ingredient): AA | undefined => {
  // calculating percentage complete protein
  // if an aa comes in low w/ respect to total protein, then it is a limiting factor
  // a limiting aa is one that when considered in proportion to the total amount of protein, has the lowest score

  const percent_expected = ingredient.aas.map(aa => {
      // the expected proportion of the ingredients protein in order for it to be complete
      const expected = EAA_PROPORTIONS[aa.name]*ingredient.total_protein_g;
      const actual = aa.total_protein_g;
      if (actual > 0 && expected > 0) {
          return [aa.name, actual/expected];
    } else {
        return [aa.name, 0];
    }
  });

  if (percent_expected.length > 0) {
    const limiting_aa = Math.min(percent_expected.map((p: [string, number]) => p[1]))[0];
    return ingredient.aas.find(a => a.name == limiting_aa);
  }
  return;
};

type AASummary = {
  name: string,
  limiting_aa_details: AA,
  total_protein_g: number,
  total_balanced_protein_g: number,
  aas: AA[],
};

type RecipeSummary = {
  percent_complete_digestible_protein: number,
  total_complete_digestible_protein_g: number,
  total_protein_g: number,
  ingredient_summaries: AASummary[],
};

/**
This calculates the protein balance for all ingredients and returns the percent of consumed
protein that is digestible and balanced protein from the essential amino acids.
*/
const calculatedPercentDigestibleProtein = (ingredients: Ingredient[]): RecipeSummary => {
  let total_achievable_protein_g = 0;
  let protein_g = 0;

  if (ingredients.length == 0) {
      return {
        "percent_complete_digestible_protein": 0,
        "total_complete_digestible_protein_g": 0,
        "total_protein_g": 0,
        "ingredient_summaries": [],
      };
  }

  const ingredient_summaries = ingredients.map(ingredient => {
    const limiting_aa_details = getLimitingAa(ingredient);
    let limiting_aa;
    let total_limiting_aa_g = 0;
    let total_achievable_protein_food_g = 0;

    if (limiting_aa_details) {
        limiting_aa = limiting_aa_details['name']

        // calculate the total digestible complete protein by dividing the limiting aa by its proportion
        total_limiting_aa_g = limiting_aa_details['total_protein_g'];
        total_achievable_protein_food_g = ingredient['td'] * Math.min(total_limiting_aa_g / EAA_PROPORTIONS[limiting_aa], ingredient['total_protein_g']);
    }

    total_achievable_protein_g += total_achievable_protein_food_g
    protein_g += ingredient['total_protein_g']

    return {
        'name': ingredient['name'],
        'limiting_aa_details': limiting_aa_details,
        'total_protein_g': ingredient['total_protein_g'],
        'total_balanced_protein_g': total_achievable_protein_food_g,
        'aas': ingredient['aas'],
    };
  });

  return {
      "percent_complete_digestible_protein": total_achievable_protein_g/protein_g,
      "total_complete_digestible_protein_g": total_achievable_protein_g,
      "total_protein_g": protein_g,
      "ingredient_summaries": ingredient_summaries,
  };
};

const getMatchingFoodItems = (query: string): any[] => {
  const ms = findLimitVectorQuery(query, 20, 'info');

  return ms.filter(m => m.score >= 0.6);
};

const getMeasureConversion = (requested_units: string, units: string): number | undefined => {
    /**
    get the conversion multipler to go from total units to the equivalent number of requested_units
    */
    const matches = findLimitVectorQuery(requested_units, 5, 'measures');

    for (let i = 0; i < matches.length; i++) {
      const match = matches[i];
      if (match.id === units || requested_units.indexOf(match.id) > -1) {
          return 1;
      }
    }
    return;
};
/**
This calculates the proportion of protein that is digestible complete protein.
This is calculated for 1 ingredient, however it can be extrapolated to multiple meals.

This takes the gram weight of an ingredient, the gram weight of protein per 100 g of that ingredient,
and the gram weight of each essential amino acid per 100g of that ingredient, and then
the total digestibility score of that ingredient as inputs.
*/


/**
Recipe generation prompt:
give me a recipe for vegan mac and cheese for 1 person. give me the recipe in the following format, JSON only: { "total_servings": 5,  "ingredients": [{"units": "cup", "name": "wheat pasta", "total": 1}, {"units":"tsp", "name":"salt","total": 0.5}, {"units": "lbs", "name": "beef", "total": 1}, {"units": "teaspoon", "name": "mustard", "total": 0.25}, {"units": "tablespoon", "name":"peanut butter", "total": 2}, {"units":"tbsp", "name":"sour cream", "total":1.5}], "instructions": "Boil the pasta for 11 minutes with the salt in water. Serve immediately."}

Recipe name generation prompt:
generate the names of 20 vegan breakfast meals. give the output in the following format, JSON only: ["the name of meal 1", "the name of meal 2", "the name of meal 3"]

pre-generate a bunch of recipes and their amino acid balances

Let the user also put in their own meal names. We can then recommend snacks to round out their amino acid balance.
User can scale the recipes according to their calorie needs through a UI and then we can give better info about total digestible balanced protein. TODO Do we have calorie data?
*/
export const computeRecipeSummary = (recipe: Recipe): RecipeSummary => {
    /**
    for each ingredient in a recipe, find the food entry that best matches it, the td_types entry that best matches it,
    and compute the gram weight

    computing gram weight: if there is a weight entry in cup, tsp, teaspoon, tbsp, tablespoon, we can probably work with that
    find closest match for ingredient in food_info or td_types: put all food names into a collection in a vector db and all td_types in their own collection
    and do a search
    */
  const ingredients = [];
  for (let i = 0; i < recipe.ingredients.length; i++) {
    const ing = recipe['ingredients'][i];
    const food_query = ing['name'];
    const measure_units_query = ing['units'];
    const measure_amount_query = ing['total'];


    // each food item has it's name, id, per 100g stats for protein and amino acids, and the td score
    const food_items = getMatchingFoodItems(food_query);

    if (!food_items.length) {
        console.log(f"Couldn't find a matching food item for query {food_query}");
        continue;
    }

    for (let j = 0; j < food_items.length; j++) {
        const food_item = food_items[j];
        const metadata = food_item['metadata'];
        const protein_per_100g = metadata['protein_per_100g'];
        const food_name = metadata['tmp_name'];
        const aas = metadata['aas'].map(a => JSON.parse(a));
        const weights = metadata['weights'].map(w => json.loads(w));
        const td_score = metadata['td_score'];

        let ingredient;
        let gram_weight;

        for (let w = 0; w < weights.length; w++) {
          const weight = weights[w];
          const conversion = getMeasureConversion(measure_units_query, weight['Msre_Desc']);
          if (conversion) {
              gram_weight = conversion * weight['Gm_Wgt'] * measure_amount_query;
              break
          }
        }

        if (!gram_weight) {
            console.log(`Insufficient weight data. Can't convert ${measure_amount_query} ${measure_units_query} of ${food_query} to grams.`);
            continue;
        }

        // calculate total protein grams in queried amount of food
        const total_protein_ing = gram_weight*protein_per_100g/100;

        ingredient = createInitialIngredient(food_name, food_query, total_protein_ing, gram_weight, aas);
        ingredient['amount'] = measure_amount_query;
        ingredient['unit'] = measure_units_query;

        if (td_score) {
          setTd(ingredient, td_score);
        }

        if (ingredient) {
            ingredients.push(ingredient);
            break
        }
    }
  }

  return calculatedPercentDigestibleProtein(ingredients);
};
