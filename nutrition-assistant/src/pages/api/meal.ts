import { PromptTemplate } from "langchain/prompts";
import { OpenAI } from "langchain/llms/openai";
import { LLMChain } from "langchain/chains";
import dotenv from 'dotenv';
dotenv.config();

const foodNamesTemplate = 'generate the names of 3 {preference} {mealtime} meals for 1 person. give the output in the following format, JSON only: ["the name of meal 1", "the name of meal 2", "the name of meal 3"]'

const mealNamesPrompt = new PromptTemplate({
  template: foodNamesTemplate,
  inputVariables: ["mealtime", "preference"],
});

export default async function handler(req, res) {
  const { body } = req;
  const { mealtime, preference, mealcount } = body;

  const model = new OpenAI({ 
    openAIApiKey: process.env.OPENAI_API_KEY, // In Node.js defaults to process.env.OPENAI_API_KEY
    temperature: 0.8 });

  const mealNameChain = new LLMChain({ llm: model, prompt: mealNamesPrompt });
  console.log(req.body);
  try {
    const resp = await mealNameChain.call({ 
      mealtime,
      preference,
    });
    console.log(resp);
    //const mealNames = JSON.parse(resp.res.text);
    //const recipes = [];
    //const recipeSummaries = [];
    return res.status(200);
  } catch (error) {
    const { data, status, statusText } = error.response;
    console.error(data.error);
    return res.status(500).json({"message": JSON.stringify(data.error)});
  }
};
