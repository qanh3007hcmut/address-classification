import unicodedata

# Các dấu thanh tiếng Việt (class 1)
TONAL_MARKS = {
    "\u0301",  # sắc (́)
    "\u0300",  # huyền (̀)
    "\u0309",  # hỏi (̉)
    "\u0303",  # ngã (̃)
    "\u0323",  # nặng (̣)
}

# Các dấu hình dạng (class 2)
SHAPE_MARKS = {
    "\u0306",  # breve (ă)
    "\u0302",  # circumflex (â, ê, ô)
    "\u031B",  # horn (ơ, ư)
}

def decompose_char(c):
    """Tách 1 ký tự thành (base, lớp1, lớp2)"""
    decomp = unicodedata.normalize("NFD", c)
    base = next((x for x in decomp if unicodedata.category(x)[0] == "L"), c)
    class1 = [x for x in decomp if x in TONAL_MARKS]
    class2 = [x for x in decomp if x in SHAPE_MARKS]
    return base, class1, class2

def char_cost(a, b):
    """Tính chi phí giữa 2 ký tự"""
    if a == b:
        return 0.0

    base_a, tone_a, shape_a = decompose_char(a)
    base_b, tone_b, shape_b = decompose_char(b)

    # Nếu khác base letter -> lỗi nặng
    if base_a != base_b:
        return 1.0

    layers_a = len(tone_a + shape_a)
    layers_b = len(tone_b + shape_b)
    
    layers_diff = abs(layers_a - layers_b) - 1        
    tone_diff = 1 if tone_a != tone_b else 0
    shape_diff = 1 if shape_a != shape_b else 0
    no_layers = 1 if layers_a == 0 or layers_b == 0 else 0
    return (layers_diff + tone_diff + shape_diff + no_layers) * 0.25

def vietnamese_weighted_edit_distance(s1, s2):
    """Levenshtein distance có trọng số dấu tiếng Việt"""
    a = s1
    b = s2

    dp = [[0.0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        dp[i][0] = dp[i - 1][0] + 1.0
    for j in range(1, len(b) + 1):
        dp[0][j] = dp[0][j - 1] + 1.0

    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            dp[i][j] = min(
                dp[i - 1][j] + 1.0,       # delete
                dp[i][j - 1] + 1.0,       # insert
                dp[i - 1][j - 1] + char_cost(a[i - 1], b[j - 1])  # substitute
            )
    return dp[-1][-1]

