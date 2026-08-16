import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Investment Dashboard",
    page_icon="📈",
    layout="wide",
)

# 🔗 วางลิงก์ CSV จาก Google Sheets ของคุณที่นี่
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS7u4PJQHrPLgKoCb28f_C4C862tgiMWlXEYkxbjUfipmuKZVG6JhI2vQbMLFPRogMdoSu8v-4eO1k-/pub?gid=11095553&single=true&output=csv"


@st.cache_data(ttl=60)  # ดึงข้อมูลใหม่ทุกๆ 1 นาที
def load_data():
  return pd.read_csv(SHEET_URL)


st.title("🚀 INVESTMENT DASHBOARD")

try:
  df = load_data()

  # คํานวณผลตอบแทน %
  df["Profit_Pct"] = (
      df["Profit_THB"] / (df["Value_THB"] - df["Profit_THB"])
  ) * 100

  total_value = df["Value_THB"].sum()
  total_profit = df["Profit_THB"].sum()
  total_cost = total_value - total_profit
  total_return = (total_profit / total_cost) * 100 if total_cost != 0 else 0

  # สรุปผล
  c1, c2, c3, c4 = st.columns(4)
  c1.metric("มูลค่าพอร์ตรวม", f"฿{total_value:,.2f}")
  c2.metric("เงินต้นรวม", f"฿{total_cost:,.2f}")
  c3.metric("กำไร/ขาดทุนรวม", f"฿{total_profit:,.2f}", f"{total_return:.2f}%")
  c4.metric(
      "บรรยากาศพอร์ต", "🟢 เขียวขจี" if total_profit > 0 else "🔴 แดงเดือด"
  )

  st.divider()

  # กราฟ
  col1, col2 = st.columns(2)
  with col1:
    st.subheader("📊 สัดส่วนพอร์ต")
    fig_pie = px.pie(df, values="Value_THB", names="Asset", hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

  with col2:
    st.subheader("📈 ผลตอบแทน %")
    df["Color"] = df["Profit_Pct"].apply(
        lambda x: "#10B981" if x >= 0 else "#EF4444"
    )
    fig_bar = px.bar(
        df,
        x="Asset",
        y="Profit_Pct",
        text_auto=".2f",
        color="Color",
        color_discrete_map="identity",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

except Exception as e:
  st.error("กรุณาตรวจสอบลิงก์ Google Sheets หรือโครงสร้างข้อมูลครับ")
