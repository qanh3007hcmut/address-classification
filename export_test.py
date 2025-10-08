from utils.data import get_data, get_prefix_dict
from utils.trie import build_all_automaton, trie_pipeline
from utils.fuzz import fuzz_pipeline
from utils.input import preprocess_input, select_candidate_by_order_administrative, select_candidate_by_order_administrative_v2
import time
import sys
sys.path.append("test")
DATA = get_data()
PREFIX = get_prefix_dict()

AUTOMATON = build_all_automaton(DATA, PREFIX)

import json

with open("test/latest_test.json", "r", encoding="utf-8") as f:
    tests = json.load(f)

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

filtered_cases = [
    (i, *case) for i, case in all_cases
    if i in SKIP_INDEXES and case[4] == "public test case"
]

results = []

for i, input_text, expected_province, expected_district, expected_ward, notes in filtered_cases:
    test = {
        "text": input_text,
        "result": {
            "province": expected_province,
            "district": expected_district,
            "ward": expected_ward
        },
        "notes": notes
    }
    results.append(test)

with open("exports/tests.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print(f"Results saved to test.json")