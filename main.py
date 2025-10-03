from utils.data import get_data, get_prefix_dict
from utils.fuzz import fuzz_pipeline
from utils.preprocess import to_diacritics, to_normalized, to_nospace
from utils.trie import count_diacritics, score, build_all_automaton, check_automaton, classify_with_trie, detect_with_last, trie_pipeline
from utils.input import normalize_input, preprocess_input, replace_alias, add_comma_before_administrative, select_candidate

DATA = get_data()
PREFIX = get_prefix_dict()
AUTOMATON = build_all_automaton(DATA, PREFIX)

import time
start = time.perf_counter_ns()

input = "Thôn Thành Bắc, Xã Quảng Thành, TP Thanh Hoá, Thanh Hoá"
tests = [
    "Thôn Xuân Lũng Bình Trung, Cao Lộc, Lạng Sơn", # 240 order
    "Tổ 8, Ấp An Bình Minh Hòa, Châu Thành, Kiên Giang", # 246 order
    "Khóm 1,Thị Trấn Tam Bình, Vĩnh Long", # 249 prefix ko khớp output
    "Thôn Thành Bắc, Xã Quảng Thành, TP Thanh Hoá, Thanh Hoá", # 257 chưa sửa
    "Khu phố Nam Tân, TT Thuận Nam, Hàm Thuận Bắc, Bình Thuận." # 286 thầy lỏ detect thiếu
    "3/107 Ngõ Quỳnh Thanh Nhàn, Hai Bà Trưng, Hà Nội", # 289 xử lý order
    "24/98C, Phố Hữu Nghị Xuân Khanh, Sơn Tây, Hà Nội", # 303, xử lý order
    "Hà Tân Hưng Hà, Tân Hưng, Long An" # 305 xử lý order
    "- Khu B Chu Hoà, Việt HhiPhú Thọ" # 309 thầy lỏ detect thiếu
    "A:12A.21BlockA C/c BCA,P.AnKhánh,TP.Thủ Đức, TP. HCM", # 313 thầy lỏ detect thiếu
    "L10C12 Hẻm 90, Ng, Bỉnh Khiêm, TP. Rạch Giá, Kiên Giang", # 314 thầy lỏ detect thiếu
    "51 Phạm Ngũ Lão, Lê Lợi Sơn Tây, Hà Nội", # 316
    "Long Bình, An Hải, Ninh Phước, Ninh Thuận", # 322, 296, 295, 287, 259 Vấn đề i như dưới, xử lý sau (order process), idea split lấy 3 cái cuối
    "191A Nguyễn Thị Định An Phú, Quận 2, Tp Hồ Chí Minh", # 334 chưa xử lý, lưu để sau
    "Van Điểm, H hường TLín, Thành phốHa Nội",
    ", H Nam Trực, Nam Đị8nh",
    "F.07, Q6, ",
    "Yên Bình, H fHữu Lũng, Lạng Sơn",
    "Phưng Khâm Thiên Quận Đ.Đa T.Phố HàNội",
    " T.PhôSông Công t. Thái Nguyên", 
    " Chi Lăng,H Chi Lăng,Tỉnh Lạng5 Sơn",
    ",Diễn Châu,TỉnhNghệ An",
    "  Chư Se T Gia Lai",
    "vĩnh Hưng, , Long An",
    "F.LoWng Binh, TpThủ Đưc, TPHCM",
    "TT Hội An,,TAn Giang", 
    "TTr.Quỳnh Côi,HQuỳnh Phụ,TThai Bình",
    "Tích Sơn T.Phốvinh Yên t vĩnh phúc",
    "P.Thủy Châu, T.X. Hương Thủy, TTH",
    "Q1, HCM",
    "TX. Bình Long",
    "TT Tân Châu",
    "H Yên Mỹ",
    "T Bắc Ninh",
    "Q Cầu Giấy, HN",
    "QuậnBinh, HCM",
    "200 Thích Qunarg Đức X.Yên Phong Tỉnh Bắc Kạn"
]

for raw in tests:
    print(preprocess_input(raw))
    # print(raw, "\n", 5*" ", "->", add_comma_before_administrative(replace_alias(raw)))

outputs = trie_pipeline(input, AUTOMATON)
end = time.perf_counter_ns() - start
print(f"{end * 10**(-9): .9f}")

fuzz_output = fuzz_pipeline(input, outputs)
end = time.perf_counter_ns() - start
print(f"{end * 10**(-9): .9f}")

print(preprocess_input(input).split(","))
output = select_candidate(fuzz_output, preprocess_input(input).split(","))
end = time.perf_counter_ns() - start
print(f"{end * 10**(-9): .9f}")

print("-"*5, "TRIE", "-"*5)
[print(out) for out in outputs]
print("-"*5, "FUZZ", "-"*5)
[print(out) for out in fuzz_output]
print("-"*5, "RAW INPUT SELECT", "-"*5)
[print(out) for out in output]
# outputs = classify_with_trie(input, AUTOMATON, "normalized")
# outputs = classify_with_trie('p thanh xuan q 12', AUTOMATON, "diacritics", ('Hồ Chí Minh', None, None), 277)
# outputs = check_automaton(AUTOMATON["diacritics"]["districts"], to_normalized("Vinh"))
# outputs = check_automaton(AUTOMATON["normalized"]["districts"], to_normalized("vương p13 quận 8 tp"))
# outputs = check_automaton(AUTOMATON["diacritics"]["wards"], to_diacritics(to_normalized(input)))
# outputs = score(PREFIX, (None, 'Hương Thủy', 'Thủy Châu'), (None, 'tx', 'p'),'thuathue', "nospace", (None, None, 'Thủy Châu'), "diacritics")
# input = "Sơn Hà"
# outputs = check_automaton(AUTOMATON["normalized"]["districts"], to_normalized(input))
print(detect_with_last(AUTOMATON["diacritics"]["districts"], to_diacritics(to_normalized(preprocess_input(input))), None, None, None))
# print(
#     score(
#         PREFIX,
#         ('Hải Dương', None, 'Yên Ninh'),
#         ('t', '', ''),
#         'x an đức hu giang',
#         "normalized",
#         (None, None, None),
#         None, 
#         ('t hải dương', None, 'yên ninh')
#     )
# )
# print(
#     fuzz_pipeline(input, [
#         (('Đồng Tháp', 'Yên Châu', 'Thanh'), 'mu', ('tỉnh', '', ''), 1307, ('tỉnhđồng tháp', 'yen chau', 'thanh')),
#         (('Đồng Tháp', 'Châu Thành', None), 'muyện', ('tỉnh', '', ''), 1287, ('tỉnhđồng tháp', 'châu thành', ''))
#     ])
# )
# (('Hải Dương', None, 'Yên Ninh'), 'x an đức hu giang', ('t', '', ''), 386, ('t hải dương', None, 'yên ninh'))
# X An Đức, Huyên Ninh Giang, T.Hải Dương
# (('Hải Dương', None, 'An Đức'), 'huyên ninh giang', ('t', '', 'x'), 325, ('t hải dương', None, 'x an đức'))
# print(count_diacritics("Thạnh Xuân"))
# print(score("Nghệ An", "Vinh", "Đông Vĩnh", 'phuong quan', "diacritics"))