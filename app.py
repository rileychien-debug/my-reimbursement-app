import streamlit as st
import pandas as pd
from datetime import datetime

# 設定網頁標題與圖示
st.set_page_config(page_title="小額代墊報帳追蹤", layout="wide")

# --- 1. 基礎設定與資料存儲 (測試版使用 session_state) ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=[
        'id', 'user_id', 'name', 'amount', 'invoice_date', 'reason', 'status', 'created_at'
    ])

# 模擬同仁名單 (身分證字號 : {姓名, 權限})
USER_LIST = {
    "A123456789": {"name": "rileychien", "role": "admin"}, # 行政人員
    "B123456789": {"name": "王小明", "role": "staff"},
    "C123456789": {"name": "李小華", "role": "staff"}
}

# --- 2. 登入介面 ---
st.title("小額代墊報帳追蹤")
user_id = st.text_input("請輸入身分證字號登入", type="password")

if user_id in USER_LIST:
    user_info = USER_LIST[user_id]
    user_name = user_info['name']
    is_admin = (user_info['role'] == "admin")
    
    st.success(f"歡迎回來，{user_name}！")
    
    # --- 3. User 1 功能：新增報帳申請 ---
    with st.expander("➕ 新增代墊報帳申請"):
        amount = st.number_input("代墊金額", min_value=0, max_value=10000, step=1)
        invoice_date = st.date_input("發票日期", value=datetime.now()) # 預設為今天
        reason = st.text_input("支出原因 (例如：買辦公室文具)")
        
        st.write("**實體單據檢查：**")
        c1 = st.checkbox("A. 我已在收據簽名蓋章")
        c2 = st.checkbox("B. 我已註明支出原因")
        c3 = st.checkbox("C. 我已核對統編")
        
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
                    'created_at': datetime.now() # 用於排序
                }
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_data])], ignore_index=True)
                st.balloons()
                st.success("申請成功！請將實體單據交給行政同仁。")
            else:
                st.warning("請確保資訊填寫完整並勾選所有檢查項。")

    # --- 4. User 1 功能：個人進度查詢 ---
    st.subheader("我的報帳進度")
    # 僅顯示自己的案件
    my_claims = st.session_state.db[st.session_state.db['user_id'] == user_id]
    
    if not my_claims.empty:
        # 按申請時間排序，新的在上面
        my_claims = my_claims.sort_values(by='created_at', ascending=False)
        for idx, row in my_claims.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                col1.write(f"📅 發票日: {row['invoice_date']} | **{row['reason']}** (${row['amount']})")
                
                if row['status'] == "Submitted":
                    col2.warning("🟡 實體單據核核中")
                elif row['status'] == "Reviewing":
                    col2.info("🔵 行政已登錄，待撥款")
                    if col3.button("收到款項", key=f"rec_{row['id']}"):
                        st.session_state.db.at[idx, 'status'] = "Done"
                        st.rerun()
                else:
                    col2.success("🟢 已結案 (Done)")
                st.divider()
    else:
        st.info("目前尚無申請紀錄。")

    # --- 5. User 2 功能：行政管理後台 ---
    if is_admin:
        st.markdown("---")
        st.header("🛡️ 行政管理後台")
        
        # 篩選出所有尚未結案的案件 (Submitted & Reviewing)
        admin_view = st.session_state.db[st.session_state.db['status'] != "Done"]
        
        if not admin_view.empty:
            # 按申請時間排序，新的在上面
            admin_view = admin_view.sort_values(by='created_at', ascending=False)
            
            # 使用表格呈現
            st.write("待處理清單：")
            for idx, row in admin_view.iterrows():
                with st.expander(f"【{row['status']}】{row['name']} - ${row['amount']} ({row['reason']})"):
                    st.write(f"**申請人姓名：** {row['name']}")
                    st.write(f"**身分證 ID：** {row['user_id']}")
                    st.write(f"**發票日期：** {row['invoice_date']}")
                    st.write(f"**總金額：** {row['amount']}")
                    st.write(f"**支出原因：** {row['reason']}")
                    st.write(f"**申請時間：** {row['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    
                    if row['status'] == "Submitted":
                        if st.button("確認已登錄校內系統 (Review)", key=f"admin_rev_{row['id']}"):
                            st.session_state.db.at[idx, 'status'] = "Reviewing"
                            st.rerun()
        else:
            st.write("✅ 目前沒有待處理的申請。")

elif user_id != "":
    st.error("查無此 ID，請聯繫系統管理員。")