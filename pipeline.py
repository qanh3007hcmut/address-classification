from utils.data import get_data, get_prefix_dict
from utils.trie import build_all_automaton, trie_pipeline
from utils.fuzz import fuzz_pipeline
from utils.input import preprocess_input, select_candidate_by_order_administrative

DATA = get_data()
PREFIX = get_prefix_dict()
AUTOMATON = build_all_automaton(DATA, PREFIX)

def process(input : str):
    result = trie_pipeline(input, AUTOMATON)
    result = fuzz_pipeline(input, result)
    result = select_candidate_by_order_administrative(result, input)
    return result[0][0]