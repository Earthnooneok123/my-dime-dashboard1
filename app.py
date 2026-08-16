# ----------------------------------------------------
# 1. เพิ่ม Sidebar Filter & ปุ่ม Refresh
# ----------------------------------------------------
st.sidebar.header("⚙️ ตั้งค่า & คัดกรอง")
if st.sidebar.button("🔄 อัปเดตข้อมูลทันที"):
  st.cache_data.clear()
  st.rerun()

categories = ["ทั้งหมด"] + list(df["Category"].dropna().unique())
selected_cat = st.sidebar.selectbox("เลือกหมวดหมู่สินทรัพย์:", categories)

# คัดกรองข้อมูลตาม Sidebar
if selected_cat != "ทั้งหมด":
  df_display = df[df["Category"] == selected_cat]
else:
  df_display = df.copy()

# ----------------------------------------------------
# 2. เพิ่ม Progress Bar เป้าหมายพอร์ต (เช่น เป้า 500,000 บาท)
# ----------------------------------------------------
GOAL_AMOUNT = 500000.0
progress_pct = min(total_value / GOAL_AMOUNT, 1.0)

st.subheader("🎯 เป้าหมายพอร์ตระยะยาว (500,000 บาท)")
st.progress(progress_pct)
st.caption(
    f"ความคืบหน้า: {progress_pct*100:.2f}% (ขาดอีก"
    f" ฿{max(GOAL_AMOUNT - total_value, 0):,.2f} บาท)"
)
st.divider()
