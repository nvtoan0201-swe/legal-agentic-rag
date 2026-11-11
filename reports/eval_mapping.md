# Ánh xạ bộ thangvip/vietnamese-legal-qa vào corpus (bước 4)

_Sinh tự động bởi `scripts/build_eval.py` — không sửa tay._ Revision `9bd2b0e66fc5a9d09b4df22fade7a8d9592834c2`.

Bộ QA có 9,715 điều luật và 29,145 cặp hỏi–đáp do LLM sinh, chỉ gồm Luật/
Bộ luật. Ánh xạ = số hiệu (lấy từ `doc_name`) + số Điều (lấy từ đầu `article_content`), sau đó xác
minh bằng độ trùng từ giữa `article_content` và văn bản điều trong corpus.

## 1. Kết quả ánh xạ

| match            |   điều |   cặp hỏi-đáp | ý nghĩa                                                       |
|:-----------------|-------:|--------------:|:--------------------------------------------------------------|
| not_in_corpus    |   5860 |         17580 | số hiệu không có trong corpus (luật ngoài 6 lĩnh vực)         |
| draft_law        |   2316 |          6948 | dự thảo luật, bỏ                                              |
| not_core         |    683 |          2049 | luật ngoại vi (lĩnh vực khác, chỉ vào corpus vì sửa luật gốc) |
| ok               |    598 |          1794 | ánh xạ được, nội dung khớp, văn bản lõi                       |
| article_missing  |    241 |           723 | văn bản có trong corpus nhưng không có điều này sau parse     |
| no_number        |     15 |            45 | doc_name không có số hiệu                                     |
| content_mismatch |      2 |             6 | có số hiệu + điều nhưng nội dung khác (độ trùng từ < 0.5)     |

Phân bố độ trùng từ (các điều có số hiệu + điều trong corpus):

| sim        |   count |
|:-----------|--------:|
| (0.0, 0.3] |       0 |
| (0.3, 0.5] |       2 |
| (0.5, 0.7] |       0 |
| (0.7, 0.9] |       1 |
| (0.9, 1.0] |    1280 |

## 2. Theo văn bản có trong corpus

| so_ky_hieu   | văn bản                                       | hiệu lực   |   article_missing |   content_mismatch |   not_core |   ok |
|:-------------|:----------------------------------------------|:-----------|------------------:|-------------------:|-----------:|-----:|
| 16/2023/QH15 | Luật Giá số 16/2023/QH15                      | in_force   |                 0 |                  0 |         75 |    0 |
| 23/2008/QH12 | Luật Giao thông đường bộ số 23/2008/QH12      | expired    |                 0 |                  0 |          0 |   82 |
| 26/2001/QH10 | Luật Giao thông đường bộ số 26/2001/QH10      | expired    |                 0 |                  0 |          0 |   77 |
| 35/2024/QH15 | Luật Đường bộ số 35/2024/QH15                 | in_force   |                 0 |                  0 |          0 |   86 |
| 36/2024/QH15 | Trật tự, an toàn giao thông đường bộ          | in_force   |                 0 |                  0 |          0 |   87 |
| 41/2024/QH15 | Luật Bảo hiểm xã hội                          | in_force   |                 0 |                  0 |          0 |  142 |
| 43/2024/QH15 | Luật Sửa đổi, bổ sung một số điều của Luật Đấ | in_force   |                 0 |                  0 |          5 |    0 |
| 52/2010/QH12 | Luật Nuôi con nuôi số 52/2010/QH12            | in_force   |                 0 |                  0 |         52 |    0 |
| 56/2024/QH15 | Luật sửa đổi, bổ sung một số điều của Luật Ch | expired    |                 0 |                  0 |         11 |    0 |
| 58/2014/QH13 | Luật Bảo hiểm xã hội số 58/2014/QH13          | expired    |                 0 |                  0 |          0 |  124 |
| 64/2010/QH12 | Luật Tố tụng hành chính số 64/2010/QH12       | expired    |                 0 |                  0 |        265 |    0 |
| 66/2006/QH11 | Luật Hàng không dân dụng Việt Nam số 66/2006/ | expired    |                 0 |                  0 |        202 |    0 |
| 93/2015/QH13 | Nghị quyết số 93/2015/QH13 Về việc thực hiện  | expired    |               241 |                  2 |          0 |    0 |
| 94/2015/QH13 | Luật Thi hành tạm giữ, tạm giam số 94/2015/QH | expired    |                 0 |                  0 |         73 |    0 |

## 3. Bộ eval sinh ra

| category     |   dev |   test |   All |
|:-------------|------:|-------:|------:|
| expired      |   669 |    180 |   849 |
| out_of_scope |    76 |     15 |    91 |
| single_hop   |   759 |    186 |   945 |
| All          |  1504 |    381 |  1885 |

### Theo lĩnh vực

| domain              |   expired |   out_of_scope |   single_hop |
|:--------------------|----------:|---------------:|-------------:|
| bhxh                |       372 |              0 |          426 |
| giao_thong_duong_bo |       477 |              0 |          519 |
| —                   |         0 |             91 |            0 |

### "Đường tắt" trong câu hỏi (tỉ lệ)

`mentions_article` = câu hỏi nêu sẵn "Điều N"; `names_law` = nêu tên luật; `names_version` = nêu số
hiệu hoặc năm. Câu hỏi thật của người dùng hiếm khi có các thông tin này, nên khi báo cáo cần tách
riêng nhóm không có đường tắt.

| category     |   mentions_article |   names_law |   names_version |
|:-------------|-------------------:|------------:|----------------:|
| expired      |               0.84 |        0.67 |            0.08 |
| out_of_scope |               0.7  |        0.63 |            0.09 |
| single_hop   |               0.84 |        0.61 |            0.14 |

## 4. Nhận xét

- **Độ phủ lĩnh vực rất lệch:** câu dùng được chỉ thuộc 2/6 lĩnh vực (BHXH, giao thông đường bộ).
  Bộ QA không có Bộ luật Lao động 2019, Luật HN&GĐ 2014, Luật Đất đai 2024 hay Luật thuế TNCN.
  → Bộ câu tự viết và bộ multi-hop sinh nháp phải bù cho lao động, HN&GĐ, đất đai và thuế TNCN.
- `article_missing` gần như toàn bộ là **trùng số hiệu**: 93/2015/QH13 trong bộ QA là Luật Tố tụng
  hành chính, còn trong corpus là Nghị quyết 93/2015/QH13 về BHXH. Bước xác minh đã loại đúng.
- **Câu về luật đã hết hiệu lực** (BHXH 2014, GTĐB 2008/2001) được xếp vào `expired`, chưa có
  gold: phải điền điều tương ứng của luật thay thế khi duyệt. `forbidden_articles` là điều của luật
  cũ.
- **`out_of_scope`** lấy từ luật hoàn toàn không có trong corpus. Đây là ngoài phạm vi theo nghĩa
  corpus; vài câu có thể giao nhau với luật trong corpus, cần duyệt.
- Câu hỏi và đáp án đều do LLM sinh, chưa qua người duyệt, nên mọi item có `reviewed=false`.

### Ví dụ nội dung không khớp

| doc_name                                              | so_ky_hieu   |   dieu |      sim |
|:------------------------------------------------------|:-------------|-------:|---------:|
| Luật Tố tụng hành chính của Quốc hội, số 93/2015/QH13 | 93/2015/QH13 |      4 | 0.3125   |
| Luật Tố tụng hành chính của Quốc hội, số 93/2015/QH13 | 93/2015/QH13 |      2 | 0.423913 |
