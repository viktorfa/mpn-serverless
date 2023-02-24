import ingredientsList from "./ingredients-list";

export const getIngredientsDetails = async ({ mpnIngredients }) => {
  const ingredientKeys = Object.keys(mpnIngredients);

  const ingredientDetails = ingredientKeys
    .map((key) => ingredientsList[key])
    .filter((x) => !!x);

  return ingredientDetails;
};
