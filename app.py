from datetime import date, timedelta
import sqlite3
import uuid
import streamlit as st

st.set_page_config(page_title="囡囡課外活動助手", layout="wide")


# --- 初始化 SQLite 資料庫 ---
def init_db():
  conn = sqlite3.connect("schedule.db")
  c = conn.cursor()
  # 建立活動庫表格
  c.execute(
      """
        CREATE TABLE IF NOT EXISTS activities (
            act_id TEXT PRIMARY KEY,
            name TEXT,
            time TEXT
        )
    """
  )
  # 建立行程表格
  c.execute(
      """
        CREATE TABLE IF NOT EXISTS schedule (
            item_id TEXT PRIMARY KEY,
            act_id TEXT,
            date TEXT,
            name TEXT,
            time TEXT
        )
    """
  )
  conn.commit()
  conn.close()


init_db()


# --- 資料庫操作小幫手 ---
def get_activities():
  conn = sqlite3.connect("schedule.db")
  c = conn.cursor()
  c.execute("SELECT act_id, name, time FROM activities")
  rows = c.fetchall()
  conn.close()
  return {row[0]: {"name": row[1], "time": row[2]} for row in rows}


def add_activity_db(act_id, name, time):
  conn = sqlite3.connect("schedule.db")
  c = conn.cursor()
  c.execute(
      "INSERT OR REPLACE INTO activities (act_id, name, time) VALUES (?, ?, ?)",
      (act_id, name, time),
  )
  conn.commit()
  conn.close()


def delete_activity_db(act_id):
  conn = sqlite3.connect("schedule.db")
  c = conn.cursor()
  c.execute("DELETE FROM activities WHERE act_id = ?", (act_id,))
  c.execute("DELETE FROM schedule WHERE act_id = ?", (act_id,))
  conn.commit()
  conn.close()


def get_schedule():
  conn = sqlite3.connect("schedule.db")
  c = conn.cursor()
  c.execute("SELECT item_id, act_id, date, name, time FROM schedule")
  rows = c.fetchall()
  conn.close()

  sched = {}
  for row in rows:
    item_id, act_id, d_str, name, time = row
    d = date.fromisoformat(d_str)
    if d not in sched:
      sched[d] = []
    sched[d].append(
        {"item_id": item_id, "act_id": act_id, "name": name, "time": time}
    )
  return sched


def add_schedule_db(item_id, act_id, d_str, name, time):
  conn = sqlite3.connect("schedule.db")
  c = conn.cursor()
  c.execute(
      "INSERT OR REPLACE INTO schedule (item_id, act_id, date, name, time)"
      " VALUES (?, ?, ?, ?, ?)",
      (item_id, act_id, d_str, name, time),
  )
  conn.commit()
  conn.close()


def delete_schedule_db(item_id):
  conn = sqlite3.connect("schedule.db")
  c = conn.cursor()
  c.execute("DELETE FROM schedule WHERE item_id = ?", (item_id,))
  conn.commit()
  conn.close()


# 如果資料庫係空嘅，預設加兩個樣本
activities = get_activities()
if not activities:
  default_id1 = str(uuid.uuid4())[:8]
  default_id2 = str(uuid.uuid4())[:8]
  add_activity_db(default_id1, "鋼琴班", "16:00")
  add_activity_db(default_id2, "游泳班", "10:00")
  activities = get_activities()

schedule = get_schedule()

st.title("👧 囡囡課外活動管理助手")

# --- 側邊欄：管理活動種類 ---
with st.sidebar:
  st.header("⚙️ 設定活動種類")
  act_name = st.text_input("活動名稱 (例如: 芭蕾舞)")
  act_time = st.text_input("時間 (例如: 16:00)")
  if st.button("＋ 新增活動種類"):
    if act_name:
      new_id = str(uuid.uuid4())[:8]
      add_activity_db(new_id, act_name, act_time)
      st.rerun()

  st.divider()
  st.subheader("📋 現有活動庫")
  if not activities:
    st.write("暫時未有活動，請在上方新增。")
  else:
    for act_id, info in list(activities.items()):
      c1, c2 = st.columns([3, 1])
      c1.write(f"**{info['name']}** ({info['time']})")
      if c2.button("🗑️", key=f"del_act_{act_id}"):
        delete_activity_db(act_id)
        st.rerun()

# --- 主區域 ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
  st.subheader("📌 將活動安排到指定日期")

  if not activities:
    st.warning("請先在左側新增至少一個活動！")
  else:
    sel_date = st.date_input("選擇起始日期", value=date.today())

    act_options = {
        act_id: f"{info['name']} ({info['time']})"
        for act_id, info in activities.items()
    }
    selected_act_id = st.selectbox(
        "選擇活動",
        options=list(act_options.keys()),
        format_func=lambda x: act_options[x],
    )

    chosen_info = activities[selected_act_id]

    c_btn1, c_btn2 = st.columns(2)

    if c_btn1.button("📅 單次新增"):
      item_id = str(uuid.uuid4())[:8]
      add_schedule_db(
          item_id,
          selected_act_id,
          sel_date.isoformat(),
          chosen_info["name"],
          chosen_info["time"],
      )
      st.success(f"成功安排 {chosen_info['name']} 於 {sel_date}！")
      st.rerun()

    if c_btn2.button("🔄 重複加未來4週"):
      for i in range(4):
        target_date = sel_date + timedelta(weeks=i)
        item_id = str(uuid.uuid4())[:8]
        add_schedule_db(
            item_id,
            selected_act_id,
            target_date.isoformat(),
            chosen_info["name"],
            chosen_info["time"],
        )
      st.success("已成功添加未來 4 週日程！")
      st.rerun()

with col2:
  st.subheader("🗓️ 月曆與行程總覽")

  if schedule:
    sorted_schedule = sorted(schedule.items())
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
              delete_schedule_db(item["item_id"])
              st.rerun()
  else:
    st.info("✨ 暫時未有任何已編排嘅活動。")
