from utils.bktree import build_BKTree, search_bktree
from utils.data import get_data, get_prefix_dict    
from utils.trie_DP import build_Trie_DP
import time
DATA = get_data()
PREFIX = get_prefix_dict()

BKTree_Province = build_BKTree(DATA["provinces"])
Trie_DP_Province = build_Trie_DP(DATA["provinces"])
input = "T Giang"
max_dist = 5
start = time.perf_counter_ns()
bktree_output = BKTree_Province.search(input, max_dist=max_dist)

end = time.perf_counter_ns() - start
print(f"{end * 10**(-9): .9f}")
print("-"*5, "BKTREE", "-"*5)
[print(out) for out in bktree_output]

start = time.perf_counter_ns()
trie_dp_output = Trie_DP_Province.search_approx(input, max_dist=max_dist)

end = time.perf_counter_ns() - start
print(f"{end * 10**(-9): .9f}")
print("-"*5, "TRIE_DP", "-"*5)
[print(out) for out in trie_dp_output]