from math import exp
from utils.data import get_data, get_prefix_dict    
from utils.input_v2 import preprocess_input
from utils.preprocess import to_normalized
from utils.trie import build_all_automaton
from utils.trie_pipeline_v2 import check_automaton, full_pipeline, spelling_detect, window_slide
from utils.spelling_error_pipeline import extract_address_components, find_match, create_list
from utils.bktree import build_bk_trees
import time
import json

with open("test/latest_test.json", "r", encoding="utf-8") as f:
    tests = json.load(f)
test_inputs = [case["text"] for case in tests]
expected_province = [case["result"]["province"] for case in tests]
expected_district = [case["result"]["district"] for case in tests]
expected_ward = [case["result"]["ward"] for case in tests]

DATA = get_data()
PREFIX = get_prefix_dict()
AUTOMATON = build_all_automaton(DATA, PREFIX)
BKTREE = build_bk_trees(DATA, PREFIX["full"]["normalized"], to_normalized)
tests = [
    ("T.T.H", "thừa thiên huế"),
    ("P4 T.Ph9ốĐông Hà", ""),
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

# for raw, expected in tests:
#     if(preprocess_input(raw) != expected and expected != ""):
#         print("Raw", 5*"-", " ", raw)
#         print("Preprocess", 5*"-", " ", preprocess_input(raw))
#         print("Expected", 5*"-", " ", expected, "\n")
        
import time
start = time.perf_counter_ns()
id = 462
raw_input = test_inputs[id - 1]
input = preprocess_input(raw_input)
print("RAW_INPUT", "-"*5, raw_input)
print("PREPROCESS_INPUT", "-"*5, input)
output = full_pipeline(input, AUTOMATON, BKTREE)
print("-"*5, f"{(time.perf_counter_ns() - start) * 10**(-9): .9f}","-"*5)

print(output[0], output[1], output[2])
print(expected_province[id-1], expected_district[id-1], expected_ward[id-1])
# output = check_automaton(AUTOMATON["normalized"]["wards"], "Tỉnh Lạng5 Sơn".lower())

# province_prefixes = ['', 'thành phố', 'thanh pho', 'thanhpho', 'tp', 'tp.', 't.p', 't', 'thnàh phố', 'thànhphố', 'tỉnh', 'tinh', 't.', 'tí', 'tinhf', 'tin', 'tnh', 't.phố', 't phố', 't.pho', 't pho']
# district_prefixes = ['', 'quận', 'quan', 'q', 'q.', 'qu', 'qaun', 'qận', 'huyện', 'huyen', 'h', 'h.', 'hu', 'hyuen', 'huyệ', 'thị xã', 'thi xa', 'thixa', 'tx', 'tx.', 't.x', 'th', 'txa', 'thịxa', 'thành phố', 'thanh pho', 'thanhpho', 'tp', 'tp.', 't.p', 'than', 'thanh', 'tph', 'thnàh phố', 'thànhphố', 't.xã', 't xã', 't.xa', 't xa', 't.phố', 't phố', 't.pho', 't pho']
# ward_prefixes = ['', 'phường', 'phuong', 'p', 'p.', 'ph', 'ph.', 'phuờng', 'phưng', 'puong', 'xã', 'xa', 'x', 'x.', 'xá', 'xạ', 'xãa', 'thị trấn', 'thi tran', 'thitran', 'tt', 'tt.', 't.t', 'th', 'ttr', 'thịtrấn', 't.trấn', 't tran', 't trấn', 't.tran']

# output = find_match(
#     input.lower().split(" "), 
#     create_list(set(DATA["provinces"])), 
#     province_prefixes, 
#     "provinces")
# output = extract_address_components("Phường 3, Quận 1, Hồ Chí Minh", DATA)

# outputs = spelling_detect(
#     input,
#     BKTREE, 
#     "wards", 
#     ('xã trung sơn ,tỉnh nghê an', (25, 'Nghệ An', 'tinh', 'tinh nghe an'))
# )
# outputs = find_best_match_advanced("thừa tỉnh huế", "provinces", BKTREE)
# print(outputs)
