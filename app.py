import calendar
from datetime import date, timedelta
import sqlite3
import uuid
import streamlit as st

st.set_page_config(page_title="囡囡課外活動助手", layout="wide")

# 自訂 CSS：電腦版與手機版完美適應的表格樣式
st.markdown(
    """
    <style>
    .calendar-scroll-container {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin-bottom: 10px;
    }
    .custom-cal-table {
        width: 100%;
        min-width: 800px;
        border-collapse: collapse;
        table-layout: fixed;
        background-color: white;
    }
    .custom-cal-table th {
        background-color: #f1f5f9;
        color: #334155;
        font-size: 13px;
        padding: 8px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .custom-cal-table td {
        border: 1px solid #e2e8f0;
        padding: 6px;
        vertical-align: top;
        height: 90px;
        background-color: #ffffff;
    }
    .month-col {
        width: 7%;
        font-weight: bold;
        color: #0284c7;
        background-color: #f0f9ff !important;
        text-align: center;
        vertical-align: middle !important;
        font-size: 13px;
    }
    .day-col {
        width: 13.2%;
    }
    
    /* 極細精緻刪除按鈕 */
    button[kind="secondary"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #ef4444 !important;
        font-weight: bold !important;
        font-size: 12px !important;
        padding: 0px !important;
        min-height: unset !important;
        height: 20px !important;
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

# --- 版面配置：左邊大位放月曆，右邊放設定 ---
col_calendar, col_setting = st.columns([3.2, 1], gap="large")

with col_calendar:
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
      f"<h3 style='text-align: center; margin: 0; color: #1e293b; font-size:"
      f" 16px; padding-top: 6px;'>"
      f"{st.session_state.start_week_date.strftime('%Y/%m/%d')} ~"
      f" {end_date_display.strftime('%Y/%m/%d')}</h3>",
      unsafe_allow_html=True,
  )

  if c_next.button("下一星期 ▶", use_container_width=True):
    st.session_state.start_week_date += timedelta(weeks=1)
    st.rerun()

  st.write("")

  color_emojis = {
      "粉紅": "🌸",
      "藍色": "🔷",
      "紫色": "🟣",
      "綠色": "🟢",
      "黃色": "🟡",
  }

  week_days = ["日", "一", "二", "三", "四", "五", "六"]

  # 計算每個月分跨幾行 (Rowspan)
  month_spans = []
  for w in range(10):
    w_start = st.session_state.start_week_date + timedelta(days=w * 7)
    m = (w_start + timedelta(days=4)).month
    month_spans.append(m)

  # 開始建構完美表格
  st.markdown(
      '<div class="calendar-scroll-container"><table'
      " class='custom-cal-table'><thead><tr>",
      unsafe_allow_html=True,
  )
  st.markdown("<th class='month-col'>月份</th>", unsafe_allow_html=True)
  for d in week_days:
    st.markdown(f"<th class='day-col'>{d}</th>", unsafe_allow_html=True)
  st.markdown("</tr></thead><tbody>", unsafe_allow_html=True)

  i = 0
  while i < 10:
    m = month_spans[i]
    count = 0
    j = i
    while j < 10 and month_spans[j] == m:
      count += 1
      j += 1

    for row_idx in range(i, j):
      week_start_d = st.session_state.start_week_date + timedelta(
          days=row_idx * 7
      )

      # 輸出每一行的開頭
      row_tags = "<tr>"
      if row_idx == i:
        row_tags += f"<td class='month-col' rowspan='{count}'>🌸<br>{m}月</td>"
      st.markdown(row_tags, unsafe_allow_html=True)

      # 渲染 7 日格子入面既內容
      for d_idx in range(7):
        curr_d = week_start_d + timedelta(d_idx)
        day_events = schedule.get(curr_d, [])

        # 用 Streamlit Container 確保入面既刪除按鈕可以完美運作
        with st.container():
          # 這裡我們用一個細格包住
          cell_container = st.columns([1])
          with cell_container[0]:
            st.markdown(
                f"<div style='font-size: 11px; font-weight: bold; color:"
                f" #475569; margin-bottom: 2px;'>{curr_d.month}/{curr_d.day}</div>",
                unsafe_allow_html=True,
            )
            if day_events:
              for ev in day_events:
                emoji = color_emojis.get(ev["color"], "📌")
                c_txt, c_del = st.columns([5, 1])
                with c_txt:
                  st.markdown(
                      f"<div style='font-size: 11px; color: #1e293b;"
                      f" white-space: nowrap;'>{emoji} {ev['name']}</div>",
                      unsafe_allow_html=True,
                  )
                with c_del:
                  if st.button(
                      "✕",
                      key=f"del_tbl_{curr_d.isoformat()}_{ev['item_id']}",
                  ):
                    delete_schedule_db(ev["item_id"])
                    st.rerun()

      st.markdown("</tr>", unsafe_allow_html=True)
    i = j

  st.markdown("</tbody></table></div>", unsafe_allow_html=True)

  st.markdown(
      "<p style='color: #64748b; font-size: 11px; text-align: center;"
      " margin-top: 4px;'>💡 手機版可左右滑動查看完整 7 日日曆</p>",
      unsafe_allow_html=True,
  )

with col_setting:
  st.header("⚙️ 設定與排程")

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
