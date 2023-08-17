import { RecipeResponse } from '../utils/recipe-client/index';
import { truncate } from '../utils/truncate';

type RecipeDetailsViewProps = {
  recipe: RecipeResponse,
  onClose: () => void
};
export function RecipeDetailsView({ recipe, onClose }: RecipeDetailsViewProps) {
  return (
    <div>
      <button className="float-right" onClick={onClose}>close</button>
      <div className="text-2xl text-center">{recipe.title}</div>
      <div className="grid sm:grid-cols-2 grid-cols-1">
        <div>
          <p>
            <div className="text-xl">ingredients</div>
            <div>
              {recipe.ingredients.map(i => (
                <div>
                  {`${i.amount} ${i.unit} ${i.name}`}
                </div>
              ))}
            </div>
          </p>
          <p>
            <div className="text-xl">instructions</div>
            <div>{recipe.instructions}</div>
          </p>
        </div>
        <div>
          <p>
            <div className="text-xl">protein breakdown</div>
            <div> total complete digestible protein: {truncate(recipe.total_complete_digestible_protein_g, 2)} g</div>

            <div className="text-xl">essential amino acid breakdown</div>
            {recipe.aas.map(aa =>
              <div>
                {`${aa.name}  ${truncate(aa.g, 2)} g`}
              </div>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
