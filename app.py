# 完全クラウド型ホログラム処理システム
# Streamlit Community Cloud + Google Colab + GitHub Storage

import streamlit as st
import requests
import json
import time
import base64
import io
from datetime import datetime

st.set_page_config(
    page_title="☁️ クラウドホログラム処理システム",
    page_icon="🔬",
    layout="wide"
)

# ===== GitHub Storage 連携 =====
class GitHubStorage:
    def __init__(self, token, repo):
        self.token = token
        self.repo = repo
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def test_connection(self):
        """GitHub接続テスト"""
        try:
            url = f"https://api.github.com/repos/{self.repo}"
            response = requests.get(url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def list_files(self, folder="data", extension=None):
        """ファイル一覧取得"""
        try:
            url = f"https://api.github.com/repos/{self.repo}/contents/{folder}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                files = response.json()
                if isinstance(files, list):
                    if extension:
                        files = [f for f in files if f['name'].endswith(f'.{extension}')]
                    return [{"name": f["name"], "size": f["size"], "download_url": f["download_url"]} for f in files]
            return []
        except Exception as e:
            st.error(f"ファイル一覧取得エラー: {e}")
            return []
    
    def upload_file(self, content, filename, folder="data", message=None):
        """ファイルアップロード"""
        try:
            url = f"https://api.github.com/repos/{self.repo}/contents/{folder}/{filename}"
            
            # 既存ファイルチェック
            existing = requests.get(url, headers=self.headers)
            sha = existing.json().get('sha') if existing.status_code == 200 else None
            
            # アップロードデータ準備
            if isinstance(content, bytes):
                content_b64 = base64.b64encode(content).decode('utf-8')
            else:
                content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
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

# ===== Google Colab サーバー連携 =====
class ColabServerClient:
    def __init__(self):
        self.servers = []
        self.current_server = None
    
    def add_server(self, name, url):
        """Colabサーバーを追加"""
        server = {"name": name, "url": url.rstrip('/')}
        
        # 接続テスト
        try:
            response = requests.get(f"{server['url']}/health", timeout=5)
            if response.status_code == 200:
                server['status'] = 'healthy'
                server['info'] = response.json()
                self.servers.append(server)
                if not self.current_server:
                    self.current_server = server
                return True
        except:
            pass
        
        server['status'] = 'unreachable'
        return False
    
    def get_server_status(self, server):
        """サーバー状態取得"""
        try:
            response = requests.get(f"{server['url']}/health", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {"status": "unreachable"}
    
    def submit_job(self, github_config, input_file, processing_config):
        """処理ジョブ投入"""
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
            
            response = requests.post(
                f"{self.current_server['url']}/submit_job",
                json=job_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['job_id'], None
            else:
                return None, f"ジョブ投入失敗: {response.status_code}"
                
        except Exception as e:
            return None, f"通信エラー: {e}"
    
    def get_job_status(self, job_id):
        """ジョブ状態確認"""
        if not self.current_server:
            return {"status": "no_server"}
        
        try:
            response = requests.get(
                f"{self.current_server['url']}/job_status/{job_id}",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {"status": "error", "message": "状態取得失敗"}

# ===== セッション初期化 =====
if "github_storage" not in st.session_state:
    st.session_state.github_storage = None
if "colab_client" not in st.session_state:
    st.session_state.colab_client = ColabServerClient()
if "current_job" not in st.session_state:
    st.session_state.current_job = None

# ===== メイン UI =====
st.title("☁️ 完全クラウド型ホログラム処理システム")
st.markdown("**あなたのPC性能は一切使用しません - すべてクラウドで処理**")

# GitHub接続設定
if st.session_state.github_storage is None:
    st.subheader("🔧 GitHub Storage 設定")
    
    github_token = st.text_input("GitHub Token:", type="password")
    github_repo = st.text_input("リポジトリ (user/repo):", placeholder="username/hologram-storage")
    
    if st.button("🔌 GitHub接続"):
        if github_token and github_repo:
            storage = GitHubStorage(github_token, github_repo)
            if storage.test_connection():
                st.session_state.github_storage = storage
                st.success("✅ GitHub接続成功!")
                st.rerun()
            else:
                st.error("❌ GitHub接続失敗")

# Colabサーバー設定
if not st.session_state.colab_client.servers:
    st.subheader("🖥️ Google Colab サーバー追加")
    
    server_name = st.text_input("サーバー名:", value="Colab Server 1")
    server_url = st.text_input("ngrok URL:", placeholder="https://abc123.ngrok.io")
    
    if st.button("➕ サーバー追加"):
        if server_name and server_url:
            if st.session_state.colab_client.add_server(server_name, server_url):
                st.success(f"✅ {server_name} を追加しました!")
                st.rerun()
            else:
                st.error("❌ サーバーに接続できませんでした")

# メイン処理UI
if st.session_state.github_storage and st.session_state.colab_client.servers:
    st.subheader("🔬 クラウド処理実行")
    
    # ファイル選択
    input_files = st.session_state.github_storage.list_files("data", "pt")
    if input_files:
        selected_file = st.selectbox("処理対象ファイル:", [f['name'] for f in input_files])
        
        # 処理実行
        if st.button("🚀 クラウド処理開始"):
            processing_config = {"type": "test_processing"}
            github_config = {
                "repo": st.session_state.github_storage.repo,
                "token": st.session_state.github_storage.token
            }
            
            job_id, error = st.session_state.colab_client.submit_job(
                github_config, selected_file, processing_config
            )
            
            if job_id:
                st.session_state.current_job = job_id
                st.success(f"✅ 処理開始: {job_id}")
    
    # ジョブ監視
    if st.session_state.current_job:
        job_status = st.session_state.colab_client.get_job_status(st.session_state.current_job)
        st.json(job_status)
