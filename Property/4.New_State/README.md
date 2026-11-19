# 4 sơ đồ trạng thái mới

Mở `index.html` để xem cả bốn sơ đồ. Các bản vẽ mới nằm riêng trong `4.New_State`.

| Sơ đồ | Bản chèn báo cáo, có nhúng dữ liệu draw.io | Nguồn chỉnh sửa | Ảnh PNG |
|---|---|---|---|
| Khách hàng | `KH.drawio.svg` | `Nguon_drawio/KH.drawio` | `PNG/KH.png` |
| Nhà cung cấp | `NCC.drawio.svg` | `Nguon_drawio/NCC.drawio` | `PNG/NCC.png` |
| Phân loại sản phẩm | `PLSP.drawio.svg` | `Nguon_drawio/PLSP.drawio` | `PNG/PLSP.png` |
| Xác thực | `XT.drawio.svg` | `Nguon_drawio/XT.drawio` | `PNG/XT.png` |

SVG dùng chữ thật, nét vector và có thể mở trong diagrams.net. Tệp `.drawio` cho phép sửa từng trạng thái, nhãn và đường chuyển. PNG được xuất ở tỉ lệ 1,5 lần để chèn tài liệu.

## Cơ sở thiết kế

- Tài liệu `C:/Users/THANH NHAN/Downloads/Ch5.PhanTich (1).pdf`, các trang 44-49 và 52-54: vòng đời đối tượng; trạng thái có ý nghĩa trong một khoảng thời gian; đúng một nút khởi đầu; trạng thái cuối tùy phạm vi; sự kiện, điều kiện, hành động; thuộc tính trạng thái; quy ước xóa logic.
- Ảnh mẫu Đơn hàng do người dùng gửi: tên trạng thái in đậm, nghĩa tiếng Việt in nghiêng, khung bo góc, đường phân ngăn, nội dung xử lý trong trạng thái, nhãn chuyển màu xanh và ô ghi chú.
- Use case trong `1.Submit_UC`, sequence trong `2.Submit_SEQ`, activity trong `Property/Act/4 module`; đối chiếu mô hình hiện có trong `Property/STATE` và sequence Phiếu nhập trong `Property/SEQ/PN.drawio.svg`.

## Phạm vi và các quyết định mô hình

| Đối tượng | Thuộc tính phân tích đề xuất | Các giá trị loại trừ nhau |
|---|---|---|
| Hồ sơ khách hàng | `customerState` | `DRAFT`, `SAVED` |
| Nhà cung cấp | `supplierState` | `NO_PRODUCTS`, `SUPPLYING`, `INACTIVE` |
| Phân loại sản phẩm | `categoryState` | `UNUSED`, `IN_USE`, `INACTIVE` |
| Ngữ cảnh xác thực của NDHT | `authState` | `NOT_AUTHENTICATED`, `AUTHENTICATING`, `AUTHENTICATED`, `LOGOUT_CONFIRMATION` |

Đây là tên thuộc tính/giá trị đề xuất ở mức phân tích, không khẳng định có sẵn cột tương ứng trong CSDL. Với NCC/phân loại, số liên kết sản phẩm phân biệt hai trạng thái đang được sử dụng; `INACTIVE` là trạng thái đã chấm dứt sử dụng.

- **Khách hàng:** phân hệ hiện chỉ có tra cứu và cập nhật. Việc khởi tạo khách mới khi lập đơn kế thừa phạm vi đã ghi trong `Property/STATE/STATE-KH.mmd`; các UC/SEQ của phân hệ KH không mô tả riêng thao tác này. `DRAFT` là hồ sơ tạm, `SAVED` là hồ sơ đã lưu. Không tự thêm khóa, xóa hoặc kết thúc hồ sơ.
- **Nhà cung cấp:** tạo NCC chưa có liên kết sản phẩm; liên kết đầu tiên chuyển sang `SUPPLYING`; bỏ liên kết cuối hợp lệ trở lại `NO_PRODUCTS`. Chỉ vô hiệu hóa khi không còn liên kết SP và chưa có phiếu nhập, theo ACT-NCC/mô hình hiện có. SP đưa vào phiếu nhập phải thuộc NCC.
- **Phân loại sản phẩm:** gán SP đầu tiên/bỏ SP cuối là biến cố từ phân hệ Sản phẩm; phải tuân thủ quyền và ràng buộc của phân hệ đó. Không vô hiệu hóa phân loại còn SP liên kết.
- **Xác thực:** đối tượng được mô hình là ngữ cảnh xác thực của NDHT, không phải vòng đời tài khoản. Hai nhánh khi kiểm tra xong là các chuyển hoàn tất có điều kiện. Đăng xuất xóa phiên và trở lại chưa đăng nhập; hủy đăng xuất giữ nguyên phiên. Không tự thêm khóa tài khoản, giới hạn số lần sai, OTP hoặc hết hạn phiên.
- **Xóa logic:** là quyết định thiết kế áp dụng gợi ý trang 49. Nút cuối của NCC/phân loại thể hiện kết thúc vòng đời sử dụng, không có nghĩa xóa vật lý bản ghi; chưa mô hình khôi phục do nguồn hiện có không quy định.

Các thao tác không đổi trạng thái nằm trong ngăn xử lý nội bộ. Quyền của tác nhân và cách xử lý khi thông tin không hợp lệ được ghi trong sơ đồ. Không dùng các bước mở danh sách/hiển thị màn hình như các trạng thái của thực thể nghiệp vụ.

## Bản xem bổ sung

`Tuong_tac/*.html` là bản xem luồng rút gọn do Archify tạo, có phóng to và xuất hình; phần xử lý nội bộ được đưa xuống các thẻ mô tả. Với KH, cập nhật được thể hiện bằng vòng lặp để bản xem không đánh dấu SAVED thành kết thúc; ký pháp xử lý nội bộ chính thức nằm ở bản SVG. Thanh công cụ của bản xem bổ sung dùng tiếng Anh vì Archify chưa có bộ dịch tiếng Việt tích hợp.

`.source` chứa dữ liệu, mã tạo bản vẽ và biên bản kiểm tra. Không cần thư mục này khi chèn SVG/PNG vào báo cáo.

## Kiểm tra đã thực hiện

Cả bốn SVG đã được kiểm tra XML, dấu tiếng Việt, chữ trong khung, nhãn không che đường chuyển, đường đi vuông góc và không xuyên trạng thái khác; đã xuất PNG và xem lại ảnh cuối. Cả bốn nguồn `.drawio` đã được nhập và dựng bằng bộ hiển thị chính thức của diagrams.net; đã xem trực tiếp thêm bản NCC và XT. Trang tổng hợp đã được kiểm tra liên kết và độ rộng ở màn hình 1440px/760px. Bốn bản xem Archify đã qua các bước kiểm tra tự động; cảnh báo còn lại là thanh công cụ dự phòng tiếng Anh đã nêu trên.
