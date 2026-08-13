from datetime import date, timedelta
import uuid
import streamlit as st

st.set_page_config(page_title="囡囡課外活動助手", layout="wide")

# --- 初始化與資料修復機制 ---
if "activities" not in st.session_state:
  st.session_state.activities = {
      "1": {"name": "鋼琴班", "time": "16:00"},
      "2": {"name": "游泳班", "time": "10:00"},
  }
else:
  # 自動防呆：如果舊 session 裡面有純字串格式嘅活動，自動幫它升級成字典格式
  fixed_activities = {}
  for k, v in st.session_state.activities.items():
    if isinstance(v, str):
      fixed_activities[k] = {"name": v, "time": "15:00"}
    else:
      fixed_activities[k] = v
  st.session_state.activities = fixed_activities

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
      new_id = str(uuid.uuid4())[:8]
      st.session_state.activities[new_id] = {"name": act_name, "time": act_time}
      st.rerun()

  st.divider()
  st.subheader("📋 現有活動庫")
  if not st.session_state.activities:
    st.write("暫時未有活動，請在上方新增。")
  else:
    for act_id, info in list(st.session_state.activities.items()):
      c1, c2 = st.columns([3, 1])
      c1.write(f"**{info['name']}** ({info['time']})")
      if c2.button("🗑️", key=f"del_act_{act_id}"):
        del st.session_state.activities[act_id]
        # 同步清理月曆中所有關聯呢個 ID 既行程
        for d in list(st.session_state.schedule.keys()):
          st.session_state.schedule[d] = [
              item
              for item in st.session_state.schedule[d]
              if item.get("act_id") != act_id
          ]
          if not st.session_state.schedule[d]:
            del st.session_state.schedule[d]
        st.rerun()

# --- 主區域 ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
  st.subheader("📌 將活動安排到指定日期")

  if not st.session_state.activities:
    st.warning("請先在左側新增至少一個活動！")
  else:
    sel_date = st.date_input("選擇起始日期", value=date.today())

    act_options = {
        act_id: f"{info['name']} ({info['time']})"
        for act_id, info in st.session_state.activities.items()
    }
    selected_act_id = st.selectbox(
        "選擇活動",
        options=list(act_options.keys()),
        format_func=lambda x: act_options[x],
    )

    chosen_info = st.session_state.activities[selected_act_id]

    c_btn1, c_btn2 = st.columns(2)

    if c_btn1.button("📅 單次新增"):
      if sel_date not in st.session_state.schedule:
        st.session_state.schedule[sel_date] = []

      item = {
          "item_id": str(uuid.uuid4())[:8],
          "act_id": selected_act_id,
          "name": chosen_info["name"],
          "time": chosen_info["time"],
      }
      st.session_state.schedule[sel_date].append(item)
      st.success(f"成功安排 {chosen_info['name']} 於 {sel_date}！")
      st.rerun()

    if c_btn2.button("🔄 重複加未來4週"):
      for i in range(4):
        target_date = sel_date + timedelta(weeks=i)
        if target_date not in st.session_state.schedule:
          st.session_state.schedule[target_date] = []

        item = {
            "item_id": str(uuid.uuid4())[:8],
            "act_id": selected_act_id,
            "name": chosen_info["name"],
            "time": chosen_info["time"],
        }
        st.session_state.schedule[target_date].append(item)

      st.success("已成功添加未來 4 週日程！")
      st.rerun()

with col2:
  st.subheader("🗓️ 月曆與行程總覽")

  if st.session_state.schedule:
    sorted_schedule = sorted(st.session_state.schedule.items())
    for d, items in sorted_schedule:
      if items:
        with st.expander(
            f"📌 {d.strftime('%Y-%m-%d (%A)')} ({len(items)} 堂)",
            expanded=True,
        ):
          for idx, item in enumerate(items):
            cols = st.columns([3, 1])
            cols[0].markdown(f"**{item['name']}** — ⏰ `{item['time']}`")

            if cols[1].button("🗑️ 刪除", key=f"del_item_{item['item_id']}"):
              st.session_state.schedule[d].pop(idx)
              if not st.session_state.schedule[d]:
                del st.session_state.schedule[d]
              st.rerun()
  else:
    st.info("✨ 暫時未有任何已編排嘅活動。")
