"use client";
import React from 'react';
import * as R from 'ramda';
import { RecipeNutritionalSummaryCard } from './RecipeNutritionalSummaryCard';
import { RecipeDetailsView } from './RecipeDetailsView';
import { Spinner } from './Spinner';
import { RecipeResponse, RecipeListResponse, RecipeMatchesResponse, RecipeNutritionSummary } from '../utils/recipe-client/index';
import {MealPreferenceUI, defaultPreferenceValue} from './MealPreferenceUI';

export default function Home() {
  const [loading, setLoading] = React.useState<boolean>(false);
  const [selectedRecipeId, setSelectedRecipeId] = React.useState<string | undefined>();
  const [selectedRecipe, setSelectedRecipe] = React.useState<RecipeResponse | undefined>();
  const [mealPreference, setMealPreference] = React.useState<string>(defaultPreferenceValue);
  const [mealTime, setMealTime] = React.useState<string | undefined>();
  const [weight, setWeight] = React.useState<number | undefined>();
  const [recipeRecommendations, setRecipeRecommendations] = React.useState<RecipeNutritionSummary[]>([]);

  React.useEffect(() => {
    if (selectedRecipeId) {
      fetch(
        '/api/recipeList', 
        { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ids: [selectedRecipeId]})}
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
  }, [selectedRecipeId]);

  const handleSubmit = async () => {
    const fields = [["meal preference", mealPreference], ["meal time", mealTime]];
    const emptyFields = fields.filter(([name, value]) => !value);
    if (emptyFields.length > 0) {
        const fieldNames = emptyFields.map(f => f[0]).join(", ");
        alert(`Please fill in the ${fieldNames} field(s).`);
    } else {
      setLoading(true);
      fetch('/api/meal', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mealtime: mealTime, preference: mealPreference, mealcount: 1}) })
      .then((x: any) => x.json())
      .then((x: RecipeMatchesResponse) => {
        setRecipeRecommendations(x.data);
        setLoading(false);
      })
      .catch((e: any) => {
        console.error(e)
        setLoading(false);
      });
    }

  };
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      {R.cond([
        [([loading, _]) => loading, R.always(<Spinner />)],
        [([loading, selectedRecipe]) => !loading && !selectedRecipe && recipeRecommendations.length === 0, R.always(null)],
        [([_, selectedRecipe]) => selectedRecipe, R.always(
          <RecipeDetailsView
            onClose={() => setSelectedRecipe(undefined)}
            recipe={selectedRecipe!}
          />
        )],
        [R.T, R.always(
          <div className="grid grid-cols-2 gap-4 border rounded" style={{height:300, overflow: 'auto'}}>
            {recipeRecommendations.map((recipe: RecipeNutritionSummary) => (
              <RecipeNutritionalSummaryCard
                key={recipe.id}
                onClick={() => setSelectedRecipeId(recipe.id)}
                recipeTitle={recipe.title}
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
            ))}
          </div>
        )]

      ])([loading, selectedRecipe])}
      <MealPreferenceUI
        setMealPreference={setMealPreference}
        setMealTime={setMealTime}
        setWeight={setWeight}
        handleSubmit={handleSubmit}
      />
    </main>
  )
}
