| Tên cột       | Kiểu dữ liệu | Mô tả                                        | Ví dụ                   |
| ------------- | ------------ | -------------------------------------------- | ----------------------- |
| event_time    | TIMESTAMP    | Thời điểm xảy ra sự kiện (UTC)               | 2019-11-01 00:00:00 UTC |
| event_type    | VARCHAR      | Loại hành vi: view / cart / purchase         | view                    |
| product_id    | INT          | ID định danh sản phẩm                        | 1003461                 |
| category_id   | BIGINT       | ID danh mục (mã nội bộ, ít dùng trực tiếp)   | 2053013555631882655     |
| category_code | VARCHAR      | Tên danh mục dạng phân cấp, có thể NULL      | electronics.smartphone  |
| brand         | VARCHAR      | Tên thương hiệu, có thể NULL                 | xiaomi                  |
| price         | FLOAT        | Giá sản phẩm (USD), một số dòng = 0          | 489.07                  |
| user_id       | INT          | ID người dùng                                | 520088904               |
| user_session  | VARCHAR      | UUID định danh phiên làm việc của người dùng | 4d3b30da-a5e4-49df-...  |
