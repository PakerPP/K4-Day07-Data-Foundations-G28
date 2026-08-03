# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Bùi Xuân Tùng (MSSV: 2A202601828)
**Nhóm:** [Điền tên nhóm]
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding chỉ về gần cùng một **hướng** trong không gian ngữ nghĩa, tức là hai đoạn văn bản nói về cùng một chủ đề/ý định dù dùng từ ngữ khác nhau. Điểm nằm trong [-1, 1]: gần 1 là cùng hướng (cùng ý), gần 0 là không liên quan, gần -1 là đối lập hướng.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn đổi trả sản phẩm bị lỗi."
- Câu B: "Làm sao để hoàn hàng khi hàng bị hỏng?"
- Tại sao tương đồng: cùng một **ý định** của người mua (đổi/trả hàng lỗi), chỉ khác cách diễn đạt — "đổi trả"/"hoàn hàng", "bị lỗi"/"bị hỏng". Embedding mã hoá ý nghĩa nên hai câu này nằm gần nhau dù chỉ trùng rất ít từ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Hôm nay trời mưa rất to ở Hà Nội."
- Câu B: "Quy định hoàn tiền cho đơn hàng bị hủy."
- Tại sao khác: khác hoàn toàn chủ đề (thời tiết vs. chính sách thanh toán TMĐT), không chia sẻ ngữ cảnh nào nên hai vector gần như trực giao (điểm ≈ 0).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ quan tâm **hướng**, đã chuẩn hoá theo độ dài vector, nên một đoạn văn dài và một câu hỏi ngắn cùng chủ đề vẫn được chấm điểm cao; còn Euclid bị ảnh hưởng bởi **độ lớn** (norm) của vector — vốn phụ thuộc độ dài văn bản — nên đoạn dài dễ bị coi là "xa" một cách giả tạo. Ngoài ra, với vector đã chuẩn hoá (unit norm) thì cosine và Euclid xếp hạng tương đương, mà cosine lại rẻ hơn: chỉ cần tích vô hướng.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Bước nhảy (step) = `chunk_size - overlap` = 500 − 50 = **450** ký tự.
> - Số chunk = `ceil((10000 − 50) / 450)` = `ceil(9950 / 450)` = `ceil(22.11)` = **23**.
> - Kiểm chứng bằng chính code trong `src/chunking.py`:
>   `len(FixedSizeChunker(chunk_size=500, overlap=50).chunk("x" * 10000))` → **23** (khớp công thức).
>
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Step giảm còn 400 nên số chunk tăng: `ceil((10000 − 100) / 400)` = `ceil(24.75)` = **25 chunks** (đã chạy code xác nhận đúng 25). Overlap lớn hơn = nhiều chunk hơn = tốn thêm chi phí nhúng và lưu trữ, đổi lại **giảm rủi ro cắt ngang một câu/ý ở đúng ranh giới chunk**: câu bị cắt vẫn xuất hiện trọn vẹn ở chunk kế bên nên vẫn truy xuất được, và mỗi chunk có thêm ngữ cảnh hai đầu để LLM hiểu đúng.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi tách câu bằng regex `re.split(r"(?<=[.!?])\s+", text.strip())`: dùng **lookbehind** để dấu chấm câu ở lại với câu đứng trước, còn khoảng trắng (kể cả `\n`) đóng vai trò dấu tách — nhờ vậy phủ được cả 4 mẫu trong docstring (`". "`, `"! "`, `"? "`, `".\n"`) chỉ bằng một biểu thức. Sau đó strip từng câu, **loại các chuỗi rỗng**, rồi gom theo bước `max_sentences_per_chunk` và nối lại bằng dấu cách. Edge case đã xử lý: text rỗng hoặc chỉ có khoảng trắng → trả `[]`; `max_sentences_per_chunk` bị truyền ≤ 0 → đã được `max(1, ...)` trong `__init__` chặn (tránh vòng lặp/step = 0); văn bản không có dấu chấm câu → coi là một câu duy nhất, trả 1 chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `chunk()` chỉ lo phần vỏ (rỗng → `[]`) rồi uỷ quyền cho `_split(text, separators)`. `_split` có **hai base case**: (1) đoạn đã ≤ `chunk_size` → trả về chính nó; (2) hết separator → cắt cứng theo `chunk_size` để bảo đảm luôn dừng. Ngược lại, lấy separator ưu tiên cao nhất và cắt: nếu separator đó **không xuất hiện** (`len(parts) == 1`) thì bỏ qua, thử separator tiếp theo; phần nào vẫn quá dài thì **đệ quy** với danh sách separator còn lại. Cuối cùng tôi thêm bước `_merge`: gộp tham lam (greedy) các mảnh nhỏ liền kề lại cho tới sát `chunk_size` — không có bước này thì với văn xuôi, separator `" "` sẽ tạo ra hàng trăm chunk cỡ 1 từ, đúng luật nhưng vô dụng cho retrieval.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuẩn hoá qua `_make_record()` thành dict `{uid, id, content, metadata, embedding}`: nhúng nội dung **một lần lúc ghi** (không nhúng lại lúc tìm kiếm), và `metadata.setdefault("doc_id", doc.id)` để `delete_document`/filter luôn có khoá làm việc. Trường `uid = f"{doc.id}#{_next_index}"` giữ mỗi chunk là một bản ghi riêng ngay cả khi hai document trùng `id`. `search()` nhúng câu hỏi rồi gọi `_search_records()` — hàm này tính **cosine** giữa query và từng embedding (dùng `_dot` + chuẩn hoá theo norm, có bảo vệ chia 0), sắp xếp giảm dần theo `score` và cắt `top_k`. Tôi dùng cosine thay vì tích vô hướng thuần để kết quả không lệ thuộc việc backend có chuẩn hoá vector hay không (mock/local đã chuẩn hoá, OpenAI thì không bảo đảm). Về `__init__`: nếu môi trường có `chromadb` thì khởi tạo `EphemeralClient` + collection và **mirror** dữ liệu sang đó, nhưng danh sách trong bộ nhớ luôn là nguồn sự thật cho phần đọc — nhờ vậy kết quả giống hệt nhau dù máy chấm có hay không có ChromaDB, và mọi lỗi phía Chroma đều được bắt để tự động quay về in-memory.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Tôi **lọc trước, tìm sau** (pre-filtering): loại bỏ các chunk không khớp toàn bộ cặp key/value trong `metadata_filter` rồi mới xếp hạng phần còn lại. Làm ngược lại (tìm top-k rồi lọc) sẽ khiến kết quả trả về ít hơn `top_k` một cách khó đoán, vì các chunk bị loại đã chiếm mất suất. Khi `metadata_filter` rỗng/`None` thì hành vi trùng khớp hoàn toàn với `search()`. `delete_document` dựng lại danh sách chỉ gồm các chunk có `metadata["doc_id"] != doc_id`, so sánh số lượng trước/sau để trả `True`/`False` — cách này xoá **tất cả** chunk của một tài liệu trong một lần duyệt và trả `False` đúng nghĩa khi không có gì bị xoá.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Ba bước RAG: retrieve `top_k` chunk → dựng prompt → gọi `llm_fn`. Ngữ cảnh được đánh số `[1] [2] [3]` kèm `source` và `score` của từng chunk, để câu trả lời có thể **trích dẫn** và tôi kiểm tra được grounding (chunk nào đẻ ra câu trả lời). Prompt ra chỉ thị rõ: chỉ trả lời dựa trên ngữ cảnh, nếu thiếu thông tin thì nói không biết — nhằm hạn chế bịa (hallucination). Trường hợp store rỗng/không truy xuất được gì, tôi **không gọi LLM** mà trả thẳng thông báo không tìm thấy thông tin, vì gọi LLM với ngữ cảnh rỗng chỉ mời nó bịa.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ python -m unittest discover -s tests -t . -v
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
Ran 42 tests in 0.007s

OK
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

> Ghi chú môi trường: máy làm bài chưa cài `pytest` (và chưa có Python 3.11), nên tôi chạy đúng bộ test đó bằng `unittest` trên Python 3.12 — cùng file `tests/test_solution.py`, cùng 42 test case. Khi nộp trên môi trường chuẩn của lab, lệnh tương đương là `pytest tests/ -v`.

Ngoài bộ test, tôi còn chạy end-to-end để chắc chắn code hoạt động thật:
- `python ingest.py` → `ingest self-check OK: parse được 4 khóa metadata, tạo 18 chunk`
- `python main.py "Chính sách đổi trả hàng như thế nào?"` → nạp store, in top-3 kèm score, agent trả lời bình thường.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Gọi `compute_similarity()` trên 5 cặp câu. Tôi ghi dự đoán **trước khi chạy**, rồi đo bằng **cả hai backend** để so sánh: `LocalEmbedder` (`paraphrase-multilingual-MiniLM-L12-v2`, 384 chiều — kết quả chính) và `MockEmbedder` (64 chiều — để đối chứng).

| Cặp | Câu A | Câu B | Dự đoán | **Điểm thực tế (local)** | Đúng? | *(mock để đối chứng)* |
|------|-----------|-----------|---------|--------------|-------|------|
| 1 | Tôi muốn đổi trả sản phẩm bị lỗi | Làm sao để hoàn hàng khi hàng bị hỏng? | cao | **+0.398** | ✓ | −0.209 |
| 2 | Chính sách giao hàng trong 3 ngày | Thời gian vận chuyển đơn hàng là bao lâu? | cao | **+0.668** | ✓ | +0.233 |
| 3 | Phương thức thanh toán bằng thẻ tín dụng | Điều kiện đăng ký làm người bán trên sàn | thấp | **+0.302** | ✗ | −0.125 |
| 4 | Chính sách bảo mật dữ liệu khách hàng | Sàn thu thập và lưu trữ thông tin cá nhân thế nào? | cao | **+0.567** | ✓ | −0.065 |
| 5 | Hôm nay trời mưa rất to ở Hà Nội | Quy định hoàn tiền cho đơn hàng bị hủy | thấp | **−0.014** | ✓ | −0.079 |

**Dự đoán đúng: 4/5.**

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **cặp 3: +0.302** dù tôi dự đoán thấp. Hai câu nói về hai chuyện khác nhau (thanh toán bằng thẻ vs. điều kiện làm người bán), nhưng chúng **cùng miền chủ đề** — đều là tiếng Việt, đều là văn phong chính sách của sàn TMĐT, dùng chung lớp từ vựng "phương thức/điều kiện/đăng ký/sàn". Embedding mã hoá cả *chủ đề* lẫn *văn phong* chứ không chỉ mã hoá ý định cụ thể, nên hai câu cùng miền luôn có một mức tương đồng nền khác 0. So sánh với cặp 5 (**−0.014**, khác miền hoàn toàn: thời tiết vs. chính sách) thì thấy rất rõ ranh giới đó.
>
> Hệ quả thực tế cho retrieval: **không có một ngưỡng score tuyệt đối nào dùng được**. Trên một kho tài liệu toàn chính sách TMĐT, mọi chunk đều sẽ được chấm quanh 0.3–0.5 chỉ vì cùng miền, nên "score ≥ 0.3 là liên quan" sẽ nhận vào đầy nhiễu. Cái đáng tin là **thứ hạng tương đối** và **khoảng cách giữa top-1 với các hạng sau** — ví dụ câu 1 ở mục 5 dưới đây, top-1 = 0.502 bỏ xa hạng 2 = 0.278, đó mới là dấu hiệu truy xuất chắc chắn; còn câu 5 có 0.593 / 0.528 / 0.488 sát nhau thì độ tin cậy thấp hơn hẳn dù điểm tuyệt đối cao hơn.
>
> Điểm đáng nói thứ hai là **cột mock**: cặp 1 gần như đồng nghĩa lại bị chấm **−0.209**, thấp hơn cả cặp 5 chẳng liên quan gì (−0.079) — xếp hạng ngược hoàn toàn. Lý do là `MockEmbedder` băm toàn chuỗi bằng MD5 rồi sinh vector giả ngẫu nhiên: xác định (deterministic, hợp để unit test chạy ổn định) nhưng **không mã hoá ý nghĩa**. Cùng một công thức cosine, cùng một `EmbeddingStore`, chỉ đổi backend là kết luận lật ngược — nên mọi nhận định về chất lượng chiến lược đều phải chạy trên embedder thật.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> ⚠️ **Trạng thái: chạy thử tạm thời — CẦN CHẠY LẠI SAU BUỔI NHÓM.** Embedder đã là thật (`EMBEDDING_PROVIDER=local`), nhưng hai đầu vào thuộc Giai đoạn 2 vẫn chưa có: (a) bộ tài liệu 5–10 file của nhóm — `data/k4_ecommerce/` mới chỉ có **2 file mẫu khởi động** (5 chunk); (b) 5 câu hỏi đánh giá + gold answer do nhóm thống nhất. Bảng dưới đây dùng 5 câu hỏi **tôi tự đặt** trên bộ mẫu, nên nó chứng minh pipeline chạy đúng chứ **chưa phải điểm đánh giá chính thức**.
>
> Cấu hình đã chạy: `build_knowledge_base("data/k4_ecommerce", embedding_fn=LocalEmbedder(), chunker=RecursiveChunker(chunk_size=300))` → 5 chunk, embedder `paraphrase-multilingual-MiniLM-L12-v2` (384 chiều).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Điều kiện để đổi trả hàng trong bao nhiêu ngày? | `k4-returns-policy` — "Người mua cần gửi yêu cầu đổi trả trong thời hạn được nêu trên trang sản phẩm…" | +0.502 | ✓ đúng chunk, top-1 | Nêu được đúng điều kiện gửi yêu cầu đổi trả |
| 2 | Người bán cần cung cấp thông tin gì khi đăng bán sản phẩm? | `k4-seller-listing` — "Người bán chịu trách nhiệm cung cấp thông tin sản phẩm chính xác…" | +0.761 | ✓ đúng chunk, top-1 | Trả lời đúng nghĩa vụ người bán |
| 3 | Khi nào đơn hàng được hoàn tiền? | `k4-returns-policy` — đoạn về thời hạn đổi trả | +0.361 | ~ đúng tài liệu, nhưng **bộ mẫu chưa có nội dung hoàn tiền** | Trả lời thiếu — do dữ liệu, không do truy xuất |
| 4 | Sản phẩm nào không được phép đăng bán? | `k4-seller-listing` — trách nhiệm cung cấp thông tin sản phẩm | +0.680 | ✗ đúng tài liệu, sai đoạn — **bộ mẫu chưa có danh mục hàng cấm** | Không trả lời được, tài liệu không chứa thông tin |
| 5 | Quy trình xử lý khiếu nại của khách hàng ra sao? | `k4-returns-policy` — thời hạn đổi trả; hạng 2 = "Người bán có trách nhiệm phản hồi theo quy trình của sàn" | +0.593 | ✓ chunk liên quan ở hạng 2 | Trả lời được ở mức khái quát |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **3 / 5** (câu 1, 2, 5). Câu 3 và 4 trượt vì **bộ tài liệu mẫu không chứa thông tin được hỏi** — đây là giới hạn của dữ liệu, không phải của chiến lược chunking.

**Quan sát:**
- Đổi từ mock sang local làm kết quả lật hoàn toàn: trước đó chunk **ghi chú template metadata** chiếm top-1 ở cả 5 câu (2/5 liên quan, điểm dồn quanh 0); giờ chunk nhiễu đó **biến mất khỏi top-3 của cả 5 câu**, và câu nào cũng kéo đúng tài liệu đúng chủ đề lên đầu. Đây là bằng chứng cụ thể cho nhận định ở mục 4: chất lượng embedder quyết định, không phải công thức cosine.
- **Khoảng cách điểm (score gap) là chỉ báo tin cậy tốt hơn điểm tuyệt đối.** Câu 1: 0.502 → 0.278 (cách 0.224) — truy xuất chắc chắn. Câu 5: 0.593 / 0.528 / 0.488 — điểm cao hơn nhưng ba chunk sát nhau, tức mô hình không thực sự phân biệt được, và đúng là câu này chỉ trả lời được ở mức khái quát. Câu 4 điểm top-1 rất cao (+0.680) nhưng **sai** — điểm cao không bảo chứng cho câu trả lời đúng khi tài liệu không chứa thông tin.
- `search_with_filter` đã kiểm chứng có tác dụng: lọc `{"category": "returns"}` hoặc `{"doc_id": "k4-returns-policy"}` cho 3/3 kết quả đúng tài liệu, so với 1/3 khi không lọc. Đây là hướng tôi sẽ khai thác ở Giai đoạn 2 cho ít nhất 1 câu hỏi cần metadata filtering.
- Rút ra cho khâu thu thập dữ liệu của nhóm: phải **làm sạch phần hướng dẫn/template** lẫn trong file `.md` (chính nó là chunk nhiễu ở lần chạy mock), và bộ câu hỏi đánh giá phải bảo đảm tài liệu **thực sự chứa** câu trả lời — nếu không thì đo chiến lược chunking bằng những câu như 3 và 4 là vô nghĩa.
- **Việc phải làm để lấy trọn 10 điểm phần này:** sau khi nhóm chốt bộ tài liệu + 5 câu hỏi, chạy lại đúng cấu hình trên và thay toàn bộ bảng.

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
| Kết quả truy xuất của tôi (Competition Results) | 6 / 10 *(tạm tính — chờ dữ liệu & câu hỏi của nhóm)* |
| **Tổng phần cá nhân** | **55 / 60** *(tạm tính)* |
