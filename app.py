import calendar
from datetime import date, timedelta
import uuid
import streamlit as st

st.set_page_config(page_title="囡囡課外活動助手", layout="wide")

# 自訂 CSS：強制光亮模式背景及精緻刪除按鈕
st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
    }
    .stApp {
        background-color: #ffffff !important;
        color: #1e293b !important;
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

# --- 建立 Streamlit 內置 SQL 連線 ---
conn = st.connection("sql", type="sql")


# --- 初始化資料庫表格 ---
def init_db():
  with conn.session as s:
    s.execute(
        """
            CREATE TABLE IF NOT EXISTS activities (
                act_id TEXT PRIMARY KEY,
                name TEXT,
                time TEXT,
                color TEXT
            )
        """
    )
    s.execute(
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
    s.commit()


init_db()


def get_activities():
  df = conn.query("SELECT act_id, name, time, color FROM activities", ttl=0)
  if df.empty:
    return {}
  result = {}
  for _, row in df.iterrows():
    result[row["act_id"]] = {
        "name": row["name"],
        "time": row["time"],
        "color": row["color"] if row["color"] else "藍色",
    }
  return result


def add_activity_db(act_id, name, time, color):
  with conn.session as s:
    # 確保資料表有 color 欄位 (相容性處理)
    s.execute(
        "INSERT OR REPLACE INTO activities (act_id, name, time, color) VALUES"
        " (:act_id, :name, :time, :color)",
        {"act_id": act_id, "name": name, "time": time, "color": color},
    )
    s.commit()


def delete_activity_db(act_id):
  with conn.session as s:
    s.execute("DELETE FROM activities WHERE act_id = :act_id", {"act_id": act_id})
    s.commit()


def get_schedule():
  df = conn.query(
      "SELECT item_id, act_id, date, name, time, color FROM schedule", ttl=0
  )
  sched = {}
  if df.empty:
    return sched
  for _, row in df.iterrows():
    d = date.fromisoformat(row["date"])
    if d not in sched:
      sched[d] = []
    sched[d].append(
        {
            "item_id": row["item_id"],
            "act_id": row["act_id"],
            "name": row["name"],
            "time": row["time"],
            "color": row["color"] if row["color"] else "藍色",
        }
    )
  return sched


def add_schedule_db(item_id, act_id, d_str, name, time, color):
  with conn.session as s:
    s.execute(
        "INSERT OR REPLACE INTO schedule (item_id, act_id, date, name, time,"
        " color) VALUES (:item_id, :act_id, :date, :name, :time, :color)",
        {
            "item_id": item_id,
            "act_id": act_id,
            "date": d_str,
            "name": name,
            "time": time,
            "color": color,
        },
    )
    s.commit()


def delete_schedule_db(item_id):
  with conn.session as s:
    s.execute(
        "DELETE FROM schedule WHERE item_id = :item_id", {"item_id": item_id}
    )
    s.commit()


activities = get_activities()
if not activities:
  add_activity_db(str(uuid.uuid4())[:8], "鋼琴班", "16:00", "粉紅")
  add_activity_db(str(uuid.uuid4())[:8], "游泳班", "10:00", "藍色")
  activities = get_activities()

schedule = get_schedule()

st.title("👧 囡囡課外活動管理助手")

# --- 自動偵測是否為手機版 ---
headers = st.context.headers
ua = headers.get("User-Agent", "").lower() if headers else ""
is_mobile = any(
    device in ua for device in ["iphone", "android", "ipad", "mobile"]
)

with st.sidebar:
  st.header("⚙️ 顯示設定")
  override_mode = st.radio(
      "裝置模式選擇",
      ["自動偵測", "強制電腦版月曆", "強制手機版清單"],
      index=0,
  )

if override_mode == "強制手機版清單":
  is_mobile = True
elif override_mode == "強制電腦版月曆":
  is_mobile = False

col_calendar, col_setting = st.columns([3.2, 1], gap="large")

with col_calendar:
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
      f" 15px; padding-top: 6px;'>"
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

  # ==========================================
  # A. 手機版：上下清單檢視
  # ==========================================
  if is_mobile:
    st.header("📋 黎緊 10 個星期活動清單 (手機專用)")
    weekdays_zh = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]

    for w in range(10):
      week_start_d = st.session_state.start_week_date + timedelta(days=w * 7)
      st.markdown(
          f"<h4 style='color: #0284c7; margin-top: 15px; font-size:"
          f" 14px;'>── 星期 ({week_start_d.strftime('%Y/%m/%d')} 起) ──</h4>",
          unsafe_allow_html=True,
      )

      for i in range(7):
        current_d = week_start_d + timedelta(days=i)
        day_events = schedule.get(current_d, [])
        w_day_name = weekdays_zh[(current_d.weekday() + 1) % 7]

        with st.container(border=True):
          col_d_info, col_d_act = st.columns([1.2, 3])
          with col_d_info:
            is_today = "🔥 " if current_d == date.today() else ""
            st.markdown(
                f"<div style='font-size: 13px; font-weight: bold; color:"
                f" #1e293b;'>{is_today}{current_d.strftime('%m/%d')} ({w_day_name})</div>",
                unsafe_allow_html=True,
            )

          with col_d_act:
            if day_events:
              for ev in day_events:
                emoji = color_emojis.get(ev["color"], "📌")
                c_t, c_d = st.columns([4, 1])
                with c_t:
                  st.markdown(
                      f"<span style='font-size: 13px; color: #1e293b;'>{emoji}"
                      f" <b>{ev['name']}</b> ({ev['time']})</span>",
                      unsafe_allow_html=True,
                  )
                with c_d:
                  if st.button(
                      "✕", key=f"del_m_{current_d.isoformat()}_{ev['item_id']}"
                  ):
                    delete_schedule_db(ev["item_id"])
                    st.rerun()
            else:
              st.markdown(
                  "<span style='color: #94a3b8; font-size: 12px;'>（無活動）</span>",
                  unsafe_allow_html=True,
              )

  # ==========================================
  # B. 電腦版：橫向月曆檢視
  # ==========================================
  else:
    st.header("🗓️ 黎緊 10 個星期總覽 (月曆)")
    week_days = ["日", "一", "二", "三", "四", "五", "六"]

    h_cols = st.columns([0.6, 1, 1, 1, 1, 1, 1, 1])
    h_cols[0].markdown(
        "<div style='font-weight: bold; text-align: center; background-color:"
        " #e2e8f0; padding: 6px 2px; border-radius: 4px; color: #334155; font-size:"
        " 11px;'>月份</div>",
        unsafe_allow_html=True,
    )
    for idx, d_name in enumerate(week_days):
      h_cols[idx + 1].markdown(
          f"<div style='font-weight: bold; text-align: center;"
          f" background-color: #f1f5f9; padding: 6px; border-radius: 4px;"
          f" color: #334155; font-size: 12px;'>{d_name}</div>",
          unsafe_allow_html=True,
      )

    last_month = None
    for w in range(10):
      week_start_d = st.session_state.start_week_date + timedelta(days=w * 7)
      current_month = (week_start_d + timedelta(days=4)).month
      row_cols = st.columns([0.6, 1, 1, 1, 1, 1, 1, 1])

      with row_cols[0]:
        if current_month != last_month:
          st.markdown(
              f"<div style='min-height: 90px; display: flex; flex-direction:"
              f" column; align-items: center; justify-content: center; font-weight:"
              f" bold; color: #0284c7; background-color: #f0f9ff; border-left:"
              f" 3px solid #0284c7; border-radius: 4px; font-size: 12px; text-align:"
              f" center;'>🌸<br>{current_month}月</div>",
              unsafe_allow_html=True,
          )
          last_month = current_month
        else:
          st.markdown(
              "<div style='min-height: 90px; border-left: 3px solid #e0f2fe;'>"
              "</div>",
              unsafe_allow_html=True,
          )

      for i in range(7):
        current_d = week_start_d + timedelta(days=i)
        day_events = schedule.get(current_d, [])
        with row_cols[i + 1]:
          with st.container(border=True):
            st.markdown(
                f"<div style='font-size: 11px; font-weight: bold; color:"
                f" #475569;'>{current_d.month}/{current_d.day}</div>",
                unsafe_allow_html=True,
            )
            rendered_count = 0
            if day_events:
              for ev in day_events:
                emoji = color_emojis.get(ev["color"], "📌")
                c_txt, c_del = st.columns([5, 1])
                with c_txt:
                  st.caption(f"{emoji} {ev['name']} ({ev['time']})")
                with c_del:
                  if st.button(
                      "✕", key=f"del_d_{current_d.isoformat()}_{ev['item_id']}"
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
