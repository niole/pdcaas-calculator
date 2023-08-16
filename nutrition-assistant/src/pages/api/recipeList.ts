import { recipeClient } from './recipeClient';

export default async function handler(req, res) {
  const { body } = req;
  const { recipe_names } = body;

  try {
    const recipes = await recipeClient.recipeListRecipeListPost({ recipe_names });

    return res.status(200).json(recipes);
  } catch (error) {
    console.error(error);
    return res.status(500).json(error);
  }

}
