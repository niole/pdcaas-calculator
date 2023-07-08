import { OpenAI } from "langchain/llms/openai";
import R from 'ramda';
import { Either, Recipe } from '../../types';
import jsonParse from '../../utils/jsonParse';
import { LLMChain } from "langchain/chains";
import recipePrompt, {t} from '../../utils/prompts/recipePrompt';
import mealNamesPrompt from '../../utils/prompts/foodNamesPrompt';
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
//    const mealNamesResp = await new LLMChain({ llm: model, prompt: mealNamesPrompt, verbose: true }).call({ 
//      mealtime,
//      preference,
//    });

    const mealNames = ["Fruit Salad","Veggie Omelette", "Bacon and Egg Toast"] // JSON.parse(mealNamesResp.text);

    const recipes: [string, Either<Recipe, Error>][] = await Promise.all(mealNames.map(mealname =>
      model.call(t(mealname))
    ))
    .then(rs => {
      return R.zip(mealNames, rs.map(jsonParse<Recipe>));
    });

    const [parsedRecipes, failedParseRecipes] = R.partition(R.pipe(R.prop(1), R.prop('kind'), R.whereEq('success')))(recipes);

    failedParseRecipes.forEach(([name, r]: [string, Either<Recipe, Error>]) => {
      console.info(`Recipe generation for mealname ${name} failed. `, r.value);
    })

    console.log(parsedRecipes);
    //const recipeSummaries = [];
    return res.status(200);
  } catch (error) {
    console.error(error);
    return res.status(500).json(error);
  }
};
