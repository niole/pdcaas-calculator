import { RecipeClient } from '../../utils/recipe-client/index';
import dotenv from 'dotenv';
dotenv.config();

export const recipeClient = new RecipeClient({ BASE: process.env.RECIPE_MATCH_API_SERVER_DOMAIN as string }).default;
