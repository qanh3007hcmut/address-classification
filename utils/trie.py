from typing import Literal
from utils.preprocess import to_diacritics, to_normalized, to_nospace
from utils.input import preprocess_input

def build_automaton(
    dictionary: list[str], 
    address_type: Literal["provinces", " districts", "wards"],
    prefix_dict : dict[str, dict[str, dict[str, list[str]]]],
):
    import ahocorasick
    def get_abbreviation(address: str):
        input = address.lower().split()
        return "".join([word[0] for word in input])
    
    A_normalized = ahocorasick.Automaton()
    A_diacritics = ahocorasick.Automaton()
    A_nospace = ahocorasick.Automaton()

    for word in dictionary:
        if not word:
            continue
        variants: dict[str, str] = {"": word}

        for prefix in prefix_dict["full"]["normalized"][address_type]:
            variants[prefix + " "] = prefix + " " + word
            # variants[get_abbreviation(prefix) + " "] = (get_abbreviation(prefix) + " " + word)
    
            variants[prefix] = prefix + word
            variants[get_abbreviation(prefix)] = get_abbreviation(prefix) + word

        if word.isdigit() or word in ["I", "III", "IV", "V", "VII"]:
            variants.pop("")
            

        for k, v in variants.items():

            var_normalized = to_normalized(v)
            var_diacritics = to_diacritics(var_normalized)
            var_nospace = to_nospace(var_diacritics)

            pref_normalized = to_normalized(k)
            pref_diacritics = to_diacritics(pref_normalized)
            pref_nospace = to_nospace(pref_diacritics)

            # if var_normalized != var_diacritics:
            # if not word.isdigit():
            A_normalized.add_word(var_normalized, (pref_normalized, [word], len(var_normalized)))
            
            if var_diacritics in A_diacritics:
                pref, words, l = A_diacritics.get(var_diacritics)
                if word not in words:
                    words.append(word)
                A_diacritics.add_word(var_diacritics, (pref, words, l))
            else:
                A_diacritics.add_word(var_diacritics, (pref_diacritics, [word], len(var_diacritics)))

            # nospace: gom nhiều word vào list
            if var_nospace in A_nospace:
                pref, words, l = A_nospace.get(var_nospace)
                if word not in words:
                    words.append(word)
                A_nospace.add_word(var_nospace, (pref, words, l))
            else:
                A_nospace.add_word(var_nospace, (pref_nospace, [word], len(var_nospace)))

    A_normalized.make_automaton()
    A_diacritics.make_automaton()
    A_nospace.make_automaton()
    return A_normalized, A_diacritics, A_nospace


def build_all_automaton(data: dict, prefix_dict):  # -> dict[str, dict[Any, Any]]:
    automaton = {
        "normalized": {},
        "diacritics": {},
        "nospace": {},
    }
    for k, v in data.items():
        (
            automaton["normalized"][k],
            automaton["diacritics"][k],
            automaton["nospace"][k],
        ) = build_automaton(v, k,prefix_dict)
    return automaton


def check_automaton(automaton, input: str):
    result: list[tuple[str, str, str]] = []
    best_candidates: dict[str, list[tuple[str, str, str]]] = {}

    for end, (prefix, words, length) in automaton.iter(input):
        start = end - length + 1

        for word in words:
            if word.isdigit():
                if (end + 1) < len(input) and input[end + 1].isdigit():
                    continue  # skip candidate vì bị cắt số

            remaining, origin = remove_detected(input, (start, end))
            remaining, origin = to_normalized(remaining), to_normalized(origin)
            candidate = (remaining, prefix, origin)

            if word not in best_candidates:
                best_candidates[word] = [candidate]
            else:
                current_best_len = len(best_candidates[word][0][0]) + len(best_candidates[word][0][1])
                new_len = len(remaining)
                if new_len < current_best_len:
                    best_candidates[word] = [candidate]
                elif new_len == current_best_len:
                    if candidate not in best_candidates[word]:
                        best_candidates[word].append(candidate)

            result.append((word, remaining, prefix))

    # flatten thành list
    return [(k, rem, pre, org) for k, vals in best_candidates.items() for rem, pre, org in vals]

def remove_detected(input: str, detected: tuple[int, int]):
    return input[: detected[0]] + input[detected[1] + 1 :], input[detected[0] : detected[1]+1]


def detect_with_last(automaton, input_remaining, last_value, last_prefix, last_org):
    if last_value: 
        return [(last_value, input_remaining, last_prefix, last_org)]
    return check_automaton(automaton, input_remaining) + [(last_value, input_remaining, last_prefix, last_org)]

def classify_case(addr):
    labels = ["province", "district", "ward"]
    present = [label for value, label in zip(addr, labels) if value]
    return ", ".join(present) if present else "none"


def count_diacritics(text: str) -> int:
    import unicodedata

    count = 0
    for ch in text:
        decomp = unicodedata.normalize("NFD", ch)
        # Nếu ký tự sau khi phân rã có chứa "combining mark" => là ký tự có dấu
        if any(unicodedata.category(c) == "Mn" for c in decomp):
            count += 1
    return count


def score(
    address: tuple[str | None, str | None, str | None] = (None, None, None),
    prefix: tuple[str | None, str | None, str | None] = (None, None, None),
    remaining=None,
    processor=None,
    origin: tuple[str | None, str | None, str | None] = (None, None, None)
):
    weight = {
        "address": 50,
        "diacritics": 30,
        "address_detected": 30,
        "prefix": 50,
        "remaining": 25,
    }
    processor_dict = {"normalized": 3, "diacritics": 2, "nospace": 1, None: 0}
    province, district, ward = address
    province_org, district_org, ward_org = origin
    province_prefix, district_prefix, ward_prefix = prefix

    # component scoring order: (name, score base, current, last)
    components = [
        ("provinces", 3, province, province_prefix, province_org),
        ("districts", 2, district, district_prefix, district_org),
        ("wards", 1, ward, ward_prefix, ward_org),
    ]
    address_sc, addr_detected_sc, diacritic_sc, prefix_sc, size_total = 0, 0, 0, 0, 1
    for _, base_score, current, pref, org in components:
        if current:
            address_sc += base_score
            # if processor == "normalized":
            #     diacritic_sc += count_diacritics(current)
            if org:
                size_total += len(org)
                normalized_input = to_normalized(current)
                diacritics_input = to_diacritics(normalized_input)
                nospace_input = to_nospace(diacritics_input)
                if normalized_input in org and normalized_input != diacritics_input:
                    addr_detected_sc += processor_dict["normalized"]
                    diacritic_sc += count_diacritics(normalized_input) * processor_dict["normalized"]
                elif diacritics_input in org:
                    addr_detected_sc += processor_dict["diacritics"]
                elif nospace_input in org:
                    addr_detected_sc += processor_dict["nospace"]
                        
            if pref:
                prefix_sc += len(pref)
                prefix_sc += count_diacritics(pref)
                

    remaining_sc = float(size_total / len(remaining)) if remaining else 10000
    # processor_sc = processor_dict[processor] if processor else 0

    return int(
        address_sc * weight["address"]
        + diacritic_sc * weight["diacritics"]
        # + processor_sc * weight["processor"]
        + addr_detected_sc * weight["address_detected"]
        + prefix_sc * weight["prefix"]
        + int(remaining_sc * weight["remaining"])
    )


def classify_with_trie(
    input: str,
    automaton: dict,
    processor: Literal["normalized", "diacritics", "nospace"],
    last_output: tuple[str | None, str | None, str | None] = (None, None, None),
    last_origin: tuple[str | None, str | None, str | None] = (None, None, None),
    last_prefix: tuple[str, str, str] = ('', '', ''),
):
    candidates = []
    groups = {}
    normalized_input = to_normalized(input)
    diacritics_input = to_diacritics(normalized_input)
    nospace_input = to_nospace(diacritics_input)
    processed_input = (
        normalized_input if processor == "normalized" else 
        diacritics_input if processor == "diacritics" else 
        nospace_input
    )
    last_province, last_district, last_ward = last_output
    last_origin_province, last_origin_district, last_origin_ward = last_origin
    last_prefix_province, last_prefix_district, last_prefix_ward = last_prefix

    for detected_province, province_remaining, province_prefix, province_org in detect_with_last(
        automaton[processor]["provinces"],
        processed_input,
        last_province,
        last_prefix_province,
        last_origin_province
    ):
        for detected_district, district_remaining, district_prefix, district_org in detect_with_last(
            automaton[processor]["districts"],
            province_remaining,
            last_district,
            last_prefix_district,
            last_origin_district
        ):
            for detected_ward, ward_remaining, ward_prefix, ward_org in detect_with_last(
                automaton[processor]["wards"],
                district_remaining,
                last_ward,
                last_prefix_ward,
                last_origin_ward
            ):
                if all([
                    last_province, (detected_province == last_province),
                    last_district, (detected_district == last_district),
                    last_ward, (detected_ward == last_ward),
                    last_prefix_province ,(province_prefix == last_prefix_province),
                    last_prefix_district, (district_prefix == last_prefix_district),
                    last_prefix_ward, (ward_prefix == last_prefix_ward),
                ]):
                    continue
                output = (
                    (detected_province, detected_district, detected_ward),
                    ward_remaining,
                    (province_prefix, district_prefix, ward_prefix),
                    score(
                        (detected_province, detected_district, detected_ward),
                        (province_prefix, district_prefix, ward_prefix),
                        ward_remaining,
                        processor,
                        (province_org, district_org, ward_org)
                    ),
                    (province_org, district_org, ward_org),
                )
                candidates.append(output)
                case = classify_case(
                    (detected_province, detected_district, detected_ward)
                )
                if groups.get(case):
                    if groups[case][0][3] < output[3]:
                        groups[case] = [output]
                    elif groups[case][0][3] == output[3]:
                        groups[case].append(output)
                else:
                    groups[case] = [output]

    # return sorted([val for val in groups.values()], key=lambda x: x[2], reverse=True)
    # return [val for vals in groups.values() for val in vals]
    return candidates


def trie_pipeline(
    input: str, 
    automaton: dict, 
):
    # input_tmp = normalize_input(input)
    input = preprocess_input(input)
    normalized_outputs = classify_with_trie(input, automaton, processor="normalized")

    trie_results = {}
    for (
        normalized_address,
        normalized_remaining,
        normalized_prefix,
        normalized_score,
        normalized_origin
    ) in normalized_outputs:
        if all(normalized_address) and all(normalized_prefix) and not normalized_remaining:
            return [(
                normalized_address,
                normalized_remaining,
                normalized_prefix,
                normalized_score,
                normalized_origin
            )]

        diacritics_outputs = classify_with_trie(
            normalized_remaining,
            automaton,
            "diacritics",
            normalized_address,
            normalized_origin,
            normalized_prefix,
        )
        better_diacritics = False

        for (
            diacritics_address,
            diacritics_remaining,
            diacritics_prefix,
            diacritics_score,
            diacritics_origin
        ) in diacritics_outputs:
            # if all(diacritics_address) and not diacritics_remaining:
            #     return [(diacritics_address, diacritics_remaining, diacritics_score)]

            if (
                ((all(diacritics_address) and not diacritics_remaining) or diacritics_score >= normalized_score)
                and
                (not trie_results.get(diacritics_address) or trie_results[diacritics_address][3] < diacritics_score)
            ):
                trie_results[diacritics_address] = (
                    diacritics_address,
                    diacritics_remaining,
                    diacritics_prefix,
                    diacritics_score,
                    diacritics_origin
                )
                better_diacritics = True
                continue

            nospace_outputs = classify_with_trie(
                diacritics_remaining,
                automaton,
                "nospace",
                diacritics_address,
                diacritics_origin,
                diacritics_prefix,
            )
            for (
                nospace_address,
                nospace_remaining,
                nospace_prefix,
                nospace_score,
                nospace_origin
            ) in nospace_outputs:
                # if all(nospace_address) and not nospace_remaining:
                #     return [(nospace_address, nospace_remaining, nospace_score)]

                if (
                    (
                        (all(nospace_address) and not nospace_remaining) or 
                        (nospace_score >= diacritics_score and nospace_score >= normalized_score)
                    ) and 
                    (
                        not trie_results.get(nospace_address) or
                        trie_results[nospace_address][3] < nospace_score
                    )
                ):
                    trie_results[nospace_address] = (
                        nospace_address,
                        nospace_remaining,
                        nospace_prefix,
                        nospace_score,
                        nospace_origin
                    )
                    
                    continue

        if not better_diacritics and (not trie_results.get(normalized_address) or trie_results[normalized_address][3] < normalized_score):
            trie_results[normalized_address] = (
                normalized_address,
                normalized_remaining,
                normalized_prefix,
                normalized_score,
                normalized_origin
            )
    
    trie_results = sorted(
        [res for res in trie_results.values()], key=lambda x: x[3], reverse=True
    )
    from itertools import groupby
    # _, group = next(groupby(trie_results, key=lambda x: x[3]))
    # best_results = list(group)
    # return best_results
    
    groups = groupby(trie_results, key=lambda x: x[3])
    top_groups = []
    max_sc = 0
    for score, group in groups:
        max_sc = max(max_sc , score)
        if score >= max_sc - 160:
            top_groups.extend(list(group))
        else: break

    return top_groups
    
