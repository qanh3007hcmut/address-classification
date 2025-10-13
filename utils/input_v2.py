import re
from utils.decorators import track_time_ns, track_variable, track_input
from utils.process_save import (
    __DELETE_START_NUMBER__PATTERN__, __DELETE_START_NUMBER__REPLACE__,
    __CLEAN_SPACE__PATTERN__, __CLEAN_SPACE__REPLACE__,
    __CLEAN_DOT_LEFT__PATTERN__, __CLEAN_DOT_LEFT__REPLACE__,
    __CLEAN_START_SPACE__PATTERN__, __CLEAN_START_SPACE__REPLACE__,
    __CLEAN_END_SPACE__PATTERN__, __CLEAN_END_SPACE__REPLACE__,
    __ADD_SPACE_AFTER_COMMA__PATTERN__, __ADD_SPACE_AFTER_COMMA__REPLACE__,
    __ADD_SPACE_AFTER_DOT__PATTERN__, __ADD_SPACE_AFTER_DOT__REPLACE__,
    __ADD_SPACE_UPPERCASE_WITH_COMMA_BEFORE__PATTERN__, __ADD_SPACE_UPPERCASE_WITH_COMMA_BEFORE__REPLACE__,
    __ADD_COMMA_BEFORE_PREFIX__PATTERN__, __ADD_COMMA_BEFORE_PREFIX__REPLACE__,
    __ADD_COMMA_BEFORE_XA__PATTERN__, __ADD_COMMA_BEFORE_XA__REPLACE__,
    __ADD_SPACE_AFTER_PREFIX__PATTERN__, __ADD_SPACE_AFTER_PREFIX__REPLACE__,
    __SPLIT_LOWER_UPPER__PATTERN__, __SPLIT_LOWER_UPPER__REPLACE__,
    __DELETE_NUMBER_3_DIGITS__PATTERN__, __DELETE_NUMBER_3_DIGITS__REPLACE__,
    __DELETE_NUMBER_AFTER_DIACRITICS__PATTERN__, __DELETE_NUMBER_AFTER_DIACRITICS__REPLACE__,
    __DELETE_NUMBER_1_2_DIGITS_WITHOUT_WARD_DISTRICT__PATTERN__, __DELETE_NUMBER_1_2_DIGITS_WITHOUT_WARD_DISTRICT__REPLACE__,
    __DELETE_NUMBER_1_2_DIGITS_WITHOUT_WARD_DISTRICT_NO_SPACE__PATTERN__, __DELETE_NUMBER_1_2_DIGITS_WITHOUT_WARD_DISTRICT_NO_SPACE__REPLACE__,
    __EXPAND_DISTRICT_WITH_NUMBERS__PATTERN__, __EXPAND_DISTRICT_WITH_NUMBERS__REPLACE__,
    __EXPAND_WARD_WITH_NUMBERS__PATTERN__, __EXPAND_WARD_WITH_NUMBERS__REPLACE__,
    ALIAS_ABBREV_WITH_DOT_REGEX_MAP, 
    ALIAS_ABBREV_WITHOUT_DOT_REGEX_MAP,
    ALIAS_ABBREV_WITHOUT_DOT_WITH_COMMA_SPACE_REGEX_MAP, 
    ALIAS_LONG_REGEX_MAP,
    ALIAS_PLACE_REGEX_MAP
)

@track_input("text")
def general_process_input(text :  str):
    input = text
    
    # Split
    input = __SPLIT_LOWER_UPPER__PATTERN__.sub(__SPLIT_LOWER_UPPER__REPLACE__, input)
    
    # Delete
    input = __DELETE_START_NUMBER__PATTERN__.sub(__DELETE_START_NUMBER__REPLACE__, input)
    input = __DELETE_NUMBER_3_DIGITS__PATTERN__.sub(__DELETE_NUMBER_3_DIGITS__REPLACE__, input)
    input = __DELETE_NUMBER_1_2_DIGITS_WITHOUT_WARD_DISTRICT__PATTERN__.sub(__DELETE_NUMBER_1_2_DIGITS_WITHOUT_WARD_DISTRICT__REPLACE__, input)
    input = __DELETE_NUMBER_1_2_DIGITS_WITHOUT_WARD_DISTRICT_NO_SPACE__PATTERN__.sub(__DELETE_NUMBER_1_2_DIGITS_WITHOUT_WARD_DISTRICT_NO_SPACE__REPLACE__, input)
    input = __DELETE_NUMBER_AFTER_DIACRITICS__PATTERN__.sub(__DELETE_NUMBER_AFTER_DIACRITICS__REPLACE__, input)

    # Space
    input = __CLEAN_SPACE__PATTERN__.sub(__CLEAN_SPACE__REPLACE__, input)
    input = __CLEAN_START_SPACE__PATTERN__.sub(__CLEAN_START_SPACE__REPLACE__, input)
    input = __CLEAN_END_SPACE__PATTERN__.sub(__CLEAN_END_SPACE__REPLACE__, input)
    input = __ADD_SPACE_AFTER_COMMA__PATTERN__.sub(__ADD_SPACE_AFTER_COMMA__REPLACE__, input)
    input = __ADD_SPACE_AFTER_DOT__PATTERN__.sub(__ADD_SPACE_AFTER_DOT__REPLACE__, input)
    input = __ADD_SPACE_UPPERCASE_WITH_COMMA_BEFORE__PATTERN__.sub(__ADD_SPACE_UPPERCASE_WITH_COMMA_BEFORE__REPLACE__, input)
    
    return input

@track_input("text")
def final_clean(text :  str):
    input = text
    input = __CLEAN_DOT_LEFT__PATTERN__.sub(__CLEAN_DOT_LEFT__REPLACE__, input)
    input = __ADD_COMMA_BEFORE_PREFIX__PATTERN__.sub(__ADD_COMMA_BEFORE_PREFIX__REPLACE__, input)
    input = __ADD_COMMA_BEFORE_XA__PATTERN__.sub(__ADD_COMMA_BEFORE_XA__REPLACE__, input)
    input = __ADD_SPACE_AFTER_PREFIX__PATTERN__.sub(__ADD_SPACE_AFTER_PREFIX__REPLACE__, input)
    
    return input

@track_input("text")
def expand_abbreviation(text : str):
    input = __EXPAND_DISTRICT_WITH_NUMBERS__PATTERN__.sub(__EXPAND_DISTRICT_WITH_NUMBERS__REPLACE__, text)
    input = __EXPAND_WARD_WITH_NUMBERS__PATTERN__.sub(__EXPAND_WARD_WITH_NUMBERS__REPLACE__, input)
    for repl, pattern in ALIAS_PLACE_REGEX_MAP.items():
        input = pattern.sub(repl, input)
    
    for repl, pattern in ALIAS_ABBREV_WITH_DOT_REGEX_MAP.items():
        input = pattern.sub(repl, input)
    
    for repl, pattern in ALIAS_ABBREV_WITHOUT_DOT_WITH_COMMA_SPACE_REGEX_MAP.items():
        input = pattern.sub(repl, input)
    
    for repl, pattern in ALIAS_ABBREV_WITHOUT_DOT_REGEX_MAP.items():
        input = pattern.sub(repl, input)
        
    for repl, pattern in ALIAS_LONG_REGEX_MAP.items():
        input = pattern.sub(repl, input)
    
    return input

@track_time_ns
def preprocess_input(text : str):
    input = text    
    input = general_process_input(input)
    input = expand_abbreviation(input)
    input = final_clean(input)
    
    return input

def test_pattern(text : str, pattern : re.Pattern, repl : str):
    return pattern.sub(repl, text)