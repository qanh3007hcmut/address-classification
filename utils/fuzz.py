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
    from itertools import groupby

    selected = []

    for _, g in groupby(trie_results, key=lambda x: x[3]):
        g_list = list(g)

        if len(g_list) == 1:
            selected.extend(g_list)
            continue

        # fuzz ratio
        _, ratio_list, _ = get_best_by_fuzz(g_list, input, fuzz.ratio)
        if len(ratio_list) == 1:
            selected.extend(ratio_list)
            continue

        # fuzz partial ratio
        _, partial_ratio_list, _ = get_best_by_fuzz(g_list, input, fuzz.partial_ratio)
        if len(partial_ratio_list) == 1:
            selected.extend(partial_ratio_list)
            
        else:
            # fallback: giữ nguyên toàn bộ group
            selected.extend(g_list)

    return selected
    