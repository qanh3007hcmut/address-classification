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

# ============================================================================
# BK-Tree Implementation
# ============================================================================

class BKTreeNode:
    """Node in a BK-tree"""
    def __init__(self, word: str):
        self.word = word
        self.children = {}  # distance -> child node
    
    def __repr__(self):
        return f"BKTreeNode('{self.word}')"


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
    
    def insert(self, word: str):
        """Insert a word into the BK-tree"""
        # word = self.normalize_text(word)
        
        if self.root is None:
            self.root = BKTreeNode(word)
            self.size += 1
            return
        
        current = self.root
        while True:
            # distance = self.levenshtein_distance(current.word, word)
            distance = Levenshtein.distance(current.word, word)
            
            if distance == 0:
                # Word already exists
                return
            
            if distance in current.children:
                current = current.children[distance]
            else:
                current.children[distance] = BKTreeNode(word)
                self.size += 1
                break
    
    def search(self, word: str, max_distance: int = 2) -> List[Tuple[str, int]]:
        """
        Search for words within max_distance of the query word
        Returns list of (word, distance) tuples
        """
        if self.root is None:
            return []
        
        word = self.normalize_text(word)
        results = []
        
        def _search_recursive(node: BKTreeNode):
            distance = Levenshtein.distance(node.word, word)
            
            if distance <= max_distance:
                results.append((node.word, distance))
            
            # Search child nodes within the distance range
            for child_distance in range(max(1, distance - max_distance), 
                                      distance + max_distance + 1):
                if child_distance in node.children:
                    _search_recursive(node.children[child_distance])
        
        _search_recursive(self.root)
        return sorted(results, key=lambda x: x[1])  # Sort by distance
    
    def get_closest_match(self, word: str, max_distance: int = 3) -> Optional[Tuple[str, int]]:
        """Get the closest match for a word"""
        results = self.search(word, max_distance)
        return results[0] if results else None


# ============================================================================
# Data Loading Functions
# ============================================================================

def load_data_from_file(file_path: str) -> List[str]:
    """Load data from a text file, one item per line"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []


def build_bk_trees(data : dict[str , list[Any]]) -> Dict[str, BKTree]:
    """
    Build BK-trees for districts, wards, and provinces
    """
    trees = {}
    
    for tree_type, values in data.items():        
        tree = BKTree(tree_type=tree_type)
        for item in values:
            tree.insert(item)
        
        trees[tree_type] = tree
    
    return trees


# Global trees dict for caching
_bk_trees = None

def set_bk_trees(tree):
    global _bk_trees
    if _bk_trees is None:
        _bk_trees = tree
    return _bk_trees

def search_best_in_tree(tree_type: str, query: str, max_distance: int = 3):
    """Search for the best match in a specific BK-tree"""
    global _bk_trees
    if not _bk_trees: 
        return 
    
    if tree_type not in _bk_trees:
        return None
    
    tree = _bk_trees[tree_type]
    results = tree.search(query, max_distance)
    return results[0] if results else None


# Cache for search results
@lru_cache(maxsize=1000)
def cached_search_best_in_tree(tree_type, query, max_distance):
    """Cached version of search_best_in_tree for performance"""
    return search_best_in_tree(tree_type, query, max_distance)


# ============================================================================
# Advanced Matching Functions
# ============================================================================

def find_best_match_advanced(input_string: str, bk_tree_type: Literal['provinces', 'districts', 'wards'], trees_dict, max_distance: int = 3):
    """
    Advanced function to find the best match using both 2-word and 3-word combinations
    Prioritizes 3-word matches when distances are equal
    """    
    set_bk_trees(trees_dict)
    # Clean and split input into words
    cleaned_input = input_string.strip().lower()
    
    words = [w for w in cleaned_input.split() if len(w.strip()) > 1]
    if len(words) < 2:
        return None
    
    candidates = []
    
    # Try 2-word combinations
    for i in range(len(words) - 1):
        two_word_query = ' '.join(words[i:i+2])
        match = cached_search_best_in_tree(bk_tree_type, two_word_query, max_distance)
        if match:
            candidates.append({
                'match': match[0],
                'distance': match[1],
                'word_count': 2,
                'query': two_word_query
            })
    
    # Try 3-word combinations (if possible)
    if len(words) >= 3:
        for i in range(len(words) - 2):
            three_word_query = ' '.join(words[i:i+3])
            match = cached_search_best_in_tree(bk_tree_type, three_word_query, max_distance)
            if match:
                candidates.append({
                    'match': match[0],
                    'distance': match[1],
                    'word_count': 3,
                    'query': three_word_query
                })
    
    if not candidates:
        return None
    
    # Sort candidates: 
    # 1. First by distance (lower is better)
    # 2. Then by word count (higher is better - prioritize 3-word)
    candidates.sort(key=lambda x: (x['distance'], -x['word_count']))
    return candidates[0]
