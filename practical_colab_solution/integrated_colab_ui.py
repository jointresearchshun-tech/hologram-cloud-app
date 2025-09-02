# practical_colab_solution.py

import streamlit as st
import requests

def integrated_colab_ui():
    st.subheader("🤝 Google Colab 接続")

    try:
        server_name = st.secrets["colab"]["server_1_name"]
        server_url = st.secrets["colab"]["server_1_url"]

        st.write(f"🔗 {server_name}: {server_url}")

        # FastAPI の /health エンドポイントを叩いて接続テスト
        try:
            resp = requests.get(f"{server_url}/health", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"✅ {server_name} 接続成功！")
                st.json(data)
            else:
                st.warning(f"⚠️ {server_name} 応答あり (status={resp.status_code})")
        except Exception as e:
            st.error(f"❌ {server_name} に接続できません: {e}")

    except Exception as e:
        st.warning(f"⚠️ Colab サーバー設定が見つかりません: {e}")
