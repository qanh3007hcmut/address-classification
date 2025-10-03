def to_normalized(address: str):
    import unicodedata

    address = address.lower()
    res = []
    number = []

    def flush_number():
        """Đưa số ra res nếu hợp lệ, ngược lại bỏ qua"""
        nonlocal number
        if number:
            num_str = "".join(number)
            if len(num_str) < 3 and not (len(num_str) == 2 and int(num_str) > 61):
                res.append(num_str)
            number = []

    for ch in address:
        if ch in {",", ".", "-", "/"}:
            flush_number()
            res.append(" ")  # thay bằng khoảng trắng
        elif ch.isdigit():
            number.append(ch)
        else:
            cat = unicodedata.category(ch)
            if cat.startswith("L") or ch.isspace():
                flush_number()
                res.append(ch)
            # ký tự khác thì bỏ qua

    # xử lý nếu kết thúc bằng số
    flush_number()

    # gom lại, loại bớt khoảng trắng thừa
    return " ".join("".join(res).split())

def to_diacritics(address : str) :
    import unicodedata
    nfkd_form = unicodedata.normalize('NFD', address)
    nfkd_form = ''.join([c for c in nfkd_form if unicodedata.category(c) != 'Mn'])
    return nfkd_form.replace("đ", "d")

# Only apply for building automaton (not input)
def to_nospace(address : str):
    return address.replace(" ", "")


def remove_diacritics(s: str) -> str:
    import unicodedata
    res = []
    for ch in s:
        # tách NFD để xem ký tự này có dấu không
        decomp = unicodedata.normalize("NFD", ch)
        # nếu ký tự gốc có dấu (có Mn đi kèm) thì bỏ luôn
        if any(unicodedata.category(c) == "Mn" for c in decomp):
            continue
        res.append(ch)
    return "".join(res)

def normalize_input(address_input):
    """
    Normalize Vietnamese address input for consistent parsing.

    This function standardizes address strings by:
    1. Cleaning whitespace, dot at last word and converting to lowercase
    2. Adding proper spacing around punctuation
    3. Handling prefix letters next to digits (p1 -> p. 1, q11 -> q. 11)
    4. Separating concatenated prefecture words from location names
    5. Handling abbreviated prefecture indicators
    6. Expanding abbreviated prefixes with dots
    7. Adding commas before administrative prefixes when missing

    Args:
        address_input (str): Raw Vietnamese address string

    Returns:
        str: Normalized address string ready for component extraction

    Examples:
        >>> normalize_input("P1,Q1,TPHCM")
        "p. 1, q. 1, tp. hcm"

        >>> normalize_input("Đăk Nang H. Krông Nô TĐắk Nông")
        "đăk nang, h. krông nô, tđắk nông"

        >>> normalize_input("x my thành,huyệncai lậy")
        "x. my thành, huyện cai lậy"

        >>> normalize_input("Nguyễn Khuyến Thị trấn Vĩnh Trụ, Lý Nhân, Hà Nam")
        "nguyễn khuyến, thị trấn vĩnh trụ, lý nhân, hà nam"
    """
    import re

    # Step 1: Basic normalization - lowercase, clean whitespace, remove "-" and dot at last word
    normalized = " ".join(address_input.lower().split())
    normalized = normalized.replace("-", "")
    normalized = normalized.rstrip(".")
    # print(f"Step 1 - Basic normalization: '{normalized}'")

    # Step 2: Add space after commas for consistent parsing
    normalized = re.sub(r",(?=\S)", ", ", normalized)
    # print(f"Step 2a - After adding space after commas: '{normalized}'")

    # Step 2b: Add space after dots (always normalize)
    normalized = re.sub(r"\.(?=\S)", ". ", normalized)
    # print(f"Step 2b - After adding space after dots: '{normalized}'")

    # Step 3: Expand standalone prefix letters with dots
    # Only match letters followed by SPACE and then letters (not digits)
    normalized = re.sub(r"\b([xhqtp])\s+(?=[a-zA-ZÀ-ỹ])", r"\1. ", normalized)
    # print(f"Step 3 - After expanding standalone prefixes: '{normalized}'")

    # Step 4: Handle prefix letters next to digit
    # First handle concatenated cases like "q1p2" -> "q. 1 p. 2"
    normalized = re.sub(r"([pq])(\d{1,2})([pq]\d{1,2})", r"\1. \2 \3", normalized)
    # Then handle the general case with word boundaries
    normalized = re.sub(r"\b([pq])(\d{1,2})\b", r"\1. \2", normalized)
    # Also handle cases where digits are followed by letters (like "p1huyện")
    normalized = re.sub(r"([pq])(\d{1,2})([a-zA-ZÀ-ỹ])", r"\1. \2 \3", normalized)
    # print(f"Step 4 - After handling prefix+digit (improved): '{normalized}'")

    # Step 5: Separate concatenated full prefecture words from location names
    normalized = re.sub(
        r"\b(huyện|quận|phường|xã|thị xã|thành phố|tỉnh|thị trấn)([a-zA-ZÀ-ỹ])",
        r"\1 \2",
        normalized,
    )
    # print(f"Step 5 - After separating concatenated words: '{normalized}'")

    # Step 6: Handle abbreviated concatenated prefixes
    # Match multi-letter abbreviations only
    normalized = re.sub(
        r"\b(tp|tx|tt)([a-zA-ZÀ-ỹ])", r"\1. \2", normalized
    )  # tp, tx, tt
    # print(f"Step 6 - After handling 'tp', 'tx', 'tt': '{normalized}'")

    # Step 7: Add commas before administrative prefixes when missing
    # This handles cases like "street name thị trấn ward name" -> "street name, thị trấn ward name"
    admin_prefixes = (
        r"\b(huyện|quận|phường|xã|thị xã|thành phố|tỉnh|thị trấn|tp\.|t\. phố|tx\.|tt\.|p\.|q\.|h\.|x\.)\s+"
    )

    # Find all administrative prefixes and add commas before them if not at beginning
    # Use a more careful approach to avoid double commas
    matches = list(re.finditer(admin_prefixes, normalized, flags=re.IGNORECASE))

    if matches:
        # Process matches from right to left to avoid position shifts
        for match in reversed(matches):
            start_pos = match.start()

            # Only add comma if the prefix is not at the beginning and not already preceded by comma/space-comma
            if start_pos > 0:
                # Check what's immediately before the match
                char_before = normalized[start_pos - 1]
                chars_before_2 = (
                    normalized[max(0, start_pos - 2) : start_pos]
                    if start_pos >= 2
                    else ""
                )

                # Skip inserting comma between 't.' and the following 'p.'/'phố'/'x.' (t. p./t. phố/t. x.)
                matched_prefix_text = normalized[start_pos : match.end()].lower()
                is_after_t = re.search(r"\bt\.\s*$", normalized[:start_pos], flags=re.IGNORECASE) is not None
                is_follow_token = re.match(r"^(p\.|phố|x\.)\s+", matched_prefix_text, flags=re.IGNORECASE) is not None
                if is_after_t and is_follow_token:
                    continue

                # Don't add comma if already preceded by comma (with or without space)
                if char_before != "," and chars_before_2 != ", ":
                    # Insert comma before the administrative prefix
                    normalized = normalized[:start_pos] + ", " + normalized[start_pos:]
    # print(f"Step 7 - After adding commas before administrative prefixes: '{normalized}'")
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized