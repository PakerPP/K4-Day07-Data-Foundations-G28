# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Điền tên nhóm]
**Thành viên:**

| # | Họ tên | MSSV |
|---|--------|------|
| 1 | Bùi Xuân Tùng | 2A202601828 |
| 2 | Đặng Ngọc Anh | 2A202601706 |
| 3 | Nguyễn Quang Sơn | 2A202601956 |
| 4 | Nguyễn Trung Hiếu | 2A202601620 |
| 5 | Trần Trung Kiên | 2A202601754 |

**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Các chính sách hỗ trợ khách hàng của TIKI

**Phạm vi cụ thể nhóm tập trung:**
Đổi trả + điều kiện người bán

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | k4-dang-ky-ban-hang.md | [https://seller.tiki.vn/knowledge-base/307/lich-su-su-kien-va-thanh-toan](https://seller.tiki.vn/knowledge-base/307/lich-su-su-kien-va-thanh-toan) | 2026-08-03 | 17423 | OK |
| 2 | returns-policy.md | [https://seller.tiki.vn/knowledge-base/451/chinh-sach-bao-ve-nguoi-mua](https://seller.tiki.vn/knowledge-base/451/chinh-sach-bao-ve-nguoi-mua) | 2026-08-03 | 11484 | OK |
| 3 | TIKI_Chinh_sach_khieu_nai.md | [https://seller.tiki.vn/knowledge-base/454/chinh-sach-bao-ve-nguoi-mua](https://seller.tiki.vn/knowledge-base/454/chinh-sach-bao-ve-nguoi-mua) | 2026-08-03 | 3894 | OK |
| 4 | TIKI_chinh_sach_bao_mat.md | [https://seller.tiki.vn/knowledge-base/455/chinh-sach-bao-ve-nguoi-mua](https://seller.tiki.vn/knowledge-base/455/chinh-sach-bao-ve-nguoi-mua) | 2026-08-03 | 2362 | OK |
| 5 | TIKI_huong-dan-dong-goi-gui-hang.md | [https://seller.tiki.vn/knowledge-base/503/chinh-sach-bao-ve-nguoi-mua](https://seller.tiki.vn/knowledge-base/503/chinh-sach-bao-ve-nguoi-mua) | 2026-08-03 | 2112 | OK |
| 6 | TIKI_chinh_sach_kiem_hang.md | [https://seller.tiki.vn/knowledge-base/570/chinh-sach-bao-ve-nguoi-mua](https://seller.tiki.vn/knowledge-base/570/chinh-sach-bao-ve-nguoi-mua) | 2026-08-03 | 835 | OK |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [X] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [X] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| doc_id | text | k4_chinh_sach_kiem_hang | mã định danh của tài liệu |
| title | text | chính sách kiểm hàng | giúp hiểu rõ nguồn trả lời lấy từ đâu |
| customer_role | text | buyer | Giúp bot đang hiểu thêm về người dùng đang tương tác là ai |
| category | text | return | phân loại tài liệu để bot tìm kiếm dữ liệu nhanh hơn |
| language | text | vi | tốt trong trường hợp query đa ngôn ngữ |
| source_url | text | https://tiki.vn/chinh-sach-kiem-hang | kiểm tra nguồn dữ liệu |
| retrieved_at | datetime | 2026-08-03 | Thời gian rút trích dữ liệu |
| document_version| text | 2026.01 | Truy xuất theo phiên bản của tài liệu |
---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây. **Mỗi người chọn một chiến lược khác nhau** để có cơ sở so sánh.

**Thành viên 1 — Bùi Xuân Tùng (2A202601828)**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — Đặng Ngọc Anh (2A202601706)**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — Nguyễn Quang Sơn (2A202601956)**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 4 — Nguyễn Trung Hiếu (2A202601620)**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 5 — Trần Trung Kiên (2A202601754)**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Bùi Xuân Tùng | | | | |
| Đặng Ngọc Anh | | | | |
| Nguyễn Quang Sơn | | | | |
| Nguyễn Trung Hiếu | | | | |
| Trần Trung Kiên | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Tôi được đổi trả hàng trong bao nhiêu ngày kể từ khi nhận hàng? | 30 ngày kể từ lúc nhận hàng thành công với mọi lý do. Riêng Thiết bị số - Phụ kiện số và Điện gia dụng do Tiki Trading bán, lỗi kỹ thuật được đổi trả trong 365 ngày. | `k4_returns_policy` — mục "Thời gian hỗ trợ đổi trả tại Tiki" |
| 2 | Sau khi yêu cầu đổi trả được duyệt thì bao lâu tôi phải gửi hàng về, và bao lâu được hoàn tiền? | Phải bàn giao hàng trong 07 ngày làm việc kể từ khi yêu cầu được chấp thuận, quá hạn Tiki có quyền hủy. Hoàn tiền sau khi kiểm tra chất lượng, khoảng 3-5 ngày làm việc; thẻ Visa/Master/JCB thêm 1-3 tuần. | `k4_returns_policy` — mục "Quy trình yêu cầu hoàn trả" + "Quy trình hoàn tiền" |
| 3 | Tôi khiếu nại đơn hàng qua kênh nào và bao lâu Tiki phản hồi? | Hotline 19006035 (8h-21h hằng ngày), email hotro@tiki.vn, hoặc chat trực tiếp. Tiki Care tiếp nhận và liên hệ làm rõ không quá 3 ngày làm việc. | `k4_tiki_chinh_sach_khieu_nai` — Bước 1 và Bước 2 |
| 4 | Khi nhận hàng tôi được phép kiểm tra sản phẩm tới mức nào? | Được mở niêm phong thùng hàng của Tiki để kiểm tra, nhưng không được mở seal riêng của sản phẩm và không kiểm tra sâu (cắm điện, dùng thử, ghi chép dữ liệu). | `k4_chinh_sach_kiem_hang` — toàn bộ tài liệu |
| 5 | Thông tin thẻ thanh toán của tôi được lưu trữ như thế nào? | Tiki không trực tiếp lưu thông tin thẻ, chỉ lưu token đã được Đối Tác Cổng Thanh Toán mã hóa. Thẻ quốc tế do Đối Tác lưu trữ; thẻ nội địa Tiki chỉ lưu mã đơn hàng, mã giao dịch và tên ngân hàng. | `k4_security_policy` — mục "Chính sách bảo mật giao dịch trong thanh toán" |

> Câu 5 là câu cần lọc metadata: từ khoá "thanh toán" trùng với tài liệu hoàn tiền nên nếu không lọc, chunk của `k4_returns_policy` sẽ chiếm top-1. Lọc `{"category": "security"}` thì cả 3 kết quả đều đúng tài liệu.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
