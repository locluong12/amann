import streamlit as st
import streamlit.components.v1 as components

# --- Cấu hình trang ---
st.set_page_config(page_title="Quản lý kho phụ tùng", page_icon="📦", layout="wide")

# --- Biến cấu hình ---
ADMIN_PIN = "111222"

# --- Ẩn sidebar khi chưa đăng nhập ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False
if "selected_menu" not in st.session_state:
    st.session_state.selected_menu = "Quản lý kho"
if "selected_sub_menu" not in st.session_state:
    st.session_state.selected_sub_menu = "Tồn kho"

if not st.session_state.authenticated:
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none;
        }
        .appview-container .main {
            margin-left: 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    from pages.login import login_page
    login_page()
    st.stop()

# --- Style sidebar chữ trắng, nền tối và các style tuỳ biến khác ---
st.markdown("""
<style>
    html, body {
        background-color: #000000 !important;
        margin: 0;
        padding: 0;
        height: 100%;
        color: white !important;
    }
    .main, .block-container, .stApp {
        background-color: #000000 !important;
        min-height: 100vh;
        padding-top: 0 !important;
        margin-top: 0 !important;
        color: white !important;
    }
    header, div.block-container > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
        background-color: #000000 !important;
    }
    section[data-testid="stSidebar"] { 
        background-color: #222 !important; 
        color: white !important; 
    }
    section[data-testid="stSidebar"] * { 
        color: white !important; 
    }
    .stSidebar .stTextInput input { 
        color: white !important; 
        background-color: #1a1a1a !important; 
    }
    .stSidebar .stTextInput input::placeholder { 
        color: #bbb !important; 
    }
    div[data-baseweb="select"] > div { 
        background-color: #2a9d8f !important; 
        color: white !important; 
    }
    div[data-baseweb="select"] > div:hover { 
        background-color: #2a9d8f !important; 
    }
    .stButton > button { 
        background-color: #2a9d8f; 
        color: white; 
        border-radius: 8px; 
        font-weight: bold; 
        width: 100%; 
        border: none;
    }
    .stButton > button:hover { 
        background-color: #2a9d8f; 
        color: white;
    }
    .stButton.active > button { 
        background-color: #2a9d8f !important; 
    }
    h1 { 
        font-size: 28px; 
        text-align: center; 
        color: white; 
        padding-top: 50px; 
    }
</style>
""", unsafe_allow_html=True)

# Ẩn sidebar mặc định của Streamlit multi-page
st.markdown("""<style>[data-testid="stSidebarNav"] { display: none; }</style>""", unsafe_allow_html=True)

# --- MENU chính ---
menu = st.sidebar.selectbox(
    "",
    ["Quản lý kho", "Quản lý hệ thống"],
    index=["Quản lý kho", "Quản lý hệ thống"].index(st.session_state.selected_menu)
)

if menu != st.session_state.selected_menu:
    st.session_state.selected_menu = menu
    st.session_state.selected_sub_menu = (
        "Xem tồn kho" if menu == "Quản lý kho" else "Quản lý nhân viên"
    )
    st.rerun()

# --- SUB MENU: Quản lý kho ---
if menu == "Quản lý kho":
    sub_menus = ["Tồn kho", "Nhập kho", "Xuất kho", "Thống kê"]
    for sub in sub_menus:
        if st.sidebar.button(sub, key=sub, type="primary" if st.session_state.selected_sub_menu == sub else "secondary"):
            st.session_state.selected_sub_menu = sub
            st.rerun()

    if st.session_state.selected_sub_menu == "Tồn kho":
        from pages.view_stock import show_view_stock
        show_view_stock()
    elif st.session_state.selected_sub_menu == "Nhập kho":
        from pages.import_stock import show_material_page
        show_material_page()
    elif st.session_state.selected_sub_menu == "Xuất kho":
        from pages.export_stock import show_export_stock
        show_export_stock()
    elif st.session_state.selected_sub_menu == "Thống kê":
        from pages.dashboard import show_dashboard
        show_dashboard()

# --- SUB MENU: Quản lý hệ thống ---
elif menu == "Quản lý hệ thống":
    if not st.session_state.admin_authenticated:
        st.sidebar.markdown("### Nhập mã PIN để truy cập")
        input_pin = st.sidebar.text_input("Mã PIN", type="password")
        if st.sidebar.button("Xác nhận"):
            if input_pin == ADMIN_PIN:
                st.session_state.admin_authenticated = True
                st.success("✅ Truy cập thành công!")
                st.rerun()
            else:
                st.sidebar.error("❌ Sai mã PIN.")
        st.stop()

    sub_menus = ["Quản lý nhân viên", "Quản lý máy móc"]
    for sub in sub_menus:
        if st.sidebar.button(sub, key=sub, type="primary" if st.session_state.selected_sub_menu == sub else "secondary"):
            st.session_state.selected_sub_menu = sub
            st.rerun()

    if st.session_state.selected_sub_menu == "Quản lý nhân viên":
        from pages.employees import show_employees
        show_employees()
    elif st.session_state.selected_sub_menu == "Quản lý máy móc":
        from pages.machine import show_machine_page
        show_machine_page()

    # --- Nút thoát quyền quản lý ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Thoát quyền quản lý"):
        st.session_state.admin_authenticated = False
        st.session_state.selected_menu = "Quản lý kho"
        st.session_state.selected_sub_menu = "Xem tồn kho"
        st.rerun()
