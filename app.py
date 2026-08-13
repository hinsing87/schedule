import calendar
from datetime import date, timedelta
import sqlite3
import uuid
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="囡囡課外活動助手", layout="wide")


# --- 初始化 SQLite 資料庫 ---
def init_db():
  conn = sqlite3.connect("schedule.db")
  c = conn.cursor()
  c.execute(
      """
        CREATE TABLE IF NOT EXISTS activities (
            act_id TEXT PRIMARY KEY,
            name TEXT,
            time TEXT,
            color TEXT
        )
    """
  )
  c.execute(
      """
        CREATE TABLE IF NOT EXISTS schedule (
            item_id TEXT PRIMARY KEY,
            act_id TEXT,
            date TEXT,
            name TEXT,
            time TEXT,
            color TEXT
        )
    """
  )
  conn.commit()
  conn.close()


init_db()


def get_activities():
  conn = sqlite3.connect("schedule.db")
  c = conn.cursor()
  try:
    c.execute("SELECT act_id, name, time, color FROM activities")
  except sqlite3.OperationalError:
    c.execute("ALTER TABLE activities ADD COLUMN color TEXT")
    conn.commit()
    c.execute("SELECT act_id, name, time, color FROM activities")
  rows = c.fetchall()
  conn.close()
  return {
      row[0]: {
          "name": row[1],
          "time": row[2],
          "color": row[3] if row[3] else "藍色",
      }
      for row in rows
  }


def add_activity_db(act_id, name, time, color):
  conn = sqlite3.connect("schedule.db")
  c = conn.cursor()
  c.execute(
      "INSERT OR REPLACE INTO activities (act_id, name, time, color) VALUES"
      " (?, ?, ?, ?)",
      (act_id, name, time, color),
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
  try:
    c.execute("SELECT item_id, act_id, date, name, time, color FROM schedule")
  except sqlite3.OperationalError:
    c.execute("ALTER TABLE schedule ADD COLUMN color TEXT")
    conn.commit()
    c.execute("SELECT item_id, act_id, date, name, time, color FROM schedule")
  rows = c.fetchall()
  conn.close()

  sched = {}
  for row in rows:
    item_id, act_id, d_str, name, time, color = row
    d = date.fromisoformat(d_str)
    if d not in sched:
      sched[d] = []
    sched[d].append(
        {
            "item_id": item_id,
            "act_id": act_id,
            "name": name,
            "time": time,
            "color": color if color else "藍色",
        }
    )
  return sched


def add_schedule_db(item_id, act_id, d_str, name, time, color):
  conn = sqlite3.connect("schedule.db")
  c = conn.cursor()
  c.execute(
      "INSERT OR REPLACE INTO schedule (item_id, act_id, date, name, time,"
      " color) VALUES (?, ?, ?, ?, ?, ?)",
      (item_id, act_id, d_str, name, time, color),
  )
  conn.commit()
  conn.close()


def delete_schedule_db(item_id):
  conn = sqlite3.connect("schedule.db")
  c = conn.cursor()
  c.execute("DELETE FROM schedule WHERE item_id = ?", (item_id,))
  conn.commit()
  conn.close()


# 顏色對應樣式配置
color_styles = {
    "粉紅": (
        "background-color: #fce7f3; color: #9d174d; border: 1px solid"
        " #fbcfe8;",
        "#db2777",
    ),
    "藍色": (
        "background-color: #eff6ff; color: #1e40af; border: 1px solid"
        " #bfdbfe;",
        "#3b82f6",
    ),
    "紫色": (
        "background-color: #f3e8ff; color: #6b21a8; border: 1px solid"
        " #e9d5ff;",
        "#9333ea",
    ),
    "綠色": (
        "background-color: #f0fdf4; color: #166534; border: 1px solid"
        " #bbf7d0;",
        "#16a34a",
    ),
    "黃色": (
        "background-color: #fefce8; color: #854d0e; border: 1px solid"
        " #fef08a;",
        "#ca8a04",
    ),
}

activities = get_activities()
if not activities:
  add_activity_db(str(uuid.uuid4())[:8], "鋼琴班", "16:00", "粉紅")
  add_activity_db(str(uuid.uuid4())[:8], "游泳班", "10:00", "藍色")
  activities = get_activities()

schedule = get_schedule()

st.title("👧 囡囡課外活動管理助手")

# --- 版面配置：左邊設定，中間大月曆 ---
col_left, col_center = st.columns([1, 2.8], gap="large")

with col_left:
  st.header("⚙️ 活動設定與排程")

  # 1. 新增活動種類
  with st.expander("＋ 新增活動種類", expanded=True):
    act_name = st.text_input("活動名稱 (例如: 芭蕾舞)")
    act_time = st.text_input("時間 (例如: 16:00)")
    act_color = st.selectbox(
        "選擇標籤顏色", ["粉紅", "藍色", "紫色", "綠色", "黃色"]
    )
    if st.button("確認新增活動"):
      if act_name:
        new_id = str(uuid.uuid4())[:8]
        add_activity_db(new_id, act_name, act_time, act_color)
        st.success(f"已新增: {act_name}")
        st.rerun()

  # 2. 現有活動庫管理
  st.subheader("📋 現有活動庫")
  if not activities:
    st.write("暫時未有活動。")
  else:
    for act_id, info in list(activities.items()):
      c_a, c_b = st.columns([3, 1])
      c_a.write(f"**{info['name']}** ({info['time']})")
      if c_b.button("🗑️", key=f"del_act_{act_id}"):
        delete_activity_db(act_id)
        st.rerun()

  st.divider()

  # 3. 將活動安排到指定日期
  st.subheader("📌 安排活動到日期")
  if activities:
    sel_date = st.date_input("選擇日期", value=date.today())
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
          chosen_info["color"],
      )
      st.success("成功安排！")
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
            chosen_info["color"],
        )
      st.success("成功新增未來4週！")
      st.rerun()

with col_center:
  st.header("🗓️ 月曆總覽")

  # 處理 Session State 中的年月切換
  if "view_year" not in st.session_state:
    st.session_state.view_year = date.today().year
  if "view_month" not in st.session_state:
    st.session_state.view_month = date.today().month

  # 檢查網址參數是否有刪除動作並即時處理
  query_params = st.query_params
  if "delete_item" in query_params:
    del_id = query_params["delete_item"]
    delete_schedule_db(del_id)
    st.query_params.clear()
    st.rerun()

  # 月份切換控制列
  c_prev, c_title, c_next = st.columns([1, 4, 1])

  if c_prev.button("◀ 上個月", use_container_width=True):
    if st.session_state.view_month == 1:
      st.session_state.view_month = 12
      st.session_state.view_year -= 1
    else:
      st.session_state.view_month -= 1
    st.rerun()

  c_title.markdown(
      f"<h3 style='text-align: center; margin: 0; color: #1e293b;'>"
      f"{st.session_state.view_year} 年 {st.session_state.view_month} 月</h3>",
      unsafe_allow_html=True,
  )

  if c_next.button("下個月 ▶", use_container_width=True):
    if st.session_state.view_month == 12:
      st.session_state.view_month = 1
      st.session_state.view_year += 1
    else:
      st.session_state.view_month += 1
    st.rerun()

  st.write("")

  # 準備月曆 HTML 結構
  cal = calendar.Calendar(firstweekday=6)
  month_matrix = cal.monthdayscalendar(
      st.session_state.view_year, st.session_state.view_month
  )

  week_days = ["日", "一", "二", "三", "四", "五", "六"]

  calendar_html_parts = [
      """
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: transparent; color: #1e293b; margin: 0; padding: 0; }
        .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; }
        .cal-header { font-weight: bold; text-align: center; background-color: #f1f5f9; padding: 8px; border-radius: 6px; color: #334155; font-size: 13px; }
        .calendar-box { border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px; min-height: 120px; background-color: #ffffff; display: flex; flex-direction: column; position: relative; box-sizing: border-box; }
        .calendar-box-empty { border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px; min-height: 120px; background-color: #f8fafc; opacity: 0.3; }
        .day-num { font-size: 13px; font-weight: bold; color: #1e293b; margin-bottom: 4px; }
        .event-card { position: relative; padding: 4px 20px 4px 6px; border-radius: 4px; font-size: 11px; margin-bottom: 3px; line-height: 1.2; box-sizing: border-box; }
        .event-delete-x { position: absolute; top: 2px; right: 4px; text-decoration: none; font-weight: bold; font-size: 11px; cursor: pointer; }
        .event-delete-x:hover { opacity: 0.7; }
    </style>
    <div class="cal-grid">
    """
  ]

  for d_name in week_days:
    calendar_html_parts.append(f'<div class="cal-header">{d_name}</div>')

  for week in month_matrix:
    for day in week:
      if day == 0:
        calendar_html_parts.append('<div class="calendar-box-empty"></div>')
      else:
        current_d = date(
            st.session_state.view_year, st.session_state.view_month, day
        )
        day_events = schedule.get(current_d, [])

        events_html = ""
        for ev in day_events:
          card_style, x_color = color_styles.get(
              ev["color"], color_styles["藍色"]
          )
          events_html += f"""
                    <div class="event-card" style="{card_style}">
                        <b>{ev['name']}</b><br>{ev['time']}
                        <a href="?delete_item={ev['item_id']}" class="event-delete-x" style="color: {x_color};" title="刪除">✕</a>
                    </div>
                    """

        calendar_html_parts.append(
            f"""
                <div class="calendar-box">
                    <div class="day-num">{day}</div>
                    {events_html}
                </div>
                """
        )

  calendar_html_parts.append("</div>")
  full_calendar_html = "".join(calendar_html_parts)

  # 透過 components.v1.html 完美渲染成型，徹底解決源碼外露問題
  components.html(full_calendar_html, height=750, scrolling=True)
