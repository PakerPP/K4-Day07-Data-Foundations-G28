# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Quang Sơn  
**MSSV:** 2A202601956  
**Nhóm:** G28  
**Ngày:** 2026-08-03

## 1. Khởi động

### Độ tương tự cosine

Cosine similarity đo góc giữa hai vector embedding. Điểm cao nghĩa là hai đoạn văn có hướng ngữ nghĩa gần nhau; điểm gần 0 thường cho thấy ít liên quan, còn điểm âm biểu thị hướng đối lập.

- Ví dụ tương tự cao: “Tôi muốn đổi trả sản phẩm bị lỗi” và “Làm sao để hoàn hàng khi hàng bị hỏng?” Cả hai đều diễn đạt ý định hoàn/đổi một sản phẩm lỗi.
- Ví dụ tương tự thấp: “Hôm nay trời mưa rất to ở Hà Nội” và “Quy định hoàn tiền cho đơn hàng bị hủy.” Đây là hai chủ đề không liên quan.

Cosine được ưu tiên vì nó so sánh hướng vector và ít bị ảnh hưởng bởi độ dài văn bản hay độ lớn embedding. Khoảng cách Euclid có thể tăng chỉ vì norm khác nhau, dù hai văn bản vẫn cùng ý nghĩa.

### Bài toán chunking

Với tài liệu 10.000 ký tự, `chunk_size=500` và `overlap=50`:

```
ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 23 chunks
```

Nếu `overlap=100`, số chunk là `ceil(9900 / 400) = 25`. Overlap lớn hơn làm tăng chi phí nhúng và lưu trữ, nhưng giúp giữ trọn ý/câu ở ranh giới giữa hai chunk và cải thiện khả năng truy xuất.

## 2. Hướng tiếp cận triển khai

`SentenceChunker` dùng regex để tách tại khoảng trắng sau `.`, `!` hoặc `?`, giữ dấu kết thúc câu trong câu trước đó. Sau khi loại bỏ khoảng trắng thừa, các câu được gom theo `max_sentences_per_chunk`; đầu vào rỗng trả về danh sách rỗng.

`RecursiveChunker` thử lần lượt các separator `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng là cắt cứng. Hàm đệ quy dừng khi đoạn đã đủ ngắn hoặc không còn separator; các mảnh nhỏ liền kề được gộp tối đa trong giới hạn `chunk_size`.

`compute_similarity` tính `dot(a, b) / (||a|| × ||b||)` và trả về `0.0` nếu một vector có độ lớn bằng 0, tránh lỗi chia cho 0.

`ChunkingStrategyComparator` chạy ba chiến lược có sẵn (`FixedSizeChunker`, `SentenceChunker`, `RecursiveChunker`) và trả về danh sách chunk, số chunk, cùng độ dài trung bình cho từng chiến lược.

`EmbeddingStore` dùng danh sách bản ghi trong bộ nhớ làm cơ chế chính: mỗi bản ghi giữ nội dung, metadata, embedding và ID duy nhất. Khi tìm kiếm, query được embed rồi các bản ghi được xếp theo cosine similarity. `search_with_filter` lọc metadata trước khi xếp hạng; `delete_document` xóa mọi chunk có cùng `metadata["doc_id"]`. Nếu ChromaDB có sẵn, dữ liệu còn được đồng bộ vào collection tạm thời nhưng chức năng vẫn hoạt động khi không có ChromaDB.

`KnowledgeBaseAgent` triển khai luồng RAG: lấy top-k chunk, đưa chúng cùng nguồn vào prompt, yêu cầu LLM chỉ trả lời từ ngữ cảnh, rồi gọi `llm_fn`. Khi không tìm thấy chunk, agent trả về thông báo không có thông tin thay vì gọi LLM với ngữ cảnh rỗng.

## 3. Hoàn thiện mã nguồn và kiểm thử

Các TODO trong `src/chunking.py`, `src/store.py` và `src/agent.py` đã được hoàn thành.

Kết quả kiểm thử:

```text
$ python3 -m unittest discover -s tests -t . -v
Ran 42 tests in 0.006s

OK
```

**Số test đạt:** **42 / 42**.

Ngoài unit test, đã chạy thành công:

```text
$ python3 ingest.py
ingest self-check OK: parse được 4 khóa metadata, tạo 18 chunk

$ python3 main.py "Chính sách đổi trả hàng như thế nào?"
Đã nạp 85 chunk vào EmbeddingStore
```

Lưu ý: môi trường hiện tại không cài `pytest`, vì vậy dùng `unittest` để chạy chính file test của lab. Trên môi trường chuẩn có `pytest`, có thể chạy `pytest tests/ -v`.

## 4. Ghi chú phạm vi

Báo cáo này hoàn thành các mục cá nhân thuộc **Giai Đoạn 1**. Phần dự đoán embedding thực, benchmark 5 câu hỏi và kết quả retrieval chính thức thuộc Giai Đoạn 2, cần bộ dữ liệu/câu hỏi đã được cả nhóm thống nhất nên không tự điền bằng dữ liệu giả định.
