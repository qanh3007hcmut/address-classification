from utils.data import get_data, get_prefix_dict
from utils.trie import build_all_automaton, trie_pipeline
from utils.fuzz import fuzz_pipeline
import sys
sys.path.append("test")
DATA = get_data()
PREFIX = get_prefix_dict()

AUTOMATON = build_all_automaton(DATA, PREFIX)

import json
import pytest

with open("test/latest_test.json", "r", encoding="utf-8") as f:
    tests = json.load(f)

test_inputs = [case["text"] for case in tests]
expected_province = [case["result"]["province"] for case in tests]
expected_district = [case["result"]["district"] for case in tests]
expected_ward = [case["result"]["ward"] for case in tests]
test_ids = [f"{i}_{case["notes"]}" for (i, case) in enumerate(tests, 1)]

# @pytest.mark.parametrize(
#     "input_text, expected_province, expected_district, expected_ward", 
#     list(zip(test_inputs, expected_province,expected_district, expected_ward)), 
#     ids=test_ids
# )
@pytest.mark.parametrize(
    "input_text, expected_province, expected_district, expected_ward", 
    list(zip(test_inputs, expected_province, expected_district, expected_ward)), 
    ids=test_ids
)
def test_classify(input_text, expected_province, expected_district, expected_ward):
    result = trie_pipeline(input_text, AUTOMATON)
    result = fuzz_pipeline(input_text, result)
    result = result[0][0]
    expected_province = expected_province or None
    expected_district = expected_district or None
    expected_ward = expected_ward or None
    assert result[0] == expected_province
    assert result[1] == expected_district
    assert result[2] == expected_ward
