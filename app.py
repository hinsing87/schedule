import calendar
from datetime import date, timedelta
import sqlite3
import uuid
import streamlit as st

st.set_page_config(page_title="囡囡課外活動助手", layout="wide")

# 自訂 CSS：精簡版面與完美高度對齊
st.markdown(
    """
    <style>
    [data-testid="stVerticalBlock"] div:has(> [data-testid="stContainer"]) {
        min-height: 150px;
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

# --- 版面配置：左邊設定，中間 10 週連續檢視 ---
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

    c_btn1, c_btn2, c_btn3 = st.columns(3)
    if c_btn1.button("📅 單次", use_container_width=True):
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

    if c_btn2.button("🔄 4週", use_container_width=True):
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
      st.success("成功新增4週！")
      st.rerun()

    if c_btn3.button("🚀 8週", use_container_width=True):
      for i in range(8):
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
      st.success("成功新增8週！")
      st.rerun()

  st.divider()

  # 2. 新增活動種類
  st.subheader("＋ 新增活動種類")
  act_name = st.text_input("活動名稱 (例如: 芭蕾舞)")
  act_time = st.text_input("時間 (例如: 16:00)")
  act_color = st.selectbox(
      "選擇標籤顏色", ["粉紅", "藍色", "紫色", "綠色", "黃色"]
  )
  if st.button("確認新增活動", use_container_width=True):
    if act_name:
      new_id = str(uuid.uuid4())[:8]
      add_activity_db(new_id, act_name, act_time, act_color)
      st.success(f"已新增: {act_name}")
      st.rerun()

  st.divider()

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
  st.header("🗓️ 黎緊 10 個星期總覽")

  today = date.today()
  days_to_sunday = (today.weekday() + 1) % 7
  current_sunday = today - timedelta(days=days_to_sunday)

  if "start_week_date" not in st.session_state:
    st.session_state.start_week_date = current_sunday

  # 導航控制列
  c_prev, c_title, c_next = st.columns([1, 4, 1])

  if c_prev.button("◀ 上一星期", use_container_width=True):
    st.session_state.start_week_date -= timedelta(weeks=1)
    st.rerun()

  end_date_display = st.session_state.start_week_date + timedelta(
      days = (10 * 7) - 1
  )
  c_title.markdown(
      f"<h3 style='text-align: center; margin: 0; color: #1e293b;'>"
      f"{st.session_state.start_week_date.strftime('%Y/%m/%d')} ~"
      f" {end_date_display.strftime('%Y/%m/%d')}</h3>",
      unsafe_allow_html=True,
  )

  if c_next.button("下一星期 ▶", use_container_width=True):
    st.session_state.start_week_date += timedelta(weeks=1)
    st.rerun()

  st.write("")

  # 纖細嘅左邊月份欄 + 7日星期標題 (總共 8 欄，但好窄)
  header_cols = st.columns([0.45, 1, 1, 1, 1, 1, 1, 1])
  header_cols[0].markdown(
      "<div style='font-weight: bold; text-align: center;"
      " background-color: #e2e8f0; padding: 6px 2px; border-radius: 4px;"
      " color: #334155; font-size: 11px;'>月份</div>",
      unsafe_allow_html=True,
  )
  week_days = ["日", "一", "二", "三", "四", "五", "六"]
  for i, day_name in enumerate(week_days):
    header_cols[i + 1].markdown(
        f"<div style='font-weight: bold; text-align: center;"
        f" background-color: #f1f5f9; padding: 6px; border-radius: 4px;"
        f" color: #334155; font-size: 12px;'>{day_name}</div>",
        unsafe_allow_html=True,
    )

  color_emojis = {
      "粉紅": "🌸",
      "藍色": "🔷",
      "紫色": "🟣",
      "綠色": "🟢",
      "黃色": "🟡",
  }

  last_month = None

  # 連續渲染 10 個星期
  for w in range(10):
    week_start_d = st.session_state.start_week_date + timedelta(days=w * 7)
    week_thursday = week_start_d + timedelta(days=4)
    current_month = week_thursday.month

    row_cols = st.columns([0.45, 1, 1, 1, 1, 1, 1, 1])

    # 左邊極窄月份直行標籤：只喺新月份開始嗰行顯示一次
    with row_cols[0]:
      if current_month != last_month:
        st.markdown(
            f"<div style='height: 100%; min-height: 150px; display: flex;"
            f" flex-direction: column; align-items: center; justify-content:"
            f" center; font-weight: bold; color: #0284c7;"
            f" background-color: #f0f9ff; border-left: 3px solid #0284c7;"
            f" border-radius: 4px; font-size: 12px; text-align: center; padding:"
            f" 2px;'>🌸<br>{current_month}月</div>",
            unsafe_allow_html=True,
        )
        last_month = current_month
      else:
        # 同一個月份就保持空白但對齊高度，營造直行連貫感
        st.markdown(
            "<div style='min-height: 150px; border-left: 3px solid #e0f2fe;'"
            "⊃</div>",
            unsafe_allow_html=True,
        )

    # 渲染 7 日格仔
    for i in range(7):
      current_d = week_start_d + timedelta(days=i)
      day_events = schedule.get(current_d, [])

      with row_cols[i + 1]:
        with st.container(border=True):
          st.markdown(
              f"<div style='font-size: 13px; font-weight: bold; color:"
              f" #475569;'>{current_d.month}/{current_d.day}</div>",
              unsafe_allow_html=True,
          )

          rendered_count = 0
          if day_events:
            for ev in day_events:
              emoji = color_emojis.get(ev["color"], "📌")
              c_txt, c_del = st.columns([6, 1])
              with c_txt:
                st.caption(f"{emoji} {ev['name']} ({ev['time']})")
              with c_del:
                if st.button(
                    "✕", key=f"del_10w_{current_d.isoformat()}_{ev['item_id']}"
                ):
                  delete_schedule_db(ev["item_id"])
                  st.rerun()
              rendered_count += 1

          while rendered_count < 2:
            st.caption(
                "<span style='opacity:0; user-select:none;'>-</span>",
                unsafe_allow_html=True,
            )
            rendered_count += 1
