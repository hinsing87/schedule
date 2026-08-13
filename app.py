# (前面 init_db 等函數保持不變，直接替換 col_calendar 之後的程式碼)

with col_calendar:
  st.header("🗓️ 黎緊 10 個星期總覽")
  
  # ... (導航控制列程式碼不變) ...

  # 建立一個包含整個 Table 的 CSS 容器
  st.markdown("""
  <style>
      .scroll-table-container {
          overflow-x: auto;
          width: 100%;
          -webkit-overflow-scrolling: touch;
      }
      .custom-cal-table {
          width: 100%;
          min-width: 600px;
          border-collapse: collapse;
          table-layout: fixed;
      }
      .custom-cal-table th, .custom-cal-table td {
          border: 1px solid #e2e8f0;
          padding: 4px;
          text-align: center;
          vertical-align: top;
          width: 12%;
      }
      .month-cell { width: 8%; font-weight: bold; color: #0284c7; background: #f0f9ff; }
  </style>
  """, unsafe_allow_html=True)

  st.markdown('<div class="scroll-table-container"><table class="custom-cal-table">', unsafe_allow_html=True)
  
  # 表頭
  header_html = "<tr><th class='month-cell'>月份</th>" + "".join([f"<th>{d}</th>" for d in ["日","一","二","三","四","五","六"]]) + "</tr>"
  st.markdown(header_html, unsafe_allow_html=True)

  last_month = None
  for w in range(10):
      week_start_d = st.session_state.start_week_date + timedelta(days=w * 7)
      current_month = (week_start_d + timedelta(days=4)).month
      
      row_html = "<tr>"
      # 月份欄
      if current_month != last_month:
          row_html += f"<td class='month-cell' rowspan='{10}'>{current_month}月</td>" # 呢度邏輯要優化，為左簡單，可以改做只顯示當前月
          last_month = current_month
      
      # 日期格
      for i in range(7):
          curr_d = week_start_d + timedelta(days=i)
          day_events = schedule.get(curr_d, [])
          events_html = "".join([f"<div style='font-size:10px;'>{ev['name']}</div>" for ev in day_events])
          row_html += f"<td><div style='font-size:11px; font-weight:bold;'>{curr_d.day}</div>{events_html}</td>"
      
      row_html += "</tr>"
      st.markdown(row_html, unsafe_allow_html=True)

  st.markdown('</table></div>', unsafe_allow_html=True)

# (後面的 col_setting 部分保持不變)
