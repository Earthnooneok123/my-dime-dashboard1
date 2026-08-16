import pandas as pd
import plotly.express as px
import streamlit as st

# ตั้งค่าหน้าตา Dashboard
st.set_page_config(
    page_title="Investment Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS เพื่อความสวยงาม
st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: bold; }
    </style>
""",
    unsafe_allow_html=True,
)

# 🔗 ลิงก์ CSV จาก Google Sheets ของคุณ
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS7u4PJQHrPLgKoCb28f_C4C862tgiMWlXEYkxbjUfipmuKZVG6JhI2vQbMLFPRogMdoSu8v-4eO1k-/pub?gid=11095553&single=true&output=csv"


@st.cache_data(ttl=60)  # ดึงข้อมูลใหม่จาก Google Sheets ทุกๆ 1 นาที
def load_data():
  return pd.read_csv(SHEET_URL)


st.title("🚀 INVESTMENT DASHBOARD")
st.caption("ดึงข้อมูลโดยตรงจาก Google Sheets อัปเดตเรียลไทม์")
st.divider()

try:
  df = load_data()

  # คัดกรองเอาเฉพาะแถวที่มีข้อมูลสินทรัพย์จริงๆ (ตัดแถว 'รวมทั้งหมด' หรือแถวว่างออก)
  df = df.dropna(subset=["Asset"])
  df = df[
      ~df["Asset"].str.contains("รวม", na=False)
  ]  # ป้องกันแถวรวมสะสมกระทบการคำนวณ

  # แปลงคอลัมน์ตัวเลขให้แน่ใจว่าเป็น numeric
  df["Value_THB"] = pd.to_numeric(df["Value_THB"], errors="coerce").fillna(0)
  df["Profit_THB"] = pd.to_numeric(df["Profit_THB"], errors="coerce").fillna(0)

  # คำนวณผลตอบแทน %
  df["Cost_THB"] = df["Value_THB"] - df["Profit_THB"]
  df["Profit_Pct"] = df.apply(
      lambda r: (r["Profit_THB"] / r["Cost_THB"] * 100)
      if r["Cost_THB"] != 0
      else 0,
      axis=1,
  )

  # สรุปภาพรวมพอร์ต
  total_value = df["Value_THB"].sum()
  total_profit = df["Profit_THB"].sum()
  total_cost = total_value - total_profit
  total_return = (total_profit / total_cost * 100) if total_cost != 0 else 0

  # Summary Cards
  col1, col2, col3, col4 = st.columns(4)
  col1.metric("มูลค่าพอร์ตรวม", f"฿{total_value:,.2f}")
  col2.metric("เงินต้นรวม", f"฿{total_cost:,.2f}")
  col3.metric("กำไร/ขาดทุนรวม", f"฿{total_profit:,.2f}", f"{total_return:.2f}%")
  col4.metric(
      "บรรยากาศพอร์ต", "🟢 เขียวขจี" if total_profit >= 0 else "🔴 แดงเดือด"
  )

  st.divider()

  # กราฟแสดงผล
  c1, c2 = st.columns(2)

  with c1:
    st.subheader("📊 สัดส่วนพอร์ต (Donut Chart)")
    fig_pie = px.pie(
        df,
        values="Value_THB",
        names="Asset",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_pie.update_traces(textinfo="percent+label")
    fig_pie.update_layout(showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

  with c2:
    st.subheader("📈 ผลตอบแทน % รายสินทรัพย์")
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
    fig_bar.update_layout(yaxis_title="กำไร (%)", xaxis_title="")
    st.plotly_chart(fig_bar, use_container_width=True)

  st.divider()

  # แสดงตารางข้อมูลจาก Google Sheets
  st.subheader("📋 ข้อมูลปัจจุบันใน Google Sheets")
  st.dataframe(
      df[["Asset", "Category", "Value_THB", "Profit_THB", "Profit_Pct"]],
      column_config={
          "Asset": "สินทรัพย์",
          "Category": "หมวดหมู่",
          "Value_THB": st.column_config.NumberColumn(
              "มูลค่า (บาท)", format="฿%.2f"
          ),
          "Profit_THB": st.column_config.NumberColumn(
              "กำไร/ขาดทุน (บาท)", format="฿%.2f"
          ),
          "Profit_Pct": st.column_config.NumberColumn(
              "กำไร (%)", format="%.2f%%"
          ),
      },
      use_container_width=True,
      hide_index=True,
  )

except Exception as e:
  st.error(
      f"เกิดข้อผิดพลาดในการโหลดข้อมูลจาก Google Sheets: {e}\nกรุณาตรวจสอบว่าเลือกเผยแพร่ไฟล์เป็นรูปแบบ"
      " .csv หรือยังครับ"
  )
