
from sqlalchemy import create_engine
import streamlit as st

@st.cache_resource
def get_engine():
    return create_engine('mysql+pymysql://root:Luongloc1210%40@localhost/warehouse')
