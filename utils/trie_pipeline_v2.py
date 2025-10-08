from typing import Any, Literal
from utils.preprocess import to_normalized_no_comma_deleted as to_normalized
from utils.preprocess import to_diacritics
from utils.address_matcher import find_best_match_advanced


def check_automaton(automaton, input: str):
    res_dict: dict[str, tuple[str, str, str]] = {}
    result = []

    for end, (prefix, words, length) in automaton.iter(input):
        for word in words:
            if word.isdigit():
                if (end + 1) < len(input) and input[end + 1].isdigit():
                    continue  # skip candidate vì bị cắt số
            detected_input = input[(end - length + 1) : (end + 1)]
            candidate = (word, prefix, detected_input)
            if not res_dict.get(end + 1):
                res_dict[end + 1] = candidate
            else:
                # nếu đã có candidate rồi thì giữ candidate có detected_input dài hơn
                if len(res_dict[end + 1][2]) < length:
                    res_dict[end + 1] = candidate

            result.append(candidate)

    return res_dict
    return list(res_dict.values())


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
        if best_key and 0 <= comp - int(best_key) <= 1:
            value = address_dict[best_key]
            return (best_key, *value)
        
    return None


def classify_pipeline(
    raw_input: str,
    automaton: dict[str, dict[str, Any]],
    address_type: Literal["provinces", "districts", "wards"],
    last_output: tuple[str, tuple[int | str, str, str, str]] | None = None
):
    
    _, last_address = last_output or (None, None)
    normalized_input = to_normalized(raw_input)

    output = check_address(normalized_input, automaton["normalized"][address_type], last_address)
    if output:
        start = int(output[0]) - len(output[3])
        raw_input = raw_input[0:start] + "," + raw_input[start:]
        output = (int(output[0]) + 1, output[1], output[2], output[3])
        return raw_input, output

    diacritics_input = to_diacritics(normalized_input)
    output = check_address(diacritics_input, automaton["diacritics"][address_type], last_address)
    if output:
        start = int(output[0]) - len(output[3])
        raw_input = raw_input[0:start] + "," + raw_input[start:]
        output = (int(output[0]) + 1, output[1], output[2], output[3])
        return raw_input, output

    return output

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
    
    abbrev_dict = {
        "provinces" : ["t", "p"],
        "districts" : ["h", "q", "t"],
        "wards" : ["p", "x", "t"]
    }
    
    prefix_dict = {
        "provinces" : ["tỉnh", "thành phố"],
        "districts" : ["huyện", "quận", "thị xã", "thành phố"],
        "wards" : ["phường", "xã", "thị trấn"]
    }
    actual_output = None
    input_to_split = input
    input_used = input
    index_found = len(input_to_split)
    slides_diff = 0
    if last_output:
        input_used = last_output[0]
        input_to_split = last_output[0].split(",")[0]
        index_found = int(last_output[1][0]) - len(last_output[1][3]) - 1
        
    inputs = input_to_split.split()   
    for slide in window_slide(inputs, 2, 3):
        combined_input = " ".join(slide)
        output = find_best_match_advanced(combined_input, address_type, bktree)    
        if output:
            actual_output = output
            index_found -= len(combined_input) - len(output["query"])
            slides_diff = len(slide) - output["word_count"]
            break
        
        if combined_input[0] in abbrev_dict[address_type]:
            output = find_best_match_advanced(combined_input[1:], address_type, bktree)    
            if output:
                actual_output = output
                index_found -= len(combined_input) - len(output["query"])
                slides_diff = len(slide) - output["word_count"]
                break
    if not actual_output:
        return actual_output
            
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
    
    if check_1_token and check_1_token in prefix_dict[address_type]:
        detected = check_1_token + " " + actual_output["query"]
        prefix = check_1_token
    elif check_2_token and check_2_token in prefix_dict[address_type]:
        detected = check_2_token + " " + actual_output["query"]
        prefix = check_2_token            
    elif check_1_token and check_1_token_second and check_1_token_second in prefix_dict[address_type]:
        detected = check_1_token_second + " " + actual_output["query"]
        prefix = check_1_token_second
        full_output = (index_found, actual_output["match"], prefix, detected)
        start = index_found - len(detected) - 1 - 2 - len(check_1_token)
        raw_input = input_used[0:start] + "," + input_used[start:]
        return raw_input, full_output
    
    full_output = (index_found, actual_output["match"], prefix, detected)
    start = index_found - len(detected) - 1 
    raw_input = input_used[0:start] + "," + input_used[start:]
    
    return raw_input, full_output


def full_pipeline(
    raw_input: str,
    automaton: dict[str, dict[str, Any]],
    bktree: dict[str, Any]
):
    parts = [p.strip() for p in raw_input.split(",")]
    
    can_province_none = False if parts[-1] else True
    can_district_none = True if len(parts) >= 2 and not parts[-2] else False
    can_ward_none = True if len(parts) >= 3 and not parts[-3] else False
    
    input = to_normalized(raw_input)

    province = (
        classify_pipeline(input, automaton, "provinces") or 
        spelling_detect(input, bktree, "provinces")
    ) if not can_province_none else None
    province_input = province[0] if province else input
    
    district = (
        classify_pipeline(province_input, automaton, "districts", province) or 
        spelling_detect(province_input, bktree, "districts", province)
    ) if not can_district_none else None
    
    district_input = district[0] if district else province_input
    
    ward = (
        classify_pipeline(district_input, automaton, "wards", district or province) or
        spelling_detect(district_input, bktree, "wards", district or province)
    ) if not can_ward_none else None
    
    return  (
        province[1][1] if province else None, 
        district[1][1] if district else None,
        ward[1][1] if ward else None
    )