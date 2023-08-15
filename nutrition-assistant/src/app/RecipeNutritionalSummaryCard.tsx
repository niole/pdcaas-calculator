import {truncate} from '../utils/truncate';

type Props = {
  recipeTitle: string,
  gramsDigestibleProtein: number,
  gramsProtein: number,
  digestible_eaa_Histidine_g: number | null,
  digestible_eaa_Isoleucine_g: number | null,
  digestible_eaa_Leucine_g: number | null,
  digestible_eaa_Lysine_g: number | null,
  digestible_eaa_Methionine_g: number | null,
  digestible_eaa_Phenylalanine_g: number | null,
  digestible_eaa_Threonine_g: number | null,
  digestible_eaa_Tryptophan_g: number | null,
  digestible_eaa_Valine_g: number | null,
};

export function RecipeNutritionalSummaryCard(props: Props) {
  const {
    recipeTitle,
    gramsDigestibleProtein,
    gramsProtein,
  } = props;
  const percentDigestibleProtein = truncate(gramsProtein > 0 ? 100*gramsDigestibleProtein/gramsProtein : 0, 2);
  return (
    <div>
      <h2>{recipeTitle}</h2>
      <div>digestible protein: {truncate(gramsDigestibleProtein, 2)} g</div>
      <div> total protein: {truncate(gramsProtein, 2)} g</div>
      <div>score: {percentDigestibleProtein} %</div>
    </div>
  );
}
