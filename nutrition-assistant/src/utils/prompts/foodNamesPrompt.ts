import { PromptTemplate } from "langchain/prompts";

const foodNamesTemplate = 
  'generate the names of 25 {preference} {mealtime} meals for 1 person. give the output in the following format, JSON only: ["the name of meal 1", "the name of meal 2", "the name of meal 3"]';

const mealNamesPrompt = new PromptTemplate({
  template: foodNamesTemplate,
  inputVariables: ["mealtime", "preference"],
});

export default mealNamesPrompt;
