import streamlit as st
from datetime import datetime, date, timedelta
import calendar

st.set_page_config(page_title="囡囡課外活動助手", layout="wide")

# 初始化
if "activities" not in st.session_state:
    st.session_state.activities = {"鋼琴班": "16:00", "游泳班": "10:00"}
if "schedule" not in st.session_state:
    st.session_state.schedule = {}

st.title("👧 囡囡課外活動管理助手")

# --- 側邊欄：管理活動 ---
with st.sidebar:
    st.header("⚙️ 設定活動")
    act_name = st.text_input("活動名稱")
    act_time = st.text_input("時間 (HH:MM)")
    if st.button("新增活動"):
        st.session_state.activities[act_name] = act_time
        st.rerun()

# --- 主區域 ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📌 新增行程")
    sel_date = st.date_input("選擇起始日期")
    sel_act = st.selectbox("選擇活動", list(st.session_state.activities.keys()))
    
    col_a, col_b = st.columns(2)
    if col_a.button("單次新增"):
        if sel_date not in st.session_state.schedule: st.session_state.schedule[sel_date] = []
        st.session_state.schedule[sel_date].append({"name": sel_act, "time": st.session_state.activities[sel_act]})
        st.rerun()
    
    if col_b.button("每週新增 (未來4週)"):
        for i in range(4):
            d = sel_date + timedelta(weeks=i)
            if d not in st.session_state.schedule: st.session_state.schedule[d] = []
            st.session_state.schedule[d].append({"name": sel_act, "time": st.session_state.activities[sel_act]})
        st.rerun()

with col2:
    st.subheader("🗓️ 月曆總覽")
    # 生成當月月曆
    year, month = sel_date.year, sel_date.month
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)
    
    header = ["日", "一", "二", "三", "四", "五", "六"]
    st.table(pd.DataFrame(columns=header)) # 這裡我們簡單化處理
    
    # 顯示當月所有行程
    st.subheader(f"{month}月行程清單")
    for d, items in sorted(st.session_state.schedule.items()):
        if d.month == month and d.year == year:
            with st.expander(f"{d} - {len(items)} 個活動"):
                for idx, item in enumerate(items):
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"**{item['name']}** @ {item['time']}")
                    if c2.button("刪除", key=f"del_{d}_{idx}"):
                        st.session_state.schedule[d].pop(idx)
                        st.rerun()
