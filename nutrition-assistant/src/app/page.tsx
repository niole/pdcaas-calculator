"use client";
import React from 'react';
import * as R from 'ramda';
import { RecipeNutritionalSummaryCard } from './RecipeNutritionalSummaryCard';
import { RecipeDetailsView } from './RecipeDetailsView';
import { RecipeResponse, RecipeListResponse, RecipeMatchesResponse, RecipeNutritionSummary } from '../utils/recipe-client/index';


const inputClasses = "outline rounded outline-1";

const defaultPreferenceValue = "I want to eat healthy, lots of fruits and veggies.";

const testData = [["Vegan Oatmeal Pancakes",[{"id":"Easy Vegan and Gluten-Free Pancakes (Strawberry Shortcake w/ Whipped Cream)","metadata":{"percent_complete_digestible_protein":0,"total_complete_digestible_protein_g":0,"total_protein_g":33.530260000000006},"score":0.509036779,"values":[]},{"id":"Jumbo Chickpea Pancake - A High Protein, Filling Vegan Breakfast or Lunch!","metadata":{"percent_complete_digestible_protein":0,"total_complete_digestible_protein_g":0,"total_protein_g":11.18518375},"score":0.496326268,"values":[]},{"id":"Healthy Chocolate Chip Cookie Pota'Dough Dip! Vegan, Gluten-Free, Bean-free, Soy-free, and optionally Nut-free.","metadata":{"percent_complete_digestible_protein":0,"total_complete_digestible_protein_g":0,"total_protein_g":20.202009498941422},"score":0.443739474,"values":[]}]],["Tofu Scramble Burrito",[{"id":"High Protein Vegan Breakfast Burrito","metadata":{"percent_complete_digestible_protein":0,"total_complete_digestible_protein_g":0,"total_protein_g":40.04271249999999},"score":0.454664826,"values":[]},{"id":"Grilled Tofu with Pineapple Salsa and Coconut Rice","metadata":{"percent_complete_digestible_protein":0,"total_complete_digestible_protein_g":0,"total_protein_g":10.582175000000001},"score":0.438385248,"values":[]},{"id":"Tex Mex Spaghetti Squash with Black Bean Guacamole","metadata":{"percent_complete_digestible_protein":0,"total_complete_digestible_protein_g":0,"total_protein_g":22.86011125},"score":0.379612625,"values":[]}]],["Vegan French Toast",[{"id":"Challah French Toast","metadata":{"percent_complete_digestible_protein":0,"total_complete_digestible_protein_g":0,"total_protein_g":49.339522500000015},"score":0.514613867,"values":[]},{"id":"French Toast Bread Pudding","metadata":{"percent_complete_digestible_protein":0,"total_complete_digestible_protein_g":0,"total_protein_g":88.2532075},"score":0.47838226,"values":[]},{"id":"Heather's Toasted Super Seed Power Bread from Yum Universe (Vegan, GF)","metadata":{"percent_complete_digestible_protein":0,"total_complete_digestible_protein_g":0,"total_protein_g":117.9299175},"score":0.445821047,"values":[]}]]];



//- user input: Make me a balanced <kind> meal for <meal-time>. My bodyweight in kg is <count>.
// - on submit, get meal names from chatgpt, then send each mealname to a aws function or a worker thread, which generates the recipe for each mealname
// - when the recipes come back, give them to another lambda, which does the scoring, this means I need to deploy the sqlite3 db OR I can rewrite the python script in typescript and call it from a webworker

const MealPreferenceUI = props => {
  return (
    <>
      Describe your meal preferences: <textarea className={inputClasses} onChange={e => props.setMealPreference(e.target.value)} rows={3} defaultValue={defaultPreferenceValue} />
      Meal time: <input className={inputClasses}  onChange={e => props.setMealTime(e.target.value)} placeholder="e.g breakfast, snack..." />
      <button onClick={props.handleSubmit} className="px-4 py-2 font-semibold text-sm bg-cyan-500 text-white rounded-full shadow-sm">
        Submit
      </button>
    </>
  )

};

type RecipeNutritionSummaryWithKey = RecipeNutritionSummary & { key: string };

function formatRecipeSummaries(resp: RecipeMatchesResponse): RecipeNutritionSummaryWithKey[] {
  return R.flatten(resp.data.map(x =>
    x[1].map(r => ({ ...r, key: `${r.id}-${x[0]}`}))
  ));
}

export default function Home() {
  const [selectedRecipeTitle, setSelectedRecipeTitle] = React.useState<string | undefined>();
  const [selectedRecipe, setSelectedRecipe] = React.useState<RecipeResponse | undefined>();
  const [mealPreference, setMealPreference] = React.useState<string>(defaultPreferenceValue);
  const [mealTime, setMealTime] = React.useState<string | undefined>();
  const [weight, setWeight] = React.useState<number | undefined>();
  const [recipeRecommendations, setRecipeRecommendations] = React.useState<RecipeNutritionSummaryWithKey[]>(formatRecipeSummaries({ data: [] }));

  React.useEffect(() => {
    if (selectedRecipeTitle) {
      fetch(
        'http://localhost:3000/api/recipeList', 
        { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({recipe_names: [selectedRecipeTitle]})}
      )
      .then(x => x.json())
      .then(({ data }: RecipeListResponse) => {
          if (data.length > 0) {
            setSelectedRecipe(data[0]);
          } else {
            console.error(`No recipes were found for recipe ${recipe.id}`);
          }
      });
    } else {
      setSelectedRecipe(undefined);
    }
  }, [selectedRecipeTitle]);

  const handleSubmit = async () => {
    const fields = [["meal preference", mealPreference], ["meal time", mealTime]];
    const emptyFields = fields.filter(([name, value]) => !value);
    if (emptyFields.length > 0) {
        const fieldNames = emptyFields.map(f => f[0]).join(", ");
        alert(`Please fill in the ${fieldNames} field(s).`);
    } else {
      fetch('http://localhost:3000/api/meal', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mealtime: mealTime, preference: mealPreference, mealcount: 1}) })
      .then((x: any) => x.json())
      .then((x: RecipeMatchesResponse) => {
        setRecipeRecommendations(formatRecipeSummaries(x));
      })
      .catch((e: any) => console.error(e));
    }

  };
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      {selectedRecipe ? <RecipeDetailsView onClose={() => setSelectedRecipe(undefined)} recipe={selectedRecipe} /> : (
        <div className="grid grid-rows-3 grid-flow-col gap-4">
          {recipeRecommendations ? recipeRecommendations.map((recipe: RecipeNutritionSummaryWithKey) => (
            <RecipeNutritionalSummaryCard
              key={recipe.key}
              onClick={() => setSelectedRecipeTitle(recipe.id)}
              recipeTitle={recipe.id}
              gramsDigestibleProtein={recipe.total_complete_digestible_protein_g}
              gramsProtein={recipe.total_protein_g}
              digestible_eaa_Histidine_g={recipe.digestible_eaa_Histidine_g}
              digestible_eaa_Isoleucine_g={recipe.digestible_eaa_Isoleucine_g}
              digestible_eaa_Leucine_g={recipe.digestible_eaa_Leucine_g}
              digestible_eaa_Lysine_g={recipe.digestible_eaa_Lysine_g}
              digestible_eaa_Methionine_g={recipe.digestible_eaa_Methionine_g}
              digestible_eaa_Phenylalanine_g={recipe.digestible_eaa_Phenylalanine_g}
              digestible_eaa_Threonine_g={recipe.digestible_eaa_Threonine_g}
              digestible_eaa_Tryptophan_g={recipe.digestible_eaa_Tryptophan_g}
              digestible_eaa_Valine_g={recipe.digestible_eaa_Valine_g}
             />
          )) : null}
        </div>
      )}
      <MealPreferenceUI
        setMealPreference={setMealPreference}
        setMealTime={setMealTime}
        setWeight={setWeight}
        handleSubmit={handleSubmit}
      />
    </main>
  )
}
