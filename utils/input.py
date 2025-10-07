import re

from utils.preprocess import to_diacritics, to_normalized, to_nospace

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
    "thành phố": ["tỉnh phố", "tỉnh phô", "tỉnh pho", "tỉnh phường"], 
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
    s = re.sub(r"([a-zđ])([A-ZĐ])", r"\1 \2", s)
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
    # B1: thêm dấu phẩy trước từ hành chính (nếu chưa có)
    text = re.sub(rf'(?<!^)(?<!,\s)(?<!,)\s*({administrative_terms})', r', \1', text)
    # B2: xóa dấu phẩy thừa ngay sau từ hành chính
    text = re.sub(rf'({administrative_terms})\s*,\s*', r'\1 ', text)
    return text

def final_normalize(s:str):
    # Bỏ số 1-2 chữ số không đứng sau "quận" hoặc "phường"
    s = re.sub(r"(?<!quận\s)(?<!phường\s)\b\d{1,2}\b", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s)      
    return s.strip()

def partial_select(input:str):
    parts = input.split(",")
    
    if(len(parts) > 3): return ", ".join(parts[-3:])
    return input

def preprocess_input(text: str) -> str:
    """Chuẩn hóa input: lowercase, space hợp lý, tách số và chữ."""
    text = normalize_input(text)
    text = replace_alias(text)
    text = add_comma_before_administrative(text)
    text = final_normalize(text)
    # text = partial_select(text)
    return text

def select_candidate_by_order_administrative(candidates, input: str):
    if len(candidates) == 1:
        return candidates
    
    processed_input = preprocess_input(input)
    parts = processed_input.split(",")
    
    def calc_order_score(cand):
        """Tính điểm sắp xếp cho một ứng viên"""
        if (
            len(parts) > 1 
            and all(len(p.split()) <= 3 for p in parts)
        ):
            rev_parts = [part.strip() if part.strip() else None for part in parts][::-1]
            norm_tuple = cand[4]
            order_matches = 0
            for i in range(min(len(rev_parts), len(norm_tuple))):
                rev, norm = rev_parts[i], norm_tuple[i]
                if rev and norm and rev == norm:
                    order_matches += 100
                elif not rev and not norm:
                    order_matches += 50
                elif rev and norm and norm in rev:
                    pos = rev.find(norm)
                    order_matches += pos + 1 + len(norm)
                else:
                    break
            return order_matches
        else:
            output_tuple = reversed(cand[0])
            norm_tuple = reversed(cand[4])
            
            score = 0
            order_matches = True
            prev_pos = -1
            for output, norm in zip(output_tuple, norm_tuple):
                if not norm: continue
                normalized = to_normalized(output)
                diacritics = to_diacritics(normalized)
                nospace = to_nospace(diacritics)
                pos = -1
                if(normalized == norm):
                    pos = processed_input.find(normalized)
                elif(diacritics == norm):
                    pos = processed_input.find(diacritics)
                elif(nospace == norm):
                    pos = processed_input.find(nospace)     
                else:
                    score -= 100
                    
                if pos != -1:
                    if pos < prev_pos:
                        order_matches = False
                        break
                    else:
                        prev_pos = pos
                        score += pos + 2*len(norm)
            
            if not order_matches: 
                score = -100
                
            return score
                    

    # Sắp xếp giảm dần theo điểm tính được
    return sorted(candidates, key=calc_order_score, reverse=True)

def align_candidate(input : str, candidate_norm):
    """
    parts: list[str]
    candidate_norm: tuple (province, district, ward) đã normalize
    """
    indexes = []
    for norm in candidate_norm:
        if norm:
            idx = input.find(norm)
            indexes.append(idx if idx >= 0 else None)
        else:
            indexes.append(None)
    return indexes


def select_candidate_by_order_administrative_v2(candidates, input : str):
    from collections import defaultdict
    groups = defaultdict(list)

    for cand in candidates:
        norm_tuple = tuple(reversed(cand[4]))
        idxs = align_candidate(input, norm_tuple)

        # Tính điểm
        score = 0
        valid_order = True
        prev = -1
        for idx in idxs:
            if idx is not None:
                score += 100 + idx  # exact match
                if idx < prev:  # sai thứ tự
                    valid_order = False
                prev = idx
        if valid_order:
            score += 200  # bonus giữ đúng thứ tự

        groups[score].append(cand)

    return groups[max(groups)] 
 