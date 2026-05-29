import duckdb
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def get_conn():
    token = os.getenv("MOTHERDUCK_TOKEN") or st.secrets.get("MOTHERDUCK_TOKEN", "")
    return duckdb.connect(f"md:my_db?motherduck_token={token}")

def query(sql: str):
    conn = get_conn()
    return conn.execute(sql).df()
