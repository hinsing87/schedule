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
      st.rerun()

  st.divider()
  st.subheader("📋 現有活動庫")
  # 遍歷活動庫並加上刪除按鈕
  for name, t in list(st.session_state.activities.items()):
    c1, c2 = st.columns([3, 1])
    c1.write(f"**{name}** ({t})")
    if c2.button("🗑️", key=f"del_act_{name}"):
      del st.session_state.activities[name]
      # 同步清理已排程的該項活動
      for d in st.session_state.schedule:
        st.session_state.schedule[d] = [i for i in st.session_state.schedule[d] if i['name'] != name]
      st.rerun()

# --- 主區域 ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
  st.subheader("📌 將活動安排到指定日期")
  
  if not st.session_state.activities:
    st.warning("請先在左側新增至少一個活動！")
  else:
    sel_date = st.date_input("選擇起始日期", value=date.today())
    sel_act = st.selectbox("選擇活動", list(st.session_state.activities.keys()))
    act_time_val = st.session_state.activities.get(sel_act, "15:00")

    c_btn1, c_btn2 = st.columns(2)

    if c_btn1.button("📅 單次新增"):
      if sel_date not in st.session_state.schedule:
        st.session_state.schedule[sel_date] = []
      item = {"name": sel_act, "time": act_time_val}
      st.session_state.schedule[sel_date].append(item)
      st.rerun()

    if c_btn2.button("🔄 重複加未來4週"):
      for i in range(4):
        target_date = sel_date + timedelta(weeks=i)
        if target_date not in st.session_state.schedule:
          st.session_state.schedule[target_date] = []
        item = {"name": sel_act, "time": act_time_val}
        st.session_state.schedule[target_date].append(item)
      st.success("已成功添加未來 4 週日程！")
      st.rerun()

with col2:
  st.subheader("🗓️ 月曆與行程總覽")

  if st.session_state.schedule:
    sorted_schedule = sorted(st.session_state.schedule.items())
    for d, items in sorted_schedule:
      if items:
        with st.expander(f"📌 {d.strftime('%Y-%m-%d (%A)')} ({len(items)} 堂)", expanded=True):
          for idx, item in enumerate(items):
            cols = st.columns([3, 1])
            cols[0].markdown(f"**{item['name']}** — ⏰ `{item['time']}`")
            if cols[1].button("🗑️ 刪除", key=f"del_{d}_{idx}"):
              st.session_state.schedule[d].pop(idx)
              if not st.session_state.schedule[d]:
                del st.session_state.schedule[d]
              st.rerun()
  else:
    st.info("✨ 暫時未有任何已編排嘅活動。")
