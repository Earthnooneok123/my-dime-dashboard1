import re
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# ตั้งค่าหน้าตา Dashboard
st.set_page_config(page_title="AI Virtual Office", page_icon="🏢", layout="wide")

# CSS จัดโซนโต๊ะทำงาน
st.markdown("""
    <style>
    .office-zone { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border: 2px solid #ddd; margin-bottom: 20px; }
    .stMetric { background-color: white; padding: 10px; border-radius: 10px; box-shadow: 2px 2px 5px #ccc; }
    </style>
""", unsafe_allow_html=True)

# ฟังก์ชันข้อมูล
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS7u4PJQHrPLgKoCb28f_C4C862tgiMWlXEYkxbjUfipmuKZVG6JhI2vQbMLFPRogMdoSu8v-4eO1k-/pub?gid=11095553&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(): return pd.read_csv(SHEET_URL)

def clean_currency(val):
    if pd.isna(val): return 0.0
    return float(re.sub(r"[฿\$,\s]", "", str(val)))

try:
    df = load_data()
    df = df.dropna(subset=["Asset"])
    df["Value_THB"] = df["Value_THB"].apply(clean_currency)
    df["Profit_THB"] = df["Profit_THB"].apply(clean_currency)
    df["Cost_THB"] = df["Value_THB"] - df["Profit_THB"]
    df["Profit_Pct"] = df.apply(lambda r: (r["Profit_THB"] / r["Cost_THB"] * 100) if r["Cost_THB"] != 0 else 0, axis=1)

    # Sidebar
    st.sidebar.title("🏢 BOSS CONTROL")
    st.sidebar.image("https://media.giphy.com/media/xTiTnHvXHHxOTcdmxO/giphy.gif", width=150)
    st.sidebar.markdown("---")
    selected_cat = st.sidebar.selectbox("เลือกโซนงาน:", ["ทั้งหมด"] + list(df["Category"].dropna().unique()))

    # หน้าหลัก
    st.title("💻 AI Virtual Office HQ")
    
    # แบ่งโซนทำงาน (เหมือนภาพเรฟ)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🛠️ Dev Agent Zone")
        st.write("สถานะ: กำลัง Optimization ระบบพอร์ต")
        st.metric("Total Assets", f"฿{df['Value_THB'].sum():,.0f}")
        
    with col2:
        st.subheader("📊 Research Agent Zone")
        st.write("สถานะ: วิเคราะห์แนวโน้มตลาด...")
        if not df.empty:
            top = df.loc[df['Profit_Pct'].idxmax()]
            st.success(f"Best: {top['Asset']} (+{top['Profit_Pct']:.1f}%)")
            
    with col3:
        st.subheader("🛡️ Security Agent Zone")
        st.write("สถานะ: ปกป้องพอร์ต (Spider-Man Ready)")
        st.metric("Profit", f"฿{df['Profit_THB'].sum():,.0f}")

    st.divider()

    # กราฟ
    chart1, chart2 = st.columns(2)
    with chart1:
        st.plotly_chart(px.pie(df, values="Value_THB", names="Asset", title="Asset Allocation"), use_container_width=True)
    with chart2:
        st.plotly_chart(px.bar(df, x="Asset", y="Profit_Pct", title="Performance per Asset"), use_container_width=True)

    st.subheader("📋 ตารางบันทึกงาน")
    st.dataframe(df[["Asset", "Category", "Value_THB", "Profit_Pct"]], use_container_width=True)

except Exception as e:
    st.error("ออฟฟิศยังไม่เปิดทำการ: " + str(e))
