# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Trung Hiếu
**Mã sinh viên:** 2A202601620
**Nhóm:** G28-E403
**Ngày:** 2026-08-04

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding chỉ gần như cùng một **hướng** trong không gian nhiều chiều, cho thấy hai đoạn văn bản mang ý nghĩa/chủ đề gần nhau dù có thể dùng từ ngữ khác nhau. Cosine similarity nằm trong [-1, 1]; càng gần 1 thì hai văn bản càng "nói cùng một ý".

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sản phẩm bị lỗi kỹ thuật được đổi trả trong 365 ngày."
- Câu B: "Hàng hỏng do nhà sản xuất thì thời hạn bảo hành lên tới một năm."
- Tại sao tương đồng: cả hai câu cùng nói về thời hạn xử lý khi sản phẩm có lỗi kỹ thuật ("365 ngày" ~ "một năm", "lỗi kỹ thuật" ~ "hỏng do nhà sản xuất"), chỉ khác cách diễn đạt con số và thuật ngữ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Tiki hỗ trợ khách hàng đổi trả miễn phí trong 30 ngày."
- Câu B: "Hôm nay tôi đi siêu thị mua rau và trái cây."
- Tại sao khác: một câu về chính sách đổi trả TMĐT, một câu về sinh hoạt cá nhân — không chia sẻ chủ đề, thực thể hay từ vựng liên quan, nên vector của chúng gần như trực giao.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ đo **hướng** của vector nên không bị ảnh hưởng bởi độ dài (norm) của vector — vốn phụ thuộc vào độ dài văn bản. Euclidean distance cộng dồn cả chênh lệch độ lớn lẫn hướng, nên một đoạn văn dài và một câu ngắn cùng chủ đề có thể bị coi là "xa nhau" chỉ vì khác độ dài, dẫn đến so sánh sai lệch giữa các văn bản có độ dài khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính:
> - Bước nhảy (step) = chunk_size − overlap = 500 − 50 = **450**
> - Số chunk = ceil((10000 − 50) / 450) = ceil(9950 / 450) = ceil(22.11) = **23**
>
> Đáp án: **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Step giảm còn 500 − 100 = 400, số chunk = ceil((10000 − 100)/400) = ceil(24.75) = **25 chunks** (tăng thêm 2). Overlap lớn hơn giúp giảm rủi ro một câu/ý quan trọng bị cắt đứt đúng ngay ranh giới hai chunk — phần nội dung ở mép chunk trước được lặp lại ở đầu chunk sau nên vẫn còn nguyên vẹn ở ít nhất một chunk khi truy xuất. Đánh đổi là nhiều chunk hơn đồng nghĩa tốn thêm chi phí embedding và lưu trữ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận khi lập trình các phần chính trong gói `src/NguyenTrungHieu-2A202601620`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `([.!?])(?:\s+|$)` với `re.split` và giữ lại nhóm bắt (capturing group) chứa dấu câu, sau đó tự ghép dấu câu trở lại vào câu đứng trước bằng một vòng lặp tích lũy: mỗi khi gặp token là `.`/`!`/`?`, tôi nối nó vào `buffer` rồi chốt thành một câu hoàn chỉnh. Cách này giữ nguyên dấu câu ở cuối mỗi câu mà không cần lookbehind, đồng thời tự động xử lý luôn phần "câu cuối" không có dấu kết thúc (`|$`). Edge case: chuỗi rỗng/toàn khoảng trắng trả về `[]`; các câu rỗng bị lọc bỏ trước khi gom nhóm; `max_sentences_per_chunk` được `max(1, ...)` chặn ở `__init__`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Tách thành hai bước như baseline chung của lab: `_split()` đệ quy thử lần lượt từng separator trong danh sách ưu tiên để cắt văn bản xuống dưới `chunk_size` (nếu một separator không xuất hiện trong đoạn, tự động rơi xuống separator kế tiếp); sau đó `_coalesce()` chạy vòng lặp gộp tham lam các mảnh nhỏ liền kề lại gần `chunk_size` để tránh sinh ra hàng loạt chunk quá nhỏ. Hai base case của `_split`: (1) đoạn đã ≤ `chunk_size` → giữ nguyên; (2) hết separator để thử → cắt cứng theo từng `chunk_size` ký tự, đảm bảo đệ quy luôn dừng kể cả khi `separators=[]`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuẩn hoá qua `_make_record()` thành dict `{uid, id, content, metadata, embedding}`, trong đó `uid = f"{doc.id}#{index}"` đảm bảo mỗi chunk có khoá riêng biệt kể cả khi hai `Document` trùng `id`; nội dung được nhúng (embed) ngay khi ghi để không phải tính lại lúc tìm kiếm, và `metadata.setdefault("doc_id", doc.id)` đảm bảo luôn có khoá dùng cho lọc/xoá. `search()` nhúng câu hỏi rồi gọi `_search_records()` — hàm dùng chung tính **tích vô hướng** (`_dot`) giữa vector câu hỏi và từng vector đã lưu, sắp xếp giảm dần theo điểm và cắt lấy `top_k`. Nếu môi trường có `chromadb`, `__init__` khởi tạo collection thật và `add_documents`/`search` chuyển sang gọi API ChromaDB song song với việc vẫn lưu bản sao trong `self._store`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Chọn **lọc trước, tìm sau**: nếu có `metadata_filter`, chỉ giữ lại các record khớp toàn bộ cặp key/value (`all(record["metadata"].get(k) == v ...)`) rồi mới gọi `_search_records()` xếp hạng trên tập đã lọc; nếu không có filter thì hành vi trùng khớp hoàn toàn với `search()`. `delete_document()` dựng lại `self._store` chỉ gồm các record có `metadata["doc_id"] != doc_id`, so sánh độ dài trước/sau để biết có xoá được gì hay không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Theo đúng 3 bước RAG: `store.search(question, top_k)` lấy chunk liên quan → `_format_context()` dựng ngữ cảnh đánh số `[1] [2] [3]` kèm nguồn (`doc_id`) của từng chunk → gọi `llm_fn(prompt)`. Prompt ra chỉ thị rõ ràng: chỉ dùng ngữ cảnh được cung cấp để trả lời, nếu không đủ thông tin thì phải nói không biết — nhằm hạn chế mô hình bịa. Khi không tìm được chunk nào, ngữ cảnh được thay bằng câu thông báo rõ ràng thay vì để trống, giúp LLM phản hồi đúng thay vì suy diễn.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ LAB_SOLUTION_PACKAGE='src.NguyenTrungHieu-2A202601620' python -m pytest tests/ -v

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

============================= 42 passed in 0.04s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Đã dùng `LocalEmbedder` (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, 384 chiều) để có kết quả phản ánh ngữ nghĩa tiếng Việt thật; cột `mock` chỉ để đối chứng.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (local) | Đúng? | *(mock đối chứng)* |
|------|-----------|-----------|---------|--------------|-------|------|
| 1 | Sản phẩm bị lỗi kỹ thuật được đổi trả trong 365 ngày. | Hàng hỏng do nhà sản xuất thì thời hạn bảo hành lên tới một năm. | cao | **0.5391** | ✓ | −0.1487 |
| 2 | Nhà Bán phải cung cấp giấy đăng ký kinh doanh khi mở tài khoản Doanh nghiệp. | Để đăng ký gian hàng Doanh nghiệp cần có giấy phép kinh doanh hợp lệ. | cao | **0.7274** | ✓ | −0.0282 |
| 3 | Tiki hỗ trợ khách hàng đổi trả miễn phí trong 30 ngày. | Hôm nay tôi đi siêu thị mua rau và trái cây. | thấp | **0.1254** | ✓ | 0.2318 |
| 4 | Đơn vị vận chuyển thu hồi hàng trong 24 giờ đối với khu vực nội thành. | Nhà Bán không được tạo nhiều gian hàng trùng lặp trên sàn Tiki. | thấp | **0.0586** | ✓ | −0.0443 |
| 5 | Con mèo của tôi rất thích ngủ trên ghế sofa. | Con mèo của tôi rất thích ngủ trên ghế sofa. | cao | **1.0000** | ✓ | 1.0000 |

**Dự đoán đúng: 5/5.**

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **cặp 2 (0.7274)** — cao hơn tôi nghĩ dù hai câu không dùng chung từ nào ngoài "đăng ký"/"giấy phép kinh doanh". `LocalEmbedder` bắt được rằng cả hai câu cùng diễn đạt một yêu cầu thủ tục giống hệt nhau (cần giấy tờ đăng ký kinh doanh để mở tài khoản Doanh nghiệp), tức nó mã hoá **quan hệ ngữ nghĩa/logic** giữa hai câu chứ không chỉ đếm từ trùng lặp bề mặt — khác hẳn `MockEmbedder` (cột đối chứng cho điểm âm cho cùng cặp này). Ngược lại, cặp 4 dù cùng miền "vận hành TMĐT" (vận chuyển vs. quy định gian hàng) vẫn được chấm thấp (0.0586) vì hai câu không chia sẻ ý định cụ thể nào — cho thấy mô hình vẫn phân biệt được giữa "cùng domain nhưng khác chủ đề" và "cùng ý nghĩa", miễn là hai câu không quá ngắn/mơ hồ.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** (xem `REPORT_NHOM.md`) trên mã nguồn cá nhân trong gói `src/NguyenTrungHieu-2A202601620`.

> **Chiến lược của tôi:** `SentenceChunker(max_sentences_per_chunk=4)` — khác với FixedSizeChunker (900/150, Bùi Xuân Tùng), RecursiveChunker (600, Đặng Ngọc Anh), và các custom heading-chunker (Nguyễn Quang Sơn, Trần Trung Kiên). Chunker này nhóm 4 câu liên tiếp thành một chunk theo ranh giới câu, không quan tâm cấu trúc heading. Nạp bằng `load_documents("data/k4_ecommerce")` → `chunk_document(doc, SentenceChunker(max_sentences_per_chunk=4))` → `EmbeddingStore.add_documents()`. Kết quả: **67 chunk**, độ dài trung bình **555 ký tự** (min 127, max 1577 — dao động lớn hơn hẳn các chiến lược khác vì độ dài câu tiếng Việt trong văn bản chính sách rất không đều). Embedder: `LocalEmbedder` (384 chiều).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Tôi được đổi trả hàng trong bao nhiêu ngày kể từ khi nhận hàng? | `k4_returns_policy` — "Đặc biệt, những sản phẩm thuộc danh mục Thiết bị số... 365 ngày..." | 0.564 | ~ đúng tài liệu nhưng thiếu câu chính "30 ngày" (không lọt top-3) | Trả lời được điều kiện 365 ngày, thiếu mốc 30 ngày mặc định |
| 2 | Sau khi yêu cầu đổi trả được duyệt thì bao lâu tôi phải gửi hàng về, và bao lâu được hoàn tiền? | `k4_returns_policy` — "...Thời gian hoàn tiền đối với hàng đổi, trả..." | 0.618 | ✓ đúng chunk, top-1 | Nêu được mốc hoàn tiền 3-5 ngày làm việc |
| 3 | Tôi khiếu nại đơn hàng qua kênh nào và bao lâu Tiki phản hồi? | `k4_tiki_chinh_sach_khieu_nai` — "Chat trực tiếp đến Tiki.vn... Bước 2: Bộ phận Tiki Care..." | 0.735 | ✓ đúng chunk, top-1, điểm cao nhất trong cả 5 câu | Trả lời đúng kênh (hotline/email/chat) + thời hạn phản hồi |
| 4 | Khi nhận hàng tôi được phép kiểm tra sản phẩm tới mức nào? | `k4_packing_guide` (hạng 1, nhiễu do trùng từ "thu hồi"/"sản phẩm"); `k4_chinh_sach_kiem_hang` đúng chủ đề nằm ở hạng 2 | 0.563 | ~ liên quan nhưng chunk đúng nhất chỉ ở hạng 2 | Trả lời đúng nhờ agent vẫn tổng hợp được cả 3 chunk trong ngữ cảnh |
| 5 | Thông tin thẻ thanh toán của tôi được lưu trữ như thế nào? | `k4_security_policy` — "Đối với thẻ quốc tế: thông tin thẻ thanh toán..." | 0.614 | ✓ đúng chunk, top-1 | Trả lời đúng: chỉ lưu token, không lưu trực tiếp thông tin thẻ |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **4 / 5** (câu 1 là trường hợp lỗi — xem phân tích bên dưới).

**Kiểm chứng `search_with_filter` trên câu 5:** lọc `metadata_filter={"category": "security"}` cho cả 3/3 kết quả đều thuộc `k4_security_policy`, giữ nguyên top-1 (score 0.614) — không đổi thứ hạng vì không có tài liệu khác chứa từ khoá "thẻ thanh toán" mạnh bằng `k4_security_policy` trong chiến lược này, nhưng vẫn loại được khả năng nhiễu nếu về sau nhóm thêm tài liệu mới cùng nhắc "thanh toán".

**Phân tích lỗi (câu 1):** đây là điểm yếu rõ nhất của `SentenceChunker`. Vì gộp đúng 4 câu liên tiếp bất kể nội dung, câu chứa mốc chính "30 ngày" (`"Thời gian hỗ trợ đổi trả... trong vòng 30 ngày..."`) bị gộp chung với các câu lân cận ít liên quan hơn về mặt từ vựng nhúng, khiến vector của cả chunk "loãng" đi và rơi khỏi top-3 — trong khi câu về "365 ngày" (trường hợp ngoại lệ, ít quan trọng hơn) lại lọt top-1 vì câu liền trước/sau nó trong cùng chunk có nhiều từ khoá trùng với câu hỏi hơn. Đây là hạn chế cố hữu của việc chunk theo **số lượng câu cố định** thay vì theo cấu trúc ngữ nghĩa/heading: chunker không biết câu nào là "câu chủ đạo" của đoạn.

**Quan sát chung:**
- `SentenceChunker` cho độ dài chunk dao động rất lớn (127-1577 ký tự) vì câu trong văn bản chính sách Tiki có độ dài rất khác nhau (câu liệt kê ngắn xen giữa câu diễn giải dài) — đây là điểm yếu so với `RecursiveChunker`/`FixedSizeChunker` vốn kiểm soát được kích thước tối đa.
- Điểm mạnh: câu 3 đạt score cao nhất (0.735) trong toàn bộ benchmark vì tài liệu khiếu nại được viết thành các câu ngắn, rõ ràng theo từng bước — nhóm 4 câu vừa đủ để giữ trọn "kênh liên hệ + thời hạn phản hồi" mà không lẫn nội dung khác.
- Gợi ý cải thiện (khớp với Bài tập 3.5 của nhóm): kết hợp `SentenceChunker` với việc giữ heading của mục cha (như cách Nguyễn Quang Sơn/Trần Trung Kiên làm) sẽ giải quyết được lỗi ở câu 1, vì chunk sẽ luôn biết nó thuộc mục "Thời gian hỗ trợ đổi trả" dù nội dung câu cụ thể có bị chia nhỏ.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *[Điền sau buổi demo — cần nghe phần trình bày của các thành viên/nhóm khác trước khi viết.]*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **57 / 60** |
