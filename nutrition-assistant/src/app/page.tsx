"use client";
import React from 'react';
import * as R from 'ramda';
import { RecipeNutritionalSummaryCard } from './RecipeNutritionalSummaryCard';
import { RecipeDetailsView } from './RecipeDetailsView';
import { RecipeResponse, RecipeListResponse, RecipeMatchesResponse, RecipeNutritionSummary } from '../utils/recipe-client/index';
import {MealPreferenceUI, defaultPreferenceValue} from './MealPreferenceUI';

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
        '/api/recipeList', 
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
      fetch('/api/meal', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mealtime: mealTime, preference: mealPreference, mealcount: 1}) })
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
