import streamlit as st
import requests
import json
import time
import base64
from datetime import datetime
import logging
from typing import Optional, Dict, List, Tuple

import streamlit as st

st.write("All secret keys:", list(st.secrets.keys()))
st.write("GitHub secret block:", st.secrets.get("github"))

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
    
    # Secrets からの自動設定を試行
    github_connected = False
    try:
        if st.session_state.github_storage is None:
            # 複数の設定パターンを試行
            token = None
            repo = None
            
            # パターン1: github.token, github.default_repo
            try:
                token = st.secrets["github"]["token"]
                repo = st.secrets["github"]["default_repo"]
            except KeyError:
                pass
            
            # パターン2: GITHUB_TOKEN, GITHUB_REPO
            if not token:
                try:
                    token = st.secrets["GITHUB_TOKEN"]
                    repo = st.secrets["GITHUB_REPO"]
                except KeyError:
                    pass
            
            # パターン3: github_token, github_repo
            if not token:
                try:
                    token = st.secrets["github_token"]
                    repo = st.secrets["github_repo"]
                except KeyError:
                    pass
            
            if token and repo:
                github_storage = GitHubStorage(token, repo)
                if github_storage.test_connection():
                    st.session_state.github_storage = github_storage
                    st.success(f"✅ GitHub 自動接続成功: {repo}")
                    github_connected = True
                else:
                    st.error(f"❌ GitHub 接続失敗: {repo}")
                    st.info("トークンの権限やリポジトリ名を確認してください")
            else:
                st.info("💡 Secrets に GitHub 設定が見つかりません")
                
    except Exception as e:
        st.warning(f"⚠️ Secrets 読み込みエラー: {str(e)}")
    
    # Secrets設定の詳細ガイド
    if not github_connected:
        with st.expander("📋 Secrets設定ガイド", expanded=False):
            st.markdown("""
            **Streamlit Cloud での Secrets 設定方法:**
            
            1. **GitHub Personal Access Token を作成:**
               - GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
               - "Generate new token (classic)" をクリック
               - スコープで `repo` にチェック
               - トークンをコピー
            
            2. **Streamlit Cloud の Secrets に追加:**
               ```toml
               [github]
               token = "ghp_your_token_here"
               default_repo = "username/repository-name"
               ```
               
            **または:**
               ```toml
               GITHUB_TOKEN = "ghp_your_token_here"
               GITHUB_REPO = "username/repository-name"
               ```
            
            3. **リポジトリを作成:**
               - GitHub で新しいリポジトリを作成
               - `data/` と `results/` フォルダを作成
            """)
    
    # 手動設定UI
    with st.expander("🔧 手動 GitHub 設定", expanded=not github_connected):
        col1, col2 = st.columns(2)
        
        with col1:
            manual_token = st.text_input(
                "GitHub Token:", 
                type="password",
                help="ghp_ で始まるPersonal Access Token"
            )
        
        with col2:
            manual_repo = st.text_input(
                "Repository (owner/repo):", 
                placeholder="username/repository-name",
                help="例: john/my-hologram-project"
            )
        
        if st.button("🔗 GitHub 接続テスト"):
            if manual_token and manual_repo:
                with st.spinner("接続テスト中..."):
                    github_storage = GitHubStorage(manual_token, manual_repo)
                    if github_storage.test_connection():
                        st.session_state.github_storage = github_storage
                        st.success(f"✅ GitHub 手動接続成功: {manual_repo}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ GitHub 接続に失敗しました")
                        st.info("以下を確認してください:")
                        st.info("• トークンが正しい")
                        st.info("• リポジトリが存在する")
                        st.info("• トークンに repo 権限がある")
            else:
                st.error("Token と Repository を両方入力してください")
        
        # テスト用のサンプル設定
        if st.button("📝 サンプル設定で試す"):
            st.code("""
# GitHub でテスト用リポジトリを作成後、以下をSecrets に設定:
[github]
token = "ghp_your_actual_token_here"
default_repo = "your-username/hologram-test"
            """)
    
    return st.session_state.github_storage is not None

def manage_colab_servers():
    """Colabサーバー管理UI"""
    st.subheader("🖥️ Google Colab サーバー管理")
    
    # 既存サーバー一覧
    if st.session_state.colab_client.servers:
        st.write("**登録済みサーバー:**")
        for i, server in enumerate(st.session_state.colab_client.servers):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                status_color = {"healthy": "🟢", "unhealthy": "🟡", "unreachable": "🔴"}
                current_mark = " (現在)" if server == st.session_state.colab_client.current_server else ""
                st.write(f"{status_color.get(server['status'], '⚪')} {server['name']}{current_mark}")
            
            with col2:
                if st.button(f"選択", key=f"select_{i}"):
                    st.session_state.colab_client.switch_server(server['name'])
                    st.success(f"サーバーを {server['name']} に切り替えました")
                    st.rerun()
            
            with col3:
                if st.button(f"削除", key=f"delete_{i}"):
                    st.session_state.colab_client.remove_server(server['name'])
                    st.success(f"{server['name']} を削除しました")
                    st.rerun()
            
            with col4:
                if st.button(f"テスト", key=f"test_{i}"):
                    with st.spinner("テスト中..."):
                        st.session_state.colab_client.check_all_servers()
                    st.rerun()
    
    # 新しいサーバー追加
    with st.expander("🆕 新しいサーバーを追加"):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            server_name = st.text_input("サーバー名:", placeholder="Colab Server 1")
        with col2:
            server_url = st.text_input("ngrok URL:", placeholder="https://abc123.ngrok.io")
        
        if st.button("➕ サーバー追加"):
            if server_name and server_url:
                with st.spinner(f"{server_name} に接続中..."):
                    if st.session_state.colab_client.add_server(server_name, server_url):
                        st.success(f"✅ {server_name} を追加しました！")
                        st.rerun()
                    else:
                        st.error("❌ サーバーに接続できませんでした。URLを確認してください。")
            else:
                st.error("サーバー名とURLを入力してください")

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
        else:
            st.info(f"{folder_to_view} フォルダにファイルがありません")

def processing_ui():
    """メイン処理UI"""
    if not (st.session_state.github_storage and st.session_state.colab_client.servers):
        st.warning("GitHub接続とColabサーバーの設定を完了してください")
        return
    
    st.subheader("🔬 クラウド処理実行")
    
    # 入力ファイル選択
    input_files = st.session_state.github_storage.list_files("data", [".pt", ".pth", ".zip"])
    
    if not input_files:
        st.info("処理対象のファイルがありません。先にファイルをアップロードしてください。")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_file = st.selectbox("処理対象ファイル:", [f['name'] for f in input_files])
        file_info = next(f for f in input_files if f["name"] == selected_file)
        
        st.write(f"**選択ファイル:** {file_info['name']} ({file_info['size']:,} bytes)")
    
    with col2:
        processing_type = st.selectbox(
            "処理タイプ:", 
            ["hologram_processing", "image_analysis", "custom_processing"]
        )
    
    # 処理設定
    with st.expander("⚙️ 詳細設定"):
        col1, col2 = st.columns(2)
        
        with col1:
            batch_size = st.number_input("バッチサイズ:", min_value=1, max_value=128, value=32)
            quality = st.select_slider("品質設定:", options=["低", "中", "高"], value="中")
        
        with col2:
            use_gpu = st.checkbox("GPU使用", value=True)
            save_intermediate = st.checkbox("中間結果を保存", value=False)
    
    # 処理実行
    if st.button("🚀 クラウド処理開始", type="primary"):
        processing_config = {
            "type": processing_type,
            "batch_size": batch_size,
            "quality": quality,
            "use_gpu": use_gpu,
            "save_intermediate": save_intermediate,
            "output_folder": "results"
        }
        
        github_config = {
            "repo": st.session_state.github_storage.repo,
            "token": st.session_state.github_storage.token
        }
        
        with st.spinner("ジョブを投入中..."):
            job_id, error = st.session_state.colab_client.submit_job(
                github_config, file_info, processing_config
            )
        
        if job_id:
            st.session_state.current_jobs[job_id] = {
                "file": selected_file,
                "config": processing_config,
                "started_at": datetime.now(),
                "server": st.session_state.colab_client.current_server['name']
            }
            st.success(f"✅ 処理開始: {job_id}")
            st.rerun()
        else:
            st.error(f"❌ {error}")

def job_monitoring_ui():
    """ジョブ監視UI"""
    if not st.session_state.current_jobs:
        return
    
    st.subheader("📊 処理状況監視")
    
    for job_id, job_info in list(st.session_state.current_jobs.items()):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{job_id}**")
                st.write(f"ファイル: {job_info['file']} | サーバー: {job_info['server']}")
            
            with col2:
                if st.button("🔄", key=f"refresh_{job_id}", help="状態更新"):
                    job_status = st.session_state.colab_client.get_job_status(job_id)
                    st.json(job_status)
            
            with col3:
                if st.button("❌", key=f"cancel_{job_id}", help="キャンセル"):
                    if st.session_state.colab_client.cancel_job(job_id):
                        del st.session_state.current_jobs[job_id]
                        st.success("ジョブをキャンセルしました")
                        st.rerun()
            
            # 状態表示
            job_status = st.session_state.colab_client.get_job_status(job_id)
            
            status_colors = {
                "pending": "🟡",
                "running": "🟢", 
                "completed": "✅",
                "failed": "❌",
                "cancelled": "⚪"
            }
            
            status = job_status.get("status", "unknown")
            st.write(f"{status_colors.get(status, '❓')} 状態: {status}")
            
            if status in ["completed", "failed", "cancelled"]:
                # 完了したジョブは履歴に移動
                st.session_state.processing_history.append({
                    "job_id": job_id,
                    "status": status,
                    "completed_at": datetime.now(),
                    **job_info
                })
                del st.session_state.current_jobs[job_id]
                st.rerun()
            
            st.divider()

# ===== サイドバー =====
def sidebar():
    """サイドバーUI"""
    with st.sidebar:
        st.title("⚙️ システム設定")
        
        # システム状態
        st.subheader("📈 システム状態")
        
        github_status = "✅ 接続済み" if st.session_state.github_storage else "❌ 未接続"
        st.write(f"GitHub: {github_status}")
        
        colab_status = f"✅ {len(st.session_state.colab_client.servers)}台" if st.session_state.colab_client.servers else "❌ 未接続"
        st.write(f"Colab: {colab_status}")
        
        active_jobs = len(st.session_state.current_jobs)
        st.write(f"アクティブジョブ: {active_jobs}")
        
        # 処理履歴
        if st.session_state.processing_history:
            st.subheader("📋 処理履歴")
            for record in st.session_state.processing_history[-5:]:  # 最新5件
                st.write(f"{record['status']} {record['file']}")
        
        # システム情報
        st.subheader("ℹ️ システム情報")
        st.write("**各サービスの役割:**")
        st.write("🖥️ **Streamlit**: UI・制御")
        st.write("📁 **GitHub**: ファイル保管")
        st.write("⚡ **Colab**: GPU処理実行")
        
        if st.button("🔄 システム全体をリフレッシュ"):
            # サーバー状態チェック
            if st.session_state.colab_client.servers:
                st.session_state.colab_client.check_all_servers()
            st.rerun()

# ===== メインアプリケーション =====
def main():
    """メインアプリケーション"""
    st.title("☁️ 完全クラウド型ホログラム処理システム")
    st.markdown("**あなたのPC性能は一切使用しません - すべてクラウドで処理**")
    
    # サイドバー
    sidebar()
    
    # GitHub接続設定
    github_connected = setup_github_connection()
    
    # Colabサーバー管理（新しい統合版）
    from practical_colab_solution import integrated_colab_ui
    integrated_colab_ui()
    
    st.divider()
    
    if github_connected:
        # ファイル管理UI
        file_management_ui()
        
        st.divider()
        
        # 処理実行UI
        processing_ui()
        
        # ジョブ監視UI
        job_monitoring_ui()

if __name__ == "__main__":
    initialize_session_state()
    main()
