import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from sqlalchemy import text
from database import get_engine

def load_machines(engine, selected_group, selected_pos, search_name):
    query = """
    SELECT g.mc_name AS group_mc_name,
           m.name AS machine_name,
           mp.mc_pos AS machine_pos
    FROM machine m
    JOIN group_mc g ON m.group_mc_id = g.id
    LEFT JOIN machine_pos mp ON m.group_mc_id = mp.mc_id
    WHERE (:group_name = 'Tất cả' OR g.mc_name = :group_name)
      AND (:pos = 'Tất cả' OR mp.mc_pos = :pos)
      AND (:search_name = '' OR m.name LIKE :search_name)
    ORDER BY m.name DESC
    LIMIT 1000
    """
    df = pd.read_sql_query(text(query), engine, params={
        "group_name": selected_group,
        "pos": selected_pos,
        "search_name": f"%{search_name}%"
    })
    return df

def show_machine_page():
    st.markdown("<h1 style='text-align: center;'>Quản lý máy móc</h1>", unsafe_allow_html=True)
    engine = get_engine()

    with engine.connect() as conn:
        group_list = conn.execute(text("SELECT mc_name FROM group_mc")).scalars().all()
        pos_list = conn.execute(text("SELECT DISTINCT mc_pos FROM machine_pos WHERE mc_pos IS NOT NULL")).scalars().all()

        group_data = conn.execute(text("SELECT id, mc_name FROM group_mc")).fetchall()
        group_name_to_id = {g.mc_name: g.id for g in group_data}

    # ======== State mặc định ========
    if 'search_name' not in st.session_state:
        st.session_state.search_name = ""
    if 'reload_machines' not in st.session_state:
        st.session_state.reload_machines = False
    st.markdown("""
        <style>
        /* Đổi màu chữ tiêu đề tab (tab labels) sang trắng */
        div[role="tablist"] button[role="tab"] {
            color: white !important;
        }

        /* Đổi màu chữ label input sang trắng */
        label, .css-1v0mbdj.e1fqkh3o3 {
            color: white !important;
        }

        /* Đổi màu chữ tiêu đề và text input */
        .stTextInput label, .stSelectbox label, .stDateInput label, .stTextArea label {
            color: white !important;
        }

        /* Đổi màu chữ tiêu đề và input trong dataframe (nếu cần) */
        div[data-testid="stDataFrameContainer"] {
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)
    # ======== Bộ lọc ngang ========
    col1, col2 = st.columns([2, 2])

    with col1:
        search_name = st.text_input("🔍 Tìm theo tên máy:", value=st.session_state.search_name)
        st.session_state.search_name = search_name

    with col2:
        selected_group = st.selectbox("Nhóm máy", ["Tất cả"] + group_list)

    # ======== Làm mới dữ liệu sau khi thêm máy ========
    if st.session_state.reload_machines:
        st.session_state.reload_machines = False

    # ======== Lấy danh sách máy ========
    df = load_machines(engine, selected_group, "Tất cả", search_name)

    st.subheader("📋 Danh sách máy")
    if not df.empty:
        # Hiển thị dữ liệu dưới dạng bảng
        st.dataframe(df)  # Hiển thị bảng dữ liệu với cột máy và vị trí

        
       
    # ======== Thêm máy mới ========
    st.markdown("---")
    st.subheader("➕ Thêm máy mới")

    # Chỉ cho phép thêm 1 máy
    with st.form("add_machine_form"):
        new_name = st.text_input(" Tên máy mới")
        selected_group_new = st.selectbox(" Nhóm máy", list(group_name_to_id.keys()))
        new_pos = st.text_input(" Vị trí máy mới")
        st.markdown("""
            <style>
            /* CSS cho button trong form_submit_button */
            form div.stButton > button {
                background-color: #008080 !important;  /* xanh ngọc */
                color: white !important;
                font-weight: bold !important;
                border: none !important;
            }

            form div.stButton > button:hover {
                background-color: #006666 !important; /* đậm hơn khi hover */
                color: white !important;
            }
            </style>
            """, unsafe_allow_html=True)
        st.markdown("""
            <style>
            div.stDownloadButton > button:first-child {
                background-color: #20c997;
                color: white;
                border: none;
            }
            div.stDownloadButton > button:first-child:hover {
                background-color: #17a2b8;
                color: white;
            }
            </style>
            """, unsafe_allow_html=True)








        submitted = st.form_submit_button("Thêm máy")

        if submitted:
            if not new_name.strip() or not new_pos.strip():
                st.warning("⚠️ Vui lòng nhập đầy đủ tên máy và vị trí.")
            else:
                try:
                    with engine.begin() as conn:
                        group_id = group_name_to_id[selected_group_new]
                        dept_id_default = 1

                        insert_machine = text(""" 
                            INSERT INTO machine (name, group_mc_id, dept_id) 
                            VALUES (:name, :group_id, :dept_id) 
                        """)
                        result = conn.execute(insert_machine, {
                            "name": new_name.strip(),
                            "group_id": group_id,
                            "dept_id": dept_id_default
                        })
                        machine_id = result.lastrowid

                        insert_pos = text(""" 
                            INSERT INTO machine_pos (mc_id, mc_pos) 
                            VALUES (:mc_id, :mc_pos) 
                        """)
                        conn.execute(insert_pos, {
                            "mc_id": machine_id,
                            "mc_pos": new_pos.strip()
                        })

                    st.success(f"✅ Đã thêm máy: {new_name} với vị trí: {new_pos}")
                    st.session_state.reload_machines = True
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi khi thêm máy: {e}")
