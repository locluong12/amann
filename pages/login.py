import streamlit as st

# Hàm kiểm tra thông tin đăng nhập
def check_login(username, password):
    return username == "admin" and password == "12345"

# Hàm hiển thị trang đăng nhập
def login_page():
    # Căn giữa tiêu đề
    st.markdown("<h1 style='text-align: center;'>Login Page</h1>", unsafe_allow_html=True)

    # Tạo cột để căn giữa
    col1, col2, col3 = st.columns([1, 6, 1])  # Điều chỉnh tỷ lệ cột cho hợp lý
    with col2:
        # Tạo input cho tên người dùng và mật khẩu
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        # Hiển thị nút Login
        if st.button("Login"):
            if check_login(username, password):
                # Đánh dấu người dùng đã đăng nhập thành công
                st.session_state["authenticated"] = True
                st.success("Login successful")
                # Tự động reload ứng dụng khi đăng nhập thành công
                st.rerun()
            else:
                st.error("Invalid username or password")

# Gọi hàm login_page khi chạy ứng dụng
if __name__ == "__main__":
    login_page()
