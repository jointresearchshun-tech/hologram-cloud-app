import streamlit as st
import requests
import json
import time
import base64
from datetime import datetime

st.set_page_config(
    page_title="☁️ クラウドホログラム処理システム",
    page_icon="🔬",
    layout="wide"
)

# ===== GitHub Storage クラス =====
class GitHubStorage:
    def __init__(self, token, repo):
        self.token = token
        self.repo = repo
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def test_connection(self):
        try:
            url = f"https://api.github.com/repos/{self.repo}"
            response = requests.get(url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def list_files(self, folder="data", extensions=None):
        try:
            url = f"https://api.github.com/repos/{self.repo}/contents/{folder}"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                files = response.json()
                if isinstance(files, list):
                    if extensions:
                        files = [f for f in files if any(f['name'].endswith(ext) for ext in extensions)]
                    return [{"name": f["name"], "size": f["size"], "download_url": f["download_url"]} for f in files]
            return []
        except Exception as e:
            st.error(f"ファイル一覧取得エラー: {e}")
            return []
    
    def upload_file(self, content, filename, folder="results", message=None):
        try:
            url = f"https://api.github.com/repos/{self.repo}/contents/{folder}/{filename}"
            existing = requests.get(url, headers=self.headers)
            sha = existing.json().get('sha') if existing.status_code == 200 else None

            content_b64 = base64.b64encode(content).decode('utf-8')
            
            data = {
                "message": message or f"Upload {filename}",
                "content": content_b64
            }
            if sha:
                data["sha"] = sha
            
            response = requests.put(url, json=data, headers=self.headers, timeout=30)
            return response.status_code in [200, 201]
        except Exception as e:
            st.error(f"アップロードエラー: {e}")
            return False

# ===== Google Colab サーバー クライアント =====
class ColabServerClient:
    def __init__(self):
        self.servers = []
        self.current_server = None
    
    def add_server(self, name, url):
        server = {"name": name, "url": url.rstrip('/')}
        try:
            response = requests.get(f"{server['url']}/health", timeout=5)
            if response.status_code == 200:
                server['status'] = 'healthy'
                server['info'] = response.json()
                self.servers.append(server)
                if not self.current_server:
                    self.current_server = server
                return True
        except Exception:
            pass
        server['status'] = 'unreachable'
        return False
    
    def submit_job(self, github_config, input_file, processing_config):
        if not self.current_server:
            return None, "利用可能なColabサーバーがありません"
        try:
            job_data = {
                "job_id": f"job_{int(time.time())}",
                "github_repo": github_config['repo'],
                "github_token": github_config['token'],
                "input_file": input_file,   
                "processing_config": processing_config,
                "timestamp": datetime.now().isoformat()
            }
            response = requests.post(f"{self.current_server['url']}/submit_job", json=job_data, timeout=30)
            if response.status_code == 200:
                return response.json().get('job_id'), None
            else:
                return None, f"ジョブ投入失敗: {response.status_code}"
        except Exception as e:
            return None, f"通信エラー: {e}"
    
    def get_job_status(self, job_id):
        if not self.current_server:
            return {"status": "no_server"}
        try:
            response = requests.get(f"{self.current_server['url']}/job_status/{job_id}", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return {"status": "error", "message": "状態取得失敗"}

# ===== セッション初期化 =====
def initialize_session_state():
    if "github_storage" not in st.session_state:
        try:
            st.session_state.github_storage = GitHubStorage(
                st.secrets["github"]["token"],
                st.secrets["github"]["default_repo"]
            )
        except Exception:
            st.session_state.github_storage = None
    if "colab_client" not in st.session_state:
        st.session_state.colab_client = ColabServerClient()
    if "current_job" not in st.session_state:
        st.session_state.current_job = None

# ===== メイン UI =====
def main():
    st.title("☁️ 完全クラウド型ホログラム処理システム")
    st.markdown("**あなたのPC性能は一切使用しません - すべてクラウドで処理**")

    # GitHub接続設定
    if st.session_state.github_storage is None:
        st.subheader("🔧 GitHub Storage 設定")
        st.warning("Secrets に GitHub Token を設定してください")
    else:
        st.success(f"✅ GitHub 接続成功: {st.session_state.github_storage.repo}")

    # Colabサーバー設定
    if not st.session_state.colab_client.servers:
        st.subheader("🖥️ Google Colab サーバー追加")
        server_name = st.text_input("サーバー名:", value="Colab Server 1")
        server_url = st.text_input("ngrok URL:", placeholder="https://abc123.ngrok.io")
        if st.button("➕ サーバー追加"):
            if st.session_state.colab_client.add_server(server_name, server_url):
                st.success(f"✅ {server_name} を追加しました!")
                st.experimental_rerun()
            else:
                st.error("❌ サーバーに接続できませんでした")

    # ファイルアップロード
    st.subheader("📤 GitHub にファイルをアップロード")
    uploaded_file = st.file_uploader("ローカルファイルを選択", type=["pt", "pth", "zip", "png", "jpg"])
    if uploaded_file is not None and st.button("⬆️ アップロード実行"):
        content = uploaded_file.read()
        success = st.session_state.github_storage.upload_file(
            content,
            uploaded_file.name,
            folder="data",
            message="Upload from Streamlit"
        )
        if success:
            st.success(f"✅ {uploaded_file.name} をアップロードしました！")
            st.experimental_rerun()
        else:
            st.error("❌ アップロード失敗")

    # ファイルダウンロード
    st.subheader("📥 GitHub からダウンロード")
    download_files = st.session_state.github_storage.list_files("data")
    if download_files:
        file_to_download = st.selectbox("ダウンロードするファイルを選択:", [f['name'] for f in download_files])
        if st.button("⬇️ ダウンロード実行"):
            file_info = next(f for f in download_files if f['name'] == file_to_download)
            response = requests.get(file_info["download_url"])
            if response.status_code == 200:
                b64 = base64.b64encode(response.content).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_to_download}">📂 {file_to_download} をダウンロード</a>'
                st.markdown(href, unsafe_allow_html=True)
            else:
                st.error("❌ ダウンロード失敗")

    # メイン処理UI
    if st.session_state.github_storage and st.session_state.colab_client.servers:
        st.subheader("🔬 クラウド処理実行")
        input_files = st.session_state.github_storage.list_files("data", [".pt", ".pth", ".zip"])
        if input_files:
            selected = st.selectbox("処理対象ファイル:", [f['name'] for f in input_files])
            file_info = next(f for f in input_files if f["name"] == selected)

            if st.button("🚀 クラウド処理開始"):
                processing_config = {"type": "hologram_processing"}
                github_config = {
                    "repo": st.session_state.github_storage.repo,
                    "token": st.session_state.github_storage.token
                }
                job_id, error = st.session_state.colab_client.submit_job(github_config, file_info, processing_config)
                if job_id:
                    st.session_state.current_job = job_id
                    st.success(f"✅ 処理開始: {job_id}")
                else:
                    st.error(error)

        if st.session_state.current_job:
            st.info(f"ジョブ監視中: {st.session_state.current_job}")
            job_status = st.session_state.colab_client.get_job_status(st.session_state.current_job)
            st.json(job_status)

if __name__ == "__main__":
    initialize_session_state()
    main()
