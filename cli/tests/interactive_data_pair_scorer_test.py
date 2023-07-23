from fine_tune.interactive_data_pair_scorer import InteractiveDataPairScorer

def number_score_parser(d):
    if d == "":
        return 0
    else:
        return int(d)

def main():
    actual1 = []
    scorer1 = InteractiveDataPairScorer(
            cache=None,
            query=lambda : [1],
            matches=lambda x: [1, 2, 2],
            scores=[0, 1],
            score_parser=number_score_parser,
            out=lambda x: actual1.append(x),
            max_input_failures=10,
        )
    scorer1.run()

    assert(actual1 == [(1, 1, 1), (1, 2, 0), (1, 2, 0)])

if __name__ == "__main__":
    main()
