import calendar
from datetime import date, timedelta
import sqlite3
import uuid
import streamlit as st

st.set_page_config(page_title="囡囡課外活動助手", layout="wide")

# 自訂 CSS：雙月月曆格高度與樣式微調
st.markdown(
    """
    <style>
    [data-testid="stVerticalBlock"] div:has(> [data-testid="stContainer"]) {
        min-height: 160px;
    }
    
    [data-testid="stContainer"] {
        padding-top: 2px !important;
        padding-bottom: 2px !important;
    }
    
    /* 完美無邊框、紅色、極細嘅刪除按鈕樣式 */
    button[kind="secondary"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #ef4444 !important;
        font-weight: bold !important;
        font-size: 13px !important;
        padding: 0px !important;
        min-height: unset !important;
        height: 22px !important;
    }
    button[kind="secondary"]:hover {
        background-color: #fee2e2 !important;
        color: #991b1b !important;
        border-radius: 4px !important;
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


activities = get_activities()
if not activities:
  add_activity_db(str(uuid.uuid4())[:8], "鋼琴班", "16:00", "粉紅")
  add_activity_db(str(uuid.uuid4())[:8], "游泳班", "10:00", "藍色")
  activities = get_activities()

schedule = get_schedule()

st.title("👧 囡囡課外活動管理助手")

# --- 版面配置：左邊設定，中間雙月大月曆 ---
col_left, col_center = st.columns([1, 3.2], gap="large")

with col_left:
  st.header("⚙️ 活動設定與排程")

  # 1. 將活動安排到指定日期
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
    if c_btn1.button("📅 單次新增", use_container_width=True):
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

    if c_btn2.button("🔄 重複加4週", use_container_width=True):
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

  st.divider()

  # 2. 新增活動種類
  with st.expander("＋ 新增活動種類", expanded=False):
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

  # 3. 現有活動庫管理
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

with col_center:
  st.header("🗓️ 雙月月曆總覽")

  # 處理 Session State 中的年月切換（以第一個月份為準）
  if "view_year" not in st.session_state:
    st.session_state.view_year = date.today().year
  if "view_month" not in st.session_state:
    st.session_state.view_month = date.today().month

  # 計算第二個月的年月
  m1_year, m1_month = st.session_state.view_year, st.session_state.view_month
  if m1_month == 12:
    m2_year, m2_month = m1_year + 1, 1
  else:
    m2_year, m2_month = m1_year, m1_month + 1

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
      f"{m1_year} 年 {m1_month} 月 & {m2_year} 年 {m2_month} 月</h3>",
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


  # 渲染單個月份月曆的函式
  def render_month_calendar(year, month):
    st.markdown(
        f"<h4 style='text-align: center; color: #334155; margin-bottom: 10px;'>"
        f"{year} 年 {month} 月</h4>",
        unsafe_allow_html=True,
    )

    # 顯示 7 列星期標題
    week_days = ["日", "一", "二", "三", "四", "五", "六"]
    header_cols = st.columns(7)
    for i, day_name in enumerate(week_days):
      header_cols[i].markdown(
          f"<div style='font-weight: bold; text-align: center;"
          f" background-color: #f1f5f9; padding: 6px; border-radius: 4px;"
          f" color: #334155; font-size: 12px;'>{day_name}</div>",
          unsafe_allow_html=True,
      )

    cal = calendar.Calendar(firstweekday=6)
    month_matrix = cal.monthdayscalendar(year, month)
    color_emojis = {
        "粉紅": "🌸",
        "藍色": "🔷",
        "紫色": "🟣",
        "綠色": "🟢",
        "黃色": "🟡",
    }

    for week in month_matrix:
      cols = st.columns(7)
      for i, day in enumerate(week):
        with cols[i]:
          if day == 0:
            with st.container(border=False):
              st.write("")
          else:
            current_d = date(year, month, day)
            day_events = schedule.get(current_d, [])

            with st.container(border=True):
              st.markdown(f"**{day}**")

              rendered_count = 0
              if day_events:
                for ev in day_events:
                  emoji = color_emojis.get(ev["color"], "📌")
                  c_txt, c_del = st.columns([6, 1])
                  with c_txt:
                    st.caption(f"{emoji} {ev['name']} ({ev['time']})")
                  with c_del:
                    if st.button("✕", key=f"del_{year}_{month}_{ev['item_id']}"):
                      delete_schedule_db(ev["item_id"])
                      st.rerun()
                  rendered_count += 1

              while rendered_count < 2:
                st.caption(
                    "<span"
                    " style='opacity:0; user-select:none;'>-</span>",
                    unsafe_allow_html=True,
                )
                rendered_count += 1


  # 左右並排顯示兩個月份
  col_m1, col_m2 = st.columns(2, gap="medium")

  with col_m1:
    render_month_calendar(m1_year, m1_month)

  with col_m2:
    render_month_calendar(m2_year, m2_month)
