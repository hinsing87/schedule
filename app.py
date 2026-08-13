from datetime import datetime, date
import streamlit as st

# 設定網頁標題與佈局
st.set_page_config(
    page_title="囡囡課外活動時間表", page_icon="📅", layout="wide"
)

st.title("👧 囡囡課外活動管理助手")
st.write("輕鬆設定課外活動，並指派到指定日期，隨時查看每日上堂時間！")

# 初始化 Session State
if "activities" not in st.session_state:
  st.session_state.activities = {
      "鋼琴班": "16:00 - 17:00",
      "游泳訓練": "10:00 - 11:30",
      "繪畫班": "14:30 - 16:00",
      "英文拼音": "17:00 - 18:00",
  }

if "schedule" not in st.session_state:
  st.session_state.schedule = {date(2026, 8, 15): [("鋼琴班", "16:00 - 17:00")]}

# --- 側邊欄：設定與新增活動 ---
with st.sidebar:
  st.header("⚙️ 設定活動種類")

  with st.form("add_activity_form"):
    new_name = st.text_input("活動名稱 (例如: 芭蕾舞)")
    new_time = st.text_input("預設時間 (例如: 15:00 - 16:30)")
    submit_btn = st.form_submit_button("＋ 新增活動種類")

    if submit_btn and new_name:
      st.session_state.activities[new_name] = new_time
      st.success(f"成功新增活動：{new_name}")

  st.divider()
  st.subheader("📋 現有活動庫")
  for act_name, act_time in st.session_state.activities.items():
    st.markdown(f"**{act_name}** (`{act_time}`)")

# --- 主畫面：安排活動與檢視月曆 ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
  st.subheader("📌 將活動安排到指定日期")

  with st.form("schedule_form"):
    selected_date = st.date_input(
        "選擇日期", value=date(2026, 8, 15)
    )
    chosen_activity = st.selectbox(
        "選擇要上嘅活動", list(st.session_state.activities.keys())
    )

    assign_btn = st.form_submit_button("📅 將活動加入這一天")

    if assign_btn:
      time_slot = st.session_state.activities[chosen_activity]
      if selected_date not in st.session_state.schedule:
        st.session_state.schedule[selected_date] = []

      item = (chosen_activity, time_slot)
      if item not in st.session_state.schedule[selected_date]:
        st.session_state.schedule[selected_date].append(item)
        st.success(
            f"已成功將 {chosen_activity} ({time_slot}) 安排到"
            f" {selected_date}！"
        )
      else:
        st.warning("呢一日已經有呢個活動啦！")

with col2:
  st.subheader("👁️ 每日上堂時間檢視")

  check_date = st.date_input(
      "查看邊一日嘅時間表？", value=date(2026, 8, 15), key="check_date_picker"
  )

  if (
      check_date in st.session_state.schedule
      and st.session_state.schedule[check_date]
  ):
    st.markdown(f"### 🗓️ {check_date} 的上堂時間：")
    for idx, (act_name, act_time) in enumerate(
        st.session_state.schedule[check_date]
    ):
      c1, c2 = st.columns([3, 1])
      with c1:
        st.info(f"**{act_name}** — ⏰ **{act_time}**")
      with c2:
        if st.button("刪除", key=f"del_{check_date}_{idx}"):
          st.session_state.schedule[check_date].pop(idx)
          st.rerun()
  else:
    st.info(f"✨ {check_date} 這天暫時未有安排任何課外活動。")

st.divider()

# --- 總覽清單 (純 Python 實現，唔需 Pandas) ---
st.subheader("📚 所有已編排的日程總覽")
if st.session_state.schedule:
  # 整理成表格數據
  table_data = []
  # 按日期排序
  sorted_dates = sorted(st.session_state.schedule.keys())
  for d in sorted_dates:
    for act_name, act_time in st.session_state.schedule[d]:
      table_data.append(
          {"日期": d.strftime("%Y-%m-%d"), "活動名稱": act_name, "上堂時間": act_time}
      )

  st.table(table_data)
else:
  st.write("暫時未有任何日程紀錄。")
