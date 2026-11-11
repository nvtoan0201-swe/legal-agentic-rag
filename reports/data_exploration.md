# Khám phá dữ liệu: th1nhng0/vietnamese-legal-documents

_Sinh tự động bởi `scripts/explore_metadata.py` — không sửa tay._

## 1. Tổng quan

- metadata: 171,556 văn bản, 17 cột gốc
- relationships: 1,033,255 cạnh
- văn bản trung ương có tính quy phạm (`eligible`): 43,698

## 2. Các cột metadata và tỉ lệ thiếu

| cột                 | null   | thiếu (gồm 'Chưa phân loại', 'Chưa xác định', rỗng)   |   số giá trị khác nhau | ví dụ                                             |
|:--------------------|:-------|:------------------------------------------------------|-----------------------:|:--------------------------------------------------|
| id                  | 0.0%   | 0.0%                                                  |                 171556 | 8733                                              |
| title               | 0.0%   | 0.0%                                                  |                 170579 | Thông tư số 01/GD-ĐT Hướng dẫn việc dạy học tiếng |
| so_ky_hieu          | 0.0%   | 0.0%                                                  |                  71722 | 01/GD-ĐT                                          |
| ngay_ban_hanh       | 0.1%   | 0.1%                                                  |                  14304 | 03/02/1997                                        |
| loai_van_ban        | 0.0%   | 0.0%                                                  |                     31 | Thông tư                                          |
| ngay_co_hieu_luc    | 2.9%   | 2.9%                                                  |                  15759 | 03/02/1997                                        |
| ngay_het_hieu_luc   | 53.2%  | 53.2%                                                 |                   7744 | 01/01/2017                                        |
| nguon_thu_thap      | 50.7%  | 50.7%                                                 |                  13565 | Công báo điện tử;                                 |
| ngay_dang_cong_bao  | 73.6%  | 73.6%                                                 |                   6945 | 25/01/2013                                        |
| nganh               | 37.4%  | 38.3%                                                 |                   1165 | Tài chính                                         |
| linh_vuc            | 2.8%   | 69.1%                                                 |                   2158 | Chưa phân loại                                    |
| co_quan_ban_hanh    | 0.4%   | 0.5%                                                  |                   1832 | Bộ Giáo dục và Đào tạo                            |
| chuc_danh           | 3.2%   | 3.3%                                                  |                    590 | Thứ trưởng                                        |
| nguoi_ky            | 1.1%   | 1.2%                                                  |                   5555 | Trần Xuân Nhĩ                                     |
| pham_vi             | 0.0%   | 0.0%                                                  |                     51 | Trung ương                                        |
| thong_tin_ap_dung   | 100.0% | 100.0%                                                |                      0 |                                                   |
| tinh_trang_hieu_luc | 0.0%   | 1.9%                                                  |                      8 | Chưa xác định                                     |

Tỉ lệ ngày có giá trị nhưng không parse được theo DD/MM/YYYY: `ngay_ban_hanh` 0.0%, `ngay_co_hieu_luc` 0.0%, `ngay_het_hieu_luc` 0.0%, `ngay_dang_cong_bao` 0.0%

## 3. Phân bố

### 3.1 Theo loại văn bản

| loai_van_ban                 |   số văn bản |
|:-----------------------------|-------------:|
| Quyết định                   |        91183 |
| Nghị quyết                   |        28337 |
| Thông tư                     |        17232 |
| Bản dịch văn bản             |        10952 |
| Chỉ thị                      |         8543 |
| Nghị định                    |         5328 |
| Thông tư liên tịch           |         3519 |
| Văn bản hợp nhất             |         2232 |
| Sắc lệnh                     |          981 |
| Văn bản hệ thống hóa         |          762 |
| Công văn                     |          732 |
| Luật                         |          610 |
| Lệnh                         |          379 |
| Văn bản hành chính liên quan |          281 |
| Pháp lệnh                    |          248 |
| Văn bản liên quan            |           43 |
| Chương trình                 |           42 |
| Nghị quyết liên tịch         |           34 |
| Hiệp định                    |           24 |
| Bộ luật                      |           17 |
| Văn bản khác                 |           16 |
| Công ước                     |           16 |
| Thông báo                    |           11 |
| Chưa xác định                |            9 |
| Thông tư liên bộ             |            7 |
| Hiến pháp                    |            6 |
| Nghị định thư                |            4 |
| Sắc luật                     |            4 |
| Bản ghi nhớ                  |            2 |
| Thỏa thuận                   |            1 |
| Quy định                     |            1 |

### 3.2 Theo phạm vi

| pham_vi         |   số văn bản |
|:----------------|-------------:|
| Địa phương      |       114360 |
| Trung ương      |        56730 |
| TỈNH BÌNH PHƯỚC |          122 |
| Toàn quốc       |          106 |
| Tỉnh Hà Giang   |           40 |

### 3.3 Theo thập kỉ ban hành

|       |   số văn bản |
|:------|-------------:|
| 1920s |            1 |
| 1940s |          689 |
| 1950s |          639 |
| 1960s |          382 |
| 1970s |          858 |
| 1980s |         3687 |
| 1990s |        15582 |
| 2000s |        51286 |
| 2010s |        54539 |
| 2020s |        43795 |
| 3020s |            1 |

### 3.4 Theo năm (2010–2026), chỉ văn bản trung ương có tính quy phạm

|   nam_ban_hanh |   Bộ luật |   Luật |   Nghị quyết |   Nghị định |   Pháp lệnh |   Quyết định |   Thông tư |   Thông tư liên tịch |   Văn bản hợp nhất |
|---------------:|----------:|-------:|-------------:|------------:|------------:|-------------:|-----------:|---------------------:|-------------------:|
|           2010 |         0 |     19 |           24 |         121 |           1 |          223 |        714 |                  102 |                  0 |
|           2011 |         0 |      8 |           34 |         127 |           4 |          238 |        830 |                  103 |                  0 |
|           2012 |         1 |     23 |           27 |         107 |           5 |          175 |        696 |                  126 |                  7 |
|           2013 |         0 |     17 |           24 |         218 |           3 |          217 |        725 |                  115 |                 39 |
|           2014 |         0 |     29 |           28 |         123 |           2 |          176 |        851 |                  107 |                 37 |
|           2015 |         5 |     22 |           34 |         140 |           0 |          102 |        782 |                  116 |                 97 |
|           2016 |         0 |     10 |           45 |         174 |           2 |           63 |        837 |                   79 |                104 |
|           2017 |         0 |     18 |           20 |         154 |           0 |           59 |        633 |                    5 |                 63 |
|           2018 |         0 |     16 |           10 |         164 |           2 |           53 |        679 |                   16 |                119 |
|           2019 |         1 |     17 |           15 |         102 |           0 |           49 |        553 |                    2 |                186 |
|           2020 |         0 |     21 |           16 |         160 |           1 |           41 |        553 |                    5 |                197 |
|           2021 |         0 |      3 |           18 |         135 |           0 |           43 |        547 |                    9 |                100 |
|           2022 |         0 |     12 |           17 |         121 |           3 |           29 |        470 |                    1 |                135 |
|           2023 |         0 |     16 |            8 |          91 |           1 |           46 |        508 |                    3 |                115 |
|           2024 |         0 |     32 |           21 |         181 |           1 |           40 |        642 |                    2 |                297 |
|           2025 |         0 |     83 |          122 |         357 |           4 |           65 |        860 |                   18 |                325 |
|           2026 |         0 |      9 |           39 |         196 |           1 |           14 |        408 |                   17 |                233 |
|           3024 |         0 |      0 |            0 |           0 |           0 |            0 |          1 |                    0 |                  0 |

### 3.5 Theo ngành (top 25)

| nganh                               |   số văn bản |
|:------------------------------------|-------------:|
| nan                                 |        64175 |
| Tài chính                           |        19686 |
| Nội vụ                              |        10619 |
| Lao động - Thương binh và Xã hội    |         9881 |
| Tài nguyên và Môi trường            |         6673 |
| Nông nghiệp và phát triển nông thôn |         6410 |
| Xây dựng                            |         5168 |
| Tư pháp                             |         4025 |
| Công Thương                         |         3907 |
| Giáo dục và đào tạo                 |         3872 |
| Giao thông Vận tải                  |         3472 |
| Y tế                                |         3387 |
| Kế hoạch và Đầu tư                  |         3244 |
| Văn hóa Thể thao và Du lịch         |         2672 |
| Khoa học và công nghệ               |         2444 |
| Thông tin và Truyền thông           |         2354 |
| Công an                             |         1777 |
| Ngân hàng                           |         1585 |
| Chưa phân loại                      |         1535 |
| Quốc phòng                          |         1300 |
| Nông nghiệp và Môi trường           |         1195 |
| Thanh tra                           |          661 |
| Văn hóa - Thông tin                 |          467 |
| Ngoại giao                          |          450 |
| Tài nguyên và Môi trường, Tài chính |          381 |

### 3.6 Theo lĩnh vực (top 30)

| linh_vuc                                                                                                    |   số văn bản |
|:------------------------------------------------------------------------------------------------------------|-------------:|
| Chưa phân loại                                                                                              |       113772 |
| nan                                                                                                         |         4785 |
| Đất đai                                                                                                     |         2916 |
| Quản lý thuế, phí, lệ phí và thu khác của ngân sách nhà nước                                                |         2390 |
| Quản lý thuế, phí và lệ phí                                                                                 |         1742 |
| Lĩnh vực giá                                                                                                |         1656 |
| Lao động, tiền lương, tiền công                                                                             |         1479 |
| Tổ chức- Biên chế                                                                                           |         1302 |
| Ngân sách nhà nước                                                                                          |         1289 |
| Quản lý ngân sách                                                                                           |         1228 |
| Quản lý ngân sách nhà nước                                                                                  |         1085 |
| Chính quyền địa phương                                                                                      |          880 |
| Đường bộ                                                                                                    |          874 |
| Công chức, viên chức                                                                                        |          737 |
| Tài chính khác                                                                                              |          668 |
| Lâm nghiệp                                                                                                  |          643 |
| Thi đua, khen thưởng                                                                                        |          620 |
| Môi trường                                                                                                  |          542 |
| Nông nghiệp                                                                                                 |          495 |
| Chính sách thuế                                                                                             |          474 |
| Thủy lợi                                                                                                    |          470 |
| Cải cách hành chính                                                                                         |          442 |
| Xây dựng                                                                                                    |          413 |
| Tổ chức cán bộ                                                                                              |          401 |
| An ninh và trật tự, an toàn xã hội                                                                          |          386 |
| Tài nguyên khoáng sản, địa chất                                                                             |          373 |
| Bảo trợ xã hội                                                                                              |          363 |
| Phát triển nông thôn                                                                                        |          347 |
| Kiểm tra, rà soát, hệ thống hóa, hợp nhất văn bản quy phạm pháp luật, pháp điển hệ thống quy phạm pháp luật |          344 |
| Đầu tư tại Việt Nam                                                                                         |          336 |

Trong 627 Luật/Bộ luật: `nganh` thiếu 52.0%, `linh_vuc` thiếu 72.4%. Luật ban hành từ 2024: `linh_vuc` thiếu 46.8%.

## 4. Trùng số hiệu

- `id` là duy nhất (True). Định dạng id: số 91.0%, `vbpqta_*` (bản dịch) 6.4%, còn lại là UUID / tiền tố khác.
- Bỏ bản dịch, 101725 dòng có `so_ky_hieu` trùng với dòng khác (phần lớn là số hiệu ngắn của văn bản cũ hoặc địa phương, vd `01/CT`).
- Trong văn bản trung ương có tính quy phạm, 5062 dòng trùng cả số hiệu lẫn loại. → Không dùng `so_ky_hieu` làm khoá; id điều khoản phải gắn với `id` gốc khi trùng.

|     id | so_ky_hieu   | loai_van_ban       | ngay_ban_hanh   | tinh_trang_hieu_luc   |
|-------:|:-------------|:-------------------|:----------------|:----------------------|
|  80068 | 01 TC/CĐTC   | Thông tư           | 02/01/1988      | Còn hiệu lực          |
|  78128 | 01 TC/CĐTC   | Thông tư           | 09/01/1976      | Còn hiệu lực          |
|  78074 | 01 TT/LB     | Thông tư liên tịch | 08/01/1979      | Còn hiệu lực          |
|  80067 | 01 TT/LB     | Thông tư liên tịch | 04/01/1990      | Hết hiệu lực toàn bộ  |
|  75001 | 01-TC/HCP    | Thông tư           | 01/07/1959      | Còn hiệu lực          |
| 109390 | 01-TC/HCP    | Thông tư           | 07/01/1959      | Còn hiệu lực          |
|   8769 | 01-TC/KBNN   | Thông tư           | 07/01/1997      | Hết hiệu lực toàn bộ  |
| 109922 | 01-TC/KBNN   | Thông tư           | 06/01/1997      | Còn hiệu lực          |
|  11313 | 01-TC/TCT    | Thông tư           | 02/01/1991      | Ngưng hiệu lực        |
| 110394 | 01-TC/TCT    | Thông tư           | 01/01/1991      | Còn hiệu lực          |

## 5. Trường hiệu lực và độ tin cậy

Snapshot ngày 2026-07-23 (theo dataset card).

### 5.1 Phân bố

| tinh_trang_hieu_luc     |   số văn bản |
|:------------------------|-------------:|
| Hết hiệu lực toàn bộ    |        90721 |
| Còn hiệu lực            |        71619 |
| Hết hiệu lực một phần   |         5235 |
| Chưa xác định           |         3205 |
| Ngưng hiệu lực          |          373 |
| Không còn phù hợp       |          255 |
| Chưa có hiệu lực        |          146 |
| Ngưng hiệu lực một phần |            2 |

### 5.2 Kiểm tra nhất quán nội bộ (toàn bộ dataset)

| kiểm tra                                                  |   số lỗi |   trên tổng | tỉ lệ   |
|:----------------------------------------------------------|---------:|------------:|:--------|
| 'Hết hiệu lực toàn bộ' nhưng thiếu ngày hết hiệu lực      |    10760 |       90721 | 11.9%   |
| 'Còn hiệu lực' nhưng ngày hết hiệu lực ≤ snapshot         |        1 |       71619 | 0.0%    |
| 'Còn hiệu lực' nhưng có ngày hết hiệu lực (bất kì)        |      322 |       71619 | 0.4%    |
| 'Hết hiệu lực toàn bộ' nhưng ngày hết hiệu lực > snapshot |       18 |       90721 | 0.0%    |
| 'Chưa có hiệu lực' nhưng ngày có hiệu lực ≤ snapshot      |        2 |         146 | 1.4%    |
| Ngày có hiệu lực trước ngày ban hành                      |     3213 |      166627 | 1.9%    |
| Ngày hết hiệu lực trước ngày có hiệu lực                  |      121 |       79001 | 0.2%    |
| Thiếu ngày có hiệu lực                                    |     4929 |      171556 | 2.9%    |

### 5.3 Đối chiếu với đồ thị quan hệ (văn bản trung ương có tính quy phạm)

14913 văn bản bị một văn bản khác (đã có hiệu lực) *thay thế* hoặc *bãi bỏ/quy định hết hiệu lực*. Tình trạng ghi trong metadata của chúng:

| target_status         |   số văn bản |
|:----------------------|-------------:|
| Hết hiệu lực toàn bộ  |        12797 |
| Còn hiệu lực          |         1155 |
| Hết hiệu lực một phần |          958 |
| Không còn phù hợp     |            1 |
| Chưa xác định         |            1 |
| Chưa có hiệu lực      |            1 |

Lưu ý: quan hệ 'Bãi bỏ' trên vbpl.vn có thể chỉ bãi bỏ một phần, nên 'Hết hiệu lực một phần' không hẳn là lỗi; 'Còn hiệu lực' thì đáng ngờ.

### 5.4 Đối chiếu tay với một số luật đã biết

| văn bản                                                               | tình trạng (dataset)   | hiệu lực (dataset)   | hết HL (dataset)   | thực tế                                       | khớp                  |
|:----------------------------------------------------------------------|:-----------------------|:---------------------|:-------------------|:----------------------------------------------|:----------------------|
| 10/2012/QH13 (BLLĐ 2012)                                              | Hết hiệu lực toàn bộ   | 01/05/2013           | 01/01/2021         | Hết hiệu lực toàn bộ; 01/05/2013 → 01/01/2021 | ✓                     |
| 45/2019/QH14 (BLLĐ 2019)                                              | Hết hiệu lực một phần  | 01/01/2021           | nan                | Còn hiệu lực; 01/01/2021 → —                  | ✓                     |
| 45/2013/QH13 (Luật Đất đai 2013)                                      | Hết hiệu lực toàn bộ   | 01/07/2014           | 01/01/2025         | Hết hiệu lực toàn bộ; 01/07/2014 → 01/08/2024 | ✗ ngày hết            |
| 31/2024/QH15 (Luật Đất đai 2024, hiệu lực sớm theo Luật 43/2024/QH15) | Còn hiệu lực           | 01/01/2025           | nan                | Còn hiệu lực; 01/08/2024 → —                  | ✗ ngày HL             |
| 52/2014/QH13 (Luật HN&GĐ 2014)                                        | Còn hiệu lực           | 01/01/2015           | nan                | Còn hiệu lực; 01/01/2015 → —                  | ✓                     |
| 58/2014/QH13 (Luật BHXH 2014)                                         | Hết hiệu lực toàn bộ   | 01/01/2016           | 01/07/2025         | Hết hiệu lực toàn bộ; 01/01/2016 → 01/07/2025 | ✓                     |
| 41/2024/QH15 (Luật BHXH 2024)                                         | Hết hiệu lực toàn bộ   | 01/07/2025           | 01/01/2026         | Còn hiệu lực; 01/07/2025 → —                  | ✗ tình trạng,ngày hết |
| 23/2008/QH12 (Luật GTĐB 2008)                                         | Hết hiệu lực toàn bộ   | 01/07/2009           | nan                | Hết hiệu lực toàn bộ; 01/07/2009 → 01/01/2025 | ✗ ngày hết            |
| 36/2024/QH15 (Luật TTATGTĐB)                                          | Còn hiệu lực           | 01/01/2025           | nan                | Còn hiệu lực; 01/01/2025 → —                  | ✓                     |
| 68/2014/QH13 (Luật DN 2014)                                           | Hết hiệu lực toàn bộ   | 01/07/2015           | 01/01/2021         | Hết hiệu lực toàn bộ; 01/07/2015 → 01/01/2021 | ✓                     |
| 59/2020/QH14 (Luật DN 2020)                                           | Hết hiệu lực một phần  | 01/01/2021           | nan                | Còn hiệu lực; 01/01/2021 → —                  | ✓                     |
| 04/2007/QH12 (Luật thuế TNCN 2007 (tại 07/2026))                      | nan                    | nan                  | nan                | nan                                           | không tìm thấy        |

### 5.5 Đối chiếu với bản crawl cũ (`legacy_metadata`)

Bản cũ: 518,601 văn bản, ngày ban hành mới nhất 2026-03-16 (crawl trước bản hiện tại vài tháng), tiêu đề kiểu khác (vd 'Luật Đất đai 2024'), hệ id khác. Ghép theo số hiệu + ngày ban hành cho Luật/Bộ luật/NĐ/TT trung ương: 19,115/23,187 khớp.

| hiện tại   |   Expired |   In effect |   No longer applicable |   Undetermined |   Unknown |
|:-----------|----------:|------------:|-----------------------:|---------------:|----------:|
| expired    |      8682 |         289 |                    155 |              1 |         2 |
| in force   |      1958 |        7315 |                    578 |              0 |        16 |
| other      |        13 |          17 |                     88 |              0 |         1 |

Trên các cặp có trạng thái rõ ràng ở cả hai bên, tỉ lệ đồng ý: 87.7%. Luật/Bộ luật lệch nhau: 55.

| so_ky_hieu    | tinh_trang_hieu_luc   | ngay_het_hieu_luc   | effect_status   | effectless_date   | title_legacy                                                                                                                      |
|:--------------|:----------------------|:--------------------|:----------------|:------------------|:----------------------------------------------------------------------------------------------------------------------------------|
| 48/2014/QH13  | Hết hiệu lực toàn bộ  | nan                 | In effect       | nan               | Luật Giao thông đường thủy nội địa sửa đổi 2014                                                                                   |
| 71/2014/QH13  | Hết hiệu lực toàn bộ  | 01/07/2025          | In effect       | nan               | Luật sửa đổi các Luật về thuế 2014                                                                                                |
| 61/2014/QH13  | Hết hiệu lực một phần | nan                 | Expired         | 2026-06-30        | Luật Hàng không dân dụng Việt Nam sửa đổi 2014                                                                                    |
| 24/2000/QH10  | Hết hiệu lực một phần | nan                 | Expired         | 2022-12-31        | Luật Kinh doanh bảo hiểm 2000                                                                                                     |
| 87/2015/QH13  | Còn hiệu lực          | nan                 | Expired         | 2026-02-28        | Luật hoạt động giám sát của Quốc hội và Hội đồng nhân dân 2015                                                                    |
| 86/2015/QH13  | Hết hiệu lực một phần | nan                 | Expired         | 2026-06-30        | Luật an toàn thông tin mạng 2015                                                                                                  |
| 03/2007/QH12  | Hết hiệu lực một phần | nan                 | Expired         | 2026-06-30        | Luật Phòng, chống bệnh truyền nhiễm 2007                                                                                          |
| 94/2015/QH13  | Còn hiệu lực          | nan                 | Expired         | 2026-06-30        | Luật thi hành tạm giữ, tạm giam 2015                                                                                              |
| 106/2016/QH13 | Hết hiệu lực toàn bộ  | 01/07/2025          | In effect       | nan               | Luật thuế giá trị gia tăng, Luật thuế tiêu thụ đặc biệt và Luật quản lý thuế sửa đổi 2016                                         |
| 32/2013/QH13  | Hết hiệu lực một phần | nan                 | Expired         | 2025-09-30        | Luật thuế thu nhập doanh nghiệp sửa đổi năm 2013                                                                                  |
| 39/2019/QH14  | Hết hiệu lực một phần | nan                 | Expired         | 2024-12-31        | Luật Đầu tư công 2019                                                                                                             |
| 41/2024/QH15  | Hết hiệu lực toàn bộ  | 01/01/2026          | In effect       | nan               | Luật Bảo hiểm xã hội 2024                                                                                                         |
| 19/2008/QH12  | Hết hiệu lực một phần | nan                 | Expired         | 2015-06-30        | Nghị quyết số 19/2008/QH12 về việc thí điểm cho tổ chức, cá nhân nước ngoài mua và sở hữu nhà ở tại Việt Nam do Quốc hội ban hành |
| 64/2014/QH13  | Hết hiệu lực một phần | nan                 | Expired         | 2026-06-30        | Luật Thi hành án dân sự sửa đổi 2014                                                                                              |
| 62/2014/QH13  | Còn hiệu lực          | nan                 | Expired         | 2024-12-31        | Luật tổ chức Tòa án nhân dân 2014                                                                                                 |
| 29/2018/QH14  | Còn hiệu lực          | nan                 | Expired         | 2026-02-28        | Luật Bảo vệ bí mật nhà nước 2018                                                                                                  |
| 32/2009/QH12  | Còn hiệu lực          | nan                 | Expired         | 2025-06-30        | Luật di sản văn hóa sửa đổi 2009                                                                                                  |
| 58/2010/QH12  | Còn hiệu lực          | nan                 | Expired         | 2026-06-30        | Luật viên chức 2010                                                                                                               |
| 70/2006/QH11  | Hết hiệu lực một phần | nan                 | Expired         | 2020-12-31        | Luật Chứng khoán 2006                                                                                                             |
| 14/2008/QH12  | Hết hiệu lực một phần | nan                 | Expired         | 2025-09-30        | Luật Thuế thu nhập doanh nghiệp 2008                                                                                              |
| 78/2006/QH11  | Hết hiệu lực một phần | nan                 | Expired         | 2020-06-30        | Luật quản lý thuế 2006                                                                                                            |
| 73/2021/QH14  | Còn hiệu lực          | nan                 | Expired         | 2026-06-30        | Luật Phòng, chống ma túy 2021                                                                                                     |
| 36/2013/QH13  | Còn hiệu lực          | nan                 | Expired         | 2021-06-30        | Luật cư trú sửa đổi năm 2013                                                                                                      |
| 83/2007/QH11  | Còn hiệu lực          | nan                 | Expired         | 2015-12-31        | Luật tổ chức Quốc Hội sửa đổi 2007                                                                                                |
| 41/2019/QH14  | Còn hiệu lực          | nan                 | Expired         | 2026-06-30        | Luật Thi hành án hình sự 2019                                                                                                     |

## 6. Quan hệ giữa văn bản

- 1,033,255 cạnh, 31 nhãn. 4.2% cạnh trỏ tới văn bản không có trong metadata.
- Hai bộ nhãn trộn lẫn: nhãn hành động (doc_id tác động lên other) và nhãn vai trò (other là gì của doc_id). Chiều suy ra từ ngày ban hành rất rõ (gần 0% hoặc gần 100%), nên chuẩn hoá được về (actor → target) — xem `src/legalrag/ingest/relations.py`.
- Sau chuẩn hoá và bỏ trùng: 957,032 cạnh.
- Quan hệ ở mức **văn bản**, không có mức Điều/Khoản (không biết điều nào bị sửa).

|                                       |   số cạnh |   % doc_id ban hành sau other_doc_id | loại chuẩn   | chiều   |
|:--------------------------------------|----------:|-------------------------------------:|:-------------|:--------|
| Căn cứ                                |    668173 |                                 99.6 | based_on     | fwd     |
| Dẫn chiếu                             |     72554 |                                 99.3 | cites        | fwd     |
| Văn bản quy định hết hiệu lực         |     50939 |                                  0.1 | repeals      | rev     |
| Quy định chi tiết, hướng dẫn thi hành |     39419 |                                 99.2 | guides       | fwd     |
| Thay thế                              |     37146 |                                 99.5 | replaces     | fwd     |
| Văn bản HD, QĐ chi tiết               |     34392 |                                  0.4 | guides       | rev     |
| Bãi bỏ                                |     32479 |                                 99.5 | repeals      | fwd     |
| Văn bản căn cứ                        |     26515 |                                 99.5 | based_on     | fwd     |
| Sửa đổi, bổ sung                      |     17674 |                                 99.1 | amends       | fwd     |
| Văn bản bổ sung                       |     12853 |                                  0.4 | amends       | rev     |
| Văn bản hết hiệu lực                  |     12247 |                                100   | repeals      | fwd     |
| Văn bản sửa đổi                       |      7466 |                                  0.2 | amends       | rev     |
| Văn bản quy định hết hiệu lực 1 phần  |      6100 |                                  0.2 | repeals_part | rev     |
| Văn bản dẫn chiếu                     |      5715 |                                 98.5 | cites        | fwd     |
| Hợp nhất                              |      3930 |                                 99.7 | consolidates | fwd     |
| Văn bản được HD, QĐ chi tiết          |      1388 |                                 94.4 | guides       | fwd     |
| Hướng dẫn áp dụng                     |      1333 |                                 97.7 | guides       | fwd     |
| Văn bản bị hết hiệu lực 1 phần        |      1127 |                                 99   | repeals_part | fwd     |
| Văn bản được bổ sung                  |       532 |                                100   | amends       | fwd     |
| Văn bản liên quan khác                |       387 |                                 67.8 | nan          | nan     |
| Văn bản được sửa đổi                  |       284 |                                100   | amends       | fwd     |
| Đính chính                            |       209 |                                 75.1 | corrects     | fwd     |
| Tạm ngưng hiệu lực                    |       128 |                                100   | suspends     | fwd     |
| Giải thích                            |        98 |                                 99   | guides       | fwd     |
| Đình chỉ thi hành                     |        72 |                                100   | suspends     | fwd     |
| Bản dịch                              |        55 |                                 70.4 | nan          | nan     |
| Văn bản đình chỉ 1 phần               |        21 |                                  0   | suspends     | rev     |
| Văn bản đình chỉ                      |        16 |                                  0   | suspends     | rev     |
| Công bố                               |         1 |                                100   | nan          | nan     |
| Văn bản bị đình chỉ                   |         1 |                                nan   | suspends     | fwd     |
| Văn bản bị đình chỉ 1 phần            |         1 |                                nan   | suspends     | fwd     |

### Theo loại chuẩn

| rel          |   số cạnh |
|:-------------|----------:|
| based_on     |    694688 |
| cites        |     78269 |
| repeals      |     72499 |
| guides       |     43970 |
| replaces     |     37146 |
| amends       |     18497 |
| repeals_part |      7184 |
| consolidates |      3930 |
| other        |       443 |
| corrects     |       209 |
| suspends     |       197 |

## 7. Phạm vi theo lĩnh vực (ước lượng)

Cách chọn: luật gốc theo tên (Luật/Bộ luật/Pháp lệnh) → văn bản hướng dẫn / sửa đổi / thay thế / hợp nhất (hop 1) → văn bản hướng dẫn / sửa đổi hop 1 (hop 2) + văn bản cũ bị luật gốc thay thế (pred). Chỉ văn bản trung ương, có tính quy phạm. Xem `src/legalrag/ingest/domains.py`.

| lĩnh vực            |   tổng |   anchor |   hop1 |   hop2 |   pred |   còn HL (kể cả 1 phần) |   hết HL toàn bộ |   Luật |   NĐ |   TT/TTLT |   hợp nhất |   khác |
|:--------------------|-------:|---------:|-------:|-------:|-------:|------------------------:|-----------------:|-------:|-----:|----------:|-----------:|-------:|
| lao_dong            |    430 |        8 |    176 |    246 |      0 |                     227 |              188 |     15 |  138 |       232 |         15 |     30 |
| dat_dai             |    535 |        6 |    211 |    315 |      3 |                     262 |              257 |     23 |  105 |       298 |         20 |     89 |
| hon_nhan_gia_dinh   |     96 |        4 |     31 |     61 |      0 |                      34 |               50 |      7 |   32 |        38 |         12 |      7 |
| thue_tncn           |     99 |        4 |     21 |     74 |      0 |                      62 |               16 |      4 |   15 |        51 |         25 |      4 |
| giao_thong_duong_bo |    411 |        4 |    234 |    172 |      1 |                     108 |              281 |      7 |   63 |       270 |         24 |     47 |
| bhxh                |    163 |        3 |     69 |     90 |      1 |                      88 |               68 |     11 |   48 |        86 |          7 |     11 |
| doanh_nghiep        |    900 |        7 |    263 |    623 |      7 |                     413 |              416 |     21 |  229 |       460 |         79 |    111 |
| bhyt                |    109 |        2 |     61 |     46 |      0 |                      61 |               43 |      9 |   23 |        55 |          7 |     15 |
| nha_o               |    157 |        5 |     65 |     86 |      1 |                      54 |               82 |     12 |   32 |        82 |         21 |     10 |
| cu_tru              |     30 |        3 |     19 |      6 |      2 |                      13 |               16 |      6 |    6 |        13 |          1 |      4 |

**lao_dong** — luật gốc: Không số (1994, Hết hiệu lực toàn bộ); 35/2002/QH10 (2002, Hết hiệu lực toàn bộ); 74/2006/QH11 (2006, Hết hiệu lực toàn bộ); 84/2007/QH11 (2007, Hết hiệu lực toàn bộ); 10/2012/QH13 (2012, Hết hiệu lực toàn bộ); 38/2013/QH13 (2013, Hết hiệu lực toàn bộ); 45/2019/QH14 (2019, Hết hiệu lực một phần); 74/2025/QH15 (2025, Còn hiệu lực)

**dat_dai** — luật gốc: Không số (1987, Hết hiệu lực toàn bộ); Không số (1993, Hết hiệu lực toàn bộ); 10/1998/QH10 (1998, Hết hiệu lực toàn bộ); 13/2003/QH11 (2003, Hết hiệu lực toàn bộ); 45/2013/QH13 (2013, Hết hiệu lực toàn bộ); 31/2024/QH15 (2024, Còn hiệu lực)

**hon_nhan_gia_dinh** — luật gốc: Không số (1959, Hết hiệu lực toàn bộ); Không số (1986, Hết hiệu lực toàn bộ); 22/2000/QH10 (2000, Hết hiệu lực toàn bộ); 52/2014/QH13 (2014, Còn hiệu lực)

**thue_tncn** — luật gốc: 26/2012/QH13 (2012, Hết hiệu lực một phần); 03/VBHN-VPQH (2024, Chưa xác định); 109/2025/QH15 (2025, Hết hiệu lực một phần); 112/VBHN-VPQH (2026, Chưa xác định)

**giao_thong_duong_bo** — luật gốc: 26/2001/QH10 (2001, Hết hiệu lực toàn bộ); 23/2008/QH12 (2008, Hết hiệu lực toàn bộ); 35/2024/QH15 (2024, Còn hiệu lực); 36/2024/QH15 (2024, Còn hiệu lực)

**bhxh** — luật gốc: 71/2006/QH11 (2006, Hết hiệu lực toàn bộ); 58/2014/QH13 (2014, Hết hiệu lực toàn bộ); 41/2024/QH15 (2024, Hết hiệu lực toàn bộ)

**doanh_nghiep** — luật gốc: 13/1999/QH10 (1999, Hết hiệu lực toàn bộ); 60/2005/QH11 (2005, Hết hiệu lực toàn bộ); 37/2013/QH13 (2013, Hết hiệu lực toàn bộ); 68/2014/QH13 (2014, Hết hiệu lực toàn bộ); 59/2020/QH14 (2020, Hết hiệu lực một phần); 59/2020/QH14 (2020, Còn hiệu lực); 76/2025/QH15 (2025, Còn hiệu lực)

**bhyt** — luật gốc: 25/2008/QH12 (2008, Hết hiệu lực một phần); 46/2014/QH13 (2014, Hết hiệu lực một phần)

**nha_o** — luật gốc: 56/2005/QH11 (2005, Hết hiệu lực toàn bộ); 65/2014/QH13 (2014, Hết hiệu lực toàn bộ); 27/2023/QH15 (2023, Hết hiệu lực một phần); 27/VBHN-VPQH (2024, Chưa xác định); 14/VBHN-VPQH (2025, Chưa xác định)

**cu_tru** — luật gốc: 81/2006/QH11 (2006, Hết hiệu lực toàn bộ); 36/2013/QH13 (2013, Còn hiệu lực); 68/2020/QH14 (2020, Còn hiệu lực)
