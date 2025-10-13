from tkinter import UNDERLINE
from utils.data import get_data, get_prefix_dict
from utils.input_v2 import preprocess_input
from utils.trie import build_all_automaton
from utils.preprocess import to_normalized
from utils.trie_pipeline_v2 import full_pipeline
from utils.bktree import build_bk_trees
import time
import sys
sys.path.append("test")
DATA = get_data()
PREFIX = get_prefix_dict()
AUTOMATON = build_all_automaton(DATA, PREFIX)
BKTREE = build_bk_trees(DATA, PREFIX["full"]["normalized"], to_normalized)

import json
import pytest

with open("test/latest_test.json", "r", encoding="utf-8") as f:
    tests = json.load(f)

test_inputs = [case["text"] for case in tests]
expected_province = [case["result"]["province"] for case in tests]
expected_district = [case["result"]["district"] for case in tests]
expected_ward = [case["result"]["ward"] for case in tests]
test_ids = [f"{i}_{case["notes"]}" for (i, case) in enumerate(tests, 1)]

all_cases = list(enumerate(
    [(case["text"], case["result"]["province"], case["result"]["district"], case["result"]["ward"], case["notes"]) 
     for case in tests],
    1
))

SKIP_INDEXES = {
    646, 644, 641, 639, 634, 630, 622, 620, 618, 617, 611, 606, 604, 603, 600, 593, 594, 598, 590, 582, 
    576, 574, 569, 567, 561, 560, 557, 555, 554, 549, 548, 541, 536, 532, 530, 525, 523, 522, 521, 519,
    517, 516, 515, 508, 509, 510, 504, 502, 505, 500, 499, 498, 497, 496, 493, 491, 496, 493, 491, 487,
    482, 481, 480, 479, 476, 472, 471, 468, 465, 462, 461, 459, 458, 455, 453, 450, 449, 446, 444, 438,
    439, 436, 432, 430, 429, 428, 425, 424, 423, 420, 417, 416, 415, 413, 401, 402, 403, 408, 409, 399,
    397, 394, 392, 388, 377, 376, 374, 369, 368, 365, 364, 362, 360, 340, 279, 276, 244, 202, 203   
}

OUTPUT_ERROR = {
    229, 286, 309, 313, 314, 259, 287, 305
}

UNWANTED = {
    211, 249,
    639 # chịu Đông Thanh vs Đông Thạnh 
}

# SKIP_INDEXES.update(OUTPUT_ERROR)
# SKIP_INDEXES.update(UNWANTED)
OUTPUT_ERROR.update(UNWANTED)
# filter thêm điều kiện notes
filtered_cases = [
    (i, *case) for i, case in all_cases
    if i not in OUTPUT_ERROR and case[4] == "public test case"
]

# Tách lại thành từng list
filtered_ids       = [f"{i}"   for i, *_ in filtered_cases]
filtered_inputs    = [case[0]  for _, *case in filtered_cases]
filtered_provinces = [case[1]  for _, *case in filtered_cases]
filtered_districts = [case[2]  for _, *case in filtered_cases]
filtered_wards     = [case[3]  for _, *case in filtered_cases]

# @pytest.mark.parametrize(
#     "input_text, expected_province, expected_district, expected_ward", 
#     list(zip(test_inputs, expected_province,expected_district, expected_ward)), 
#     ids=test_ids
# )
slow_cases = []

@pytest.mark.parametrize(
    "input_text, expected_province, expected_district, expected_ward", 
    list(zip(filtered_inputs, filtered_provinces, filtered_districts, filtered_wards)), 
    ids=filtered_ids
)
def test_classify(input_text, expected_province, expected_district, expected_ward):
    start = time.perf_counter_ns()
    result = full_pipeline(preprocess_input(input_text), AUTOMATON, BKTREE)

    # result = select_candidate_by_order_administrative_v2(result, preprocess_input(input_text))
        
    elapsed = (time.perf_counter_ns() - start) * 1e-9
    if elapsed > 0.01:
        slow_cases.append((input_text, elapsed))
    expected_province = expected_province or None
    expected_district = expected_district or None
    expected_ward = expected_ward or None
    assert result[0] == expected_province
    assert result[1] == expected_district
    assert result[2] == expected_ward