import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. 基礎設定與模擬資料庫 ---
# 實際使用時，建議連結 Google Sheets 或是真正的資料庫
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=[
        'id', 'name', 'amount', 'reason', 'tax_id', 'status', 'timestamp'
    ])

# 模擬同仁名單 (身分證字號 : 姓名)
USER_LIST = {
    "A123456789": {"name": "rileychien", "role": "admin"}, # 行政人員
    "B123456789": {"name": "王小明", "role": "staff"},
    "C123456789": {"name": "李小華", "role": "staff"}
}

# --- 2. 登入邏輯 ---
st.title("校內小額代墊報帳追蹤平台")

user_id = st.text_input("請輸入身分證字號登入", type="password")

if user_id in USER_LIST:
    user_info = USER_LIST[user_id]
    user_name = user_info['name']
    is_admin = (user_info['role'] == "admin")
    
    st.success(f"歡迎回來，{user_name}！")
    
    # --- 3. User 1 功能：填寫報帳單 ---
    with st.expander("➕ 新增代墊報帳申請"):
        amount = st.number_input("代墊金額", min_value=0, max_value=10000)
        reason = st.text_input("支出原因")
        tax_id = st.text_input("統一編號 (若無請填無)")
        st.write("**請確認實體單據：**")
        c1 = st.checkbox("A. 我已在收據簽名蓋章")
        c2 = st.checkbox("B. 我已註明支出原因")
        c3 = st.checkbox("C. 我已核對統編")
        
        if st.button("確認送出 (Submitted)"):
            if c1 and c2 and c3 and amount > 0:
                new_data = {
                    'id': len(st.session_state.db) + 1,
                    'name': user_name,
                    'amount': amount,
                    'reason': reason,
                    'tax_id': tax_id,
                    'status': "Submitted",
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_data])], ignore_index=True)
                st.balloons()
                st.success("申請已送出！請將實體單據繳交給行政人員。")
            else:
                st.warning("請完整填寫資訊並勾選檢查項目。")

    # --- 4. User 1 功能：我的申請進度 ---
    st.subheader("我的報帳進度")
    my_claims = st.session_state.db[st.session_state.db['name'] == user_name]
    
    if not my_claims.empty:
        for idx, row in my_claims.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"**[{row['timestamp']}]** {row['reason']} - ${row['amount']}")
            
            # 狀態顯示
            status = row['status']
            if status == "Submitted":
                col2.warning("🟡 實體單據審核中")
            elif status == "Reviewing":
                col2.info("🔵 行政已登錄，待撥款")
                if col3.button("收到錢了", key=f"rec_{row['id']}"):
                    st.session_state.db.at[idx, 'status'] = "Done"
                    st.rerun()
            else:
                col2.success("🟢 已結案 (Done)")
    else:
        st.info("目前沒有您的報帳紀錄。")

    # --- 5. User 2 功能：行政管理面板 ---
    if is_admin:
        st.divider()
        st.header("🛡️ 行政管理後台")
        pending_claims = st.session_state.db[st.session_state.db['status'] == "Submitted"]
        
        if not pending_claims.empty:
            st.write("待處理清單 (請於校內系統登錄後點選 Review)")
            for idx, row in pending_claims.iterrows():
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"**{row['name']}**: ${row['amount']}")
                c2.write(f"原因: {row['reason']}")
                if c3.button("Review", key=f"rev_{row['id']}"):
                    st.session_state.db.at[idx, 'status'] = "Reviewing"
                    st.rerun()
        else:
            st.write("目前沒有待處理的申請。")

elif user_id != "":
    st.error("查無此身分證字號，請洽單位行政人員。")