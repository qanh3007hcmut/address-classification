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

def get_best_by_fuzz_v2(trie_results, scorer=fuzz.ratio, processor=to_normalized):
    def keyfunc(x):
        input, (end, comp, prefix, detected_input) = x
        start = (int(end) - len(detected_input) - 1)
        if start < 0: start = 0 
        text_extracted = input[start:int(end)]
        return scorer(
            text_extracted,
            prefix + " " + comp,
            processor=processor
        )
    
    sorted_list = sorted(trie_results, key=keyfunc, reverse=True)

    max_score, group = next(groupby(sorted_list, key=keyfunc))
    best_results = list(group)
    return max_score, best_results, sorted_list


def fuzz_pipeline(input: str, trie_results: list | None) :
    from itertools import groupby
    if not trie_results:
        return None
    
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
    
def fuzz_pipeline_v2(trie_results: list | None) :
    if not trie_results:
        return [None]
    
    if len(trie_results) == 1:
        return trie_results
    
    # fuzz ratio
    _, ratio_list, _ = get_best_by_fuzz_v2(trie_results, fuzz.ratio)
    if len(ratio_list) == 1:
        return ratio_list

    # fuzz partial ratio
    _, partial_ratio_list, _ = get_best_by_fuzz_v2(trie_results, fuzz.partial_ratio)
    if len(partial_ratio_list) == 1:
        return partial_ratio_list
    
    return trie_results 
