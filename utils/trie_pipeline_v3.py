from typing import Any, Literal
from utils.fuzz import fuzz_pipeline_v2
from utils.preprocess import to_normalized_no_comma_deleted as to_normalized
from utils.preprocess import to_diacritics
from utils.address_matcher import find_best_match_advanced
from utils.bktree import bktree_find

ABBRE_DICT = {
    "provinces" : ["t", "p"],
    "districts" : ["h", "q", "t"],
    "wards" : ["p", "x", "t"]
}

PREFIX_DICT = {
    "provinces" : ["tỉnh", "thành phố"],
    "districts" : ["huyện", "quận", "thị xã", "thành phố"],
    "wards" : ["phường", "xã", "thị trấn"]
}

def check_automaton(automaton, input: str):
    res_dict: dict[str, list[tuple[str, str, str]]] = {}
    result = []

    for end, (prefix, words, length) in automaton.iter(input):
        for word in words:
            if word.isdigit():
                if (end + 1) < len(input) and input[end + 1].isdigit():
                    continue  # skip candidate vì bị cắt số
            detected_input = input[(end - length + 1) : (end + 1)]
            candidate = (word, prefix, detected_input)
            if not res_dict.get(end + 1):
                res_dict[end + 1] = [candidate]
            else:
                # nếu đã có candidate rồi thì giữ candidate có detected_input dài hơn
                if len(res_dict[end + 1][0][2]) < length:
                    res_dict[end + 1] = [candidate]
                elif len(res_dict[end + 1][0][2]) == length:
                    res_dict[end + 1].append(candidate)
                    

            result.append(candidate)

    return res_dict


def check_address(
    processed_input: str,
    automaton: dict[str, Any],
    last_address = None
):
    address_dict = check_automaton(automaton, processed_input)
    comp = len(processed_input)
    if last_address:
        comp = int(last_address[0]) - len(last_address[3]) - 1
        
    if address_dict:
        best_key = max((k for k in address_dict.keys() if int(k) <= comp), default=None)
        if best_key :
            values = address_dict[best_key]
            return [(best_key, *value) for value in values]
        
    return [None]   


def process_trie_output(
    raw_input: str, 
    address_type: Literal["provinces", "districts", "wards"],
    output : tuple[int | str, str, str, str] | None,
    last_output: tuple[str, tuple[int | str, str, str, str]] | None = None
):
    
    if not output: 
        return None

    index_found, actual_output, prefix, detected_input = output
    # xử lý đuôi (bỏ phần thừa + ghép lại last input detected)
    last_output_start_index = int(last_output[1][0]) - len(last_output[1][3]) - 1 if last_output else int(index_found)
    new_raw_input = raw_input[: int(index_found)] + raw_input[last_output_start_index:]
    
    if not prefix:            
        start_idx = int(index_found) - len(detected_input) - 1
        cutted_input = new_raw_input[:start_idx].strip().split()
        check_2_first_token = cutted_input[-2:] if len(cutted_input) >= 2 else None
        check_3_first_token = cutted_input[-3:] if len(cutted_input) >= 3 else None

        if check_2_first_token and check_2_first_token[0] in PREFIX_DICT[address_type]:
            new_prefix = check_2_first_token[0]
            new_start_idx = start_idx - len(new_prefix) - len(check_2_first_token[1]) - 2
            new_raw_input = new_raw_input[:new_start_idx] + ", " + new_prefix + " " + new_raw_input[start_idx + 1:]
            new_index_found = int(index_found) - len(check_2_first_token[1]) - 1
            return new_raw_input, (new_index_found, actual_output, new_prefix, new_prefix + " " + detected_input)  
        elif check_3_first_token and f"{check_3_first_token[0]} {check_3_first_token[1]}" in PREFIX_DICT[address_type]:
            new_prefix = f"{check_3_first_token[0]} {check_3_first_token[1]}"
            new_start_idx = start_idx - len(check_3_first_token[0]) - len(check_3_first_token[1]) - len(check_3_first_token[2]) - 3
            new_raw_input = new_raw_input[:new_start_idx] + ", " + new_prefix + " " + new_raw_input[start_idx:]
            new_index_found = int(index_found) - len(check_3_first_token[2]) - 1
            return new_raw_input, (new_index_found, actual_output, new_prefix, new_prefix + " " + detected_input)
        
    start_idx = int(index_found) - len(detected_input) - 1
    if start_idx > 0:
        new_raw_input = new_raw_input[:start_idx] + "," + new_raw_input[start_idx:]
    
    return new_raw_input, (index_found, actual_output, prefix, detected_input)
        

def classify_trie_normalized(
    raw_input: str,
    automaton: dict[str, dict[str, Any]],
    address_type: Literal["provinces", "districts", "wards"],
    last_output: tuple[str, tuple[int | str, str, str, str]] | None = None
):
    _, last_address = last_output or (None, None)
    normalized_input = to_normalized(raw_input)

    output = check_address(normalized_input, automaton["normalized"][address_type], last_address)
    processed_output = [process_trie_output(raw_input, address_type, out, last_output) for out in output]
    processed_output = fuzz_pipeline_v2(processed_output)
    if processed_output and processed_output[0]:
        return processed_output[0]

    return None

def classify_trie_diacritics(
    raw_input: str,
    automaton: dict[str, dict[str, Any]],
    address_type: Literal["provinces", "districts", "wards"],
    last_output: tuple[str, tuple[int | str, str, str, str]] | None = None
):
    _, last_address = last_output or (None, None)
    normalized_input = to_normalized(raw_input)
    diacritics_input = to_diacritics(normalized_input)
    output = check_address(diacritics_input, automaton["diacritics"][address_type], last_address)
    processed_output = [process_trie_output(raw_input, address_type, out, last_output) for out in output]
    processed_output = fuzz_pipeline_v2(processed_output)
    if processed_output and processed_output[0]:
        return processed_output[0]

    return None

def bktree_spelling_check(input : str,
    bktree : dict[str, Any],
    prefix_dict : dict[str, list[str]],
    address_type: Literal["provinces", "districts", "wards"],
    last_output: tuple[str, tuple[int | str, str, str, str]] | None = None
):
    
    input_to_split = input
    input_used = input
    index_found = len(input_to_split)
    if last_output:
        input_used = last_output[0]
        input_to_split = last_output[0].split(",")[0]
        index_found = int(last_output[1][0]) - len(last_output[1][3]) - 1
        if index_found < 0:
            return None
        
    inputs = input_to_split.split()
    inputs = " ".join(inputs[-min(5, len(inputs)):])
    output = bktree_find(inputs, bktree[address_type], prefix_dict, to_normalized, address_type)
    if not output:
        return None
    
    idx_diff, actual_output, prefix, detected_input = output
    idx_found : int = index_found - idx_diff
    start = idx_found - len(detected_input) - 1
    raw_input = input_used[0:start] + "," + input_used[start:]
    
    return raw_input, (idx_found, actual_output, prefix, detected_input)

def combine_diacritics_bktree(
    input: str,
    automaton: dict[str, dict[str, Any]],
    bktree : dict[str, Any],
    prefix_dict : dict[str, list[str]],
    address_type: Literal["provinces", "districts", "wards"],
    last_output: tuple[str, tuple[int | str, str, str, str]] | None = None
):
    output_trie_diacritics = classify_trie_diacritics(input, automaton, address_type, last_output)
    output_spelling_check = bktree_spelling_check(input, bktree, prefix_dict, address_type, last_output)
    if not output_trie_diacritics:
        return output_spelling_check
    
    if not output_spelling_check:
        return output_trie_diacritics
    
    if (len(output_trie_diacritics[1][1]) + len(output_trie_diacritics[1][3])) > (len(output_spelling_check[1][1]) + len(output_spelling_check[1][3])):
        return output_trie_diacritics
    else: 
        return output_spelling_check
    
def full_pipeline(
    raw_input: str,
    automaton: dict[str, dict[str, Any]],
    bktree: dict[str, Any]
):
    parts = [p.strip() for p in raw_input.split(",")]
    
    can_province_none = False if parts[-1] else True
    can_district_none = True if len(parts) >= 3 and not parts[-2] and parts[-3] else False
    can_ward_none = True if len(parts) >= 3 and not parts[-3] and parts[-2] and parts[1] else False
    
    input = to_normalized(raw_input)

    province = (
        classify_trie_normalized(input, automaton, "provinces") or 
        # spelling_detect(input, bktree, "provinces")
        combine_diacritics_bktree(input, automaton, bktree, PREFIX_DICT, "provinces")
    ) if not can_province_none else None
    province_input = province[0] if province else input
    
    district = (
        classify_trie_normalized(province_input, automaton, "districts", province) or 
        # spelling_detect(province_input, bktree, "districts", province)
        combine_diacritics_bktree(province_input, automaton,  bktree, PREFIX_DICT, "districts", province)
    ) if not can_district_none else None
    
    district_input = district[0] if district else province_input
    
    ward = (
        classify_trie_normalized(district_input, automaton, "wards", district or province) or
        # spelling_detect(district_input, bktree, "wards", district or province)
        combine_diacritics_bktree(district_input, automaton, bktree, PREFIX_DICT, "wards", district)
    ) if not can_ward_none else None
    
    # Better ward than district
    if all([
        not ward, 
        district and not district[1][2]
    ]):
        second_district = None
        second_ward = (
            classify_trie_normalized(province_input, automaton, "wards", province) or
            # spelling_detect(province_input, bktree, "wards", province)
            combine_diacritics_bktree(province_input, automaton, bktree, PREFIX_DICT, "wards", province)
            
        ) if not can_ward_none else None
        
        if second_ward and second_ward[1][2]:
            district = second_district
            ward = second_ward
        
    print("PROVINCE", "-"*5, province)
    print("DISTRICT", "-"*5, district)
    print("WARD", "-"*5, ward)
    return  (
        province[1][1] if province else None, 
        district[1][1] if district else None,
        ward[1][1] if ward else None
    )