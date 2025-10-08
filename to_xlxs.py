import pandas as pd
import json
import sys

from utils.data import get_data, get_prefix_dict
from utils.trie import build_all_automaton, trie_pipeline
from utils.preprocess import to_normalized
from utils.fuzz import fuzz_pipeline
from utils.input import preprocess_input, select_candidate_by_order_administrative
sys.path.append("test")

# Load data
DATA = get_data()
PREFIX = get_prefix_dict()
AUTOMATON = build_all_automaton(DATA, PREFIX)

with open("test/latest_test.json", "r", encoding="utf-8") as f:
    tests = json.load(f)

rows = []

for i, case in enumerate(tests, start=1):
    input_text = case["text"]
    notes = case.get("notes", "")
    expected_province = case["result"].get("province") or None
    expected_district = case["result"].get("district") or None
    expected_ward = case["result"].get("ward") or None

    # Run pipeline
    import time
    start = time.perf_counter_ns()
    result = trie_pipeline(input_text, AUTOMATON)
    result = fuzz_pipeline(input_text, result)
    result = select_candidate_by_order_administrative(result, preprocess_input(input_text).split(","))
       
    result = result[0][0]
    time_exec = (time.perf_counter_ns() - start) * 10**(-9)

    got_province, got_district, got_ward = result

    # Check pass/fail
    fail_reasons = []
    if got_province != expected_province:
        fail_reasons.append(f"Province mismatch (expected '{expected_province}', got '{got_province}')")
    if got_district != expected_district:
        fail_reasons.append(f"District mismatch (expected '{expected_district}', got '{got_district}')")
    if got_ward != expected_ward:
        fail_reasons.append(f"Ward mismatch (expected '{expected_ward}', got '{got_ward}')")

    status = "PASS" if not fail_reasons else "FAIL"
    fail_reason = "; ".join(fail_reasons)

    rows.append({
        "index": i,
        "input": input_text,
        "normalized": to_normalized(input_text),
        "notes": notes,
        "expected_province": expected_province,
        "expected_district": expected_district,
        "expected_ward": expected_ward,
        "got_province": got_province,
        "got_district": got_district,
        "got_ward": got_ward,
        "time_ms": time_exec,
        "status": status,
        "fail_reason": fail_reason
    })

# Save to Excel
df = pd.DataFrame(rows)
df.to_excel("exports/test_results.xlsx", index=False, engine="openpyxl")
print("✅ Exported to test_results.xlsx")
