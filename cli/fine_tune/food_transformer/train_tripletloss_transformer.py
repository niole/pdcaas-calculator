import click
from datasets import load_dataset
from sentence_transformers import InputExample, losses, SentenceTransformer, evaluation
from torch.utils.data import DataLoader
from itertools import groupby

@click.command()
@click.option('--inpath', '-i', type=str, required=True)
@click.option('--outpath', '-o', type=str, required=True)
@click.option('--modelpath', '-m', type=str, default='multi-qa-MiniLM-L6-cos-v1')
def main(inpath, outpath, modelpath):
    dataset = load_dataset(path="./", data_files=[inpath])

    grouped_data = groupby(dataset["train"], lambda x: x["query"])
    train_examples = []

    for (name, examples) in grouped_data:
        es = list(examples)
        positives = [e for e in es if e["score"] == 1]
        negatives = [e for e in es if e["score"] == 0]

        for pos in positives:
            for neg in negatives:
                train_examples.append(InputExample(texts=[name, pos["match"], neg["match"]]))

    model = SentenceTransformer(modelpath)
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
    train_loss = losses.TripletLoss(model=model)

    e_sentences = train_examples[:200]
    evaluator = evaluation.MSEEvaluator(
        source_sentences=[s.texts[0] for s in e_sentences],
        target_sentences=[s.texts[1] for s in e_sentences],
        teacher_model=model,
        show_progress_bar=True
      )

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=10,
        evaluation_steps=100,
        evaluator=evaluator,
        output_path=outpath
    )

if __name__ == "__main__":
    main()
