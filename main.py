from rapidfuzz import fuzz
import Levenshtein
from utils.data import get_data, get_prefix_dict
from utils.decorators import track_time_ns
from utils.fuzz import fuzz_pipeline_v2
from utils.preprocess import to_normalized
from utils.trie import build_all_automaton
# from utils.input import preprocess_input
from utils.input_v2 import preprocess_input, test_pattern
from input_test.export_sample import export_sample, export_diff
from utils.bktree import bktree_find_v1, build_bk_trees, bktree_find, fuzzy_prefix, prefix_helper
from utils.trie_pipeline_v2 import PREFIX_DICT, bktree_spelling_check

DATA = get_data()
PREFIX = get_prefix_dict()
AUTOMATON = build_all_automaton(DATA, PREFIX)
BKTREE = build_bk_trees(DATA, PREFIX["full"]["normalized"], to_normalized)

test_pass = [
    ("T.T.H", "thừa thiên huế"),
    
]

test_not_pass = [
    ("P4 T.Ph9ốĐông Hà", "a"),
    ("Mỹ Hòa xã Mỹ Long, H.Cai Laậy, Tiền Giang", ""), # 265
    ("T. Phước Trạch 2 Ea Phê, Krông Păc, Đắk Lắk", ""), # 259
    ("PhườngNguyễn Trãi, T.P Kon Tum, T Kon Tum", ""),
    (" Muyện Châu Thành TỉnhĐồng Tháp", ""),
    ("Thôn Xuân Lũng Bình Trung, Cao Lộc, Lạng Sơn", ""), # 240 order
    ("Tổ 8, Ấp An Bình Minh Hòa, Châu Thành, Kiên Giang", ""), # 246 order
    ("Khóm 1,Thị Trấn Tam Bình, Vĩnh Long", ""), # 249 prefix ko khớp output
    ("Thôn Thành Bắc, Xã Quảng Thành, TP Thanh Hoá, Thanh Hoá", ""), # 257 chưa sửa
    ("Khu phố Nam Tân, TT Thuận Nam, Hàm Thuận Bắc, Bình Thuận.", ""), # 286 thầy lỏ detect thiếu
    ("3/107 Ngõ Quỳnh Thanh Nhàn, Hai Bà Trưng, Hà Nội", ""), # 289 xử lý order
    ("24/98C, Phố Hữu Nghị Xuân Khanh, Sơn Tây, Hà Nội", ""), # 303, xử lý order
    ("Hà Tân Hưng Hà, Tân Hưng, Long An", ""), # 305 xử lý order
    ("- Khu B Chu Hoà, Việt HhiPhú Thọ", ""), # 309 thầy lỏ detect thiếu
    ("A:12A.21BlockA C/c BCA,P.AnKhánh,TP.Thủ Đức, TP. HCM", ""), # 313 thầy lỏ detect thiếu
    ("L10C12 Hẻm 90, Ng, Bỉnh Khiêm, TP. Rạch Giá, Kiên Giang", ""), # 314 thầy lỏ detect thiếu
    ("51 Phạm Ngũ Lão, Lê Lợi Sơn Tây, Hà Nội", ""), # 316
    ("Long Bình, An Hải, Ninh Phước, Ninh Thuận", ""), # 322, 296, 295, 287, 259 Vấn đề i như dưới, xử lý sau (order process), idea split lấy 3 cái cuối
    ("191A Nguyễn Thị Định An Phú, Quận 2, Tp Hồ Chí Minh", ""), # 334 chưa xử lý, lưu để sau
    ("Van Điểm, H hường TLín, Thành phốHa Nội", ""),
    (", ""), H Nam Trực, Nam Đị8nh", ""),
    ("F.07, Q6, ", ""),
    ("Yên Bình, H fHữu Lũng, Lạng Sơn", ""),
    ("Phưng Khâm Thiên Quận Đ.Đa T.Phố HàNội", ""),
    (" T.PhôSông Công t. Thái Nguyên", ""), 
    (" Chi Lăng,H Chi Lăng,Tỉnh Lạng5 Sơn", ""),
    (", ""),Diễn Châu,TỉnhNghệ An", ""),
    ("  Chư Se T Gia Lai", ""),
    ("vĩnh Hưng, , Long An", ""),
    ("F.LoWng Binh, TpThủ Đưc, TPHCM", ""),
    ("TT Hội An,,TAn Giang", ""), 
    ("TTr.Quỳnh Côi,HQuỳnh Phụ,TThai Bình", ""),
    ("Tích Sơn T.Phốvinh Yên t vĩnh phúc", ""),
    ("P.Thủy Châu, T.X. Hương Thủy, TTH", ""),
    ("Q1, HCM", ""),
    ("TX. Bình Long", ""),
    ("TT Tân Châu", ""),
    ("H Yên Mỹ", ""),
    ("T Bắc Ninh", ""),
    ("Q Cầu Giấy, HN", ""),
    ("QuậnBinh, HCM", ""),
    ("200 Thích Qunarg Đức X.Yên Phong Tỉnh Bắc Kạn", "")
]

# input = "phường 2, Tỉnhyên Bái"
# input = preprocess_input(input)
# export_sample(preprocess_input, dst = "input_test/sample_test.json")
# export_diff(preprocess_input)


input = "phong cnốc "
# output = bktree_spelling_check(input, BKTREE, PREFIX["full"]["normalized"], "districts", ('thành phố phan rang tháp lhàm, ninh thuận', (40, 'Ninh Thuận', '', 'ninh thuận')))
# output = (BKTREE["wards"].dynamic_phrase_search(input , to_normalized))
output = prefix_helper(["th ị xã"], PREFIX_DICT, "districts")
# output = bktree_find(input, BKTREE["districts"], PREFIX_DICT, to_normalized, "districts")
print(output)
# print(BKTREE["wards"].progressive_search(input, to_normalized))
# print(fuzzy_prefix("oã", PREFIX["full"]["normalized"], "wards"))
