import re

(
    __CLEAN_SPACE__PATTERN__, 
    __CLEAN_SPACE__REPLACE__
) = (
    re.compile(r"(?:\s+)"),
    " ",
)

(
    __CLEAN_START_SPACE__PATTERN__,
    __CLEAN_START_SPACE__REPLACE__,
) = (
    re.compile(r"(?:^\s+)"), 
    ""
)

(
    __CLEAN_END_SPACE__PATTERN__,
    __CLEAN_END_SPACE__REPLACE__,
) = (
    re.compile(r"(?:\s+$)"), 
    ""
)

(
    __CLEAN_DOT_LEFT__PATTERN__,
    __CLEAN_DOT_LEFT__REPLACE__,
) = (
    re.compile(r"(?:\.+)"), 
    ""
)

(
    __ADD_SPACE_AFTER_COMMA__PATTERN__, 
    __ADD_SPACE_AFTER_COMMA__REPLACE__
) = (
    re.compile(r"(?:\s*,\s*)"),
    ", ",
)

(
    __ADD_SPACE_AFTER_DOT__PATTERN__, 
    __ADD_SPACE_AFTER_DOT__REPLACE__
) = (
    re.compile(r"(?:\s*\.\s*)"),
    ". ",
)

(
    __ADD_SPACE_UPPERCASE_WITH_COMMA_BEFORE__PATTERN__, 
    __ADD_SPACE_UPPERCASE_WITH_COMMA_BEFORE__REPLACE__
) = (
    re.compile(r"(?:(?<=^)|(?<=,\s))([A-Z])([A-Z])(?=[a-zà-ỹ]+)"),
    r"\1 \2",
)

(
    __SPLIT_LOWER_UPPER__PATTERN__, 
    __SPLIT_LOWER_UPPER__REPLACE__ 
) = (
    re.compile(r"([a-zà-ỹđ])([A-ZĐ])"),
    r"\1 \2",
)

(
    __DELETE_START_NUMBER__PATTERN__,
    __DELETE_START_NUMBER__REPLACE__,
) = (
    re.compile(r"(?:^\d+\s*)", re.IGNORECASE), 
    ""
)

(
    __DELETE_NUMBER_3_DIGITS__PATTERN__,
    __DELETE_NUMBER_3_DIGITS__REPLACE__,
) = (
    re.compile(r"(?:\d{3,}\s*)", re.IGNORECASE), 
    ""
)

(
    __DELETE_NUMBER_AFTER_DIACRITICS__PATTERN__,
    __DELETE_NUMBER_AFTER_DIACRITICS__REPLACE__,
) = (
    re.compile(r"(?:(?<=[à-ỹ])\d+)", re.IGNORECASE), 
    ""
)

(
    __DELETE_NUMBER_1_2_DIGITS_WITHOUT_WARD_DISTRICT__PATTERN__,
    __DELETE_NUMBER_1_2_DIGITS_WITHOUT_WARD_DISTRICT__REPLACE__,
) = (
    re.compile(r"(?:(?<!phường)(?<!p)(?<!quận)(?<!q)\s\d{1,2}\s*)", re.IGNORECASE), 
    " "
)

(
    __DELETE_NUMBER_1_2_DIGITS_WITHOUT_WARD_DISTRICT_NO_SPACE__PATTERN__,
    __DELETE_NUMBER_1_2_DIGITS_WITHOUT_WARD_DISTRICT_NO_SPACE__REPLACE__,
) = (
    re.compile(r"(?<!phường)(?<!p)(?<!quận)(?<!q)(?<!\s)(?<!\.)(?<!\d)(\d{1,2})\b", re.IGNORECASE), 
    " "
)
# ABBRERIATION

(
    __EXPAND_DISTRICT_WITH_NUMBERS__PATTERN__,
    __EXPAND_DISTRICT_WITH_NUMBERS__REPLACE__,
) = (
    re.compile(r"\b[q](\d{1,2})\b", re.IGNORECASE),
    r"quận \1"
)

(
    __EXPAND_WARD_WITH_NUMBERS__PATTERN__,
    __EXPAND_WARD_WITH_NUMBERS__REPLACE__,
) = (
    re.compile(r"\b[pf](\d{1,2})\b", re.IGNORECASE), 
    r"phường \1"
)

ALIAS_LONG_MAP = {
    "thành phố hồ chí minh": ["tphcm"],
    "thừa thiên huế": ["tỉnh tỉnh h", "tỉnh tỉnh huyện"],
    "thiên huế": ["tỉnh huế"],
    "thành phố": ["tp", "tpho", "tỉnh phố", "tỉnh phô", "tỉnh pho", "tỉnh p", "tỉnh phường"],
    "thị trấn": ["tt", "ttr", "thi tran", "tỉnh tỉnh"],
    "thị xã": ["tx", "thi xa", "thi xã", "thị xa", "tỉnh xã"],
    "phường": ["phưng"],
    "huyện": ["huyen"],
    "tỉnh": ["tnh"],
    # "quận": [],
    "xã": ["xa"],
}

ALIAS_ABBREV_MAP = {
    "phường": ["p", "f"],
    "huyện": ["h"],
    "tỉnh": ["t"],
    "quận": ["q"],
    "xã": ["x"],
}

ALIAS_ABBREV_WITH_DOT_REGEX_MAP = {
    repl: re.compile(
        rf"\b(?:{'|'.join(map(re.escape, aliases))})\b\.",
        re.IGNORECASE
    )
    for repl, aliases in ALIAS_ABBREV_MAP.items()
}

ALIAS_ABBREV_WITHOUT_DOT_WITH_COMMA_SPACE_REGEX_MAP = {
    repl: re.compile(
        rf"(?:(?<=^)|(?<=,\s))\b(?:{'|'.join(map(re.escape, aliases))})\b",
        re.IGNORECASE
    )
    for repl, aliases in ALIAS_ABBREV_MAP.items()
}

ALIAS_ABBREV_WITHOUT_DOT_REGEX_MAP = {
    repl: re.compile(
        rf"(?:(?<=^)|(?<=\s))\b(?:{'|'.join(map(re.escape, aliases))})(?=\b(?!'))",
        re.IGNORECASE
    )
    for repl, aliases in ALIAS_ABBREV_MAP.items()
}

ALIAS_LONG_REGEX_MAP = {
    repl: re.compile(
        rf"\b(?:{'|'.join(map(re.escape, aliases))})\b",
        re.IGNORECASE
    )
    for repl, aliases in ALIAS_LONG_MAP.items()
}

ALIAS_PLACE = {
    "thừa thiên huế": ["tth"],
    "hồ chí minh": ["hcm", "h. c. minh"],
    "hà nội": ["hn"],
    "đống đa": ["đ. đa"],
}

ALIAS_PLACE_REGEX_MAP = {
    repl: re.compile(
        rf"\b(?:{'|'.join(map(re.escape, aliases))})\b",
        re.IGNORECASE
    )
    for repl, aliases in ALIAS_PLACE.items()
}

(
    __ADD_COMMA_BEFORE_PREFIX__PATTERN__,
    __ADD_COMMA_BEFORE_PREFIX__REPLACE__
) = (
    re.compile(r"(?<!^)\s*(?<!,\s)(thành phố|tỉnh|thị xã|huyện|quận|phường)", re.IGNORECASE),
    r", \1"
)

(
    __ADD_SPACE_AFTER_PREFIX__PATTERN__,
    __ADD_SPACE_AFTER_PREFIX__REPLACE__
) = (
    re.compile(r"(thành phố|tỉnh|thị xã|huyện|quận|phường|xã)\s*", re.IGNORECASE),
    r"\1 "
)

(
    __ADD_COMMA_BEFORE_XA__PATTERN__,
    __ADD_COMMA_BEFORE_XA__REPLACE__
) = (
    re.compile(r"(?<!^)\s*(?<!,\s)(?<!thị)\s(xã)", re.IGNORECASE),
    r", \1"
)