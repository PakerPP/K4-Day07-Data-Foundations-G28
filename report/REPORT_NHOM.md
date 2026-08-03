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

> Chạy `ChunkingStrategyComparator().compare(doc.content, chunk_size=500)` (tham số `overlap=chunk_size//10` cho `fixed_size`) trên 3 tài liệu đại diện — một tài liệu rất dài (`k4-dang-ky-ban-hang`, 17102 ký tự), một tài liệu trung bình (`k4_returns_policy`, 11290 ký tự) và một tài liệu ngắn (`k4_security_policy`, 2337 ký tự):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| k4-dang-ky-ban-hang (17102 ký tự) | FixedSizeChunker (`fixed_size`) | 38 | 498.74 | Không — cắt đúng vị trí ký tự, thường xuyên chia đôi câu/tiêu đề |
| k4-dang-ky-ban-hang (17102 ký tự) | SentenceChunker (`by_sentences`) | 46 | 368.96 | Một phần — giữ trọn câu nhưng không giữ heading của mục cha |
| k4-dang-ky-ban-hang (17102 ký tự) | RecursiveChunker (`recursive`) | 42 | 402.10 | Tốt — ưu tiên tách theo đoạn (`\n\n`)/dòng nên thường giữ trọn heading + nội dung ngay dưới |
| k4_returns_policy (11290 ký tự) | FixedSizeChunker (`fixed_size`) | 25 | 499.60 | Không — ví dụ mốc "30 ngày" từng bị tách khỏi dòng tiêu đề "Thời gian hỗ trợ đổi trả" |
| k4_returns_policy (11290 ký tự) | SentenceChunker (`by_sentences`) | 20 | 558.65 | Một phần — câu dài trong văn bản chính sách khiến chunk cũng dài, đôi khi vượt cả `chunk_size` tham chiếu |
| k4_returns_policy (11290 ký tự) | RecursiveChunker (`recursive`) | 28 | 396.89 | Tốt — bám theo cấu trúc heading/liệt kê sẵn có của tài liệu |
| k4_security_policy (2337 ký tự) | FixedSizeChunker (`fixed_size`) | 6 | 431.17 | Trung bình — tài liệu ngắn nên ít bị ảnh hưởng |
| k4_security_policy (2337 ký tự) | SentenceChunker (`by_sentences`) | 7 | 330.71 | Tốt — tài liệu này gồm các câu liệt kê ngắn, rõ ràng nên nhóm câu vẫn mạch lạc |
| k4_security_policy (2337 ký tự) | RecursiveChunker (`recursive`) | 6 | 385.67 | Tốt — tài liệu ngắn nên phần lớn nội dung nằm trọn trong 1-2 chunk |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây. **Mỗi người chọn một chiến lược khác nhau** để có cơ sở so sánh.

**Thành viên 1 — Bùi Xuân Tùng (2A202601828)**
- **Loại chiến lược:** FixedSize với tham số tinh chỉnh — **`chunk_size = 900` ký tự, `overlap = 150` ký tự** (mặc định của lab là 500/50). Cụ thể: `FixedSizeChunker(chunk_size=900, overlap=150)`, cho ra 50 chunk, độ dài trung bình 884.3 ký tự trên bộ 6 tài liệu.
- **Mô tả & lý do chọn cho chủ đề này:** Tôi thử 6 cấu hình trên cùng 5 câu hỏi đánh giá và thấy chunk lớn thắng rõ: ba cấu hình quanh 900 ký tự đều đạt hit@3 5/5, còn ba cấu hình 400-500 ký tự chỉ được 4/5. Lý do là tài liệu chính sách Tiki viết theo kiểu tiêu đề rồi liệt kê điều kiện bên dưới, cắt nhỏ thì con số bị tách khỏi tiêu đề của nó — chunk chứa "30 ngày" mà mất dòng "Thời gian hỗ trợ đổi trả" thì khớp với câu hỏi kém hẳn. Overlap 150 (bằng 1/6 chunk) để một điều khoản bị cắt ngang vẫn còn nguyên ở chunk kế bên.
- **Kết quả:** hit@3 5/5, top-1 3/5, MRR 0.800, điểm rubric 8/10.
- **Code snippet (nếu custom):** không phải chunker tự viết, dùng `FixedSizeChunker` có sẵn với tham số đã tinh chỉnh:
```python
chunker = FixedSizeChunker(chunk_size=900, overlap=150)
store = build_knowledge_base("data/k4_ecommerce", embedding_fn=embedder, chunker=chunker)
```

**Thành viên 2 — Đặng Ngọc Anh (2A202601706)**
- **Loại chiến lược:** `RecursiveChunker` với **`chunk_size = 600` ký tự**, separator ưu tiên mặc định `["\n\n", "\n", ". ", " ", ""]`. Cho ra **76 chunk** trên bộ 6 tài liệu, độ dài trung bình **487 ký tự** (min 102, max 600).
- **Mô tả & lý do chọn:** Tài liệu chính sách Tiki được viết theo cấu trúc heading + đoạn/liệt kê bên dưới (`## Thời gian hỗ trợ đổi trả`, `### Bước 1: ...`), nên tôi chọn `RecursiveChunker` để tận dụng đúng cấu trúc đó: nó ưu tiên tách theo đoạn (`\n\n`) và dòng (`\n`) trước khi phải cắt cứng theo ký tự, nên phần lớn chunk giữ nguyên trọn một heading cùng nội dung ngay dưới nó thay vì bị cắt ngang tuỳ tiện như FixedSizeChunker thuần cắt theo vị trí ký tự. Chạy 5 câu hỏi benchmark: **5/5 câu có chunk liên quan trong top-3** (4/5 câu đúng ngay ở top-1); câu 5 ("thông tin thẻ thanh toán lưu trữ thế nào") là câu cần lọc metadata — `search_with_filter({"category": "security"})` loại sạch nhiễu từ `k4_returns_policy` (tài liệu này cũng nhắc "hoàn tiền"/"thanh toán" nên dễ gây nhiễu nếu không lọc). Điểm yếu: câu 4 (phạm vi kiểm tra hàng khi nhận) có chunk đúng nhất từ `k4_chinh_sach_kiem_hang` chỉ xếp hạng 2 vì tài liệu này quá ngắn (835 ký tự) nên vector "loãng" hơn so với đoạn dài cùng từ khoá từ `k4_returns_policy`.
- **Code snippet (nếu custom):** không phải chunker tự viết, dùng `RecursiveChunker` có sẵn với tham số đã chọn:
```python
chunker = RecursiveChunker(chunk_size=600)
chunk_docs = [c for doc in load_documents("data/k4_ecommerce") for c in chunk_document(doc, chunker)]
store = EmbeddingStore(collection_name="k4_recursive", embedding_fn=LocalEmbedder())
store.add_documents(chunk_docs)
```

**Thành viên 3 — Nguyễn Quang Sơn (2A202601956)**
- **Loại chiến lược:** custom `HeadingPolicyChunker(chunk_size=900)`.
- **Mô tả & lý do chọn:** Chunker tách Markdown theo heading (`#` đến `######`) trước, giữ heading cùng điều khoản mà nó giới thiệu. Nếu một mục dài hơn giới hạn, phần thân được chia tiếp theo đoạn/câu và heading được lặp lại trên từng mảnh con; điều này giúp query khớp cả chủ đề lẫn điều kiện của chính sách. Trên 6 tài liệu của nhóm, cấu hình này tạo **81 chunk**, độ dài trung bình **473.1 ký tự**, độ dài lớn nhất **895 ký tự**.
- **Kết quả:** Baseline chạy bằng `_mock_embed`: top-3 có chunk liên quan ở **2/5** benchmark (câu 2 có chunk hoàn tiền ở hạng 2 và câu 5 khi lọc `category=security`), tương ứng **4/10** theo quy ước 2 điểm cho mỗi câu có hit@3. Đây là điểm baseline của pipeline; mock embedder không mã hóa ngữ nghĩa nên không dùng số liệu này để kết luận chiến lược tốt hơn các thành viên khác.
- **Code snippet (nếu custom):** chunker tự viết trong `src/NguyenQuangSon-2A202601956/policy_chunker.py`:
```python
chunker = HeadingPolicyChunker(chunk_size=900)
store = build_knowledge_base("data/k4_ecommerce", embedding_fn=embedder, chunker=chunker)
```

**Thành viên 4 — Nguyễn Trung Hiếu (2A202601620)**
- **Loại chiến lược:** `SentenceChunker` (có sẵn trong lab) với **`max_sentences_per_chunk = 4`**. Cho ra **67 chunk** trên bộ 6 tài liệu, độ dài trung bình **555 ký tự** (min 127, max 1577).
- **Mô tả & lý do chọn cho chủ đề này:** Đây là chiến lược duy nhất trong nhóm chia theo **ranh giới câu thuần túy**, không quan tâm heading/kích thước ký tự cố định — dùng để làm đối chứng cho các chiến lược "biết cấu trúc" (heading-aware) của Sơn/Kiên và các chiến lược cắt theo ký tự (FixedSize/Recursive) của Tùng/Anh. Chạy 5 câu hỏi benchmark: **4/5 câu có chunk liên quan trong top-3** (3/5 đúng ngay top-1); điểm cao nhất toàn benchmark là câu 3 (0.735) vì tài liệu khiếu nại viết theo câu ngắn, rõ ràng theo từng bước nên nhóm 4 câu vừa khít một ý hoàn chỉnh. Điểm yếu: câu 1 thất bại vì câu chứa mốc chính "30 ngày" bị gộp chung với các câu lân cận kém liên quan hơn, khiến vector "loãng" và rơi khỏi top-3 — cho thấy chunk theo **số lượng câu cố định** dễ vỡ khi câu quan trọng nằm cạnh câu không liên quan.
- **Code snippet (nếu custom):** không phải chunker tự viết, dùng `SentenceChunker` có sẵn với tham số đã chọn:
```python
chunker = SentenceChunker(max_sentences_per_chunk=4)
chunk_docs = [c for doc in load_documents("data/k4_ecommerce") for c in chunk_document(doc, chunker)]
store = EmbeddingStore(collection_name="k4_sentence", embedding_fn=LocalEmbedder())
store.add_documents(chunk_docs)
```

**Thành viên 5 — Trần Trung Kiên (2A202601754)**
- **Loại chiến lược:** Custom `HeaderChunker` — chia tài liệu theo ranh giới tiêu đề markdown (`##`, `###`), mỗi section (tiêu đề + nội dung bên dưới) thành một chunk; nếu section vẫn vượt quá `max_chunk_size`, dùng `RecursiveChunker(chunk_size=max_chunk_size)` làm fallback để cắt tiếp mà không phá cấu trúc câu. Cấu hình: `HeaderChunker(max_chunk_size=800)`, cho ra 38 chunk, độ dài trung bình 611.5 ký tự trên bộ 6 tài liệu (min 118, max 792 — do fallback recursive giới hạn ở 800).
- **Mô tả & lý do chọn cho chủ đề này:** Tôi chọn hướng ngược lại với bạn Tùng — thay vì cố định kích thước, tôi tận dụng chính cấu trúc Markdown của tài liệu chính sách Tiki (luôn có `##`/`###` phân tách các mục như "Thời gian hỗ trợ đổi trả", "Quy trình hoàn tiền", "Bước 1/Bước 2"...). Giả thuyết là mỗi chunk sẽ tương ứng đúng 1 điều khoản, giúp điểm tương tự (similarity score) không bị pha loãng bởi nội dung không liên quan nằm chung chunk. Giả thuyết đúng cho các câu hỏi chỉ cần 1 mục duy nhất (Câu 1, 4, 5), nhưng lộ điểm yếu ở câu hỏi cần thông tin trải trên 2 mục liên tiếp (Câu 2: "gửi hàng về" + "hoàn tiền" là 2 heading khác nhau) và ở các mục quá ngắn thiếu từ khoá để thắng thứ hạng (Câu 3: "Bước 1" chỉ có 2 dòng, thua một chunk dài hơn nhưng ít liên quan hơn).
- **Kết quả:** hit@3 5/5, top-1 đúng trọn vẹn 3/5 (Câu 1, 4, 5), MRR 0.900, điểm rubric 8/10.
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Bùi Xuân Tùng | FixedSizeChunker, chunk_size=900, overlap=150 | 8 | Giữ trọn điều khoản kèm tiêu đề nên hit@3 đạt 5/5; lọc metadata `category=security` đưa câu 5 từ 2/3 lên 3/3 | Chunk dài 884 ký tự trung bình nên tốn token ngữ cảnh; đoạn "hoàn tiền 3-5 ngày làm việc" hút nhầm top-1 ở câu 1 và câu 5 |
| Đặng Ngọc Anh | RecursiveChunker, chunk_size=600 | 8 | Tách theo `\n\n`/`\n` nên chunk bám sát heading gốc của tài liệu; 5/5 câu có chunk liên quan trong top-3; lọc `category=security` loại sạch nhiễu từ `k4_returns_policy` ở câu 5 | Chunk 600 ký tự đôi khi tách rời tiêu đề khỏi đoạn số liệu cụ thể (con số "30 ngày" rơi xuống hạng 2 ở câu 1); tài liệu ngắn (`k4_chinh_sach_kiem_hang`, 835 ký tự) bị tài liệu dài hơn lấn át ở câu 4 |
| Nguyễn Quang Sơn | HeadingPolicyChunker, `chunk_size=900` | 4/10 *(baseline mock, hit@3 = 2/5)* | Giữ heading cùng điều khoản; 81 chunk, trung bình 473 ký tự; hỗ trợ truy xuất theo từng mục chính sách | Kết quả nhạy với mock embedding; cần đánh giá lại bằng embedding ngữ nghĩa trước khi kết luận chất lượng |
| Nguyễn Trung Hiếu | SentenceChunker, max_sentences_per_chunk=4 | 6 | Câu 3 đạt score cao nhất toàn benchmark (0.735) vì tài liệu khiếu nại viết câu ngắn, rõ ràng theo bước; không phụ thuộc cấu trúc Markdown nên vẫn hoạt động trên văn bản không có heading | Độ dài chunk dao động rất lớn (127-1577 ký tự) vì câu tiếng Việt không đều; câu 1 thất bại do câu chứa "30 ngày" bị gộp chung với câu láng giềng kém liên quan, làm loãng vector và rớt khỏi top-3 |
| Trần Trung Kiên | Custom `HeaderChunker`, chia theo tiêu đề markdown (`##`/`###`), fallback `RecursiveChunker(chunk_size=800)` | 8 | Chunk ngắn (611.5 ký tự TB) và "sạch" theo từng điều khoản nên top-1 chính xác tuyệt đối ở câu 1, 4, 5; ít tốn token ngữ cảnh hơn hẳn so với FixedSize 900 | Câu trả lời trải trên 2 heading liên tiếp (câu 2) bị tách thành 2 chunk riêng, top-1 chỉ chứa một nửa câu trả lời; mục quá ngắn (câu 3, "Bước 1" chỉ 2 dòng) thiếu từ khoá nên bị chunk khác xếp trên, tụt xuống hạng 2 |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Các chiến lược **"biết cấu trúc tài liệu"** — dù là cắt theo đoạn/heading (`RecursiveChunker` của Anh, `HeaderChunker` của Kiên, `HeadingPolicyChunker` của Sơn) hay chunk lớn đủ để không tách rời tiêu đề khỏi nội dung (`FixedSizeChunker` 900/150 của Tùng) — đều đạt hit@3 ≥ 4/5 khi dùng embedder ngữ nghĩa thật, trong khi chiến lược chia thuần theo câu (`SentenceChunker` của Hiếu) chỉ đạt 4/5 và có độ dài chunk dao động rất lớn (127-1577 ký tự) do câu tiếng Việt trong văn bản chính sách không đều nhau. Với chủ đề chính sách TMĐT của Tiki — luôn viết theo cấu trúc `## Tiêu đề` + nội dung/liệt kê bên dưới — **`HeaderChunker`/`RecursiveChunker` (chunk theo cấu trúc, ~600-800 ký tự) là lựa chọn cân bằng tốt nhất**: chunk vừa đủ ngắn để giữ điểm số phân biệt rõ ràng, vừa giữ trọn heading để không mất ngữ cảnh chủ đề, khác với `FixedSizeChunker` 900 ký tự tuy hit@3 cao nhưng tốn nhiều token ngữ cảnh hơn hẳn cho mỗi lần truy vấn.
>
> Điểm chung thất bại giữa các chiến lược: câu hỏi cần thông tin trải trên **2 mục liền kề** (câu 2: "gửi hàng về" + "hoàn tiền" là hai heading khác nhau) luôn là câu khó nhất bất kể chiến lược nào, vì bản chất retrieval theo chunk không thể ghép ngữ cảnh từ 2 heading không liền nhau trong cùng một lần truy vấn — đây là giới hạn cấu trúc chứ không phải lỗi của một chiến lược cụ thể.

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
| 1 | Đổi trả trong bao nhiêu ngày? | FixedSizeChunker 900/150 (Tùng) / HeaderChunker (Kiên) | Có (5/5 thành viên) | Chunk nhỏ (SentenceChunker 4 câu của Hiếu, RecursiveChunker 600 của Anh) đôi khi tách câu "30 ngày" khỏi tiêu đề "Thời gian hỗ trợ đổi trả", khiến score thấp hơn hoặc rớt top-3 |
| 2 | Bao lâu gửi hàng về + bao lâu hoàn tiền? | RecursiveChunker 600 (Anh) — duy nhất trả lời trọn cả 2 vế | Có ở hầu hết thành viên, nhưng thường chỉ đúng 1 vế | Câu khó nhất toàn bộ benchmark: "gửi hàng" và "hoàn tiền" nằm ở 2 heading liền kề nhưng khác nhau — HeaderChunker (Kiên) và HeadingPolicyChunker (Sơn) đều bị tách chunk đúng ranh giới heading nên chỉ lấy được một nửa câu trả lời |
| 3 | Khiếu nại qua kênh nào, bao lâu phản hồi? | SentenceChunker 4 câu (Hiếu) — score cao nhất toàn benchmark (0.735) | Có (đa số thành viên) | Tài liệu khiếu nại viết câu ngắn, từng bước rõ ràng nên mọi chiến lược đều truy xuất tốt; chunker theo heading ngắn (Kiên) bị tụt hạng vì thiếu từ khoá cạnh tranh |
| 4 | Phạm vi kiểm tra hàng khi nhận? | FixedSizeChunker 900/150 (Tùng) / HeaderChunker (Kiên) | Có (đa số ở top-1) | `k4_chinh_sach_kiem_hang` là tài liệu ngắn nhất (835 ký tự) nên dễ bị tài liệu dài hơn (`k4_returns_policy`) lấn át thứ hạng ở các chiến lược chunk nhỏ (RecursiveChunker 600 của Anh, SentenceChunker của Hiếu) |
| 5 | Thông tin thẻ thanh toán lưu trữ thế nào? | Bất kỳ chiến lược nào + `search_with_filter({"category": "security"})` | Có, sau khi lọc metadata (100% thành viên) | Câu duy nhất trong bộ **cần** metadata filtering: `k4_returns_policy` cũng nhắc "hoàn tiền"/"thanh toán" nên gây nhiễu top-1 nếu không lọc theo `category=security` |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có — rõ nhất ở **câu 5**: mọi thành viên đều xác nhận nếu không lọc, chunk của `k4_returns_policy` (cũng chứa từ "thanh toán"/"hoàn tiền") len vào top-3 hoặc thậm chí top-1, làm loãng kết quả đúng từ `k4_security_policy`. Sau khi áp `search_with_filter(metadata_filter={"category": "security"})`, cả 3 kết quả top-3 đều đúng tài liệu ở tất cả các chiến lược đã thử — đây là bằng chứng cụ thể rằng metadata filtering không chỉ là tính năng phụ mà **cần thiết** khi corpus có nhiều tài liệu dùng chung từ vựng miền (domain vocabulary) như "thanh toán", "hoàn tiền", "sản phẩm".

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - Không có "ngưỡng score tuyệt đối" nào đúng cho toàn bộ corpus: vì mọi tài liệu cùng miền chính sách TMĐT Tiki, ngay cả các chunk không liên quan tới câu hỏi vẫn đạt cosine similarity 0.3-0.5 chỉ vì cùng văn phong/domain — điều quan trọng là **thứ hạng tương đối** và khoảng cách giữa top-1 với các hạng sau, không phải điểm số tuyệt đối.
> - Chiến lược "biết cấu trúc tài liệu" (theo heading/đoạn) luôn thắng chiến lược cắt mù theo ký tự hoặc theo câu khi tài liệu vốn có cấu trúc rõ ràng (heading + liệt kê) — nhưng đổi lại dễ vỡ khi câu trả lời cần ghép thông tin từ 2 mục liền kề (câu 2 là ví dụ điển hình ở mọi thành viên).
> - `search_with_filter` bằng metadata không phải tính năng phụ: với corpus mà nhiều tài liệu dùng chung từ vựng miền (câu 5, "thanh toán"), lọc metadata là cách duy nhất đảm bảo top-3 không lẫn tài liệu sai chủ đề.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng 6 tài liệu và cùng 5 câu hỏi, 5 chiến lược khác nhau (FixedSize 900/150, Recursive 600, HeadingPolicyChunker 900, SentenceChunker 4-câu, HeaderChunker 800) cho ra hit@3 dao động 4/5 đến 5/5 — chênh lệch không lớn về số lượng nhưng rất khác nhau về **chỗ nào thất bại**: chunk lớn/theo heading thắng ở câu cần trọn vẹn 1 mục (câu 1, 4), chunk theo câu thắng ở tài liệu có câu ngắn rõ ràng (câu 3), còn không chiến lược nào tự giải quyết được câu cần ghép 2 heading (câu 2). Điều này cho thấy "chiến lược chunking tốt nhất" phụ thuộc vào **cấu trúc của từng tài liệu cụ thể**, không có một cấu hình duy nhất tối ưu cho mọi câu hỏi.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Với câu 2 (thông tin trải 2 heading), nhóm sẽ thử thêm **overlap giữa các chunk theo heading** (ví dụ giữ heading liền trước/liền sau vào chunk hiện tại) thay vì chunk theo ranh giới heading tuyệt đối, để một câu hỏi bắc cầu 2 mục vẫn có cơ hội khớp đủ ngữ cảnh trong 1 chunk. Nhóm cũng sẽ bổ sung thêm tài liệu ngắn khác ngoài `k4_chinh_sach_kiem_hang` (835 ký tự) hoặc gộp các tài liệu quá ngắn vào tài liệu liên quan gần nhất, để tránh tình trạng tài liệu ngắn bị tài liệu dài hơn "lấn át" thứ hạng chỉ vì vector đậm đặc từ khoá hơn.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 9 / 10 |
| Thuyết trình (Demo) | *(chấm sau buổi demo)* |
| **Tổng phần nhóm** | **32 / 35** *(chưa gồm điểm Thuyết trình)* |
