# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Trung Kiên
**Nhóm:** [Tên nhóm]
**Ngày:** 3/8/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding có góc giữa chúng rất nhỏ (gần như cùng hướng trong không gian đa chiều), nghĩa là hai đoạn văn bản mang ý nghĩa ngữ nghĩa gần giống nhau, dù cách diễn đạt câu chữ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn đổi trả sản phẩm vì bị lỗi."
- Câu B: "Làm sao để hoàn trả hàng bị hư hỏng?"
- Tại sao tương đồng: Cả hai câu đều nói về cùng một chủ đề (đổi/trả hàng lỗi), dùng từ vựng gần nghĩa nhau ("đổi trả" ~ "hoàn trả", "lỗi" ~ "hư hỏng"), nên embedding của chúng sẽ nằm gần nhau trong không gian vector dù cấu trúc câu khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách giao hàng của cửa hàng như thế nào?"
- Câu B: "Hôm nay thời tiết Hà Nội có mưa không?"
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn không liên quan (chính sách giao hàng TMĐT vs. thời tiết), không chia sẻ ngữ cảnh hay từ vựng ngữ nghĩa gần nhau, nên vector embedding sẽ có góc lệch lớn.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ quan tâm đến *hướng* của vector chứ không quan tâm đến *độ lớn* (magnitude), nên nó không bị ảnh hưởng bởi độ dài văn bản hay độ "mạnh" của embedding — hai văn bản cùng ý nghĩa nhưng độ dài khác nhau vẫn cho điểm tương tự cao, trong khi Euclidean distance sẽ bị lệch bởi sự khác biệt về độ lớn vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính:
> số lượng chunk = làm_tròn_lên((10000 − 50) / (500 − 50))
> = làm_tròn_lên(9950 / 450)
> = làm_tròn_lên(22.11)
> = 23
>
> Đáp án: **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số lượng chunk tăng lên: làm_tròn_lên((10000−100)/(500−100)) = làm_tròn_lên(9900/400) = làm_tròn_lên(24.75) = **25 chunks** (tăng từ 23 lên 25). Overlap lớn hơn giúp giảm nguy cơ cắt đứt thông tin quan trọng ở ranh giới giữa hai chunk (ví dụ một câu hoặc ý bị chia làm đôi), giúp mỗi chunk giữ được nhiều ngữ cảnh hơn cho việc truy xuất — đánh đổi lại là tốn thêm dung lượng lưu trữ và thời gian embedding do có nhiều chunk hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `(?<=[.!?])[ \n]+` (lookbehind) để tách câu ngay sau dấu `.`, `!`, `?` mà không làm mất dấu câu đó khỏi câu trước; các khoảng trắng/newline liền sau đóng vai trò ranh giới câu. Các câu được gom thành nhóm tối đa `max_sentences_per_chunk` câu rồi nối lại bằng dấu cách. Edge case xử lý: chuỗi rỗng hoặc chỉ toàn khoảng trắng trả về `[]`, và các fragment rỗng sinh ra do khoảng trắng thừa/nhiều dấu câu liên tiếp bị lọc bỏ trước khi gom nhóm.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử tách văn bản bằng separator ưu tiên cao nhất (`\n\n`); nếu mảnh nào sau khi tách vẫn dài hơn `chunk_size`, hàm đệ quy `_split` được gọi lại trên chính mảnh đó với danh sách separator còn lại (`\n`, `. `, ` `, `""`). Base case gồm 2 trường hợp: (1) đoạn văn bản hiện tại đã ≤ `chunk_size` → trả về nguyên đoạn, không tách thêm; (2) đã hết separator để thử → cắt cứng theo số ký tự (`chunk_size`) để đảm bảo đệ quy luôn dừng, kể cả khi truyền `separators=[]`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được xem là một chunk độc lập; `_make_record` nhúng `content` bằng `embedding_fn` rồi lưu dict `{id, content, metadata, embedding}` vào danh sách `self._store` (nhánh ChromaDB thì gọi `collection.add(ids=..., documents=..., embeddings=..., metadatas=...)`). `search` nhúng câu truy vấn rồi tính dot product giữa embedding truy vấn và embedding của từng record đã lưu — vì `MockEmbedder`/`LocalEmbedder` đều chuẩn hoá vector về độ dài 1 nên dot product tương đương cosine similarity — sau đó sắp xếp giảm dần theo điểm và trả về `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc **trước**: `search_with_filter` quét `self._store`, giữ lại các record có `metadata` khớp toàn bộ điều kiện trong `metadata_filter`, rồi mới chạy similarity search (`_search_records`) trên tập con đã lọc thay vì lọc kết quả sau khi tìm kiếm — tránh tính điểm tương tự trên các record chắc chắn bị loại. `delete_document` xoá theo `doc_id`, khớp theo cả hai kiểu: `record["id"] == doc_id` (khi một `Document` đại diện nguyên một tài liệu, không có chunk con) hoặc `metadata["doc_id"] == doc_id` (khi nhiều chunk cùng thuộc một tài liệu, gắn qua pipeline `ingest.py`); trả về `True`/`False` dựa trên độ dài `self._store` trước và sau khi lọc.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `store.search(question, top_k=top_k)` để truy xuất các chunk liên quan nhất, sau đó ghép nội dung các chunk thành khối "Ngữ cảnh" được đánh số `[1]`, `[2]`... Prompt gồm 4 phần theo thứ tự: chỉ dẫn vai trò kèm ràng buộc "chỉ dùng ngữ cảnh để trả lời", khối Ngữ cảnh, Câu hỏi, và nhãn "Trả lời:" để LLM tiếp tục sinh câu trả lời. Nếu không tìm thấy chunk nào liên quan, ngữ cảnh được thay bằng thông báo rõ ràng thay vì để trống, giúp LLM biết trả lời "không đủ thông tin" thay vì bịa đặt.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```

**Số lượng bài test vượt qua (pass):** __ / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi thích ăn phở. | Tôi rất thích món phở. | cao | 0.7721 | Đúng |
| 2 | Chính sách đổi trả trong 30 ngày. | Hôm nay trời nắng đẹp. | thấp | -0.0551 | Đúng |
| 3 | Sản phẩm bị lỗi được hoàn tiền 100%. | Hàng hỏng thì được trả lại tiền đầy đủ. | cao | 0.2899 | Sai |
| 4 | Con mèo đang ngủ trên ghế. | Con mèo đang ngủ trên ghế. | cao | 1.0000 | Đúng |
| 5 | Thời gian giao hàng từ 2-5 ngày. | Chúng tôi không bán dữ liệu cá nhân cho bên thứ ba. | thấp | -0.0122 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là Cặp 3: hai câu gần như đồng nghĩa hoàn toàn ("hoàn tiền 100%" và "trả lại tiền đầy đủ") nhưng điểm tương tự chỉ đạt 0.2899 — thấp hơn nhiều so với dự đoán "cao", và thậm chí không cao hơn bao nhiêu so với các cặp câu hoàn toàn không liên quan (Cặp 2, 5). Trong khi đó Cặp 1, dù dùng từ khác nhau ("thích ăn phở" so với "rất thích món phở"), lại cho điểm khá cao (0.7721) vì hai câu có nhiều từ trùng lặp về mặt ký tự. Điều này cho thấy `MockEmbedder` chỉ sinh vector giả lập dựa trên đặc trưng bề mặt của chuỗi ký tự (ví dụ hash hoặc từ trùng nhau) chứ không thực sự "hiểu" ngữ nghĩa — nên hai câu đồng nghĩa nhưng diễn đạt bằng từ vựng hoàn toàn khác (như Cặp 3) lại không được nhận ra là tương đồng. Chỉ có Cặp 4 (hai câu giống hệt) đạt điểm 1.0 tuyệt đối vì cùng một chuỗi ký tự luôn cho cùng một vector — đây là minh chứng rõ ràng cho việc cần dùng embedding model thật (`EMBEDDING_PROVIDER=local`) thay vì mock nếu muốn đo lường ngữ nghĩa có ý nghĩa, đúng như lưu ý trong `exercises.md`.
---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

**Chiến lược sử dụng:** Custom `HeaderChunker` — chia theo tiêu đề markdown (`##`, `###`), fallback bằng `RecursiveChunker(chunk_size=800)` nếu section vẫn quá dài. Embedder: `LocalEmbedder` (`EMBEDDING_PROVIDER=local`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Tôi được đổi trả hàng trong bao nhiêu ngày kể từ khi nhận hàng? | Section "Thời gian hỗ trợ đổi trả tại Tiki" — nguyên vẹn cả tiêu đề lẫn nội dung (30 ngày / 365 ngày lỗi kỹ thuật) | 0.812 | Có | 30 ngày kể từ khi nhận hàng thành công; riêng lỗi kỹ thuật của Thiết bị số/Điện gia dụng do Tiki Trading bán thì 365 ngày |
| 2 | Sau khi yêu cầu đổi trả được duyệt thì bao lâu tôi phải gửi hàng về, và bao lâu được hoàn tiền? | Section "Quy trình yêu cầu hoàn trả" — chỉ chứa phần "7 ngày làm việc gửi hàng", **thiếu** phần thời gian hoàn tiền vì header chunker tách "Quy trình hoàn tiền" thành chunk riêng | 0.734 | Có (một phần) | 7 ngày làm việc để gửi hàng về sau khi duyệt (thiếu chi tiết 3-5 ngày hoàn tiền ở lần trả lời đầu — agent lấy bổ sung được nhờ chunk hoàn tiền nằm ở top-2) |
| 3 | Tôi khiếu nại đơn hàng qua kênh nào và bao lâu Tiki phản hồi? | Một chunk trung gian từ `returns_policy` nhắc tới "liên hệ Tiki Care" (nhiễu do trùng từ khoá), chunk đúng "Bước 1 — Kênh tiếp nhận" rơi xuống hạng 2 | 0.581 | Có (ở hạng 2, không phải top-1) | Hotline 19006035 (8h-21h), email hotro@tiki.vn, hoặc chat trực tiếp; phản hồi trong 3 ngày làm việc |
| 4 | Khi nhận hàng tôi được phép kiểm tra sản phẩm tới mức nào? | Toàn bộ tài liệu `k4_chinh_sach_kiem_hang` (835 ký tự, không có sub-heading nên giữ nguyên thành 1 chunk) | 0.793 | Có | Được mở thùng hàng Tiki kiểm tra nhưng không được mở seal sản phẩm hay kiểm tra sâu (cắm điện, dùng thử...) |
| 5 | Thông tin thẻ thanh toán của tôi được lưu trữ như thế nào? | Section "Chính sách bảo mật giao dịch trong thanh toán" (sau khi lọc `metadata_filter={"category": "security"}`) | 0.706 | Có | Tiki không lưu trực tiếp thông tin thẻ, chỉ lưu token đã mã hoá; thẻ quốc tế do Đối Tác Cổng Thanh Toán lưu, thẻ nội địa Tiki chỉ lưu mã đơn hàng/giao dịch/tên ngân hàng |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> So với cách tinh chỉnh `FixedSizeChunker` (900/150) của Tùng, chunker theo tiêu đề của mình cho chunk "sạch" hơn về mặt ngữ nghĩa (mỗi chunk = đúng 1 điều khoản) nhưng lại dễ vỡ khi câu trả lời cần thông tin trải trên 2 mục liền nhau (Câu 2) hoặc khi mục quá ngắn thiếu từ khoá để cạnh tranh thứ hạng (Câu 3). Bài học lớn nhất là không có chiến lược nào thắng tuyệt đối — chunk lớn giữ ngữ cảnh nhưng loãng, chunk theo cấu trúc tài liệu thì chính xác nhưng dễ cắt đứt câu trả lời đa phần; kết hợp thêm lọc metadata (như Câu 5) mới thực sự giải quyết được vấn đề nhiễu do trùng từ khoá.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **57 / 60** |
