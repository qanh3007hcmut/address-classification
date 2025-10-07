from rapidfuzz.distance import Levenshtein

class BKTree:
    def __init__(self, word):
        self.word = word
        self.children = {}  # key = khoảng cách, value = BKTree node

    def add(self, other_word):
        dist = Levenshtein.distance(self.word, other_word)
        if dist in self.children:
            self.children[dist].add(other_word)
        else:
            self.children[dist] = BKTree(other_word)

    def search(self, query, max_dist):
        results = []
        dist = Levenshtein.distance(query, self.word)
        if dist <= max_dist:
            results.append((self.word, dist))

        # chỉ cần duyệt nhánh có khoảng cách trong [dist - max_dist, dist + max_dist]
        for d in range(dist - max_dist, dist + max_dist + 1):
            child = self.children.get(d)
            if child:
                results.extend(child.search(query, max_dist))
        return results

def build_BKTree(words : list):
    tree = BKTree(words[0])
    for w in words[1:]:
        tree.add(w)
    return tree
    
def search_bktree(bktree: BKTree, query: str, max_dist: int = 5):
    candidates = bktree.search(query, max_dist=max_dist)
    return candidates

