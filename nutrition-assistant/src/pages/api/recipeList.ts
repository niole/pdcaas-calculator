import { recipeClient } from './recipeClient';

export default async function handler(req, res) {
  const { body } = req;
  const { ids } = body;

  try {
    const recipes = await recipeClient.recipeListRecipeListPost({ ids });

    return res.status(200).json(recipes);
  } catch (error) {
    console.error(error);
    return res.status(500).json(error);
  }

}
