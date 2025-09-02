import streamlit as st
import requests
import json
import time
import base64
from datetime import datetime
import logging
from typing import Optional, Dict, List, Tuple

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="☁️ クラウドホログラム処理システム",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== GitHub Storage クラス =====
class GitHubStorage:
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = f"https://api.github.com/repos/{self.repo}"
    
    def test_connection(self) -> bool:
        """GitHub接続テスト"""
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                logger.info(f"GitHub connection successful: {self.repo}")
                return True
            else:
                logger.error(f"GitHub connection failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"GitHub connection error: {e}")
            return False
    
    def list_files(self, folder: str = "data", extensions: Optional[List[str]] = None) -> List[Dict]:
        """指定フォルダ内のファイル一覧を取得"""
        try:
            url = f"{self.base_url}/contents/{folder}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 404:
                # フォルダが存在しない場合は空のリストを返す
                logger.warning(f"Folder '{folder}' not found")
                return []
            elif response.status_code != 200:
                logger.error(f"Failed to list files: {response.status_code}")
                return []
            
            files = response.json()
            if not isinstance(files, list):
                return []
            
            # ファイルのみ抽出（ディレクトリを除外）
            files = [f for f in files if f.get('type') == 'file']
            
            # 拡張子フィルタリング
            if extensions:
                files = [f for f in files if any(f['name'].lower().endswith(ext.lower()) for ext in extensions)]
            
            return [{
                "name": f["name"],
                "size": f["size"],
                "download_url": f["download_url"],
                "sha": f["sha"]
            } for f in files]
            
        except requests.RequestException as e:
            logger.error(f"Error listing files: {e}")
            st.error(f"ファイル一覧取得エラー: {e}")
            return []
    
    def upload_file(self, content: bytes, filename: str, folder: str = "results", 
                   message: Optional[str] = None) -> bool:
        """ファイルをGitHubにアップロード"""
        try:
            file_path = f"{folder}/{filename}"
            url = f"{self.base_url}/contents/{file_path}"
            
            # 既存ファイルの確認
            existing_response = requests.get(url, headers=self.headers, timeout=10)
            sha = existing_response.json().get('sha') if existing_response.status_code == 200 else None
            
            # Base64エンコード
            content_b64 = base64.b64encode(content).decode('utf-8')
            
            data = {
                "message": message or f"Upload {filename} at {datetime.now().isoformat()}",
                "content": content_b64
            }
            if sha:
                data["sha"] = sha
                data["message"] = f"Update {filename} at {datetime.now().isoformat()}"
            
            response = requests.put(url, json=data, headers=self.headers, timeout=30)
            
            if response.status_code in [200, 201]:
                logger.info(f"File uploaded successfully: {file_path}")
                return True
            else:
                logger.error(f"Upload failed: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Upload error: {e}")
            st.error(f"アップロードエラー: {e}")
            return False
    
    def download_file(self, file_info: Dict) -> Optional[bytes]:
        """ファイルをダウンロード"""
        try:
            response = requests.get(file_info["download_url"], timeout=30)
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Download failed: {response.status_code}")
                return None
        except requests.RequestException as e:
            logger.error(f"Download error: {e}")
            return None

# ===== Google Colab サーバー クライアント =====
class ColabServerClient:
    def __init__(self):
        self.servers: List[Dict] = []
        self.current_server: Optional[Dict] = None
    
    def add_server(self, name: str, url: str) -> bool:
        """新しいColabサーバーを追加"""
        server = {
            "name": name, 
            "url": url.rstrip('/'),
            "added_at": datetime.now().isoformat()
        }
        
        # ヘルスチェック
        try:
            response = requests.get(f"{server['url']}/health", timeout=5)
            if response.status_code == 200:
                server['status'] = 'healthy'
                server['info'] = response.json()
                self.servers.append(server)
                
                # 最初のサーバーを現在のサーバーに設定
                if not self.current_server:
                    self.current_server = server
                
                logger.info(f"Server added successfully: {name}")
                return True
            else:
                logger.warning(f"Server unhealthy: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Server connection failed: {e}")
        
        server['status'] = 'unreachable'
        return False
    
    def remove_server(self, server_name: str) -> bool:
        """サーバーを削除"""
        self.servers = [s for s in self.servers if s['name'] != server_name]
        if self.current_server and self.current_server['name'] == server_name:
            self.current_server = self.servers[0] if self.servers else None
        return True
    
    def switch_server(self, server_name: str) -> bool:
        """使用するサーバーを切り替え"""
        for server in self.servers:
            if server['name'] == server_name:
                self.current_server = server
                return True
        return False
    
    def check_all_servers(self) -> None:
        """全サーバーの状態をチェック"""
        for server in self.servers:
            try:
                response = requests.get(f"{server['url']}/health", timeout=5)
                server['status'] = 'healthy' if response.status_code == 200 else 'unhealthy'
                if response.status_code == 200:
                    server['info'] = response.json()
            except requests.RequestException:
                server['status'] = 'unreachable'
    
    def submit_job(self, github_config: Dict, input_file: Dict, 
                   processing_config: Dict) -> Tuple[Optional[str], Optional[str]]:
        """処理ジョブをColabサーバーに投入"""
        if not self.current_server:
            return None, "利用可能なColabサーバーがありません"
        
        if self.current_server['status'] != 'healthy':
            return None, f"現在のサーバー '{self.current_server['name']}' は利用できません"
        
        try:
            job_data = {
                "job_id": f"job_{int(time.time())}_{hash(input_file['name']) % 10000}",
                "github_repo": github_config['repo'],
                "github_token": github_config['token'],
                "input_file": input_file,
                "processing_config": processing_config,
                "timestamp": datetime.now().isoformat(),
                "client_info": "Streamlit Cloud Processing System"
            }
            
            response = requests.post(
                f"{self.current_server['url']}/submit_job", 
                json=job_data, 
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('job_id')
                logger.info(f"Job submitted successfully: {job_id}")
                return job_id, None
            else:
                error_msg = f"ジョブ投入失敗: {response.status_code} - {response.text[:100]}"
                logger.error(error_msg)
                return None, error_msg
                
        except requests.RequestException as e:
            error_msg = f"通信エラー: {e}"
            logger.error(error_msg)
            return None, error_msg
    
    def get_job_status(self, job_id: str) -> Dict:
        """ジョブの状態を取得"""
        if not self.current_server:
            return {"status": "no_server", "message": "利用可能なサーバーがありません"}
        
        try:
            response = requests.get(
                f"{self.current_server['url']}/job_status/{job_id}", 
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"status": "not_found", "message": "ジョブが見つかりません"}
            else:
                return {"status": "error", "message": f"状態取得失敗: {response.status_code}"}
                
        except requests.RequestException as e:
            return {"status": "error", "message": f"通信エラー: {e}"}
    
    def cancel_job(self, job_id: str) -> bool:
        """ジョブをキャンセル"""
        if not self.current_server:
            return False
        
        try:
            response = requests.post(
                f"{self.current_server['url']}/cancel_job/{job_id}",
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

# ===== Colab統合UI =====
def integrated_colab_ui():
    """統合されたColab UIを提供"""
    st.subheader("🖥️ Google Colab サーバー管理")
    
    tab1, tab2, tab3 = st.tabs(["🔧 サーバー設定", "📋 サーバー一覧", "🚀 クイック起動"])
    
    with tab1:
        st.write("**新しいColabサーバーを追加:**")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            server_name = st.text_input("サーバー名:", placeholder="My Colab Server", key="server_name_input")
        with col2:
            server_url = st.text_input(
                "ngrok URL:", 
                placeholder="https://abc123.ngrok.io", 
                help="ColabからのngrokURLを貼り付けてください",
                key="server_url_input"
            )
        
        if st.button("➕ サーバー追加", type="primary"):
            if server_name and server_url:
                with st.spinner(f"{server_name} に接続中..."):
                    if st.session_state.colab_client.add_server(server_name, server_url):
                        st.success(f"✅ {server_name} を追加しました！")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ サーバーに接続できませんでした")
                        st.info("以下を確認してください：")
                        st.info("• ngrok URLが正しい")
                        st.info("• Colabサーバーが動作中")
                        st.info("• ファイアウォールの問題がない")
            else:
                st.error("サーバー名とURLの両方を入力してください")
    
    with tab2:
        if st.session_state.colab_client.servers:
            st.write("**登録済みサーバー一覧:**")
            
            for i, server in enumerate(st.session_state.colab_client.servers):
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        status_icons = {"healthy": "🟢", "unhealthy": "🟡", "unreachable": "🔴"}
                        current_mark = " ⭐(現在使用中)" if server == st.session_state.colab_client.current_server else ""
                        st.write(f"{status_icons.get(server['status'], '⚪')} **{server['name']}**{current_mark}")
                        st.caption(f"URL: {server['url']}")
                    
                    with col2:
                        if st.button("選択", key=f"select_{i}"):
                            st.session_state.colab_client.switch_server(server['name'])
                            st.success(f"サーバーを {server['name']} に切り替えました")
                            st.rerun()
                    
                    with col3:
                        if st.button("削除", key=f"delete_{i}"):
                            st.session_state.colab_client.remove_server(server['name'])
                            st.success(f"{server['name']} を削除しました")
                            st.rerun()
                    
                    with col4:
                        if st.button("テスト", key=f"test_{i}"):
                            with st.spinner("接続テスト中..."):
                                st.session_state.colab_client.check_all_servers()
                                st.rerun()
                
                st.divider()
            
            if st.button("🔄 全サーバー状態更新"):
                with st.spinner("全サーバーの状態をチェック中..."):
                    st.session_state.colab_client.check_all_servers()
                st.rerun()
        else:
            st.info("登録されているサーバーがありません。新しいサーバーを追加してください。")
    
    with tab3:
        st.write("**Colab サーバーのクイック起動コード:**")
        
        colab_code = '''
# Google Colabで実行するコード
!pip install flask pyngrok requests
!pip install torch torchvision

# サーバーコードを作成
server_code = """
from flask import Flask, request, jsonify
import json
import time
from datetime import datetime
import threading
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ジョブ管理
jobs = {}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server_info": "Colab GPU Server",
        "active_jobs": len(jobs)
    })

@app.route('/submit_job', methods=['POST'])
def submit_job():
    job_data = request.get_json()
    job_id = job_data.get('job_id', f'job_{int(time.time())}')
    
    jobs[job_id] = {
        "status": "pending",
        "submitted_at": datetime.now().isoformat(),
        **job_data
    }
    
    # バックグラウンドで処理開始
    threading.Thread(target=process_job, args=(job_id,)).start()
    
    return jsonify({"job_id": job_id, "status": "submitted"})

@app.route('/job_status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    if job_id in jobs:
        return jsonify(jobs[job_id])
    else:
        return jsonify({"error": "Job not found"}), 404

@app.route('/cancel_job/<job_id>', methods=['POST'])
def cancel_job(job_id):
    if job_id in jobs:
        jobs[job_id]["status"] = "cancelled"
        return jsonify({"status": "cancelled"})
    return jsonify({"error": "Job not found"}), 404

def process_job(job_id):
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = datetime.now().isoformat()
        
        # ここに実際の処理を実装
        print(f"Processing job {job_id}")
        
        # サンプル処理（5秒待機）
        time.sleep(5)
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
"""

# ファイルに保存
with open('colab_server.py', 'w') as f:
    f.write(server_code)

# ngrok設定
from pyngrok import ngrok
import threading
import subprocess

# Flask サーバーをバックグラウンドで起動
server_process = subprocess.Popen(['python', 'colab_server.py'])

# ngrokトンネルを作成
public_url = ngrok.connect(5000)
print(f"✅ Colab サーバー起動完了!")
print(f"🌐 Public URL: {public_url}")
print(f"📋 この URL を Streamlit アプリに登録してください")
print("🔄 Ctrl+C で終了")

try:
    server_process.wait()
except KeyboardInterrupt:
    print("\\n🛑 サーバーを終了中...")
    ngrok.disconnect(public_url)
    server_process.terminate()
'''
        
        st.code(colab_code, language='python')
        
        st.info("👆 このコードをGoogle Colabの新しいノートブックにコピー&ペーストして実行してください")
        
        with st.expander("📖 使用方法"):
            st.markdown("""
            1. **Google Colabを開く**: [colab.research.google.com](https://colab.research.google.com)
            2. **新しいノートブック**を作成
            3. **GPUを有効化**: ランタイム → ランタイムのタイプを変更 → GPU
            4. **上のコード**をセルにコピーして実行
            5. **表示されるURL**をこのアプリの「サーバー追加」に登録
            6. **処理開始**！
            """)

# ===== セッション状態の初期化 =====
def initialize_session_state():
    """セッション状態を初期化"""
    if "github_storage" not in st.session_state:
        st.session_state.github_storage = None
        
    if "colab_client" not in st.session_state:
        st.session_state.colab_client = ColabServerClient()
        
    if "current_jobs" not in st.session_state:
        st.session_state.current_jobs = {}
        
    if "processing_history" not in st.session_state:
        st.session_state.processing_history = []

def setup_github_connection():
    """GitHub接続の設定"""
    st.subheader("🔧 GitHub Storage 設定")
    
    # GitHub接続状態の確認
    if st.session_state.github_storage:
        st.success(f"✅ GitHub 接続済み: {st.session_state.github_storage.repo}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 接続テスト"):
                with st.spinner("接続確認中..."):
                    if st.session_state.github_storage.test_connection():
                        st.success("✅ 接続確認OK")
                    else:
                        st.error("❌ 接続に問題があります")
                        st.session_state.github_storage = None
                        st.rerun()
        
        with col2:
            if st.button("🔌 接続をリセット"):
                st.session_state.github_storage = None
                st.success("接続をリセットしました")
                st.rerun()
        
        return True
    
    # 自動設定の試行
    github_connected = False
    try:
        if st.session_state.github_storage is None:
            # 複数の設定パターンを試行
            token = None
            repo = None
            
            # Streamlit Secrets の各パターンを試行
            secrets_patterns = [
                ("github", ["token", "default_repo"]),
                ("github", ["TOKEN", "REPO"]),
                ("GITHUB", ["TOKEN", "REPO"]),
                (None, ["GITHUB_TOKEN", "GITHUB_REPO"]),
                (None, ["github_token", "github_repo"])
            ]
            
            for section, keys in secrets_patterns:
                try:
                    if section:
                        token = st.secrets[section][keys[0]]
                        repo = st.secrets[section][keys[1]]
                    else:
                        token = st.secrets[keys[0]]
                        repo = st.secrets[keys[1]]
                    
                    if token and repo:
                        break
                except (KeyError, AttributeError):
                    continue
            
            if token and repo:
                with st.spinner("GitHub接続中..."):
                    github_storage = GitHubStorage(token, repo)
                    if github_storage.test_connection():
                        st.session_state.github_storage = github_storage
                        st.success(f"✅ GitHub 自動接続成功: {repo}")
                        github_connected = True
                        st.rerun()
                    else:
                        st.error(f"❌ GitHub 接続失敗: {repo}")
                        st.error("以下を確認してください:")
                        st.error("• トークンが有効")
                        st.error("• リポジトリが存在する")
                        st.error("• トークンに適切な権限がある (repo スコープ)")
            else:
                st.info("💡 GitHub設定が見つからないため、手動設定してください")
                
    except Exception as e:
        st.warning(f"⚠️ 設定読み込みエラー: {str(e)}")
    
    # 手動設定UI
    if not github_connected:
        with st.expander("🔧 GitHub 手動設定", expanded=True):
            st.markdown("""
            **Streamlit Cloud での GitHub 設定方法:**
            
            1. **GitHubでPersonal Access Tokenを作成:**
               - GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
               - "Generate new token (classic)"
               - Expiration: 無期限 または 適切な期間
               - Scopes: `repo` にチェック ✅
               - "Generate token" → トークンをコピー
            
            2. **GitHubでリポジトリを作成:**
               - 新しいリポジトリを作成
               - `data/` フォルダを作成 (README.md等を追加)
               - `results/` フォルダも作成しておく
            
            3. **Streamlit Cloud のSecrets設定:**
            """)
            
            st.code('''
# App settings → Secrets に以下を追加:
[github]
token = "ghp_your_token_here"
default_repo = "username/repository-name"
            ''')
            
            st.divider()
            
            # 手動入力フォーム
            st.write("**または手動で入力:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                manual_token = st.text_input(
                    "GitHub Personal Access Token:", 
                    type="password",
                    placeholder="ghp_xxxxxxxxxxxxxxxxxxxx",
                    help="GitHubのPersonal Access Token (repo権限必要)"
                )
            
            with col2:
                manual_repo = st.text_input(
                    "Repository (owner/repo):", 
                    placeholder="username/my-hologram-project",
                    help="GitHub リポジトリの形式: ユーザー名/リポジトリ名"
                )
            
            if st.button("🔗 GitHub 接続テスト", type="primary"):
                if manual_token and manual_repo:
                    with st.spinner("GitHub 接続テスト中..."):
                        github_storage = GitHubStorage(manual_token, manual_repo)
                        if github_storage.test_connection():
                            st.session_state.github_storage = github_storage
                            st.success(f"✅ GitHub 接続成功: {manual_repo}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ GitHub 接続に失敗しました")
                            st.error("確認事項:")
                            st.error("• トークンが正しい (ghp_で始まる)")
                            st.error("• リポジトリが存在し、アクセス可能")
                            st.error("• トークンにrepo権限がある")
                else:
                    st.error("TokenとRepositoryの両方を入力してください")
    
    return st.session_state.github_storage is not None

def file_management_ui():
    """ファイル管理UI"""
    if not st.session_state.github_storage:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📤 ファイルアップロード")
        
        folder_type = st.selectbox("保存先フォルダ:", ["data", "results", "custom"])
        if folder_type == "custom":
            custom_folder = st.text_input("カスタムフォルダ名:")
            folder = custom_folder if custom_folder else "data"
        else:
            folder = folder_type
        
        uploaded_file = st.file_uploader(
            "ファイルを選択", 
            type=["pt", "pth", "zip", "png", "jpg", "jpeg", "csv", "txt", "json"]
        )
        
        if uploaded_file is not None:
            st.write(f"**ファイル情報:**")
            st.write(f"- 名前: {uploaded_file.name}")
            st.write(f"- サイズ: {uploaded_file.size:,} bytes")
            st.write(f"- 保存先: {folder}/")
            
            if st.button("⬆️ アップロード実行"):
                with st.spinner("アップロード中..."):
                    content = uploaded_file.read()
                    success = st.session_state.github_storage.upload_file(
                        content, uploaded_file.name, folder=folder
                    )
                    
                if success:
                    st.success(f"✅ {uploaded_file.name} をアップロードしました！")
                else:
                    st.error("❌ アップロード失敗")
    
    with col2:
        st.subheader("📥 ファイル管理")
        
        folder_to_view = st.selectbox("フォルダ選択:", ["data", "results"], key="view_folder")
        
        if st.button("🔄 ファイル一覧更新"):
            st.rerun()
        
        files = st.session_state.github_storage.list_files(folder_to_view)
        
        if files:
            st.write(f"**{folder_to_view} フォルダ内のファイル:**")
            
            for file_info in files:
                with st.container():
                    file_col1, file_col2 = st.columns([3, 1])
                    
                    with file_col1:
                        st.write(f"📄 {file_info['name']} ({file_info['size']:,} bytes)")
                    
                    with file_col2:
                        if st.button("⬇️", key=f"download_{file_info['name']}", help="ダウンロード"):
                            with st.spinner("ダウンロード中..."):
                                content = st.session_state.github_storage.download_file(file_info)
                                
                            if content:
                                b64 = base64.b64encode(content).decode()
                                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_info["name"]}">📂 {file_info["name"]} をダウンロード</a>'
                                st.markdown(href, unsafe_allow_html=True)
                            else:
                                st.error("ダウンロード失敗")
