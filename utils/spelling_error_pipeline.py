import re
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Set
from fuzzywuzzy import fuzz
import unicodedata

def has_accents(s: str) -> bool:
        return any('WITH' in unicodedata.name(c, '') for c in s if c.isalpha())

def break_ties(candidates: List[str], original: str) -> str:
        if re.match(r'^\d+$', original.strip()):
            for cand in candidates:
                if cand == original.strip():
                    print(f"Break_ties: Selected exact numeric match '{cand}' for original '{original}'")
                    return cand
        accented = [c for c in candidates if has_accents(c)]
        if accented:
            candidates = accented
        candidates.sort(key=lambda c: fuzz.ratio(c.lower(), original), reverse=True)
        print(f"Break_ties: Selected '{candidates[0]}' for original '{original}', fuzz ratio: {fuzz.ratio(candidates[0].lower(), original)}")
        return candidates[0]

def create_list(names: Set[str]) -> List[Tuple[str, str]]:
    return [(name.lower().replace(' ', ''), name) for name in names]


def extract_address_components(text: str, data : dict[str, list[Any]]) -> Dict[str, str]:
    # Helper: Check if string has Vietnamese accents
    def has_accents(s: str) -> bool:
        return any('WITH' in unicodedata.name(c, '') for c in s if c.isalpha())

    # Tie-breaker: Prefer exact numeric matches, then accented names, then fuzz ratio
    def break_ties(candidates: List[str], original: str) -> str:
        if re.match(r'^\d+$', original.strip()):
            for cand in candidates:
                if cand == original.strip():
                    print(f"Break_ties: Selected exact numeric match '{cand}' for original '{original}'")
                    return cand
        accented = [c for c in candidates if has_accents(c)]
        if accented:
            candidates = accented
        candidates.sort(key=lambda c: fuzz.ratio(c.lower(), original), reverse=True)
        print(f"Break_ties: Selected '{candidates[0]}' for original '{original}', fuzz ratio: {fuzz.ratio(candidates[0].lower(), original)}")
        return candidates[0]

    # Levenshtein distance
    def levenshtein(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    # Load data
    provinces = set(data["provinces"])
    districts = set(data["districts"])
    wards = set(data["wards"])

    # Create lists of (condensed, original)
    def create_list(names: Set[str]) -> List[Tuple[str, str]]:
        return [(name.lower().replace(' ', ''), name) for name in names]

    province_list = create_list(provinces)
    district_list = create_list(districts)
    ward_list = create_list(wards)

    # Define prefixes
    province_prefixes = ['', 'thành phố', 'thanh pho', 'thanhpho', 'tp', 'tp.', 't.p', 't', 'thnàh phố', 'thànhphố', 'tỉnh', 'tinh', 't.', 'tí', 'tinhf', 'tin', 'tnh', 't.phố', 't phố', 't.pho', 't pho']
    district_prefixes = ['', 'quận', 'quan', 'q', 'q.', 'qu', 'qaun', 'qận', 'huyện', 'huyen', 'h', 'h.', 'hu', 'hyuen', 'huyệ', 'thị xã', 'thi xa', 'thixa', 'tx', 'tx.', 't.x', 'th', 'txa', 'thịxa', 'thành phố', 'thanh pho', 'thanhpho', 'tp', 'tp.', 't.p', 'than', 'thanh', 'tph', 'thnàh phố', 'thànhphố', 't.xã', 't xã', 't.xa', 't xa', 't.phố', 't phố', 't.pho', 't pho']
    ward_prefixes = ['', 'phường', 'phuong', 'p', 'p.', 'ph', 'ph.', 'phuờng', 'phưng', 'puong', 'xã', 'xa', 'x', 'x.', 'xá', 'xạ', 'xãa', 'thị trấn', 'thi tran', 'thitran', 'tt', 'tt.', 't.t', 'th', 'ttr', 'thịtrấn', 't.trấn', 't tran', 't trấn', 't.tran']

    # Find best match for a level
    def find_match(tokens: List[str], reference_list: List[Tuple[str, str]], prefixes: List[str], level: str) -> Tuple[Optional[str], int]:
        print(f"\nMatching for {level} with tokens: {tokens}")
        all_matches: List[Tuple[str, int, int, int]] = []

        # Prefix-driven matching
        for i in range(len(tokens)):
            token = tokens[i].lower()
            if token in [p.lower() for p in prefixes if p]:
                max_words = min(4, len(tokens) - i - 1)
                for num_name_words in range(max_words, 0, -1):
                    name_cand = ' '.join(tokens[i + 1:i + 1 + num_name_words])
                    cand_lower = name_cand.lower()
                    cond_cand = cand_lower.replace(' ', '')
                    if not cond_cand:
                        continue
                    print(f"Trying candidate for {level}: '{name_cand}' (condensed: '{cond_cand}')")

                    if level == "ward" and re.match(r'^\d+$', cand_lower.strip()):
                        if cand_lower.strip() in [orig for _, orig in reference_list]:
                            print(f"Exact numeric ward match: '{cand_lower.strip()}'")
                            return cand_lower.strip(), num_name_words + 1

                    ref_len = len(cond_cand)
                    thresh = max(1, ref_len // 2)
                    matches = []
                    for cond_ref, orig in reference_list:
                        dist = levenshtein(cond_cand, cond_ref)
                        if dist <= thresh:
                            matches.append((orig, dist))
                    if matches:
                        min_dist = min(m[1] for m in matches)
                        best_candidates = [m[0] for m in matches if m[1] == min_dist]
                        best_orig = break_ties(best_candidates, cand_lower)
                        score = fuzz.ratio(best_orig.lower(), cand_lower)
                        print(f"Match for {level}: '{best_orig}', fuzz ratio: {score}, distance: {min_dist}")
                        if score >= 80:
                            all_matches.append((best_orig, score, min_dist, num_name_words + 1))
                            if score == 100 and num_name_words >= 2:
                                print(f"Exact match for {level}: '{best_orig}', consuming {num_name_words + 1} tokens")
                                return best_orig, num_name_words + 1

        # No-prefix matching, limited to tokens after the last prefix
        last_prefix_idx = len(tokens)
        for i in range(len(tokens) - 1, -1, -1):
            if tokens[i].lower() in [p.lower() for p in prefixes if p]:
                last_prefix_idx = i
                break
        for num_name_words in range(1, min(4, len(tokens) - last_prefix_idx) + 1):
            name_cand = ' '.join(tokens[-num_name_words:])
            cand_lower = name_cand.lower()
            cand_stripped = cand_lower
            print(f"Trying no-prefix candidate for {level}: '{name_cand}'")
            for prefix in [p.lower().replace(' ', '') for p in prefixes if p]:
                if cand_stripped.startswith(prefix):
                    cand_stripped = cand_stripped[len(prefix):].strip()
                    break
            cond_cand = cand_stripped.replace(' ', '')
            if not cond_cand:
                continue
            ref_len = len(cond_cand)
            thresh = max(1, ref_len // 2)
            matches = []
            for cond_ref, orig in reference_list:
                dist = levenshtein(cond_cand, cond_ref)
                if dist <= thresh:
                    matches.append((orig, dist))
            if matches:
                min_dist = min(m[1] for m in matches)
                best_candidates = [m[0] for m in matches if m[1] == min_dist]
                best_orig = break_ties(best_candidates, cand_lower)
                score = fuzz.ratio(best_orig.lower(), cand_lower)
                print(f"Match for {level}: '{best_orig}', fuzz ratio: {score}, distance: {min_dist}")
                if score >= 80:
                    all_matches.append((best_orig, score, min_dist, num_name_words))

        if all_matches:
            best_match = max(all_matches, key=lambda x: (x[1], -x[3], -x[2]))
            print(f"Selected best match for {level}: '{best_match[0]}', consuming {best_match[3]} tokens")
            return best_match[0], best_match[3]

        print(f"No match found for {level}")
        return None, 0

    # Main extraction logic
    print(f"\nProcessing address: '{text}'")
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    print(f"Normalized whitespace: '{text}'")
    segments = [segment.strip() for segment in text.split(',') if segment.strip()]
    print(f"Comma-separated segments: {segments}")

    prefix_counts = {'province': 0, 'district': 0, 'ward': 0}
    segment_prefixes = []
    tokens = []

    prefix_lists = {
        'province': sorted([p.lower().replace(' ', '') for p in province_prefixes if p], key=len, reverse=True),
        'district': sorted([p.lower().replace(' ', '') for p in district_prefixes if p], key=len, reverse=True),
        'ward': sorted([p.lower().replace(' ', '') for p in ward_prefixes if p], key=len, reverse=True)
    }

    expected_levels = ['province', 'district', 'ward']
    current_level_idx = 0

    for segment in reversed(segments):
        segment_lower = segment.lower()
        segment_condensed = segment_lower.replace(' ', '')
        segment_tokens = []
        prefix_found = False
        prefix_type = None
        matched_prefix = None

        levels_to_check = [expected_levels[current_level_idx]] + [level for level in expected_levels if level != expected_levels[current_level_idx]]
        for level in levels_to_check:
            prefixes_to_check = prefix_lists[level]
            for prefix in prefixes_to_check:
                if segment_condensed.startswith(prefix):
                    prefix_with_spaces = next(
                        (p for p in (province_prefixes if level == 'province' else
                                     district_prefixes if level == 'district' else
                                     ward_prefixes)
                         if p.lower().replace(' ', '') == prefix),
                        prefix
                    )
                    if segment_lower.startswith(prefix_with_spaces.lower()):
                        prefix_type = level
                        prefix_counts[prefix_type] += 1
                        matched_prefix = prefix_with_spaces
                        name_part = segment[len(prefix_with_spaces):].strip()
                        if not name_part and segment_condensed[len(prefix):].isdigit():
                            name_part = segment_condensed[len(prefix):]
                        if name_part:
                            segment_tokens.append(prefix_with_spaces.lower().replace(' ', ''))
                            segment_tokens.extend(name_part.split() if ' ' in name_part else [name_part])
                            print(f"Split segment '{segment}' into prefix '{prefix_with_spaces}' and name '{name_part}'")
                        else:
                            segment_tokens.append(prefix_with_spaces.lower().replace(' ', ''))
                            print(f"Split segment '{segment}' into prefix '{prefix_with_spaces}' (no name part)")
                        prefix_found = True
                        if level == expected_levels[current_level_idx] and current_level_idx < len(expected_levels) - 1:
                            current_level_idx += 1
                        break
            if prefix_found:
                break

        if not prefix_found:
            segment_tokens = segment.split()
            print(f"No prefix found in segment '{segment}', tokens: {segment_tokens}")
            if sum(prefix_counts.values()) == 0:
                current_level_idx = 0
            elif current_level_idx > 0 and prefix_counts[expected_levels[current_level_idx - 1]] == 0:
                current_level_idx -= 1

        segment_prefixes.append((segment, prefix_type, matched_prefix))
        tokens = segment_tokens + tokens

    total_prefixes = sum(prefix_counts.values())
    print(f"Prefix counts: {prefix_counts}, Total: {total_prefixes}")
    print(f"Final tokens: {tokens}")

    result = {"province": "", "district": "", "ward": ""}
    levels = [
        ("province", province_list, province_prefixes),
        ("district", district_list, district_prefixes),
        ("ward", ward_list, ward_prefixes)
    ]

    for level_name, reference_list, prefixes in levels:
        match, num_pop = find_match(tokens, reference_list, prefixes, level_name)
        if match:
            result[level_name] = match
            tokens = tokens[:-num_pop]
            print(f"Matched {level_name}: '{match}', remaining tokens: {tokens}")
        else:
            print(f"No {level_name} matched, remaining tokens: {tokens}")

    print(f"Extracted result: {result}")
    return result

def find_match(tokens: List[str], reference_list: List[Tuple[str, str]], prefixes: List[str], level: str) -> Tuple[Optional[str], int]:
    import Levenshtein
    all_matches: List[Tuple[str, int, int, int]] = []

    # Prefix-driven matching
    for i in range(len(tokens)):
        token = tokens[i].lower()
        if token in [p.lower() for p in prefixes if p]:
            max_words = min(4, len(tokens) - i - 1)
            for num_name_words in range(max_words, 0, -1):
                name_cand = ' '.join(tokens[i + 1:i + 1 + num_name_words])
                cand_lower = name_cand.lower()
                cond_cand = cand_lower.replace(' ', '')
                if not cond_cand:
                    continue
                print(f"Trying candidate for {level}: '{name_cand}' (condensed: '{cond_cand}')")

                if level == "ward" and re.match(r'^\d+$', cand_lower.strip()):
                    if cand_lower.strip() in [orig for _, orig in reference_list]:
                        print(f"Exact numeric ward match: '{cand_lower.strip()}'")
                        return cand_lower.strip(), num_name_words + 1

                ref_len = len(cond_cand)
                thresh = max(1, ref_len // 2)
                matches = []
                for cond_ref, orig in reference_list:
                    dist = Levenshtein.distance(cond_cand, cond_ref)
                    if dist <= thresh:
                        matches.append((orig, dist))
                if matches:
                    min_dist = min(m[1] for m in matches)
                    best_candidates = [m[0] for m in matches if m[1] == min_dist]
                    best_orig = break_ties(best_candidates, cand_lower)
                    score = fuzz.ratio(best_orig.lower(), cand_lower)
                    print(f"Match for {level}: '{best_orig}', fuzz ratio: {score}, distance: {min_dist}")
                    if score >= 80:
                        all_matches.append((best_orig, score, min_dist, num_name_words + 1))
                        if score == 100 and num_name_words >= 2:
                            print(f"Exact match for {level}: '{best_orig}', consuming {num_name_words + 1} tokens")
                            return best_orig, num_name_words + 1

    # No-prefix matching, limited to tokens after the last prefix
    last_prefix_idx = len(tokens)
    for i in range(len(tokens) - 1, -1, -1):
        if tokens[i].lower() in [p.lower() for p in prefixes if p]:
            last_prefix_idx = i
            break
    for num_name_words in range(1, min(4, len(tokens) - last_prefix_idx) + 1):
        name_cand = ' '.join(tokens[-num_name_words:])
        cand_lower = name_cand.lower()
        cand_stripped = cand_lower
        print(f"Trying no-prefix candidate for {level}: '{name_cand}'")
        for prefix in [p.lower().replace(' ', '') for p in prefixes if p]:
            if cand_stripped.startswith(prefix):
                cand_stripped = cand_stripped[len(prefix):].strip()
                break
        cond_cand = cand_stripped.replace(' ', '')
        if not cond_cand:
            continue
        ref_len = len(cond_cand)
        thresh = max(1, ref_len // 2)
        matches = []
        for cond_ref, orig in reference_list:
            dist = Levenshtein.distance(cond_cand, cond_ref)
            if dist <= thresh:
                matches.append((orig, dist))
        if matches:
            min_dist = min(m[1] for m in matches)
            best_candidates = [m[0] for m in matches if m[1] == min_dist]
            best_orig = break_ties(best_candidates, cand_lower)
            score = fuzz.ratio(best_orig.lower(), cand_lower)
            print(f"Match for {level}: '{best_orig}', fuzz ratio: {score}, distance: {min_dist}")
            if score >= 80:
                all_matches.append((best_orig, score, min_dist, num_name_words))

    if all_matches:
        best_match = max(all_matches, key=lambda x: (x[1], -x[3], -x[2]))
        print(f"Selected best match for {level}: '{best_match[0]}', consuming {best_match[3]} tokens")
        return best_match[0], best_match[3]

    print(f"No match found for {level}")
    return None, 0
