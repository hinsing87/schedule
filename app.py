import calendar
from datetime import date, timedelta
import uuid
import streamlit as st
from sqlalchemy import text

st.set_page_config(page_title="囡囡課外活動管理助手", layout="wide")

# --- CSS 樣式 ---
st.markdown(
    """
    <style>
    :root { color-scheme: light; }
    .stApp { background-color: #ffffff !important; color: #1e293b !important; }
    button[kind="secondary"] {
        background-color: transparent !important; border: none !important; box-shadow: none !important;
        color: #ef4444 !important; font-weight: bold !important; font-size: 12px !important;
        padding: 0px !important; min-height: unset !important; height: 20px !important;
    }
    button[kind="secondary"]:hover { background-color: #fee2e2 !important; color: #991b1b !important; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 資料庫設定 ---
conn = st.connection("sql", type="sql")

def init_db():
  with conn.session as s:
    s.execute(text("CREATE TABLE IF NOT EXISTS activities (act_id TEXT PRIMARY KEY, name TEXT, time TEXT, color TEXT)"))
    s.execute(text("CREATE TABLE IF NOT EXISTS schedule (item_id TEXT PRIMARY KEY, act_id TEXT, date TEXT, name TEXT, time TEXT, color TEXT)"))
    s.commit()

init_db()

# --- 輔助函式 ---
def get_activities():
  df = conn.query("SELECT act_id, name, time, color FROM activities", ttl=0)
  return {row["act_id"]: {"name": row["name"], "time": row["time"], "color": row["color"]} for _, row in df.iterrows()}

def add_activity_db(act_id, name, time, color):
  with conn.session as s:
    s.execute(text("INSERT OR REPLACE INTO activities (act_id, name, time, color) VALUES (:act_id, :name, :time, :color)"), {"act_id": act_id, "name": name, "time": time, "color": color})
    s.commit()

def delete_activity_db(act_id):
  with conn.session as s:
    s.execute(text("DELETE FROM activities WHERE act_id = :act_id"), {"act_id": act_id})
    s.commit()

def get_schedule():
  df = conn.query("SELECT item_id, act_id, date, name, time, color FROM schedule", ttl=0)
  sched = {}
  for _, row in df.iterrows():
    d = date.fromisoformat(row["date"])
    if d not in sched: sched[d] = []
    sched[d].append({"item_id": row["item_id"], "name": row["name"], "time": row["time"], "color": row["color"]})
  return sched

def add_schedule_db(item_id, act_id, d_str, name, time, color):
  with conn.session as s:
    s.execute(text("INSERT OR REPLACE INTO schedule (item_id, act_id, date, name, time, color) VALUES (:item_id, :act_id, :date, :name, :time, :color)"), {"item_id": item_id, "act_id": act_id, "date": d_str, "name": name, "time": time, "color": color})
    s.commit()

def delete_schedule_db(item_id):
  with conn.session as s:
    s.execute(text("DELETE FROM schedule WHERE item_id = :item_id"), {"item_id": item_id})
    s.commit()

# --- 狀態初始化 ---
if "sel_date" not in st.session_state: st.session_state.sel_date = date.today()
if "start_week_date" not in st.session_state:
    days_to_sunday = (date.today().weekday() + 1) % 7
    st.session_state.start_week_date = date.today() - timedelta(days=days_to_sunday)

activities = get_activities()
schedule = get_schedule()

st.title("👧 囡囡課外活動管理助手")
col_calendar, col_setting = st.columns([3.2, 1], gap="large")

# --- 月曆邏輯 ---
with col_calendar:
  c_prev, c_title, c_next = st.columns([1, 4, 1])
  if c_prev.button("◀ 上一星期"):
    st.session_state.start_week_date -= timedelta(weeks=1)
    st.rerun()
  c_title.markdown(f"<h3 style='text-align:center;'>{st.session_state.start_week_date.strftime('%Y/%m/%d')} 開始</h3>", unsafe_allow_html=True)
  if c_next.button("下一星期 ▶"):
    st.session_state.start_week_date += timedelta(weeks=1)
    st.rerun()

  color_emojis = {"粉紅": "🌸", "藍色": "🔷", "紫色": "🟣", "綠色": "🟢", "黃色": "🟡"}
  
  # 繪製月曆格
  for w in range(10):
    row_cols = st.columns([0.6, 1, 1, 1, 1, 1, 1, 1])
    week_start_d = st.session_state.start_week_date + timedelta(days=w * 7)
    for i in range(7):
      current_d = week_start_d + timedelta(days=i)
      with row_cols[i+1]:
        # 日期按鈕：點擊後強制更新 session 並重新載入頁面
        if st.button(f"{current_d.month}/{current_d.day}", key=f"d_{current_d}", use_container_width=True):
            st.session_state.sel_date = current_d
            st.rerun()
        
        for ev in schedule.get(current_d, []):
            st.caption(f"{color_emojis.get(ev['color'], '📌')} {ev['name']}")

# --- 設定區邏輯 ---
with col_setting:
  st.header("⚙️ 設定與排程")
  # 將 date_input 的值與 sel_date 同步
  new_sel_date = st.date_input("選擇目標日期", value=st.session_state.sel_date)
  if new_sel_date != st.session_state.sel_date:
      st.session_state.sel_date = new_sel_date
      st.rerun()

  st.divider()
  
  # 活動庫開關
  if "edit_mode" not in st.session_state: st.session_state.edit_mode = False
  if st.button("⚙️ 設定刪除模式"): st.session_state.edit_mode = not st.session_state.edit_mode; st.rerun()

  for act_id, info in activities.items():
    c_act, c_del = st.columns([4, 1])
    with c_act:
      if st.button(f"{color_emojis.get(info['color'], '📌')} {info['name']} ({info['time']})", key=f"s_{act_id}", use_container_width=True):
        st.session_state.active_act = act_id
    with c_del:
      if st.session_state.edit_mode and st.button("✕", key=f"d_{act_id}"):
        delete_activity_db(act_id); st.rerun()

  # 新增活動
  st.subheader("＋ 新增活動")
  name = st.text_input("名稱")
  time = st.text_input("時間")
  color = st.selectbox("顏色", ["粉紅", "藍色", "紫色", "綠色", "黃色"])
  if st.button("確認新增"):
    add_activity_db(str(uuid.uuid4())[:8], name, time, color); st.rerun()
