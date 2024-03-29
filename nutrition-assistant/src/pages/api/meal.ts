import { OpenAI } from "langchain/llms/openai";
import { LLMChain } from "langchain/chains";
import mealNamesPrompt from '../../utils/prompts/foodNamesPrompt';
import { recipeClient } from './recipeClient';
import dotenv from 'dotenv';
dotenv.config();

const model = new OpenAI({ 
  openAIApiKey: process.env.OPENAI_API_KEY, // In Node.js defaults to process.env.OPENAI_API_KEY
  temperature: 0.5
});

export default async function handler(req, res) {
  const { body } = req;
  const { mealtime, preference } = body;

  try {
    const mealNamesResp = await new LLMChain({ llm: model, prompt: mealNamesPrompt, verbose: true }).call({ 
      mealtime,
      preference,
    });

    const mealNames = JSON.parse(mealNamesResp.text);

    const recipeRecommendations = 
      await recipeClient.recipeMatchesMetadataRecipeMatchesPost({ recipe_names: mealNames });

    return res.status(200).json(recipeRecommendations);
  } catch (error) {
    console.error(error);
    return res.status(500).json(error);
  }
};
