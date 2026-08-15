# --- 3 欄排版邏輯 ---
  if not activities:
    st.write("暫時未有活動，請在下方新增。")
  else:
    act_items = list(activities.items())
    for i in range(0, len(act_items), 3):  # 每次處理 3 個項目
      row_act_cols = st.columns(3)
      
      for col_idx in range(3):
        if i + col_idx < len(act_items):
          with row_act_cols[col_idx]:
            act_id, info = act_items[i + col_idx]
            emoji = color_emojis.get(info["color"], "📌")
            
            if st.session_state.edit_act_mode:
              sub_c1, sub_c2 = st.columns([4, 1])
              with sub_c1:
                if st.button(f"{emoji} {info['name']}", key=f"sel_{act_id}", use_container_width=True):
                  st.session_state.selected_act_id = act_id
              with sub_c2:
                if st.button("✕", key=f"del_act_{act_id}"):
                  delete_activity_db(act_id)
                  if st.session_state.get("selected_act_id") == act_id:
                    st.session_state.pop("selected_act_id", None)
                  st.rerun()
            else:
              if st.button(f"{emoji} {info['name']}", key=f"sel_{act_id}", use_container_width=True):
                st.session_state.selected_act_id = act_id
