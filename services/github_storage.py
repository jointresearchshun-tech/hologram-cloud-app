import requests
import base64
import logging
from datetime import datetime
from typing import Optional, Dict, List
from github import Github
import streamlit as st

logger = logging.getLogger(__name__)

class GitHubStorage:
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.github = Github(token)
        self.repository = self.github.get_repo(repo)
        
        # 直接APIアクセス用
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = f"https://api.github.com/repos/{repo}"
    
    def test_connection(self) -> bool:
        """GitHub接続テスト"""
        try:
            self.repository.get_contents("README.md")
            return True
        except Exception as e:
            logger.error(f"GitHub connection test failed: {e}")
            return False
    
    def list_files(self, folder: str = "data", extensions: Optional[List[str]] = None) -> List[Dict]:
        """指定フォルダ内のファイル一覧を取得"""
        try:
            contents = self.repository.get_contents(folder)
            files = []
            
            for content in contents:
                if content.type == "file":
                    # 拡張子フィルタリング
                    if extensions:
                        if not any(content.name.lower().endswith(ext.lower()) for ext in extensions):
                            continue
                    
                    files.append({
                        "name": content.name,
                        "size": content.size,
                        "download_url": content.download_url,
                        "sha": content.sha,
                        "path": content.path,
                        "encoding": getattr(content, 'encoding', None)  # エンコーディング情報も取得
                    })
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    def download_file(self, file_info: Dict) -> Optional[bytes]:
        """
        ファイルをダウンロード - エンコーディングの問題に対応
        """
        try:
            # Method 1: download_url を使用（推奨）
            if "download_url" in file_info and file_info["download_url"]:
                logger.info(f"Downloading via download_url: {file_info['name']}")
                response = requests.get(file_info["download_url"], timeout=60)
                if response.status_code == 200:
                    return response.content
                else:
                    logger.warning(f"Download via download_url failed: {response.status_code}")
            
            # Method 2: GitHub API Content endpoint を使用
            if "path" in file_info:
                logger.info(f"Downloading via GitHub API: {file_info['name']}")
                return self._download_via_api(file_info["path"])
            
            # Method 3: PyGithub を使用（小さなファイル用）
            if file_info.get("size", 0) < 1024 * 1024:  # 1MB未満
                logger.info(f"Downloading via PyGithub: {file_info['name']}")
                return self._download_via_pygithub(file_info)
            
            logger.error(f"All download methods failed for: {file_info['name']}")
            return None
            
        except Exception as e:
            logger.error(f"Download error for {file_info.get('name', 'unknown')}: {e}")
            return None
    
    def _download_via_api(self, file_path: str) -> Optional[bytes]:
        """GitHub API を直接使用してダウンロード"""
        try:
            url = f"{self.base_url}/contents/{file_path}"
            response = requests.get(url, headers=self.headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # エンコーディングをチェック
                if data.get("encoding") == "base64":
                    return base64.b64decode(data["content"])
                elif "download_url" in data:
                    # 大きなファイルの場合、download_urlが提供される
                    download_response = requests.get(data["download_url"], timeout=60)
                    if download_response.status_code == 200:
                        return download_response.content
                else:
                    logger.error(f"Unsupported encoding: {data.get('encoding')}")
                    return None
            else:
                logger.error(f"API download failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"API download error: {e}")
            return None
    
    def _download_via_pygithub(self, file_info: Dict) -> Optional[bytes]:
        """PyGithub を使用してダウンロード（小さなファイル用）"""
        try:
            file_path = file_info.get("path", file_info.get("name"))
            content_file = self.repository.get_contents(file_path)
            
            if hasattr(content_file, 'decoded_content'):
                # エンコーディングが適切な場合
                if content_file.encoding in ["base64", None]:
                    if content_file.encoding == "base64":
                        return content_file.decoded_content
                    else:
                        # encoding が None の場合は直接ダウンロード
                        if content_file.download_url:
                            response = requests.get(content_file.download_url, timeout=60)
                            return response.content if response.status_code == 200 else None
                else:
                    logger.error(f"Unsupported encoding: {content_file.encoding}")
                    return None
            else:
                logger.error("No decoded_content available")
                return None
                
        except Exception as e:
            logger.error(f"PyGithub download error: {e}")
            return None
    
    def upload_file(self, content: bytes, filename: str, folder: str = "results", 
                   message: Optional[str] = None) -> bool:
        """ファイルをGitHubにアップロード"""
        try:
            file_path = f"{folder}/{filename}"
            
            # 既存ファイルの確認
            try:
                existing_file = self.repository.get_contents(file_path)
                sha = existing_file.sha
                commit_message = message or f"Update {filename} at {datetime.now().isoformat()}"
            except:
                sha = None
                commit_message = message or f"Upload {filename} at {datetime.now().isoformat()}"
            
            # アップロード実行
            if sha:
                # 更新
                self.repository.update_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    sha=sha
                )
            else:
                # 新規作成
                self.repository.create_file(
                    path=file_path,
                    message=commit_message,
                    content=content
                )
            
            logger.info(f"File uploaded successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """ファイル情報を取得"""
        try:
            content = self.repository.get_contents(file_path)
            return {
                "name": content.name,
                "size": content.size,
                "download_url": content.download_url,
                "sha": content.sha,
                "path": content.path,
                "encoding": getattr(content, 'encoding', None)
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None
