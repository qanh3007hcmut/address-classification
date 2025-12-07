#!/usr/bin/env python3
"""
Vietnamese Address Matcher - Library Version
A high-performance Vietnamese address classification system using BK-trees.
"""

import unicodedata
import re
from typing import Any, List, Dict, Literal, Tuple, Optional
from functools import lru_cache
import Levenshtein
from itertools import groupby
from utils.decorators import track_input, track_time_ns, track_variable

from rapidfuzz import process, fuzz

# ============================================================================
# BK-Tree Implementation
# ============================================================================

class BKTreeNode:
    """Node in a BK-tree"""
    def __init__(self, *args):
        if len(args) == 2:
            self.word = args[0]
            self.core = args[1]       
        self.children = {}

class BKTree:
    """
    Burkhard-Keller Tree for efficient fuzzy string matching
    """
    def __init__(self, tree_type: str = "generic"):
        self.root = None
        self.tree_type = tree_type  # "districts", "wards", "provinces", or "generic"
        self.size = 0
    
    def normalize_text(self, text: str) -> str:
        """Normalize Vietnamese text for better matching"""
        # Remove extra spaces and convert to lowercase
        text = re.sub(r'\s+', ' ', text.strip().lower())
        # Normalize unicode characters
        text = unicodedata.normalize('NFC', text)
        return text
    
    def insert(self, word: str, core : str):
        """Insert a word into the BK-tree"""       
        if self.root is None:
            self.root = BKTreeNode(word, core)
            self.size += 1
            return
        
        current = self.root
        while True:
            distance = Levenshtein.distance(current.word, word)
            
            if distance == 0:
                return
            
            if distance in current.children:
                current = current.children[distance]
            else:
                current.children[distance] = BKTreeNode(word, core)
                self.size += 1
                break
    
    def search(self, word: str, preprocess = None, max_distance: int = 2):
        """
        Search for words within max_distance of the query word
        Returns list of (word, distance) tuples
        """
        if self.root is None:
            return []
        
        results = []
        word = preprocess(word) if preprocess else word.lower()
        
        def _search(node: BKTreeNode):
            distance = Levenshtein.distance(node.word, word)
            
            if distance <= max_distance:
                results.append((node.word, node.core, distance))
            
            for child_distance in range(max(1, distance - max_distance), 
                                      distance + max_distance + 1):
                if child_distance in node.children:
                    _search(node.children[child_distance])
        
        _search(self.root)
        
        return sorted(results, key=lambda x: x[1])  # Sort by distance
    
    @track_time_ns
    def progressive_search(self, text: str, preprocess=None):
        """
        Progressive left-to-right sliding search.
        Example: "thành phố hồ chí minh" →
            1. "thành phố hồ chí minh"
            2. "phố hồ chí minh"
            3. "hồ chí minh"
        """
        words = text.split()
        results = []

        # từ trái sang phải, giảm dần cụm
        for i in range(len(words) - 1):  # dừng sớm để tránh cụm quá ngắn
            phrase = " ".join(words[i:])
            max_dist = auto_distance(phrase)
            start_index = text.index(phrase)
            end_index = start_index + len(phrase)
            found = self.search(phrase, preprocess=preprocess, max_distance=max_dist)
            if found:
                for _, core, dist in found:
                    results.append((end_index, core, phrase, dist))
                break   
            print(max_dist)
            print(phrase)

        return sorted(results, key=lambda x: x[-1])

    @track_time_ns
    def dynamic_phrase_search(
        self,
        phrase: str,
        preprocess=None,
        base_distance: int | None = None,
        max_expand: int = 5,
        min_ratio: float = 0.5,
        distance_ratio_cutoff: float = 0.25,
    ) ->  list[tuple[str, str, int]]:
        """
        Adaptive BK-tree search for multi-word phrases (5–6 words).
        - Dynamically adjusts search distance.
        - Stops early if good matches found (low relative distance).
        """

        if self.root is None:
            return []

        phrase = preprocess(phrase) if preprocess else phrase.lower()
        length = len(phrase)

        # Cơ sở distance ban đầu — tỷ lệ theo độ dài cụm
        if base_distance is None:
            base_distance = max(2, int(length * 0.08))  # khoảng 8% độ dài cụm

        results = []
        current_distance = base_distance
        best_ratio = 1.0
        # curr_ratio = current_distance/length if length > 4 else 1/length
        curr_ratio = current_distance/length 
        while current_distance <= max_expand and curr_ratio <= distance_ratio_cutoff*1.5:
            results = self.search(phrase, preprocess, max_distance=current_distance)
            if not results:
                current_distance += 1
                curr_ratio = current_distance/length
                continue

            # Tính tỉ lệ khoảng cách tốt nhất hiện có
            best_distance = min(r[-1] for r in results)
            best_ratio = best_distance / max(1, length)

            # Dừng sớm nếu đạt ngưỡng độ gần mong muốn
            if best_ratio <= distance_ratio_cutoff:
                break

            current_distance += 1
            curr_ratio = current_distance/length
            
        return sorted(results, key=lambda x: (x[-1], -len(x[-2])))

def auto_distance(phrase: str) -> int:
        phrase = phrase.strip()
        n_chars = len(phrase)
        n_words = len(phrase.split())

        if n_chars <= 4:
            return 1
        elif n_words <= 2:
            return 2 if n_chars <= 8 else 3
        elif n_words <= 3:
            return 3
        elif n_words <= 5:
            return 4
        else:
            return 5
        
def build_bk_trees(data : dict[str , list[Any]], prefix_dict : dict[str, list[str]], preprocess) -> Dict[str, BKTree]:
    """
    Build BK-trees for districts, wards, and provinces
    """
    trees = {}
    
    for tree_type, values in data.items():        
        tree = BKTree(tree_type=tree_type)
        for item in values:
            core = preprocess(item)
            tree.insert(core, item)
        trees[tree_type] = tree
    
    return trees

def fuzzy_prefix(word: str, prefix_dict: dict[str, list[str]], address_type : Literal["provinces", "districts", "wards"]):
    all_prefixes = prefix_dict[address_type]
    best, score, _ = process.extractOne(word, all_prefixes, scorer=fuzz.ratio) # pyright: ignore[reportGeneralTypeIssues]
    if len(best) == 2 and score >= 50 :
        best, score, _ = process.extractOne(word, all_prefixes, scorer=fuzz.partial_token_ratio) # pyright: ignore[reportGeneralTypeIssues]
        return (word, best, score) if score > 60 else None
    return (word, best, score) if score > 80 else None

def split_text_for_address(text : str):
    """
    Split text into words and phrases for address matching
    """
    words = text.split()
    phrases = []
    if len(words) >= 4:
        phrases.append( " ".join(words[-4:]))
    
    if len(words) >= 3:
        phrases.append( " ".join(words[-3:]))
    if len(words) >= 4:
        phrases.append( " ".join(words[-4:-1]))
        
    if len(words) >= 2:
        phrases.append(" ".join(words[-2:]))
    if len(words) >= 3:
        phrases.append(" ".join(words[-3:-1]))
        
    if len(words) >= 1:
        phrases.append(words[-1])
    if len(words) >= 2:
        phrases.append(words[-2])
    if len(words) >= 3:
        phrases.append(words[-3])
        
    return phrases
    
def split_text_for_prefix(text : str, result : tuple[int, str, str, int]):
    """
    Split text into words and phrases for address matching
    """
    idx = (len(text) - 1 - result[0] - len(result[2]))
    if idx < 0:
        return []
    return split_text_for_address(text[:idx])


def prefix_checker(
    results,
    text : str,
    prefix_dict : dict[str, list[str]],
    address_type : Literal["provinces", "districts", "wards"]
): 
    prefix_outputs = []
    for result in results:
        words_for_prefix_check = split_text_for_prefix(text, result)
        raw, prefix, _ = prefix_helper(words_for_prefix_check, prefix_dict, address_type)
        prefix_outputs.append((result[0], result[1], prefix, f"{raw} {result[2]}".strip()))
        
    return prefix_outputs

def prefix_helper(
    words : list[str], 
    prefix_dict : dict[str, list[str]],
    address_type
):
    best_prefix = ("", "", 0)  # (raw, prefix, score)
    for word in words:
        output_prefix = fuzzy_prefix(word, prefix_dict, address_type)
        if not output_prefix:
            continue
        
        raw, prefix, score = output_prefix
        if score > best_prefix[2]:
            best_prefix = (raw, prefix, score)
            
        if score >= 95:
            break

    return best_prefix

def bktree_find(
        text : str, 
        bktree : BKTree, 
        prefix_dict : dict[str, list[str]], 
        preprocess, 
        address_type : Literal["provinces", "districts", "wards"]
    ) -> list[tuple[int, str, str, str]]:
    results = []
        
    words_for_address_check = split_text_for_address(text)
    for phrase in words_for_address_check:     
        start_index = text.index(phrase)
        end_index = start_index + len(phrase)
        found = bktree.dynamic_phrase_search(phrase, preprocess)
        if found:
            group = groupby(found, key = lambda x: x[-1])
            best_group = list(next(group)[1])
            results.extend([(len(text) - end_index, core, phrase, dist) for _, core, dist in best_group])        
    
    if not results:
        return []
    
    unique = {}
    for x in results:
        key = x[1]
        if key not in unique or x[-1] < unique[key][-1]:
            unique[key] = x

    results = list(unique.values())
    results = sorted(results, key=lambda x: (x[-1], -len(x[-2])))
    
    return prefix_checker(results, text, prefix_dict, address_type)
        
            
def split_text_for_address_v1(text : str, prefix : tuple[str, str]):
    """
    Split text into words and phrases for address matching
    """
    end = text.index(prefix[0]) + len(prefix[0]) + 1
    words = text[end:].split()
    phrases = []
    if len(words) >= 3:
        phrases.append( " ".join(words[-3:]))
        
    if len(words) >= 2:
        phrases.append(" ".join(words[-2:]))
    if len(words) >= 3:
        phrases.append(" ".join(words[-3:-1]))
        
    if len(words) >= 1:
        phrases.append(words[-1])
    if len(words) >= 2:
        phrases.append(words[-2])
    if len(words) >= 3:
        phrases.append(words[-3])
        
    return phrases
    
def split_text_for_prefix_v1(text : str):
    """
    Split text into words and phrases for address matching
    """
    words = text.split()
    phrases = []
    if len(words) >= 2:
        phrases.append(words[0])
        
    if len(words) >= 3:
        phrases.append(words[1])
        phrases.append( " ".join(words[0:2]))
        
    return phrases
    

def bktree_find_v1(
        text : str, 
        bktree : BKTree, 
        prefix_dict : dict[str, list[str]], 
        preprocess, 
        address_type : Literal["provinces", "districts", "wards"]
    ) -> list[tuple[int, str, str, str]]:
    results = []
        
    words_for_prefix_check : list[str] = split_text_for_prefix_v1(text)
    best_prefix : tuple[str, str] = ("", "")
    for phrases in words_for_prefix_check:
        prefix = fuzzy_prefix(phrases, prefix_dict, address_type)
        if prefix and len(best_prefix[0]) <= len(prefix):
            best_prefix = prefix
    words_for_address_check = split_text_for_address_v1(text, best_prefix)
    print(words_for_address_check)
    for phrase in words_for_address_check:     
        start_index = text.index(phrase)
        end_index = start_index + len(phrase)
        found = bktree.dynamic_phrase_search(phrase, preprocess)
        if found:
            group = groupby(found, key = lambda x: x[-1])
            best_group = list(next(group)[1])
            results.extend([(len(text) - end_index, core, phrase, dist) for _, core, dist in best_group])        
    
    if not results:
        return []
    
    unique = {}
    for x in results:
        key = x[1]
        if key not in unique or x[-1] < unique[key][-1]:
            unique[key] = x

    results = list(unique.values())
    results = sorted(results, key=lambda x: (x[-1], -len(x[-2])))
    
    return results