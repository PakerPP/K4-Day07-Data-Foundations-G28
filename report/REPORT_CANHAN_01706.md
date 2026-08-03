# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đặng Ngọc Anh 
**Mã sinh viên:** 2A202601706
**Nhóm:** G28-E403  
**Ngày:** 2026-08-03  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding gần như cùng **hướng** trong không gian nhiều chiều, tức hai đoạn văn bản mang cùng ý nghĩa/chủ đề dù có thể khác từ ngữ. Cosine similarity nằm trong [-1, 1]: càng gần 1 thì hai văn bản càng "nói cùng một chuyện".

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sản phẩm phải còn nguyên tình trạng, chưa qua sử dụng thì mới được đổi trả."
- Câu B: "Hàng muốn hoàn trả cần còn mới, chưa bóc tem và chưa dùng qua."
- Tại sao tương đồng: cả hai câu diễn đạt cùng một điều kiện nghiệp vụ (hàng phải còn mới/nguyên vẹn để được đổi trả) bằng từ ngữ khác nhau ("nguyên tình trạng" ~ "còn mới", "chưa qua sử dụng" ~ "chưa dùng qua") - embedding nắm bắt ý nghĩa nên vẫn xếp gần nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Nhà Bán cần cung cấp CMND/CCCD và mã số thuế cá nhân để đăng ký gian hàng."
- Câu B: "Hôm nay trời mưa to nên tôi ở nhà xem phim."
- Tại sao khác: hai câu không chia sẻ chủ đề, thực thể hay ý định nào — một câu về thủ tục giấy tờ đăng ký bán hàng, một câu về sinh hoạt cá nhân/thời tiết — nên vector của chúng gần như trực giao (score ≈ 0).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ đo **hướng** của vector, đã tự loại bỏ ảnh hưởng của độ dài (norm) — vốn phụ thuộc vào độ dài văn bản (câu dài có xu hướng norm lớn hơn câu ngắn dù cùng ý nghĩa). Euclidean distance thì cộng dồn cả chênh lệch độ lớn lẫn hướng, nên một đoạn văn dài và một câu hỏi ngắn cùng chủ đề có thể bị tính là "xa nhau" một cách giả tạo chỉ vì khác độ dài, dẫn tới so sánh sai lệch giữa các văn bản có độ dài khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Bước nhảy (step) = chunk_size − overlap = 500 − 50 = **450**
> - Số chunk = ceil((10000 − 50) / 450) = ceil(9950 / 450) = ceil(22.11) = **23**
> - Đã xác minh bằng code: `len(FixedSizeChunker(chunk_size=500, overlap=50).chunk("x"*10000))` → **23**, khớp với công thức.
>
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Step giảm còn 500 − 100 = 400, số chunk = ceil((10000 − 100)/400) = ceil(24.75) = **25 chunks** (tăng thêm 2 so với overlap=50; đã kiểm chứng bằng code cho ra đúng 25). Tăng overlap giúp **giảm rủi ro một câu/ý quan trọng bị cắt đứt đúng ngay ranh giới hai chunk** — phần nội dung ở mép chunk trước sẽ được lặp lại ở đầu chunk sau, nên khi truy xuất theo similarity, thông tin đó vẫn còn nguyên vẹn trong ít nhất một chunk. Đánh đổi là nhiều chunk hơn đồng nghĩa tốn thêm chi phí embedding và lưu trữ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `[.!?]\s+|\.\n` với `re.finditer` để quét lần lượt các vị trí ranh giới câu trong văn bản, thay vì `re.split` một lần: mỗi lần khớp, tôi cắt lấy đoạn từ vị trí con trỏ hiện tại đến ngay sau dấu câu (giữ lại dấu `.`/`!`/`?`), rồi đẩy con trỏ qua phần khoảng trắng đã khớp — cách này cho phép xử lý luôn phần "đuôi" còn lại sau ký tự khớp cuối cùng mà không cần thêm điều kiện riêng. Edge case đã xử lý: chuỗi rỗng/toàn khoảng trắng trả về `[]` ngay từ đầu; văn bản không có dấu câu nào thì toàn bộ nội dung rơi vào phần "đuôi" và trở thành một câu duy nhất; `max_sentences_per_chunk` được `max(1, ...)` chặn ở `__init__` để tránh chia nhóm với kích thước 0.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán chia làm hai giai đoạn tách biệt: `_split()` đệ quy để **cắt nhỏ** văn bản xuống dưới `chunk_size` bằng cách thử lần lượt từng separator trong danh sách ưu tiên (nếu separator hiện tại không xuất hiện trong đoạn, tự động rơi xuống separator kế tiếp); sau đó `_pack()` chạy một vòng lặp tích lũy (greedy accumulate) để **gộp lại** các mảnh nhỏ liền kề cho tới khi gần chạm `chunk_size`, tránh tình trạng có quá nhiều chunk tí hon vô dụng cho retrieval. Hai base case của `_split`: (1) đoạn hiện tại đã ≤ `chunk_size` → trả về nguyên vẹn; (2) hết separator để thử → cắt cứng theo từng `chunk_size` ký tự để đảm bảo đệ quy luôn dừng.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuẩn hoá qua `_make_record()` thành một dict `{id, content, metadata, vector}`, trong đó nội dung được nhúng (embed) **ngay khi ghi** để lúc tìm kiếm không phải tính lại; tôi cũng dùng `metadata.setdefault("doc_id", doc.id)` để đảm bảo luôn có khoá `doc_id` dùng cho lọc/xoá kể cả khi caller không tự gắn. `search()` nhúng câu hỏi rồi giao cho `_search_records()` — hàm dùng chung này tính **tích vô hướng** (`_dot`) giữa vector câu hỏi và từng vector đã lưu, sắp xếp giảm dần theo điểm và cắt lấy `top_k`; việc tách `_search_records()` thành hàm riêng cho phép tái sử dụng ở cả `search()` lẫn `search_with_filter()`. Nếu môi trường có `chromadb`, `__init__` sẽ khởi tạo collection thật và `add_documents`/`search` chuyển sang gọi API của ChromaDB; nếu import lỗi (không cài `chromadb`), store tự động rơi về danh sách trong bộ nhớ.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Tôi chọn **lọc trước, tìm sau**: trước tiên lọc `self._store` chỉ giữ các record có toàn bộ cặp key/value trong `metadata_filter` khớp (`all(record["metadata"].get(k) == v ...)`), sau đó mới gọi `_search_records()` để xếp hạng trên tập đã lọc. Làm ngược lại (xếp hạng trước rồi lọc sau) sẽ khiến số kết quả trả về ít hơn `top_k` một cách khó lường vì các ứng viên đúng metadata có thể đã bị loại khỏi top-k ban đầu. `delete_document()` dựng lại danh sách chỉ gồm các record có `metadata["doc_id"] != doc_id`, so sánh độ dài trước/sau để biết có xoá được gì không — cách này xoá toàn bộ chunk của một tài liệu trong một lượt duyệt duy nhất.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Theo đúng 3 bước RAG: gọi `store.search(question, top_k)` để lấy các chunk liên quan, đưa chúng vào `_build_prompt()` để dựng ngữ cảnh đánh số `[Nguồn 1] [Nguồn 2] ...`, rồi gọi `llm_fn(prompt)`. Prompt ra chỉ thị rõ ràng: chỉ trả lời dựa vào ngữ cảnh được cung cấp, nếu ngữ cảnh không đủ thì phải nói không biết — nhằm hạn chế mô hình bịa thông tin ngoài kho tri thức. Khi không tìm được chunk nào (`chunks` rỗng), tôi vẫn gọi `llm_fn` nhưng thay ngữ cảnh bằng câu thông báo "không tìm thấy ngữ cảnh liên quan" để LLM tự phản hồi phù hợp, thay vì để lỗi xảy ra khi ghép chuỗi rỗng.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ LAB_SOLUTION_PACKAGE=src.DangNgocAnh_2A202601706 python -m pytest tests/ -v

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.07s ==============================
```

> Ghi chú: `tests/test_solution.py` mặc định import gói `src` gốc (biến `LAB_SOLUTION_PACKAGE`), nên tôi chạy lại với biến môi trường trỏ vào gói cá nhân `src.DangNgocAnh_2A202601706` để xác nhận đúng code của tôi vượt qua toàn bộ test, không phải bản mẫu.

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Đã cài `LocalEmbedder` (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, 384 chiều) để có kết quả phản ánh ngữ nghĩa tiếng Việt thật; cột `mock` chỉ để đối chứng, không dùng để kết luận.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (local) | Đúng? | *(mock đối chứng)* |
|------|-----------|-----------|---------|--------------|-------|------|
| 1 | Sản phẩm còn nguyên tình trạng như khi nhận, chưa qua sử dụng thì mới được đổi trả. | Hàng muốn hoàn trả cần còn mới, chưa bóc tem và chưa dùng qua. | cao | **0.515** | ✓ | 0.071 |
| 2 | Tiki sử dụng giao thức SSL để bảo vệ thông tin tài chính khách hàng. | Mật khẩu OTP được gửi qua SMS để xác thực giao dịch. | cao | **0.326** | ✓ (nhưng thấp hơn dự đoán) | −0.149 |
| 3 | Nhà Bán cần cung cấp CMND/CCCD và mã số thuế cá nhân để đăng ký gian hàng. | Khách hàng có thể khiếu nại qua hotline 19006035. | thấp | **0.381** | ✗ | 0.076 |
| 4 | Thời gian đổi trả là 30 ngày kể từ ngày nhận hàng. | Đơn vị vận chuyển thu hồi hàng trong 24 giờ. | trung bình/thấp | **0.556** | ✗ (cao hơn dự đoán) | −0.058 |
| 5 | Hôm nay trời mưa to nên tôi ở nhà xem phim. | Chính sách bảo mật thanh toán của Tiki. | thấp | **−0.039** | ✓ | −0.200 |

**Dự đoán đúng: 3/5** (cặp 1, 2, 5 đúng hướng; cặp 3 và 4 lệch dự đoán).

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **cặp 3 (0.381)** và **cặp 4 (0.556)** — cả hai tôi đều dự đoán thấp/trung bình vì hai câu trong mỗi cặp nói về hai nghiệp vụ khác nhau (giấy tờ đăng ký bán hàng vs. kênh khiếu nại; thời hạn đổi trả vs. thời gian thu hồi vận chuyển), nhưng điểm thực tế lại cao hơn hẳn cặp 5 (khác miền hoàn toàn). Điều này cho thấy `LocalEmbedder` không chỉ mã hoá **ý định cụ thể** của câu mà còn mã hoá **miền chủ đề chung** (cùng là văn phong chính sách/thủ tục của một sàn TMĐT, cùng nhắc đến "Tiki", "khách hàng", "thời gian"...) — nên hai câu tuy khác nghiệp vụ vẫn có một mức tương đồng nền đáng kể chỉ vì cùng ngữ cảnh domain. Hệ quả cho retrieval: **không thể đặt một ngưỡng score tuyệt đối** để quyết định "liên quan hay không" trên một kho toàn chính sách Tiki, vì ngay cả các chunk không liên quan tới câu hỏi cũng có thể đạt 0.3-0.5 chỉ vì cùng miền — cần nhìn vào **thứ hạng tương đối** và khoảng cách giữa các điểm số hơn là con số tuyệt đối.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> **Chiến lược của tôi:** `RecursiveChunker(chunk_size=600)` — khác với FixedSizeChunker mà Bùi Xuân Tùng đã dùng. Chunker này ưu tiên tách theo `\n\n` / `\n` / `. ` trước khi cắt cứng, nên giữ nguyên các đoạn/heading của tài liệu chính sách Tiki (vốn được viết theo cấu trúc tiêu đề + liệt kê) thay vì cắt ngang bất kỳ vị trí ký tự nào. Nạp bằng `build_knowledge_base`-tương đương: `load_documents("data/k4_ecommerce")` → `chunk_document(doc, RecursiveChunker(chunk_size=600))` → `EmbeddingStore.add_documents()`. Kết quả: **76 chunk**, độ dài trung bình **487 ký tự** (min 102, max 600). Embedder dùng `LocalEmbedder` (`paraphrase-multilingual-MiniLM-L12-v2`, 384 chiều) để so sánh có ý nghĩa ngữ nghĩa thật.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Tôi được đổi trả hàng trong bao nhiêu ngày kể từ khi nhận hàng? | `k4_returns_policy` — "Thời gian hoàn tiền đối với hàng đổi, trả..." (hạng 1); hạng 2 là đúng đoạn "Thời gian hỗ trợ đổi trả... trong vòng 30 ngày" | 0.582 | ✓ đúng tài liệu, đúng chủ đề (hạng 2 mới là đoạn nêu con số 30 ngày) | Trích được đúng điều kiện 30 ngày miễn phí |
| 2 | Sau khi yêu cầu đổi trả được duyệt thì bao lâu tôi phải gửi hàng về, và bao lâu được hoàn tiền? | `k4_returns_policy` — đoạn "Thời gian hoàn tiền đối với hàng đổi, trả..." | 0.660 | ✓ đúng chunk, top-1 | Nêu được mốc 3-5 ngày làm việc hoàn tiền |
| 3 | Tôi khiếu nại đơn hàng qua kênh nào và bao lâu Tiki phản hồi? | `k4_tiki_chinh_sach_khieu_nai` — "Gọi điện thoại đến hotline: 19006035..." | 0.648 | ✓ đúng chunk, top-1 | Trả lời đúng kênh khiếu nại + hotline |
| 4 | Khi nhận hàng tôi được phép kiểm tra sản phẩm tới mức nào? | `k4_returns_policy` — điều kiện "còn nguyên tình trạng, đầy đủ hộp, phụ kiện..." (hạng 1); `k4_chinh_sach_kiem_hang` xuất hiện ở hạng 2-3 | 0.609 | ~ liên quan nhưng chunk đúng chủ đề nhất (`k4_chinh_sach_kiem_hang`) chỉ đứng hạng 2 | Trả lời lệch sang điều kiện đổi trả thay vì phạm vi kiểm hàng |
| 5 | Thông tin thẻ thanh toán của tôi được lưu trữ như thế nào? | `k4_security_policy` — "Tiki cung cấp tiện ích lưu giữ token..." | 0.513 | ✓ đúng chunk, top-1 | Trả lời đúng: chỉ lưu token, không lưu trực tiếp thông tin thẻ |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5** (câu 4 có chunk đúng nhất ở hạng 2 thay vì hạng 1, còn lại đều đúng top-1).

**Kiểm chứng `search_with_filter` trên câu 5** (câu duy nhất trong bộ có 2 tài liệu na ná chủ đề "thanh toán" — `k4_returns_policy` cũng nhắc "hoàn tiền"/"thanh toán"): lọc `metadata_filter={"category": "security"}` cho cả 3/3 kết quả đều thuộc `k4_security_policy` với top-1 giữ nguyên score 0.513, loại hẳn nhiễu từ `k4_returns_policy` từng lọt vào top-3 khi không lọc. Điều này khớp với ghi chú của nhóm trong `REPORT_NHOM.md`: câu 5 là câu cần metadata filtering để trả lời chắc chắn hơn.

**Quan sát về chiến lược `RecursiveChunker(chunk_size=600)`:**
- Vì tách theo `\n\n`/`\n` trước, các đoạn chunk giữ được trọn tiêu đề + nội dung ngay bên dưới (ví dụ chunk trả lời câu 3 chứa nguyên "Bước 1: ... Gọi điện thoại đến hotline...") — không bị cắt ngang câu như FixedSizeChunker thuần cắt theo ký tự.
- Điểm số tuyệt đối (0.3-0.66) thấp hơn khá nhiều so với thang thường thấy trong tài liệu tham khảo dùng chunk to hơn (900 ký tự) — vì chunk 600 ký tự đôi khi tách phần "tiêu đề chứa từ khoá" và "đoạn số liệu cụ thể" ra hai chunk liền kề (thấy rõ ở câu 1, câu 4), khiến chunk chứa đúng con số cần tìm đôi khi rơi xuống hạng 2 thay vì hạng 1.
- Câu 4 là trường hợp yếu nhất: `k4_chinh_sach_kiem_hang` (tài liệu ngắn, chỉ 835 ký tự → 1-2 chunk) lẽ ra phải là nguồn duy nhất trả lời đúng, nhưng vì nội dung ngắn nên vector của nó "loãng" hơn so với đoạn dài giàu từ khoá "kiểm tra", "sản phẩm" trong `k4_returns_policy`. Đây là gợi ý cho việc phân tích lỗi (Bài tập 3.5) của nhóm: tài liệu quá ngắn có thể bị chunk dài hơn từ tài liệu khác "lấn át" trong xếp hạng.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *[Điền sau buổi demo — cần nghe phần trình bày của các thành viên/nhóm khác trước khi viết.]*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 |
| **Tổng phần cá nhân** | **57 / 60** |
