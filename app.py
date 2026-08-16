import re
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# ตั้งค่าหน้าตา Dashboard
st.set_page_config(
    page_title="Pixel Virtual Office Dashboard",
    page_icon="🕹️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS ตกแต่งเพิ่มเติม
st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1rem; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: bold; }
    .office-banner { border-radius: 12px; overflow: hidden; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    </style>
""",
    unsafe_allow_html=True,
)

# 🔗 ลิงก์ CSV จาก Google Sheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS7u4PJQHrPLgKoCb28f_C4C862tgiMWlXEYkxbjUfipmuKZVG6JhI2vQbMLFPRogMdoSu8v-4eO1k-/pub?gid=11095553&single=true&output=csv"


@st.cache_data(ttl=60)
def load_data():
  return pd.read_csv(SHEET_URL)


def clean_currency(val):
  if pd.isna(val):
    return 0.0
  val_str = str(val)
  clean_str = re.sub(r"[฿\$,\s]", "", val_str)
  try:
    return float(clean_str)
  except ValueError:
    return 0.0


try:
  df = load_data()
  df = df.dropna(subset=["Asset"])
  df = df[~df["Asset"].str.contains("รวม", na=False)]

  df["Value_THB"] = df["Value_THB"].apply(clean_currency)
  df["Profit_THB"] = df["Profit_THB"].apply(clean_currency)
  df["Cost_THB"] = df["Value_THB"] - df["Profit_THB"]
  df["Profit_Pct"] = df.apply(
      lambda r: (r["Profit_THB"] / r["Cost_THB"] * 100)
      if r["Cost_THB"] != 0
      else 0,
      axis=1,
  )

  # Sidebar (ยังคงความคูลของ Spiderman ไว้เหมือนเดิม)
  st.sidebar.header("⚙️ ตั้งค่า & คัดกรอง")
  if st.sidebar.button("🔄 อัปเดตข้อมูลทันที"):
    st.cache_data.clear()
    st.rerun()

  categories = ["ทั้งหมด"] + list(df["Category"].dropna().unique())
  selected_cat = st.sidebar.selectbox("เลือกหมวดหมู่:", categories)

  st.sidebar.markdown("---")
  st.sidebar.markdown("### 🕸️ Security Guard")
  st.sidebar.image(
      "https://media.giphy.com/media/xTiTnHvXHHxOTcdmxO/giphy.gif", width=200
  )

  df_display = (
      df[df["Category"] == selected_cat]
      if selected_cat != "ทั้งหมด"
      else df.copy()
  )

  # Calculation
  total_value = df_display["Value_THB"].sum()
  total_profit = df_display["Profit_THB"].sum()
  total_cost = total_value - total_profit
  total_return = (total_profit / total_cost * 100) if total_cost != 0 else 0

  # --- MAIN CONTENT ---
  st.title("🕹️ PIXEL VIRTUAL OFFICE & INVESTMENT DASHBOARD")
  st.caption(f"🕒 ข้อมูลล่าสุด: {datetime.now().strftime('%d %b %Y, %H:%M')}")
  st.divider()

  # 🏢 ฝังฉากห้องทำงาน Pixel Art แบบเคลื่อนไหว (Virtual Office Banner)
  # ใช้วิดีโอ/แอนิเมชันห้องทำงานจำลองเพื่อให้ได้บรรยากาศแบบในเรฟ
  st.markdown(
      """
        <div class="office-banner">
            <iframe src="https://giphy.com/embed/3oKIPnAiaMCws8nOsE" width="100%" height="280" style="border:none;" allowFullScreen></iframe>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # Progress
  GOAL_AMOUNT = 500000.0
  progress_pct = min(total_value / GOAL_AMOUNT, 1.0)
  st.subheader("🎯 เป้าหมายพอร์ตระยะยาว (500,000 บาท)")
  st.progress(progress_pct)
  st.caption(
      f"ความคืบหน้า: {progress_pct*100:.2f}% (ขาดอีก"
      f" ฿{max(GOAL_AMOUNT - total_value, 0):,.2f} บาท)"
  )
  st.divider()

  # Metrics
  c1, c2, c3, c4 = st.columns(4)
  c1.metric("มูลค่าพอร์ตรวม", f"฿{total_value:,.2f}")
  c2.metric("เงินต้นรวม", f"฿{total_cost:,.2f}")
  c3.metric("กำไร/ขาดทุนรวม", f"฿{total_profit:,.2f}", f"{total_return:.2f}%")
  c4.metric(
      "บรรยากาศพอร์ต", "🟢 เขียวขจี" if total_profit >= 0 else "🔴 แดงเดือด"
  )

  # Top Performer
  if not df_display.empty:
    top_asset = df_display.loc[df_display["Profit_Pct"].idxmax()]
    st.info(f"🏆 **ตัวแบกพอร์ต:** {top_asset['Asset']} (+{top_asset['Profit_Pct']:.2f}%)")

  # Charts
  chart1, chart2 = st.columns(2)
  with chart1:
    st.subheader("📊 สัดส่วนพอร์ต")
    fig_pie = px.pie(
        df_display,
        values="Value_THB",
        names="Asset",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    st.plotly_chart(fig_pie, use_container_width=True)
  with chart2:
    st.subheader("📈 ผลตอบแทน %")
    df_display["Color"] = df_display["Profit_Pct"].apply(
        lambda x: "#10B981" if x >= 0 else "#EF4444"
    )
    fig_bar = px.bar(
        df_display,
        x="Asset",
        y="Profit_Pct",
        text_auto=".2f",
        color="Color",
        color_discrete_map="identity",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

  # Table
  st.subheader("📋 รายละเอียดสินทรัพย์")
  st.dataframe(
      df_display[["Asset", "Category", "Value_THB", "Profit_THB", "Profit_Pct"]],
      column_config={
          "Value_THB": st.column_config.NumberColumn(format="฿%.2f"),
          "Profit_THB": st.column_config.NumberColumn(format="฿%.2f"),
          "Profit_Pct": st.column_config.NumberColumn(format="%.2f%%"),
      },
      use_container_width=True,
      hide_index=True,
  )

except Exception as e:
  st.error(f"เกิดข้อผิดพลาด: {e}")
