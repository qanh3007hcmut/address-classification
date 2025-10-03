from rapidfuzz import fuzz
from itertools import groupby
from utils.preprocess import to_normalized

def get_best_by_fuzz(trie_results, input_text, scorer=fuzz.ratio, processor=to_normalized):
    def keyfunc(x):
        return scorer(
            input_text,
            " ".join(reversed([p for p in x[0] if p])),
            processor=processor
        )

    sorted_list = sorted(trie_results, key=keyfunc, reverse=True)

    max_score, group = next(groupby(sorted_list, key=keyfunc))
    best_results = list(group)

    return max_score, best_results, sorted_list

def fuzz_pipeline(input: str, trie_results: list) :
    if len(trie_results) == 1 : return trie_results
    
    _, ratio_list, _ = get_best_by_fuzz(trie_results, input, fuzz.ratio)
    if len(ratio_list) == 1: 
        return ratio_list
    
    _, partial_ratio_list, _ = get_best_by_fuzz(trie_results, input, fuzz.partial_ratio)
    if len(partial_ratio_list) == 1:
        return partial_ratio_list
    else: 
        return trie_results
    