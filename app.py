import calendar
from datetime import date, timedelta
import sqlite3
import uuid
import streamlit as st

st.set_page_config(page_title="囡囡課外活動助手", layout="wide")

# 自訂 CSS 令月曆格子更加靚仔清晰
st.markdown(
    """
    <style>
    .calendar-box {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 8px;
        min-height: 110px;
        background-color: #ffffff;
        margin-bottom: 8px;
    }
    .calendar-header {
        font-weight: bold;
        text-align: center;
        background-color: #f8f9fa;
        padding: 6px;
        border-radius: 4px;
        margin-bottom: 6px;
    }
    .day-num {
        font-size: 14px;
        font-weight: bold;
        color: #333333;
    }
    .event-tag {
        font-size: 11px;
        background-color: #e8f0fe;
        color: #1a73e8;
        padding: 2px 4px;
        border-radius: 4px;
        margin-top: 2px;
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- 初始化 SQLite 資料庫 ---
def init_db():
  conn = sqlite3.connect("schedule.db")
  c = conn.cursor()
  c.execute(
      """
        CREATE TABLE IF NOT EXISTS activities (
            act_id TEXT PRIMARY KEY,
            name TEXT,
            time TEXT
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
            time TEXT
        )
    """
  )
  conn.commit()
  conn.close()


init_db()


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

# --- 主區域：左邊排程，右邊傳統月曆 ---
col_form, col_calendar = st.columns([1, 2], gap="large")

with col_form:
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

  st.divider()
  st.subheader("🗑️ 管理與刪除已排行程")
  # 快速管理當日行程清單
  manage_date = st.date_input("選擇要查看/刪除行程的日子", value=date.today())
  if manage_date in schedule and schedule[manage_date]:
    for item in schedule[manage_date]:
      c_a, c_b = st.columns([3, 1])
      c_a.write(f"• **{item['name']}** ({item['time']})")
      if c_b.button("刪除", key=f"manage_del_{item['item_id']}"):
        delete_schedule_db(item["item_id"])
        st.rerun()
  else:
    st.info("這天暫時沒有活動。")

with col_calendar:
  st.subheader("🗓️ 傳統月曆檢視")

  # 選擇要查看嘅年份同月份
  col_y, col_m = st.columns(2)
  view_year = col_y.selectbox("選擇年份", [2025, 2026, 2027], index=1)
  view_month = col_m.selectbox("選擇月份", range(1, 13), index=date.today().month - 1 if view_year == date.today().year else 0)

  # 建立 7 列星期標題 (星期日開始)
  week_days = ["日", "一", "二", "三", "四", "五", "六"]
  header_cols = st.columns(7)
  for i, day_name in enumerate(week_days):
    header_cols[i].markdown(
        f"<div class='calendar-header'>{day_name}</div>",
        unsafe_allow_html=True,
    )

  # 取得該月嘅月曆網格 (以星期日為第一日: firstweekday=6)
  cal = calendar.Calendar(firstweekday=6)
  month_matrix = cal.monthdayscalendar(view_year, view_month)

  # 繪製月曆格子
  for week in month_matrix:
    cols = st.columns(7)
    for i, day in enumerate(week):
      with cols[i]:
        if day == 0:
          # 非本月日子，留空
          st.markdown(
              "<div class='calendar-box' style='background-color: #f9f9f9;"
              " opacity: 0.4;'></div>",
              unsafe_allow_html=True,
          )
        else:
          current_d = date(view_year, view_month, day)
          day_events = schedule.get(current_d, [])

          # 組合該日的活動標籤
          events_html = ""
          for ev in day_events:
            events_html += (
                f"<span class='event-tag'>📌 {ev['name']} ({ev['time']})</span>"
            )

          # 渲染單個日子嘅方格
          st.markdown(
              f"""
                    <div class='calendar-box'>
                        <span class='day-num'>{day}</span>
                        {events_html}
                    </div>
                    """,
              unsafe_allow_html=True,
          )
