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
            # 軽量なテスト - リポジトリ情報を取得
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"GitHub connection test failed: {e}")
            return False
    
    def list_files(self, folder: str = "data", extensions: Optional[List[str]] = None) -> List[Dict]:
        """
        指定フォルダ内のファイル一覧を取得 - API直接アクセスで安全に実装
        """
        try:
            # GitHub API を直接使用してファイル一覧を取得
            url = f"{self.base_url}/contents/{folder}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 404:
                logger.warning(f"Folder '{folder}' not found")
                return []
            elif response.status_code != 200:
                logger.error(f"Failed to list files: {response.status_code}")
                return []
            
            contents = response.json()
            if not isinstance(contents, list):
                return []
            
            files = []
            for content in contents:
                # ファイルのみ処理（ディレクトリを除外）
                if content.get("type") != "file":
                    continue
                
                # 拡張子フィルタリング
                if extensions:
                    if not any(content["name"].lower().endswith(ext.lower()) for ext in extensions):
                        continue
                
                # 安全にファイル情報を構築
                file_info = {
                    "name": content.get("name", ""),
                    "size": content.get("size", 0),
                    "download_url": content.get("download_url", ""),
                    "sha": content.get("sha", ""),
                    "path": content.get("path", ""),
                    "type": content.get("type", "file"),
                    "encoding": content.get("encoding", "unknown"),  # APIから直接取得
                    "url": content.get("url", "")  # Content API URL
                }
                
                files.append(file_info)
                logger.info(f"Found file: {file_info['name']} ({file_info['size']} bytes, encoding: {file_info['encoding']})")
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            st.error(f"ファイル一覧取得エラー: {e}")
            return []
    
    def download_file(self, file_info: Dict) -> Optional[bytes]:
        """
        ファイルをダウンロード - 段階的フォールバック方式
        """
        file_name = file_info.get("name", "unknown")
        file_size = file_info.get("size", 0)
        encoding = file_info.get("encoding", "unknown")
        
        logger.info(f"Starting download: {file_name} (size: {file_size}, encoding: {encoding})")
        
        # Method 1: download_url を使用（最も確実で高速）
        if file_info.get("download_url"):
            logger.info(f"Method 1: Using download_url for {file_name}")
            try:
                response = requests.get(
                    file_info["download_url"], 
                    timeout=300,  # 5分タイムアウト
                    stream=True if file_size > 1024*1024 else False  # 1MB以上はストリーミング
                )
                
                if response.status_code == 200:
                    if file_size > 1024*1024:  # 大きなファイルの場合
                        content = b""
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                content += chunk
                        return content
                    else:
                        return response.content
                else:
                    logger.warning(f"download_url failed with status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Method 1 failed for {file_name}: {e}")
        
        # Method 2: GitHub Contents API を使用
        if file_info.get("url"):
            logger.info(f"Method 2: Using Contents API for {file_name}")
            try:
                response = requests.get(file_info["url"], headers=self.headers, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # base64 エンコーディングの場合
                    if data.get("encoding") == "base64" and data.get("content"):
                        try:
                            # 改行を除去してからデコード
                            content_clean = data["content"].replace("\n", "").replace("\r", "")
                            return base64.b64decode(content_clean)
                        except Exception as e:
                            logger.error(f"Base64 decode failed: {e}")
                    
                    # download_url が提供されている場合（大きなファイル）
                    elif data.get("download_url"):
                        logger.info(f"Using download_url from Contents API response")
                        download_response = requests.get(data["download_url"], timeout=300)
                        if download_response.status_code == 200:
                            return download_response.content
                    
                else:
                    logger.warning(f"Contents API failed with status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Method 2 failed for {file_name}: {e}")
        
        # Method 3: ファイルパスから直接構築したdownload URLを使用
        if file_info.get("path"):
            logger.info(f"Method 3: Using constructed raw URL for {file_name}")
            try:
                # GitHub の raw content URL を構築
                raw_url = f"https://raw.githubusercontent.com/{self.repo}/main/{file_info['path']}"
                response = requests.get(raw_url, timeout=300)
                
                if response.status_code == 200:
                    return response.content
                else:
                    logger.warning(f"Raw URL failed with status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Method 3 failed for {file_name}: {e}")
        
        # すべての方法が失敗
        logger.error(f"All download methods failed for {file_name}")
        return None
    
    def upload_file(self, content: bytes, filename: str, folder: str = "results", 
                   message: Optional[str] = None) -> bool:
        """ファイルをGitHubにアップロード"""
        try:
            file_path = f"{folder}/{filename}"
            
            # Base64エンコード
            if isinstance(content, bytes):
                content_b64 = base64.b64encode(content).decode('utf-8')
            else:
                content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            # 既存ファイルの確認
            check_url = f"{self.base_url}/contents/{file_path}"
            check_response = requests.get(check_url, headers=self.headers, timeout=10)
            
            data = {
                "message": message or f"Upload {filename} at {datetime.now().isoformat()}",
                "content": content_b64
            }
            
            if check_response.status_code == 200:
                # ファイルが存在する場合、SHAが必要
                existing_data = check_response.json()
                data["sha"] = existing_data["sha"]
                data["message"] = message or f"Update {filename} at {datetime.now().isoformat()}"
            
            # アップロード実行
            response = requests.put(check_url, json=data, headers=self.headers, timeout=60)
            
            if response.status_code in [200, 201]:
                logger.info(f"File uploaded successfully: {file_path}")
                return True
            else:
                logger.error(f"Upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return False
    
    def get_file_info_detailed(self, file_path: str) -> Optional[Dict]:
        """ファイルの詳細情報を安全に取得"""
        try:
            url = f"{self.base_url}/contents/{file_path}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "name": data.get("name", ""),
                    "size": data.get("size", 0),
                    "download_url": data.get("download_url", ""),
                    "sha": data.get("sha", ""),
                    "path": data.get("path", ""),
                    "encoding": data.get("encoding", "unknown"),
                    "type": data.get("type", "file"),
                    "url": data.get("url", "")
                }
            else:
                logger.error(f"Failed to get file info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None
