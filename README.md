# Hướng dẫn sử dụng Address Classification Pipeline

## Mô tả
Pipeline này được thiết kế để phân loại và xử lý địa chỉ sử dụng kết hợp các thuật toán Trie, Automaton và Fuzzy matching.

## Cách sử dụng hàm `process`

### Import
```python
from pipeline import process
```

### Cú pháp
```python
result = process(input_address)
```

### Tham số
- `input` (str): Chuỗi địa chỉ cần xử lý và phân loại

### Giá trị trả về
- Trả về một tuple chứa thông tin địa chỉ đã được phân loại với cấu trúc:
  ```
  (địa_chỉ_chuẩn_hóa, input_xử_lý, prefix_phát_hiện, điểm_số, địa_chỉ_đầy_đủ)
  ```
  - `địa_chỉ_chuẩn_hóa`: tuple (tỉnh/thành, quận/huyện, phường/xã)
  - `input_xử_lý`: chuỗi input đã được tiền xử lý
  - `prefix_phát_hiện`: tuple các prefix được phát hiện (tỉnh, quận, phường)
  - `điểm_số`: điểm số đánh giá độ chính xác
  - `địa_chỉ_đầy_đủ`: tuple phần text được detect ra địa chỉ đầy đủ với prefix

### Ví dụ sử dụng
```python
# Ví dụ 1: Địa chỉ đầy đủ
address1 = "Thôn Thành Bắc, Xã Quảng Thành, TP Thanh Hoá, Thanh Hoá"
result1 = process(address1)
print(result1)
# Output: (('Thanh Hóa', 'Thanh Ba', 'Quảng Thành'), 'thon c thanh hoa', ('thanh pho', '', 'xã'), 1385, ('thanh pho thanh hoa', 'thanh ba', 'xã quảng thành'))

# Ví dụ 2: Truy cập các thành phần
result = process("Quận 1, TP.HCM")
tinh_thanh = result[0][0]  # 'Hồ Chí Minh'
quan_huyen = result[0][1]  # 'Quận 1'
phuong_xa = result[0][2]   # None hoặc tên phường/xã
diem_so = result[3]        # Điểm số đánh giá
```

## Quy trình xử lý

Pipeline thực hiện 3 bước chính:

1. **Trie Pipeline**: Sử dụng cấu trúc Trie và Automaton để tìm kiếm nhanh các thành phần địa chỉ
2. **Fuzzy Pipeline**: Áp dụng thuật toán fuzzy matching để xử lý lỗi chính tả và tìm kiếm gần đúng
3. **Candidate Selection**: Nếu có nhiều kết quả, sẽ chọn ứng viên phù hợp nhất dựa trên input đã được tiền xử lý

## Lưu ý
- Hàm sẽ tự động khởi tạo dữ liệu, từ điển prefix và automaton khi import
- Đảm bảo các module utils (data, trie, fuzz, input) có sẵn trong project
- Kết quả trả về là địa chỉ được chuẩn hóa tốt nhất từ pipeline