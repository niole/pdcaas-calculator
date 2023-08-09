type Props = {
  recipeTitle: string,
  gramsDigestibleProtein: number,
  percentDigestibleProtein: number,
  gramsProtein: number,
};

export function RecipeNutritionalSummaryCard(props: Props) {
  const {
    recipeTitle,
    gramsDigestibleProtein,
    percentDigestibleProtein,
    gramsProtein,
  } = props;

  return (
    <div>
      <h2>{recipeTitle}</h2>
      <div>digestible protein: {gramsDigestibleProtein} g</div>
      <div> total protein: {gramsProtein} g</div>
      <div>score: {percentDigestibleProtein} %</div>
    </div>
  );
}

