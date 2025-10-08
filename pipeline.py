from utils.address_matcher import build_bk_trees
from utils.data import get_data, get_prefix_dict
from utils.trie import build_all_automaton
from utils.input import preprocess_input
from utils.trie_pipeline_v2 import full_pipeline

DATA = get_data()
PREFIX = get_prefix_dict()
AUTOMATON = build_all_automaton(DATA, PREFIX)
BKTREE = build_bk_trees(DATA)

def process(input : str):
    return full_pipeline(preprocess_input(input), AUTOMATON, BKTREE)