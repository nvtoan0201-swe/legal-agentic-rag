# Báo cáo chất lượng dữ liệu (bước 3)

_Sinh tự động bởi `scripts/ingest.py` — không sửa tay._ Trạng thái hiệu lực tính tại ngày
2026-11-11 (dữ liệu nguồn snapshot 2026-07-23).

## 1. Tổng quan

- Lĩnh vực: lao_dong, bhxh, hon_nhan_gia_dinh, giao_thong_duong_bo, dat_dai, thue_tncn
- Văn bản: **1,604**. Có toàn văn: 1,564, gồm 1494
  từ HTML vbpl và 70 từ bản crawl cũ. Không có toàn
  văn: 40.
- Đơn vị: 199,021, theo loại: {'khoan': 90080, 'diem': 78986, 'dieu': 29243, 'phu_luc': 507, 'dinh_kem': 109, 'body': 96}
- Quan hệ chạm tới corpus: 87,989, cả hai đầu trong corpus:
  6,475. Cạnh nghi vấn (bên tác động
  ban hành trước bên bị tác động): 271, theo loại:
  {'based_on': 198, 'guides': 33, 'cites': 32, 'repeals': 3, 'replaces': 3, 'repeals_part': 1, 'amends': 1}

| domains             |   văn_bản |   còn_HL |   có_toàn_văn | parse_sạch   |
|:--------------------|----------:|---------:|--------------:|:-------------|
| bhxh                |       162 |       49 |           158 | 94%          |
| dat_dai             |       513 |      147 |           503 | 90%          |
| giao_thong_duong_bo |       411 |       96 |           405 | 89%          |
| hon_nhan_gia_dinh   |        92 |       31 |            87 | 78%          |
| lao_dong            |       430 |      128 |           424 | 89%          |
| thue_tncn           |        99 |       56 |            85 | 82%          |

## 2. Parse

**Parse sạch: 90.9%** trên văn bản có toàn văn. Tính riêng văn bản có ít
nhất một Điều: 96.9%. "Sạch" nghĩa là có Điều, số Điều liên tục bắt đầu
từ 1, không có điều rỗng, không có dòng "Điều N" bị loại ngoài ngoặc kép, ngoặc kép cân bằng và id
không trùng. Parser không bỏ dòng nào ngoài dòng chữ ký / nơi nhận: `bỏ_tb` = tỉ lệ ký tự bị bỏ;
`đính_kèm_tb` = tỉ lệ ký tự nằm trong phần đính kèm sau chữ ký (`#kt{n}`). Văn bản có phần đính
kèm > 50% mà vẫn có Điều: 14
(đã soát tay lần chạy 2026-11-11: đều là biểu giá / danh mục / mẫu đính kèm hợp lệ, không phải
nhận nhầm khối chữ ký).

### Theo loại văn bản

| loai_van_ban       |   n | sạch   |   điều_tb |   bỏ_tb |   đính_kèm_tb |
|:-------------------|----:|:-------|----------:|--------:|--------------:|
| Bộ luật            |   4 | 100.0% |    294.25 |    0    |          0    |
| Luật               |  54 | 100.0% |     70.7  |    0.01 |          0    |
| Nghị quyết         |   7 | 71.4%  |      4.86 |    0.03 |          0    |
| Nghị định          | 371 | 98.4%  |     26.26 |    0.01 |          0    |
| Pháp lệnh          |   4 | 100.0% |     36.25 |    0    |          0    |
| Quyết định         | 152 | 91.4%  |      8.53 |    0.02 |          0.03 |
| Thông tư           | 813 | 89.7%  |     12.23 |    0.01 |          0.01 |
| Thông tư liên tịch | 106 | 76.4%  |      8.5  |    0    |          0    |
| Văn bản hợp nhất   |  53 | 77.4%  |     41.36 |    0    |          0.03 |

### Theo nguồn toàn văn

| content_source   |    n | sạch   |
|:-----------------|-----:|:-------|
| legacy_text      |   70 | 82.9%  |
| vbpl_html        | 1494 | 91.3%  |

### Lỗi hay gặp (số văn bản)

| lỗi | số văn bản | ý nghĩa |
|---|---|---|
| `no_articles` | 96 | văn bản không có Điều (lưu thành một đơn vị #body) |
| `unclosed_quote_recovered` | 30 | ngoặc không đóng, đã tự phục hồi ở điều kế tiếp |
| `rejected_article` | 22 | dòng 'Điều N' sai thứ tự ngoài ngoặc kép (thường là trích dẫn thiếu ngoặc) |
| `article_gap` | 12 | nhảy 1 số Điều (nguồn thiếu điều hoặc lỗi gõ) |
| `duplicate_id` | 10 | id đơn vị trùng (đã thêm hậu tố _2) |
| `unbalanced_quote` | 2 | ngoặc kép mở mà không đóng tới cuối văn bản |
| `first_article_not_1` | 1 | Điều đầu tiên không phải Điều 1 |

### Luật / Bộ luật / Nghị định chưa sạch (cần xem tay)

| doc_key        | loai_van_ban   |   n_articles | parse_issues               | content_source   |
|:---------------|:---------------|-------------:|:---------------------------|:-----------------|
| 83/2022/NĐ-CP  | Nghị định      |            5 | {"first_article_not_1": 1} | vbpl_html        |
| 77/2001/NĐ-CP  | Nghị định      |            0 | {"no_articles": 1}         | vbpl_html        |
| 112/2008/NĐ-CP | Nghị định      |           20 | {"article_gap": 1}         | vbpl_html        |
| 67/2015/NĐ-CP  | Nghị định      |            2 | {"rejected_article": 2}    | vbpl_html        |
| 85/2026/NĐ-CP  | Nghị định      |           43 | {"article_gap": 2}         | vbpl_html        |
| 101/2015/NĐ-CP | Nghị định      |           19 | {"article_gap": 1}         | vbpl_html        |

## 3. Hiệu lực

| status     |   consolidated_base |   graph_replaced |   legacy |   meta_date |   meta_status |   newer_consolidation |   override |
|:-----------|--------------------:|-----------------:|---------:|------------:|--------------:|----------------------:|-----------:|
| expired    |                  58 |               84 |      159 |         788 |            31 |                     0 |          3 |
| in_force   |                  18 |                0 |        0 |           0 |           453 |                     0 |          2 |
| superseded |                   0 |                0 |        0 |           0 |             0 |                     4 |          0 |
| suspended  |                   0 |                0 |        0 |           0 |             1 |                     0 |          0 |
| unknown    |                   0 |                0 |        0 |           0 |             3 |                     0 |          0 |

Cờ cần xem lại: {'partially_expired': 202, 'raw_in_force_but_legacy_expired': 159, 'raw_in_force_but_replaced': 84, 'legacy_says_in_effect': 37, 'override': 4, 'override_unverified': 1, 'raw_in_force_but_expiry_passed': 1}

### Luật gốc

| doc_key       | status   | status_source   | ngay_co_hieu_luc   | ngay_het_hieu_luc   | content_source   |   n_articles | parse_clean   | domains                            |
|:--------------|:---------|:----------------|:-------------------|:--------------------|:-----------------|-------------:|:--------------|:-----------------------------------|
| KS@1959-12-29 | expired  | meta_date       | 13/01/1960         | 03/01/1987          | vbpl_html        |           35 | True          | ['hon_nhan_gia_dinh']              |
| KS@1986-12-29 | expired  | meta_date       | 03/01/1987         | 01/01/2001          | vbpl_html        |           57 | True          | ['hon_nhan_gia_dinh']              |
| KS@1987-12-29 | expired  | meta_date       | 29/12/1987         | 15/10/1993          | vbpl_html        |           57 | True          | ['dat_dai']                        |
| KS@1993-07-14 | expired  | meta_date       | 15/10/1993         | 01/07/2004          | vbpl_html        |           89 | True          | ['dat_dai']                        |
| KS@1994-06-23 | expired  | meta_date       | 01/01/1995         | 01/05/2013          | vbpl_html        |          198 | True          | ['lao_dong']                       |
| 10/1998/QH10  | expired  | meta_date       | 01/01/1999         | 01/07/2004          | vbpl_html        |            2 | True          | ['dat_dai']                        |
| 22/2000/QH10  | expired  | meta_date       | 01/01/2001         | 01/01/2015          | vbpl_html        |          110 | True          | ['hon_nhan_gia_dinh']              |
| 26/2001/QH10  | expired  | meta_date       | 01/01/2002         | 01/07/2009          | vbpl_html        |           77 | True          | ['giao_thong_duong_bo']            |
| 35/2002/QH10  | expired  | meta_date       | 01/01/2003         | 01/05/2013          | vbpl_html        |            3 | True          | ['lao_dong']                       |
| 13/2003/QH11  | expired  | meta_date       | 01/07/2004         | 01/07/2014          | vbpl_html        |          146 | True          | ['dat_dai']                        |
| 71/2006/QH11  | expired  | meta_date       | 01/01/2007         | 01/01/2016          | vbpl_html        |          141 | True          | ['bhxh']                           |
| 74/2006/QH11  | expired  | meta_date       | 01/07/2007         | 01/05/2013          | vbpl_html        |            3 | True          | ['lao_dong']                       |
| 84/2007/QH11  | expired  | meta_date       | 11/04/2007         | 01/05/2013          | vbpl_html        |            2 | True          | ['lao_dong']                       |
| 04/2007/QH12  | expired  | override        | 01/01/2009         | 01/07/2026          | legacy_text      |           35 | True          | ['thue_tncn']                      |
| 23/2008/QH12  | expired  | override        | 01/07/2009         | 01/01/2025          | vbpl_html        |           89 | True          | ['giao_thong_duong_bo']            |
| 10/2012/QH13  | expired  | meta_date       | 01/05/2013         | 01/01/2021          | vbpl_html        |          242 | True          | ['lao_dong']                       |
| 26/2012/QH13  | expired  | legacy          | 01/07/2013         | 01/07/2026          | vbpl_html        |            2 | True          | ['thue_tncn']                      |
| 38/2013/QH13  | expired  | meta_date       | 01/01/2015         | 01/01/2026          | vbpl_html        |           62 | True          | ['bhxh', 'lao_dong']               |
| 45/2013/QH13  | expired  | override        | 01/07/2014         | 01/08/2024          | vbpl_html        |          212 | True          | ['dat_dai']                        |
| 52/2014/QH13  | in_force | meta_status     | 01/01/2015         | nan                 | vbpl_html        |          133 | True          | ['hon_nhan_gia_dinh']              |
| 58/2014/QH13  | expired  | meta_date       | 01/01/2016         | 01/07/2025          | vbpl_html        |          125 | True          | ['bhxh']                           |
| 45/2019/QH14  | in_force | meta_status     | 01/01/2021         | nan                 | vbpl_html        |          220 | True          | ['bhxh', 'lao_dong']               |
| 31/2024/QH15  | in_force | override        | 01/08/2024         | nan                 | legacy_text      |          260 | True          | ['dat_dai']                        |
| 35/2024/QH15  | in_force | meta_status     | 01/01/2025         | nan                 | vbpl_html        |           86 | True          | ['dat_dai', 'giao_thong_duong_bo'] |
| 36/2024/QH15  | in_force | meta_status     | 01/01/2025         | nan                 | vbpl_html        |           89 | True          | ['giao_thong_duong_bo']            |
| 41/2024/QH15  | in_force | override        | 01/07/2025         | nan                 | vbpl_html        |          141 | True          | ['bhxh', 'lao_dong']               |
| 74/2025/QH15  | in_force | meta_status     | 01/01/2026         | nan                 | vbpl_html        |           55 | True          | ['bhxh', 'lao_dong']               |
| 109/2025/QH15 | in_force | meta_status     | 01/07/2026         | nan                 | vbpl_html        |           29 | True          | ['thue_tncn']                      |
