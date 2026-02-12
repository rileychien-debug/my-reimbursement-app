import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 設定網頁標題與版面
st.set_page_config(page_title="小額代墊報帳追蹤", layout="wide")

# --- 1. 資料存儲初始化 (測試版使用 session_state) ---
# 注意：若要永久保存，後續建議連結 Google Sheets
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=[
        'id', 'user_id', 'name', 'amount', 'invoice_date', 'reason', 
        'status', 'created_at', 'review_time'
    ])

# 模擬單位人員名單 (ID 為身分證字號)
USER_LIST = {
    "A123456789": {"name": "rileychien", "role": "admin"}, # 行政人員權限
    "B123456789": {"name": "王小明", "role": "staff"},     # 一般同仁權限
}

# --- 2. 登入系統 ---
st.title("小額代墊報帳追蹤")
user_id = st.text_input("請輸入身分證字號登入", type="password")

if user_id in USER_LIST:
    user_info = USER_LIST[user_id]
    user_name = user_info['name']
    is_admin = (user_info['role'] == "admin")
    now = datetime.now()
    
    st.success(f"歡迎回來，{user_name}！")
    
    # --- 3. User 1 功能：填寫申請單 ---
    with st.expander("➕ 新增代墊報帳申請"):
        amount = st.number_input("代墊金額", min_value=0, max_value=10000, step=1)
        invoice_date = st.date_input("發票日期", value=now)
        reason = st.text_input("支出原因 (例如：ChatGPT訂閱)")
        
        st.write("**實體單據檢查清單：**")
        c1 = st.checkbox("A. 已在收據簽名or蓋章")
        c2 = st.checkbox("B. 已註明支出原因")
        c3 = st.checkbox("C. 已核對統編52004800；抬頭：東海大學")
        
        if st.button("確認送出 (Submitted)"):
            if c1 and c2 and c3 and amount > 0 and reason:
                new_data = {
                    'id': len(st.session_state.db) + 1,
                    'user_id': user_id,
                    'name': user_name,
                    'amount': amount,
                    'invoice_date': invoice_date.strftime("%Y-%m-%d"),
                    'reason': reason,
                    'status': "Submitted",
                    'created_at': now,
                    'review_time': None
                }
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_data])], ignore_index=True)
                st.rerun()
            else:
                st.warning("請確保填寫完整並完成單據檢查勾選。")

    # --- 4. User 1 功能：個人進度與刪除邏輯 ---
    st.subheader("我的報帳進度")
    my_claims = st.session_state.db[st.session_state.db['user_id'] == user_id]
    
    if not my_claims.empty:
        my_claims = my_claims.sort_values(by='created_at', ascending=False)
        for idx, row in my_claims.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                col1.write(f"📅 發票日: {row['invoice_date']} | **{row['reason']}** (${row['amount']})")
                
                # --- 狀態延遲顯示邏輯 ---
                # 如果行政點了 Review，但在 1 小時內，User 1 看到的還是 Submitted (方便 User 1 誤填刪除)
                current_status = row['status']
                display_status = current_status
                if current_status == "Reviewing" and row['review_time']:
                    if now - row['review_time'] < timedelta(hours=1):
                        display_status = "Submitted"

                if display_status == "Submitted":
                    col2.warning("🟡 實體單據提交")
                    if col3.button("刪除", key=f"del_{row['id']}"):
                        st.session_state.db = st.session_state.db.drop(idx)
                        st.rerun()
                
                elif display_status == "Reviewing":
                    col2.info("🔵 行政已處理，待撥款")
                    st.caption("※ 行政已登錄系統，不可刪除。如有疑問請洽 rileychien@thu.edu.tw (分機30051)")
                    if col3.button("收到款項", key=f"rec_{row['id']}"):
                        st.session_state.db.at[idx, 'status'] = "Done"
                        st.rerun()
                
                elif display_status == "Returned":
                    col2.error("❌ 已退回 (五個工作天內未交單據)")
                    st.caption("請刪除此筆記錄並重新申請。")
                    if col3.button("刪除記錄", key=f"del_ret_{row['id']}"):
                        st.session_state.db = st.session_state.db.drop(idx)
                        st.rerun()
                
                else:
                    col2.success("🟢 已結案 (Done)")
                st.divider()
    else:
        st.info("目前尚無申請資料。")

    # --- 5. User 2 功能：行政管理面板 ---
    if is_admin:
        st.markdown("---")
        st.header("🛡️ 行政管理後台")
        # 顯示所有非結案的案件
        admin_view = st.session_state.db[st.session_state.db['status'] != "Done"]
        
        if not admin_view.empty:
            admin_view = admin_view.sort_values(by='created_at', ascending=False)
            for idx, row in admin_view.iterrows():
                # 計算是否超過五天提醒
                is_overdue = (now - row['created_at']) > timedelta(days=5)
                overdue_label = " ⚠️【逾期提醒】" if is_overdue and row['status'] == "Submitted" else ""
                
                with st.expander(f"【{row['status']}】{row['name']} - ${row['amount']}{overdue_label}"):
                    st.write(f"**申請人姓名：** {row['name']} (ID: {row['user_id']})")
                    st.write(f"**發票日期：** {row['invoice_date']} | **總金額：** {row['amount']}")
                    st.write(f"**支出原因：** {row['reason']}")
                    st.write(f"**申請時間：** {row['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    
                    if row['status'] == "Submitted":
                        c1, c2 = st.columns(2)
                        if c1.button("Review (登錄校內系統)", key=f"admin_rev_{row['id']}"):
                            st.session_state.db.at[idx, 'status'] = "Reviewing"
                            st.session_state.db.at[idx, 'review_time'] = now
                            st.rerun()
                        if c2.button("退回 (五日內未收單據)", key=f"admin_ret_{row['id']}"):
                            st.session_state.db.at[idx, 'status'] = "Returned"
                            st.rerun()
                    
                    elif row['status'] == "Reviewing":
                        # 一小時撤回機制
                        time_diff = now - row['review_time']
                        if time_diff < timedelta(hours=1):
                            mins_left = 60 - int(time_diff.total_seconds() / 60)
                            st.info(f"已標記為 Reviewing，User 1 將在一小時後看到狀態更動。撤回功能尚餘 {mins_left} 分鐘。")
                            if st.button("Undo Review (撤回)", key=f"undo_{row['id']}"):
                                st.session_state.db.at[idx, 'status'] = "Submitted"
                                st.session_state.db.at[idx, 'review_time'] = None
                                st.rerun()
                        else:
                            st.success("已完成審核 (超過 1 小時，無法撤回)")
        else:
            st.write("✅ 暫無待處理案件。")

elif user_id != "":
    st.error("查無此 ID，請聯繫 rileychien@thu.edu.tw。")