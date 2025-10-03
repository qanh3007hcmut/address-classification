def get_data():
    keys = ["provinces", "districts", "wards"]
    data: dict[str, list] = {}
    for key in keys:
        data[key] = []
        with open(f"data/{key}.txt", "r", encoding="utf-8-sig") as f:
            for line in f:
                address = (
                    line[: len(line) - 1]
                    .replace("Thành phố ", "", 1)
                    .replace("Thị Trấn ", "", 1)
                    .replace("Thị trấn ", "", 1)
                    .replace("Thị Xã ", "", 1)
                    .replace("Thị xã ", "", 1)
                    .replace("Quận ", "", 1)
                    .replace("Tỉnh ", "", 1)
                    .replace("Huyện ", "", 1)
                    .replace("Xã ", "", 1)
                    .replace("Phường ", "", 1)
                )
                data[key].append(address)

    return data

def get_prefix_dict():
    from utils.preprocess import to_nospace, to_normalized, to_diacritics
    
    full = {
        "provinces": ["thành phố", "tỉnh"],
        "districts": ["thành phố", "thị xã", "huyện", "quận"],
        "wards": ["thị trấn", "phường", "xã"],
    }
    abbreviation = {}
    for k, v in full.items():
        temp = set()
        [temp.add(get_abbreviation(e)) for e in v]
        [temp.add(get_abbreviation(e, " ")) for e in v]
        abbreviation[k] = list(temp)
  
    return {
        "full" : {
            "normalized" : {k: [to_normalized(e) for e in v] for k, v in full.items()},
            "diacritics" : {k: [to_diacritics(to_normalized(e)) for e in v] for k, v in full.items()},
            "nospace" : {k: [to_nospace(e) for e in v] for k, v in full.items()}
        },
        "abbreviation" : {
            "normalized" : {k: [to_normalized(e) for e in v] for k, v in abbreviation.items()},
            "diacritics" : {k: [to_diacritics(to_normalized(e)) for e in v] for k, v in abbreviation.items()},
            "nospace" : {k: [to_nospace(e) for e in v] for k, v in abbreviation.items()}
        }
    }
    

def get_abbreviation(address: str, sep: str = "") -> str:
    parts = address.lower().split()
    return sep.join(word[0] for word in parts)
        
def deletePrefix(address: str):
    return (
        address.replace("Thành phố ", "", 1)
        .replace("Thị Trấn ", "", 1)
        .replace("Thị trấn ", "", 1)
        .replace("Thị Xã ", "", 1)
        .replace("Thị xã ", "", 1)
        .replace("Quận ", "", 1)
        .replace("Tỉnh ", "", 1)
        .replace("Huyện ", "", 1)
        .replace("Xã ", "", 1)
        .replace("Phường ", "", 1)
    )

def unique_addresses(records):
    seen = set()
    unique = []
    
    for rec in records:
        key = rec.get("address")
        if key not in seen:
            seen.add(key)
            unique.append(rec)
    
    return unique
