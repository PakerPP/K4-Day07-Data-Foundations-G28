# Báo Cáo Cá Nhân - Lab 7: Embedding & Vector Store

**Họ tên:** Bùi Xuân Tùng (MSSV: 2A202601828)
**Nhóm:** G28-E403
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) - Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding chỉ về gần cùng một hướng, nghĩa là hai đoạn văn bản nói về cùng một chủ đề hoặc cùng một ý định dù dùng từ khác nhau. Điểm chạy từ -1 đến 1: gần 1 là cùng ý, gần 0 là không liên quan.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn đổi trả sản phẩm bị lỗi."
- Câu B: "Làm sao để hoàn hàng khi hàng bị hỏng?"
- Tại sao tương đồng: cùng ý định của người mua, chỉ khác cách diễn đạt ("đổi trả" / "hoàn hàng", "bị lỗi" / "bị hỏng"). Hai câu gần như không trùng từ nào nhưng embedding vẫn xếp chúng gần nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Hôm nay trời mưa rất to ở Hà Nội."
- Câu B: "Quy định hoàn tiền cho đơn hàng bị hủy."
- Tại sao khác: một câu về thời tiết, một câu về chính sách TMĐT, không chung ngữ cảnh nào nên hai vector gần như vuông góc.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ xét hướng của vector, đã bỏ qua độ dài, nên một câu hỏi ngắn và một đoạn văn dài cùng chủ đề vẫn khớp nhau. Euclid thì chịu ảnh hưởng của độ lớn vector, mà độ lớn lại phụ thuộc độ dài văn bản, nên đoạn dài dễ bị coi là xa dù cùng nội dung.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> step = 500 - 50 = 450
> số chunk = ceil((10000 - 50) / 450) = ceil(22.11) = 23
>
> *Đáp án:* 23 chunks. Tôi chạy `FixedSizeChunker(chunk_size=500, overlap=50).chunk("x" * 10000)` thì được đúng 23.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> step còn 400 nên số chunk tăng lên ceil(9900 / 400) = 25, chạy code cũng ra 25. Overlap lớn hơn thì tốn thêm chi phí nhúng và lưu trữ, bù lại một câu bị cắt ngang ở ranh giới chunk vẫn còn nguyên vẹn trong chunk kế bên nên không mất khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) - Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** - hướng tiếp cận:
> Tôi tách câu bằng `re.split(r"(?<=[.!?])\s+", text.strip())`. Dùng lookbehind để dấu chấm câu ở lại với câu đứng trước, còn khoảng trắng (kể cả xuống dòng) làm dấu tách, nên một biểu thức phủ được cả 4 mẫu `". "`, `"! "`, `"? "`, `".\n"`. Sau đó tôi strip từng câu, bỏ chuỗi rỗng rồi gom theo `max_sentences_per_chunk`. Text rỗng hoặc chỉ có khoảng trắng thì trả về list rỗng; văn bản không có dấu chấm câu thì coi như một câu và trả về 1 chunk.

**`RecursiveChunker.chunk` / `_split`** - hướng tiếp cận:
> `chunk()` chỉ xử lý text rỗng rồi gọi `_split(text, separators)`. `_split` dừng ở hai trường hợp: đoạn đã ngắn hơn `chunk_size` thì trả về luôn, hoặc hết separator thì cắt cứng theo `chunk_size`. Còn lại thì lấy separator ưu tiên cao nhất để cắt, separator nào không xuất hiện trong đoạn thì bỏ qua thử cái tiếp theo, mảnh nào vẫn dài quá thì đệ quy với phần separator còn lại.
>
> Tôi thêm một bước `_merge` gộp các mảnh nhỏ liền kề lại cho tới sát `chunk_size`. Lúc đầu tôi không có bước này và gặp lỗi: với văn xuôi không có xuống dòng, separator `" "` cắt ra hàng trăm chunk mỗi chunk 1 từ, vẫn qua test nhưng tìm kiếm thì vô dụng.

### Lớp EmbeddingStore

**`add_documents` + `search`** - hướng tiếp cận:
> `_make_record()` chuyển mỗi `Document` thành dict `{uid, id, content, metadata, embedding}` và nhúng nội dung ngay lúc ghi, để lúc tìm kiếm chỉ phải nhúng câu hỏi. Tôi gán `metadata.setdefault("doc_id", doc.id)` để filter và `delete_document` luôn có khoá làm việc, và thêm `uid = f"{doc.id}#{_next_index}"` vì test có trường hợp thêm hai lô document trùng `id` mà vẫn phải đếm thành hai bản ghi.
>
> `search()` nhúng câu hỏi rồi gọi `_search_records()`, hàm này tính cosine giữa query và từng embedding, sắp xếp giảm dần rồi cắt `top_k`. Đề bài gợi ý dùng tích vô hướng, nhưng tôi dùng cosine để điểm số không phụ thuộc vào việc backend có chuẩn hoá vector hay không: mock và local đều đã chuẩn hoá, riêng OpenAI thì không chắc.
>
> Ở `__init__`, nếu máy có `chromadb` thì tôi khởi tạo `EphemeralClient` và mirror dữ liệu sang đó, nhưng phần đọc vẫn lấy từ danh sách trong bộ nhớ. Làm vậy để kết quả giống nhau dù máy chấm có ChromaDB hay không, và nếu Chroma lỗi thì bắt exception rồi quay về in-memory.

**`search_with_filter` + `delete_document`** - hướng tiếp cận:
> Tôi lọc metadata trước rồi mới xếp hạng phần còn lại. Nếu làm ngược lại, lấy top-k xong mới lọc, thì số kết quả trả về sẽ ít hơn `top_k` một cách khó đoán vì các chunk bị loại đã chiếm mất suất. Khi `metadata_filter` là `None` thì hàm chạy y hệt `search()`.
>
> `delete_document` dựng lại danh sách chỉ gồm chunk có `doc_id` khác giá trị cần xoá, rồi so số lượng trước và sau để biết trả `True` hay `False`. Cách này xoá hết chunk của một tài liệu trong một lần duyệt.

### Tác tử KnowledgeBaseAgent

**`answer`** - hướng tiếp cận:
> Retrieve `top_k` chunk, ghép thành ngữ cảnh, gọi `llm_fn`. Tôi đánh số các chunk `[1] [2] [3]` kèm `source` và `score` để câu trả lời trích dẫn được, và để tôi kiểm tra xem câu trả lời dựa trên đoạn nào. Prompt nói rõ chỉ được trả lời dựa trên ngữ cảnh, thiếu thông tin thì nói không biết. Nếu store rỗng hoặc không tìm được chunk nào thì tôi trả về thông báo luôn chứ không gọi LLM, vì gọi LLM với ngữ cảnh rỗng thì nó sẽ tự bịa.

---

## 3. Hoàn thiện code (Core Implementation) - Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ LAB_SOLUTION_PACKAGE="src.BuiXuanTung-2A202601828" pytest tests/ -v
test_delete_reduces_collection_size ... ok
test_delete_returns_false_for_nonexistent_doc ... ok
test_delete_returns_true_for_existing_doc ... ok
test_filter_by_department ... ok
test_no_filter_returns_all_candidates ... ok
test_returns_at_most_top_k ... ok
test_chunks_respect_size ... ok
test_correct_number_of_chunks_no_overlap ... ok
test_empty_text_returns_empty_list ... ok
test_no_overlap_no_shared_content ... ok
test_overlap_creates_shared_content ... ok
test_returns_list ... ok
test_single_chunk_if_text_shorter ... ok
test_answer_non_empty ... ok
test_answer_returns_string ... ok
test_root_main_entrypoint_exists ... ok
test_src_package_exists ... ok
test_chunks_within_size_when_possible ... ok
test_empty_separators_falls_back_gracefully ... ok
test_handles_double_newline_separator ... ok
... (42 tests)
----------------------------------------------------------------------
Ran 42 tests in 0.005s

OK
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

> Ghi chú cấu trúc: cả nhóm dùng chung một repo nên mã nguồn của tôi để ở gói riêng `src/BuiXuanTung-2A202601828/`, thư mục `src/` gốc giữ nguyên bản template. Bộ test đã hỗ trợ sẵn việc này qua biến `LAB_SOLUTION_PACKAGE` ([tests/test_solution.py:17](../tests/test_solution.py#L17)) nên chỉ cần đặt biến môi trường như lệnh trên. Máy tôi chưa cài `pytest` nên tôi chạy bằng `python -m unittest discover -s tests -t .`, cùng file test và cùng 42 case.

Ngoài bộ test, tôi chạy thêm hai thứ để chắc chắn code hoạt động trên dữ liệu thật:

- `python ingest.py` - self-check của pipeline nạp dữ liệu: `parse được 4 khóa metadata, tạo 18 chunk`.
- Nạp 6 tài liệu của nhóm bằng `build_knowledge_base()` với `EMBEDDING_PROVIDER=local`, rồi chạy 5 câu hỏi đánh giá qua `search()`, `search_with_filter()` và `KnowledgeBaseAgent` (kết quả ở mục 5).

Lưu ý: `main.py` chạy sẽ lỗi vì nó `import` cứng từ `src/` (bản template chưa cài đặt). Tôi để nguyên `main.py` vì đó là file chung của repo, và gọi trực tiếp gói `src/BuiXuanTung-2A202601828/` khi chạy thử.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) - Cá nhân (5 điểm)

Tôi ghi dự đoán trước, sau đó gọi `compute_similarity()` bằng hai backend: `LocalEmbedder` (`paraphrase-multilingual-MiniLM-L12-v2`, 384 chiều) làm kết quả chính, và `MockEmbedder` (64 chiều) để đối chứng.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (local) | Đúng? | (mock) |
|------|-----------|-----------|---------|--------------|-------|------|
| 1 | Tôi muốn đổi trả sản phẩm bị lỗi | Làm sao để hoàn hàng khi hàng bị hỏng? | cao | +0.398 | ✓ | -0.209 |
| 2 | Chính sách giao hàng trong 3 ngày | Thời gian vận chuyển đơn hàng là bao lâu? | cao | +0.668 | ✓ | +0.233 |
| 3 | Phương thức thanh toán bằng thẻ tín dụng | Điều kiện đăng ký làm người bán trên sàn | thấp | +0.302 | ✗ | -0.125 |
| 4 | Chính sách bảo mật dữ liệu khách hàng | Sàn thu thập và lưu trữ thông tin cá nhân thế nào? | cao | +0.567 | ✓ | -0.065 |
| 5 | Hôm nay trời mưa rất to ở Hà Nội | Quy định hoàn tiền cho đơn hàng bị hủy | thấp | -0.014 | ✓ | -0.079 |

**Dự đoán đúng: 4/5.**

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 3, tôi đoán thấp nhưng đo được +0.302. Hai câu nói về hai chuyện khác nhau, thanh toán bằng thẻ và điều kiện làm người bán, nhưng cùng là văn phong chính sách sàn TMĐT và dùng chung lớp từ "phương thức", "điều kiện", "đăng ký", "sàn". So với cặp 5 chỉ được -0.014 thì thấy rõ: hai câu cùng miền chủ đề luôn có sẵn một mức tương đồng nền, còn khác miền thì mới về 0.
>
> Điều này khiến tôi bỏ ý định đặt ngưỡng score cố định để lọc kết quả. Trên kho tài liệu toàn chính sách TMĐT, chunk nào cũng sẽ được chấm quanh 0.3-0.5 chỉ vì cùng miền, nên ngưỡng kiểu "trên 0.3 là liên quan" sẽ nhận vào rất nhiều nhiễu. Ở mục 5 tôi dùng thứ hạng thay cho ngưỡng, và quả thật câu 1 với câu 5 đều có top-1 điểm cao mà lấy sai đoạn.
>
> Cột mock cho thấy một chuyện khác: cặp 1 gần như đồng nghĩa lại bị chấm -0.209, thấp hơn cả cặp 5 chẳng liên quan gì. `MockEmbedder` băm cả chuỗi bằng MD5 rồi sinh vector giả ngẫu nhiên nên nó ổn định cho unit test nhưng không mã hoá ý nghĩa. Cùng công thức cosine, cùng `EmbeddingStore`, chỉ đổi backend là thứ tự lật ngược, nên phần đánh giá chiến lược ở mục 5 tôi đều chạy bằng local.

---

## 5. Kết quả truy xuất của tôi (Competition Results) - Cá nhân (10 điểm)

Chiến lược của tôi: **`FixedSizeChunker(chunk_size=900, overlap=150)`**, chọn sau khi so 6 cấu hình (bảng bên dưới). Dữ liệu là 6 tài liệu Tiki của nhóm (37.614 ký tự), embedder `local`, top-k = 3. Bộ 5 câu hỏi và gold answer lấy từ [`REPORT_NHOM.md`](REPORT_NHOM.md) Phần 3.

> Cách chấm: một chunk chỉ được tính là đúng khi vừa khớp `doc_id` kỳ vọng, vừa chứa từ khoá bằng chứng của gold answer. Nếu chỉ chấm theo `doc_id` thì `returns-policy.md` (15 KB) sẽ luôn được tính đúng cho mọi câu về đổi trả kể cả khi lấy nhầm đoạn, đúng cái bẫy xảy ra ở câu 1. Điểm theo `docs/SCORING.md`: 2đ nếu chunk đúng ở top-1, 1đ nếu ở hạng 2-3, 0đ nếu trượt.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Tôi được đổi trả hàng trong bao nhiêu ngày kể từ khi nhận hàng? | `k4_returns_policy`, đoạn "hoàn tiền... 3-5 ngày làm việc", sai đoạn; chunk chứa "30 ngày / 365 ngày" ở hạng 2 (+0.548) | +0.626 | ~ đúng ở hạng 2 | Trả lời được 30 ngày và 365 ngày nhờ chunk hạng 2 |
| 2 | Sau khi yêu cầu đổi trả được duyệt thì bao lâu tôi phải gửi hàng về, và bao lâu được hoàn tiền? | `k4_returns_policy`, "Quy trình này có thể cần khoảng 3 -5 ngày làm việc..." | +0.662 | ✓ top-1 | Đúng cả hai vế: 07 ngày làm việc gửi trả, 3-5 ngày hoàn tiền |
| 3 | Tôi khiếu nại đơn hàng qua kênh nào và bao lâu Tiki phản hồi? | `k4_tiki_chinh_sach_khieu_nai`, "Bước 2: Bộ phận Tiki Care sẽ tiếp nhận... không quá 3 ngày làm việc" | +0.653 | ✓ top-1, hạng 2 cũng đúng | Đúng: hotline 19006035, email, chat; phản hồi trong 3 ngày làm việc |
| 4 | Khi nhận hàng tôi được phép kiểm tra sản phẩm tới mức nào? | `k4_chinh_sach_kiem_hang`, "...có thể mở niêm phong thùng hàng của Tiki để kiểm tra" | +0.522 | ✓ top-1 | Đúng: mở niêm phong thùng được, không mở seal sản phẩm, không kiểm tra sâu |
| 5 | Thông tin thẻ thanh toán của tôi được lưu trữ như thế nào? | `k4_returns_policy`, đoạn hoàn tiền, là nhiễu; chunk đúng `k4_security_policy` ở hạng 2 (+0.474) | +0.538 | ~ đúng ở hạng 2 | Đúng nhờ chunk hạng 2: Tiki chỉ lưu token đã mã hoá, không lưu thẻ |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5**, trong đó 3 câu đúng ngay top-1, 2 câu ở hạng 2. Điểm rubric: **8/10**.

### So sánh 6 chiến lược trên cùng bộ câu hỏi

| Chiến lược | Số chunk | Độ dài TB | hit@3 | top-1 | MRR | Điểm rubric /10 |
|---|---|---|---|---|---|---|
| `fixed_900_150` (của tôi) | 50 | 884.3 | 5/5 | 3/5 | 0.800 | 8 |
| `heading_900` (custom) | 76 | 503.1 | 5/5 | 3/5 | 0.767 | 8 |
| `recursive_900` | 50 | 748.6 | 5/5 | 3/5 | 0.733 | 8 |
| `fixed_500_50` | 85 | 489.0 | 4/5 | 3/5 | 0.700 | 7 |
| `sentences_3` | 89 | 419.0 | 4/5 | 2/5 | 0.600 | 6 |
| `recursive_500` | 94 | 397.0 | 4/5 | 1/5 | 0.500 | 5 |

**Nhận xét:**

Chunk lớn cho kết quả tốt hơn hẳn trên bộ tài liệu này. Ba cấu hình quanh 900 ký tự đều đạt 5/5, ba cấu hình 400-500 ký tự chỉ được 4/5, riêng `recursive_500` tuy vẫn 4/5 nhưng chỉ 1/5 ở top-1. Tôi nghĩ nguyên nhân là chính sách Tiki viết theo kiểu tiêu đề rồi liệt kê điều kiện, cắt nhỏ thì con số bị tách khỏi tiêu đề của nó. Chunk chứa "30 ngày" mà mất dòng "Thời gian hỗ trợ đổi trả" thì khớp với câu hỏi kém hẳn.

Câu 1 và câu 5 bị cùng một chunk cướp top-1, là đoạn "hoàn tiền... 3-5 ngày làm việc" của `k4_returns_policy`. Đoạn này đặc từ vựng chung của cả miền như "thời gian", "thanh toán", "khách hàng" nên câu hỏi nào trong miền cũng khớp được một phần. Đây đúng là hiện tượng tương đồng nền tôi gặp ở cặp 3 mục 4.

Lọc metadata xử lý được đúng ca đó. Vẫn câu 5, vẫn chiến lược `fixed_900_150`:

| Truy vấn | Kết quả top-3 | Chunk đúng |
|---|---|---|
| Không lọc | `k4_returns_policy`, `k4_security_policy`, `k4_security_policy` | 2/3 |
| Lọc `{"category": "security"}` | cả 3 đều `k4_security_policy` | 3/3 |

Chunk nhiễu bị loại hết và chunk đúng lên top-1. Đây là câu thoả yêu cầu "ít nhất 1 câu cần metadata filtering" ở [exercises.md:142](../exercises.md#L142).

Về khoảng cách điểm giữa top-1 và top-2: câu 4 gap chỉ +0.005 mà vẫn đúng, còn câu 1 và câu 5 điểm top-1 cao (+0.626 và +0.538) nhưng lấy sai đoạn. Nên gap nhỏ chỉ là dấu hiệu mô hình đang phân vân, còn điểm tuyệt đối cao thì không bảo đảm gì cả.

Chunker `heading_900` tôi tự viết cắt theo tiêu đề Markdown, đạt hit@3 5/5 bằng chiến lược thắng nhưng chunk ngắn hơn 43% (503 so với 884 ký tự), tức là đưa vào LLM ít chữ thừa hơn cho cùng chất lượng truy xuất. Nếu tính cả chi phí ngữ cảnh thì tôi nghĩ nó mới là lựa chọn tốt nhất, tôi sẽ nêu khi so sánh trong nhóm.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *[Điền sau buổi demo]*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation - tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **57 / 60** |
