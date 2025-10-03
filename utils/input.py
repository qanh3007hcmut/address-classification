import re

ALIAS_SINGLE_MAP = {
    "thành phố hồ chí minh": ["tphcm"],
    "thành phố": ["tp", "tpho"],
    "thị trấn": ["tt", "ttr","thi tran"],
    "thị xã": ["tx", "tỉnh xã"],
    "phường": ["p", "phuong", "phưng"],
    "huyện": ["h", "huyen"],
    "tỉnh": ["t", "tnh"],
    "quận": ["q", "quan"],
    "xã": ["x", "xa"],
}

ALIAS_MULTI_MAP = {
    "thành phố": ["tỉnh phố", "tỉnh phô", "tỉnh pho"],
    "thị trấn": ["thi tran"],
    "thị xã": ["tỉnh xã"],
}

ALIAS_PLACE = {
    "thừa thiên huế": ["tth"],
    "hồ chí minh": ["hcm"],
    "hà nội": ["hn"],
    "đống đa": ["đ. đa"]
}

def sort_dict(d: dict[str, list], reverse = False) -> dict[str, list]:
    return {k: v for k, v in sorted(d.items(), key=lambda item: len(item[0]), reverse=reverse)}

ALIAS_MAP = sort_dict(ALIAS_SINGLE_MAP)
ALIAS_PLACE = sort_dict(ALIAS_PLACE)

import re

def normalize_input(s: str) -> str:
    """Chuẩn hóa input: lowercase, space hợp lý, tách số và chữ."""
    s = s.strip()
    s = re.sub(r",\s*", ", ", s)                 
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)  
    # chèn space giữa chữ và số, bất kể hướng nào
    s = re.sub(r"(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])", " ", s)
    s = re.sub(r"\.\s*", ". ", s)                  
    s = re.sub(r"\s+", " ", s)            
    return s.lower().strip()


def build_single_rules(alias : dict) :
    pattern_dict = {}
    for replacement, aliases in alias.items():
        pattern_dict[" " + replacement + " "] = r'(?:(^|,\s*|\s+))\b(?:' + '|'.join(map(re.escape, aliases)) + r')\b(\.|\s|$)'
    return pattern_dict

def build_multi_rules(alias : dict) :
    pattern_dict = {}
    for replacement, aliases in alias.items():
        pattern_dict[replacement + " "] = r'\b(?:' + '|'.join(map(re.escape, aliases)) + r')'
    return pattern_dict

def replace_alias(text : str):
    result = text
    
    # Xử lý riêng cho "f." special case
    result = re.sub(r'(?:^|\s)f\.(?=\s|$)', ' phường ', result, flags=re.IGNORECASE)
    
    single_rules = build_single_rules(ALIAS_SINGLE_MAP)
    multi_rules = build_multi_rules(ALIAS_MULTI_MAP)
    rules_place = build_single_rules(ALIAS_PLACE)
    
    for replace, pattern in single_rules.items():
        result = re.sub(pattern, replace, result, flags=re.IGNORECASE)
        result = re.sub(r"\s+", " ", result)              
            
    for replace, pattern in multi_rules.items():
        result = re.sub(pattern, replace, result, flags=re.IGNORECASE)
        result = re.sub(r"\s+", " ", result)   
                       
    for replace, pattern in rules_place.items():
        result = re.sub(pattern, replace, result, flags=re.IGNORECASE)  
    
    result = re.sub(r"\s+", " ", result).strip()
    return result

def add_comma_before_administrative(text: str) -> str:
    """Thêm dấu phẩy trước các từ administrative."""
    administrative_terms = r'\b(?:thành phố|thị trấn|thị xã|tỉnh|huyện|quận|phường|(?<!thị )xã)\b'
    return re.sub(rf'(?<!^)(?<!,\s)(?<!,)\s*({administrative_terms})', r', \1', text)

def final_normalize(s:str):
    # Bỏ số 1-2 chữ số không đứng sau "quận" hoặc "phường"
    s = re.sub(r"(?<!quận\s)(?<!phường\s)\b\d{1,2}\b", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s)      
    return s.strip()

def preprocess_input(text: str) -> str:
    """Chuẩn hóa input: lowercase, space hợp lý, tách số và chữ."""
    text = normalize_input(text)
    text = replace_alias(text)
    text = add_comma_before_administrative(text)
    text = final_normalize(text)
    return text

def select_candidate(candidates, parts):
    rev_parts = [part.strip() if part.strip() else None for part in parts][::-1]
    best = None
    best_order_matches = 0
    
    for cand in candidates:
        norm_tuple = cand[4]
        order_matches = 0
        
        # Đếm khớp theo thứ tự
        for i in range(min(len(rev_parts), len(norm_tuple))):
            if any([
                rev_parts[i] and norm_tuple[i] and rev_parts[i] == norm_tuple[i], 
                not rev_parts[i] and not norm_tuple[i]
            ]):
                order_matches += 1
            else:
                break

        if order_matches > best_order_matches:
            best_order_matches = order_matches
            best = cand

    return [best] if best and best_order_matches > 0 else candidates
