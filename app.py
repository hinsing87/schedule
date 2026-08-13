import calendar
from datetime import date, timedelta
import streamlit as st

st.set_page_config(page_title="囡囡課外活動助手", layout="wide")

# 初始化 Session State
if "activities" not in st.session_state:
  st.session_state.activities = {"鋼琴班": "16:00", "游泳班": "10:00"}
if "schedule" not in st.session_state:
  st.session_state.schedule = {}

st.title("👧 囡囡課外活動管理助手")

# --- 側邊欄：管理活動種類 ---
with st.sidebar:
  st.header("⚙️ 設定活動種類")
  act_name = st.text_input("活動名稱 (例如: 芭蕾舞)")
  act_time = st.text_input("時間 (例如: 16:00)")
  if st.button("＋ 新增活動種類"):
    if act_name:
      st.session_state.activities[act_name] = act_time
      st.success(f"已新增: {act_name}")
      st.rerun()

  st.divider()
  st.subheader("📋 現有活動庫")
  for name, t in st.session_state.activities.items():
    st.write(f"• **{name}** ({t})")

# --- 主區域 ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
  st.subheader("📌 將活動安排到指定日期")

  sel_date = st.date_input("選擇起始日期", value=date(2026, 8, 15))
  sel_act = st.selectbox("選擇活動", list(st.session_state.activities.keys()))
  act_time_val = st.session_state.activities.get(sel_act, "15:00")

  c_btn1, c_btn2 = st.columns(2)

  # 單次新增按鈕
  if c_btn1.button("📅 單次新增"):
    if sel_date not in st.session_state.schedule:
      st.session_state.schedule[sel_date] = []

    item = {"name": sel_act, "time": act_time_val}
    if item not in st.session_state.schedule[sel_date]:
      st.session_state.schedule[sel_date].append(item)
      st.success(f"成功安排 {sel_act} 於 {sel_date}！")
      st.rerun()
    else:
      st.warning("呢一日已經有呢個活動啦！")

  # 一鍵加到未來每週相同時間
  if c_btn2.button("🔄 重複加未來4週"):
    for i in range(4):
      target_date = sel_date + timedelta(weeks=i)
      if target_date not in st.session_state.schedule:
        st.session_state.schedule[target_date] = []

      item = {"name": sel_act, "time": act_time_val}
      if item not in st.session_state.schedule[target_date]:
        st.session_state.schedule[target_date].append(item)

    st.success(f"成功將 {sel_act} 自動安排到未來 4 週嘅相同日子！")
    st.rerun()

with col2:
  st.subheader("🗓️ 月曆與行程總覽")

  # 篩選並顯示已排程嘅活動
  if st.session_state.schedule:
    # 按日期排序
    sorted_schedule = sorted(st.session_state.schedule.items())

    for d, items in sorted_schedule:
      if items:
        # 用 expander 打造乾淨嘅日曆卡片風格
        with st.expander(f"📌 {d.strftime('%Y-%m-%d (%A)')} ({len(items)} 堂)", expanded=True):
          for idx, item in enumerate(items):
            cols = st.columns([3, 1])
            cols.markdown(f"**{item['name']}** — ⏰ `{item['time']}`")
            
            # 一鍵刪除當日單一活動
            if cols.button("🗑️ 刪除", key=f"del_{d}_{idx}"):
              st.session_state.schedule[d].pop(idx)
              # 如果該日已經無晒活動，順便清空個 key
              if not st.session_state.schedule[d]:
                del st.session_state.schedule[d]
              st.rerun()
  else:
    st.info("✨ 暫時未有任何已編排嘅活動，快啲喺左邊加啦！")
