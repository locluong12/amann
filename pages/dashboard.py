import streamlit as st
import pandas as pd
import altair as alt
from database import get_engine

def show_dashboard():
    st.markdown("<h1 style='text-align: center;'>Warehouse Dashboard</h1>", unsafe_allow_html=True)

    engine = get_engine()
    with engine.begin() as conn:
        df_stock = pd.read_sql("SELECT material_no, description, stock, price, safety_stock FROM spare_parts", conn)
        total_import = pd.read_sql("SELECT SUM(quantity) AS total_import FROM import_export WHERE im_ex_flag = 1", conn).iloc[0]['total_import']
        total_export = pd.read_sql("SELECT SUM(quantity) AS total_export FROM import_export WHERE im_ex_flag = 0", conn).iloc[0]['total_export']

    total_items_in_stock = int(df_stock['stock'].sum())
    total_import = int(total_import) if total_import is not None else 0
    total_export = int(total_export) if total_export is not None else 0
    total_value_in_stock = (df_stock['stock'] * df_stock['price']).sum()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
            <div style="border: 2px solid #cccccc; border-radius: 15px; padding: 20px; text-align: center;
                        background-color: #f1f8ff; box-shadow: 2px 2px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">Total Inventory</div>
                <div style="font-size: 24px; color: #0072B5;">{total_items_in_stock}</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div style="border: 2px solid #cccccc; border-radius: 15px; padding: 20px; text-align: center;
                        background-color: #f1f8ff; box-shadow: 2px 2px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">Total Value</div>
                <div style="font-size: 24px; color: #0072B5;">${total_value_in_stock:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div style="border: 2px solid #cccccc; border-radius: 15px; padding: 20px; text-align: center;
                        background-color: #e8f5e9; box-shadow: 2px 2px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">Total Import</div>
                <div style="font-size: 24px; color: #388e3c;">{total_import}</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div style="border: 2px solid #cccccc; border-radius: 15px; padding: 20px; text-align: center;
                        background-color: #fff3e0; box-shadow: 2px 2px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">Total Export</div>
                <div style="font-size: 24px; color: #f57c00;">{total_export}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<h3 style='text-align: center;'>Stock Overview</h3>", unsafe_allow_html=True)
    stock_overview = df_stock.groupby('description').agg({'stock': 'sum'}).reset_index()
    stock_overview = stock_overview.sort_values('stock', ascending=False)
    chart_stock = alt.Chart(stock_overview).mark_bar().encode(
        x=alt.X('description:N', sort='-y'),
        y='stock:Q',
        tooltip=['description', 'stock']
    ).properties(width=800, height=400)
    st.altair_chart(chart_stock, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<h3 style='text-align: center;'>Nhập kho theo ngày</h3>", unsafe_allow_html=True)
        with engine.begin() as conn:
            df_import_history = pd.read_sql("SELECT date, quantity FROM import_export WHERE im_ex_flag = 1", conn)

        df_import_history['date'] = pd.to_datetime(df_import_history['date']).dt.date
        daily_imports = df_import_history.groupby('date')['quantity'].sum().reset_index()
        daily_imports = daily_imports.sort_values('date')
        daily_imports['date'] = daily_imports['date'].apply(lambda x: x.strftime('%d/%m/%Y'))

        chart_imports = alt.Chart(daily_imports).mark_bar(color="#4C78A8", cornerRadius=5).encode(
            x=alt.X('date:N', title='Ngày', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('quantity:Q', title='Số lượng nhập'),
            tooltip=['date:N', 'quantity:Q']
        ).properties(width=350, height=500)

        st.altair_chart(chart_imports, use_container_width=True)

    with col2:
        st.markdown("<h3 style='text-align: center;'>Xuất kho theo ngày</h3>", unsafe_allow_html=True)
        with engine.begin() as conn:
            df_export_history = pd.read_sql("SELECT date, quantity FROM import_export WHERE im_ex_flag = 0", conn)

        df_export_history['date'] = pd.to_datetime(df_export_history['date']).dt.date
        daily_exports = df_export_history.groupby('date')['quantity'].sum().reset_index()
        daily_exports = daily_exports.sort_values('date')
        daily_exports['date'] = daily_exports['date'].apply(lambda x: x.strftime('%d/%m/%Y'))

        chart_exports = alt.Chart(daily_exports).mark_bar(color="#F58518", cornerRadius=5).encode(
            x=alt.X('date:N', title='Ngày', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('quantity:Q', title='Số lượng xuất'), 
            tooltip=['date:N', 'quantity:Q']
        ).properties(width=350, height=500)

        st.altair_chart(chart_exports, use_container_width=True)

    st.markdown("<h3 style='text-align: center;'>Top 10 phụ tùng có giá trị tồn kho cao nhất</h3>", unsafe_allow_html=True)
    df_stock['total_value'] = df_stock['stock'] * df_stock['price']
    top10_value = df_stock.sort_values('total_value', ascending=False).head(10)

    chart_top10_vertical = alt.Chart(top10_value).mark_bar(
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6,
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color='#1E88E5', offset=0), alt.GradientStop(color='#90CAF9', offset=1)],
            x1=0, x2=0, y1=1, y2=0
        )
    ).encode(
        x=alt.X('description:N', sort='-y', title='Tên phụ tùng', axis=alt.Axis(labelAngle=-40)),
        y=alt.Y('total_value:Q', title='Tổng giá trị ($)', axis=alt.Axis(format=",.0f")),
        tooltip=[
            alt.Tooltip('description:N', title='Phụ tùng'),
            alt.Tooltip('stock:Q', title='Tồn kho'),
            alt.Tooltip('price:Q', title='Giá'),
            alt.Tooltip('total_value:Q', title='Tổng giá trị', format=",.0f")
        ]
    ).properties(width=800, height=400)

    st.altair_chart(chart_top10_vertical, use_container_width=True)   