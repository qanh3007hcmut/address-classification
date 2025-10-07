class TrieNode:
    __slots__ = ("children", "is_word", "word")
    def __init__(self):
        self.children = {}
        self.is_word = False
        self.word = None

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str):
        node = self.root
        for c in word:
            if c not in node.children:
                node.children[c] = TrieNode()
            node = node.children[c]
        node.is_word = True
        node.word = word

    def search_approx(self, word: str, max_dist: int):
        """
        Approximate matching với edit distance <= max_dist
        Optimized: tránh tạo list liên tục, pruning tốt
        """
        n = len(word)
        results = []

        # DP cho gốc
        init_row = list(range(n + 1))

        # stack để DFS iterative (node, char, prev_row)
        stack = [(self.root, None, init_row)]

        while stack:
            node, char, prev_row = stack.pop()

            # update row nếu char != None
            if char is not None:
                curr_row = [prev_row[0] + 1]
                min_curr = curr_row[0]

                for i in range(1, n + 1):
                    ins = curr_row[i - 1] + 1
                    dele = prev_row[i] + 1
                    rep = prev_row[i - 1] + (word[i - 1] != char)
                    v = min(ins, dele, rep)
                    curr_row.append(v)
                    if v < min_curr:
                        min_curr = v

                # prune
                if min_curr > max_dist:
                    continue

                # check từ
                if node.is_word and curr_row[-1] <= max_dist:
                    results.append((node.word, curr_row[-1]))

                # đi tiếp xuống con
                for c, child in node.children.items():
                    stack.append((child, c, curr_row))

            else:
                # root: chỉ xuống con
                for c, child in node.children.items():
                    stack.append((child, c, prev_row))

        return results
    
def build_Trie_DP(words : list):
    trie = Trie()
    [trie.insert(w) for w in words]
    return trie