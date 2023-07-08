import { PromptTemplate } from "langchain/prompts";

//const template = 
//'give me a recipe for {mealname} for 1 person. give me the recipe in the following format, JSON only: { "total_servings": 5,  "ingredients": [{"units": "cup", "name": "wheat pasta", "total": 1}, {"units":"tsp", "name":"salt","total": 0.5}, {"units": "lbs", "name": "beef", "total": 1}, {"units": "teaspoon", "name": "mustard", "total": 0.25}, {"units": "tablespoon", "name":"peanut butter", "total": 2}, {"units":"tbsp", "name":"sour cream", "total":1.5}], "instructions": "Boil the pasta for 11 minutes with the salt in water. Serve immediately."}';

/**
 * total_servings
 * ingredients
 * instructions
 */

export const t = (mealname: string) =>
`give me a recipe for ${mealname} for 1 person. give me the recipe in the following format, JSON only: { "total_servings": 5,  "ingredients": [{"units": "cup", "name": "wheat pasta", "total": 1}, {"units":"tsp", "name":"salt","total": 0.5}, {"units": "lbs", "name": "beef", "total": 1}, {"units": "teaspoon", "name": "mustard", "total": 0.25}, {"units": "tablespoon", "name":"peanut butter", "total": 2}, {"units":"tbsp", "name":"sour cream", "total":1.5}], "instructions": "Boil the pasta for 11 minutes with the salt in water. Serve immediately."}`;

//export default new PromptTemplate({
//  template,
//  inputVariables: ["mealname"],
//});
