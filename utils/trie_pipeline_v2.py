from typing import Any, Literal
from utils.fuzz import fuzz_pipeline_v2
from utils.preprocess import to_normalized_no_comma_deleted as to_normalized
from utils.preprocess import to_diacritics
from utils.address_matcher import find_best_match_advanced
from utils.bktree import bktree_find, prefix_helper
from utils.vietnamesse_edit_distance import vietnamese_weighted_edit_distance as vnm_ed

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
        best_key = max((k for k in address_dict.keys() if int(k) <= comp and abs(int(k) - comp) <= 8), default=None)
        if best_key:
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
        

def prefix_helper_check_for_trie(
    text : str,
    output : tuple[str, str, str, str] | None,
    address_type: Literal["provinces", "districts", "wards"],
):
    def split_text_for_prefix(text, end_idx, input) : 
        start = end_idx - len(input) - 1
        words = text[:start].strip().split()
        length = len(words)
        words_prefix = []
        if length >= 3:
            words_prefix.append(" ".join(words[-3:]))
        if length >= 2:
            words_prefix.append(" ".join(words[-2:]))
            words_prefix.append(" ".join(words[-3:-1]))
        
        if length >= 3:
            words_prefix.append(words[-3])
        if length >= 2:
            words_prefix.append(words[-2])
        if length >= 1:
            words_prefix.append(words[-1])
            
        return words_prefix
    
    if not output:
        return output
    
    end_index, detected_ouput, prefix, detected_input = output
    words = split_text_for_prefix(text, int(end_index), detected_input)
    if not prefix: 
        raw, prefix, _ = prefix_helper(words, PREFIX_DICT, address_type)
        detected_input = f"{raw} {detected_input}".strip()
    
    return end_index, detected_ouput, prefix, detected_input
    
        

def classify_trie_normalized(
    raw_input: str,
    automaton: dict[str, dict[str, Any]],
    address_type: Literal["provinces", "districts", "wards"],
    last_output: tuple[str, tuple[int | str, str, str, str]] | None = None
):
    _, last_address = last_output or (None, None)
    normalized_input = to_normalized(raw_input)

    output = check_address(normalized_input, automaton["normalized"][address_type], last_address)
    output = [prefix_helper_check_for_trie(normalized_input, out, address_type) for out in output]
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
) -> list[Any]:
    _, last_address = last_output or (None, None)
    normalized_input = to_normalized(raw_input)
    diacritics_input = to_diacritics(normalized_input)
    output = check_address(diacritics_input, automaton["diacritics"][address_type], last_address)
    processed_output = [process_trie_output(raw_input, address_type, out, last_output) for out in output]
    processed_output = fuzz_pipeline_v2(processed_output)
    if processed_output and processed_output[0]:
        return processed_output

    return []
    
def window_slide(inputs : list[str], min_size = 2, max_size = 3):
    slides = []
    if len(inputs) >= min_size:
        slides.append(inputs[-min_size:])
        
    if len(inputs) >= max_size:
        slides.append(inputs[-max_size:])
        
    return slides
    
def spelling_detect(
    input : str,
    bktree : dict[str, Any],
    address_type: Literal["provinces", "districts", "wards"],
    last_output: tuple[str, tuple[int | str, str, str, str]] | None = None
):
    
    actual_output = None
    input_to_split = input
    input_used = input
    index_found = len(input_to_split)
    slides_diff = 0
    if last_output:
        input_used = last_output[0]
        input_to_split = last_output[0].split(",")[0]
        index_found = int(last_output[1][0]) - len(last_output[1][3]) - 1
        if index_found < 0:
            return None
        
    inputs = input_to_split.split()   
    for slide in window_slide(inputs, 2, 3):
        combined_input = " ".join(slide)
        output = find_best_match_advanced(combined_input, address_type, bktree)    
        if output:
            actual_output = output
            index_found -= len(combined_input) - len(output["query"])
            slides_diff = len(slide) - output["word_count"]
            break
        
        if combined_input[0] in ABBRE_DICT[address_type]:
            output = find_best_match_advanced(combined_input[1:], address_type, bktree)    
            if output:
                actual_output = output
                index_found -= len(combined_input) - len(output["query"])
                slides_diff = len(slide) - output["word_count"]
                break
    if not actual_output:
        return None
    
    # print(address_type, "-"*5, "spelling check")  
    count = actual_output['word_count']
    check_1_token = inputs[-(count + 1 + slides_diff)] if len(inputs) > count + 1 else None
    check_1_token_second = inputs[-(count + 2 + slides_diff)] if len(inputs) > count + 2 else None
    check_2_token = (
        f"{check_1_token_second} {check_1_token}"
        if check_1_token and check_1_token_second
        else None
    )
    
    detected = actual_output["query"]
    prefix = ""
    
    if check_1_token and check_1_token in PREFIX_DICT[address_type]:
        detected = check_1_token + " " + actual_output["query"]
        prefix = check_1_token
    elif check_2_token and check_2_token in PREFIX_DICT[address_type]:
        detected = check_2_token + " " + actual_output["query"]
        prefix = check_2_token            
    elif check_1_token and check_1_token_second and check_1_token_second in PREFIX_DICT[address_type]:
        detected = check_1_token_second + " " + actual_output["query"]
        prefix = check_1_token_second
        full_output = (index_found, actual_output["match"], prefix, detected)
        start = index_found - len(detected) - 1 - 2 - len(check_1_token)
        raw_input = input_used[0:start] + "," + input_used[start:]
        return raw_input, full_output
    
    full_output = (index_found, actual_output["match"], prefix, detected)
    start = index_found - len(detected) - 1 
    if start > 0:
        raw_input = input_used[0:start] + "," + input_used[start:]
    else: raw_input = input_used
    
    return raw_input, full_output

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
            return []
        
    inputs = input_to_split.split()
    inputs = " ".join(inputs[-min(6, len(inputs)):])
    outputs = bktree_find(inputs, bktree[address_type], prefix_dict, to_normalized, address_type)
    if not outputs:
        return []
    
    results = []
    for output in outputs:
        idx_diff, actual_output, prefix, detected_input = output
        idx_found : int = index_found - idx_diff
        start = idx_found - len(detected_input) - 1
        if start > 0:
            raw_input = input_used[0:start] + "," + input_used[start:]
        else: raw_input = input_used
        results.append((raw_input, (idx_found, actual_output, prefix, detected_input)))
    
    return results

def combine_diacritics_bktree(
    input: str,
    automaton: dict[str, dict[str, Any]],
    bktree: dict[str, Any],
    prefix_dict: dict[str, list[str]],
    address_type: Literal["provinces", "districts", "wards"],
    last_output: tuple[str, tuple[int | str, str, str, str]] | None = None
):
    output_trie_diacritics = classify_trie_diacritics(input, automaton, address_type, last_output)
    output_spelling_check = bktree_spelling_check(input, bktree, prefix_dict, address_type, last_output)

    # Nếu cả hai đều rỗng
    if not output_trie_diacritics and not output_spelling_check:
        return None

    # Gom nhóm theo detected_output
    groups: dict[str, list[tuple[str, tuple[int | str, str, str, str]]]] = {}
    for output in output_trie_diacritics + output_spelling_check:
        _, (_, detected_output, _, _) = output
        groups.setdefault(detected_output, []).append(output)

    # --- 1️⃣ Ưu tiên độ dài nhất ---
    all_outputs = output_trie_diacritics + output_spelling_check
    key_len_detected_output = lambda x: len(x[1][1]) + len(x[1][2])
    max_len_detected_output = max(all_outputs, key=key_len_detected_output)
    max_len = key_len_detected_output(max_len_detected_output)
    max_idx = max(all_outputs, key= lambda x: x[1][0])
    has_prefix = any(item[1][2] for item in all_outputs)
    best_cands = [x for x in all_outputs
        if (
            key_len_detected_output(x) == max_len and 
            x[1][0] == max_idx[1][0] and
            (
                (has_prefix and len(x[1][2]) > 0) or
                (not has_prefix and len(x[1][2]) == 0)
            )
        )]
    if len(best_cands) == 1:
        return best_cands[0]
    
    longest_outputs = [
        x for x in all_outputs
        if key_len_detected_output(x) == max_len or \
            x[1][0] == max_idx[1][0] 
            # or key_len_garbage(x) == min_garbage
    ]
    # --- 2️⃣ Nếu trong các kết quả dài nhất có nhóm xuất hiện ở cả hai nguồn ---
    
    overlap_group = {
        output[1][1]: groups[output[1][1]]
        for output in longest_outputs
        if len(groups[output[1][1]]) == 2
    }    
    
    if len(overlap_group) == 1:
        only_group = next(iter(overlap_group.values()))
        return max(only_group, key=lambda x: len(x[1][-1]))
    
    if overlap_group:
        group = [v for _, values in overlap_group.items() for v in values]
        best = min(group, key = lambda x: vnm_ed(x[1][1], x[1][-1]))
        return best
    
    # --- 3️⃣ Nếu không có nhóm trùng thì chọn output dài nhất ---
    return longest_outputs[0]
   
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
    
    # Better district than province
    if all([
        province and not province[1][2], 
        district and not district[1][2],
    ]):
        second_district = (
            classify_trie_normalized(input, automaton, "districts") or 
            combine_diacritics_bktree(input, automaton,  bktree, PREFIX_DICT, "districts")
        ) if not can_district_none else None
        
        if province and second_district and second_district[1][2] and len(second_district[1][-1]) > len(province[1][-1]):
            province = None
            district = second_district
            
    district_input = district[0] if district else province_input
    
    ward = (
        classify_trie_normalized(district_input, automaton, "wards", district or province) or
        # spelling_detect(district_input, bktree, "wards", district or province)
        combine_diacritics_bktree(district_input, automaton, bktree, PREFIX_DICT, "wards", district or province)
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