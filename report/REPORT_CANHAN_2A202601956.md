# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Quang Sơn
**Nhóm:** G28
**Ngày:** 2026-08-03
**MSSV:** 2A202601956

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai embedding có hướng gần nhau trong không gian vector, cho thấy hai văn bản có ý nghĩa hoặc ý định gần nhau. Điểm càng gần 1 thì mức tương đồng ngữ nghĩa càng cao.

**Ví dụ có độ tương tự CAO:**

- Câu A: Tôi muốn đổi trả sản phẩm bị lỗi.
- Câu B: Làm sao để hoàn hàng khi hàng bị hỏng?
- Tại sao tương đồng: Cả hai cùng hỏi về việc hoàn/đổi một sản phẩm lỗi, chỉ khác cách diễn đạt.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Hôm nay trời mưa rất to ở Hà Nội.
- Câu B: Quy định hoàn tiền cho đơn hàng bị hủy.
- Tại sao khác: Hai câu thuộc hai miền chủ đề khác nhau: thời tiết và chính sách thương mại điện tử.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine quan tâm đến hướng của vector nên ít bị ảnh hưởng bởi độ dài văn bản hoặc độ lớn vector. Euclid đo khoảng cách tuyệt đối, vì vậy hai embedding cùng nghĩa nhưng khác norm có thể bị xem là xa hơn cần thiết.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`.
>
> Đáp án: **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap là 100, số chunk là `ceil((10000 - 100) / (500 - 100)) = ceil(24.75) = 25`, tức tăng thêm 2 chunk. Overlap lớn hơn giúp một câu hoặc điều khoản bị cắt tại ranh giới vẫn xuất hiện ở chunk kế tiếp, đổi lại tốn thêm chi phí embedding và lưu trữ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src/NguyenQuangSon-2A202601956`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `r"(?<=[.!?])\s+"` để tách tại khoảng trắng đứng sau dấu kết câu, đồng thời giữ dấu `.`, `!`, `?` ở câu trước. Hàm loại bỏ chuỗi rỗng và khoảng trắng thừa, sau đó gom tối đa `max_sentences_per_chunk` câu; đầu vào rỗng hoặc chỉ gồm khoảng trắng trả về `[]`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Chunker thử theo thứ tự `\n\n`, `\n`, `. `, khoảng trắng rồi cắt cứng khi cần. Hai base case là đoạn đã không vượt `chunk_size` và đã hết separator; các mảnh nhỏ liền kề được gộp tham lam nhưng không vượt giới hạn kích thước để tránh tạo chunk chỉ có một vài từ.

**`HeadingPolicyChunker.chunk`** — chiến lược retrieval cá nhân:
> Tôi tạo chunker cho Markdown chính sách: tách heading từ `#` đến `######` trước và giữ heading ở đầu nội dung của mục. Nếu mục dài quá 900 ký tự, phần thân được chia tiếp bằng `RecursiveChunker`, đồng thời heading được lặp lại trên mỗi chunk con để không mất chủ đề/điều khoản khi truy xuất.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuyển thành record gồm ID duy nhất, nội dung, metadata và embedding; `doc_id` luôn được bổ sung vào metadata để hỗ trợ filter và delete. Query được embedding một lần, sau đó so sánh cosine với từng record, sắp xếp giảm dần theo `score` và lấy `top_k`; ChromaDB chỉ là lựa chọn phụ, store trong bộ nhớ vẫn là fallback.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Tôi lọc metadata trước rồi mới xếp hạng, nhờ đó `top_k` chỉ chứa các chunk đúng điều kiện lọc. `delete_document` tạo lại store với các record khác `metadata["doc_id"]`, đồng thời xóa các ID tương ứng trong ChromaDB nếu backend này đang dùng; hàm trả về `False` khi không có document cần xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent lấy top-k chunk, đánh số từng chunk và đưa nội dung cùng nguồn vào phần `Ngữ cảnh` của prompt. Prompt yêu cầu LLM chỉ dùng ngữ cảnh được truy xuất và nói không biết khi thiếu thông tin; nếu store không trả kết quả, agent trả thông báo ngay thay vì gọi LLM với ngữ cảnh rỗng.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
$ LAB_SOLUTION_PACKAGE='src.NguyenQuangSon-2A202601956' .venv/bin/python -m pytest tests/ -v
============================== 42 passed in 0.04s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

Các kiểm thử bao phủ chunking, cosine similarity, thêm/tìm/lọc/xóa trong vector store và `KnowledgeBaseAgent`.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Các điểm dưới đây được tính bằng `compute_similarity()` với `_mock_embed` mặc định của lab. Mock embedder chỉ dùng để kiểm thử nên không biểu diễn ngữ nghĩa thật; vì vậy cột “Đúng?” chỉ ghi nhận việc dự đoán có khớp trực tiếp với điểm mock, không dùng để đánh giá chất lượng retrieval.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi muốn đổi trả sản phẩm bị lỗi. | Làm sao để hoàn hàng khi hàng bị hỏng? | cao | 0.035 | Không — mock không hiểu ngữ nghĩa |
| 2 | Chính sách giao hàng trong 3 ngày. | Thời gian vận chuyển đơn hàng là bao lâu? | cao | 0.045 | Không — mock không hiểu ngữ nghĩa |
| 3 | Phương thức thanh toán bằng thẻ tín dụng. | Điều kiện đăng ký làm người bán trên sàn. | thấp | -0.175 | Có |
| 4 | Chính sách bảo mật dữ liệu khách hàng. | Sàn thu thập và lưu trữ thông tin cá nhân thế nào? | cao | 0.052 | Không — mock không hiểu ngữ nghĩa |
| 5 | Hôm nay trời mưa rất to ở Hà Nội. | Quy định hoàn tiền cho đơn hàng bị hủy. | thấp | 0.117 | Có — gần 0 |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 1 và 4 có ý nghĩa rất gần nhưng score mock lại gần 0. Điều này xác nhận `_mock_embed` sinh vector xác định để test code chứ không mã hóa ý nghĩa; khi đánh giá retrieval tiếng Việt cần dùng `LocalEmbedder` hoặc một embedding model thật.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân trong `src/NguyenQuangSon-2A202601956`, với custom `HeadingPolicyChunker(chunk_size=900)`. Kho có **81 chunks** từ 6 tài liệu nhóm thu thập, độ dài trung bình **473.1 ký tự**. Lượt chạy này dùng `_mock_embed`; các kết quả là baseline kỹ thuật, không phải so sánh chất lượng ngữ nghĩa chính thức.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Tôi được đổi trả hàng trong bao nhiêu ngày kể từ khi nhận hàng? | `k4_returns_policy`: mục danh sách sản phẩm thuộc Làm đẹp - Sức khỏe. | 0.245 | Không | Chưa chấm: chưa cấu hình LLM thật. |
| 2 | Sau khi yêu cầu đổi trả được duyệt thì bao lâu tôi phải gửi hàng về, và bao lâu được hoàn tiền? | `k4-dang-ky-ban-hang`: hoàn tất thông tin cửa hàng; chunk hoàn tiền của `k4_returns_policy` ở hạng 2. | 0.427 | Có, một phần ở top-3 | Chưa chấm: chưa cấu hình LLM thật. |
| 3 | Tôi khiếu nại đơn hàng qua kênh nào và bao lâu Tiki phản hồi? | `k4_returns_policy`: danh sách sản phẩm thuộc Đồ chơi - Mẹ & Bé. | 0.338 | Không | Chưa chấm: chưa cấu hình LLM thật. |
| 4 | Khi nhận hàng tôi được phép kiểm tra sản phẩm tới mức nào? | `k4_returns_policy`: quy trình yêu cầu hoàn trả/đóng gói. | 0.350 | Không | Chưa chấm: chưa cấu hình LLM thật. |
| 5 | Thông tin thẻ thanh toán của tôi được lưu trữ như thế nào? | Sau filter `{"category": "security"}`: `k4_security_policy`; chunk lưu token và không lưu trực tiếp thẻ ở hạng 2. | 0.066 | Có, trong top-3 sau filter | Chưa chấm: chưa cấu hình LLM thật. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **2 / 5** với mock embedder (câu 2 và câu 5 sau metadata filter). Kết quả này không đủ điều kiện để kết luận chiến lược `HeadingPolicyChunker` tốt hay kém, vì README đã quy định mock không phản ánh chất lượng ngữ nghĩa.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc giữ tiêu đề và điều khoản trong cùng một chunk có thể quan trọng hơn chỉ giảm số lượng chunk. Thử nghiệm của thành viên Bùi Xuân Tùng trong báo cáo nhóm cho thấy FixedSizeChunker 900/150 đạt hit@3 5/5; đây là cơ sở để tôi chạy lại RecursiveChunker bằng embedder thật rồi so sánh công bằng trên cùng 5 benchmark.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 4 / 10 *(baseline mock; cần chạy lại bằng embedder thật + LLM)* |
| **Tổng phần cá nhân** | **54 / 60** |
