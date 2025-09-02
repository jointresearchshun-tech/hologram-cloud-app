from github import Github
import base64
import logging


class GithubStorage:
    def __init__(self, token: str, repo_name: str):
        self.github = Github(token)
        self.repo = self.github.get_repo(repo_name)
        self.logger = logging.getLogger(__name__)

    def upload_file(self, file_path: str, content: bytes, branch: str = "main"):
        """
        GitHub にファイルをアップロード（既存なら更新）。
        バイナリファイルも扱えるよう Base64 でエンコードして保存。
        """
        try:
            encoded_content = base64.b64encode(content).decode("utf-8")

            # Check if file exists
            contents = self.repo.get_contents(file_path, ref=branch)
            self.repo.update_file(
                path=file_path,
                message=f"Update {file_path}",
                content=encoded_content,
                sha=contents.sha,
                branch=branch,
            )
            self.logger.info(f"Updated file: {file_path}")

        except Exception:
            # File does not exist, create new
            encoded_content = base64.b64encode(content).decode("utf-8")
            self.repo.create_file(
                path=file_path,
                message=f"Upload {file_path}",
                content=encoded_content,
                branch=branch,
            )
            self.logger.info(f"Created file: {file_path}")

    def list_files(self, path: str = "", branch: str = "main"):
        """
        リポジトリ内のファイル一覧を取得
        """
        try:
            contents = self.repo.get_contents(path, ref=branch)
            return [c.path for c in contents]
        except Exception as e:
            self.logger.error(f"Failed to list files in {path}: {e}")
            return []

    def download_file(self, file_path: str, branch: str = "main") -> bytes:
        """
        GitHub からファイルをダウンロード（Base64 デコードしてバイナリに戻す）
        """
        try:
            file_content = self.repo.get_contents(file_path, ref=branch)
            return base64.b64decode(file_content.content)
        except Exception as e:
            self.logger.error(f"Failed to download {file_path}: {e}")
            raise

    def delete_file(self, file_path: str, branch: str = "main"):
        """
        GitHub からファイルを削除
        """
        try:
            file_content = self.repo.get_contents(file_path, ref=branch)
            self.repo.delete_file(
                path=file_path,
                message=f"Delete {file_path}",
                sha=file_content.sha,
                branch=branch,
            )
            self.logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to delete {file_path}: {e}")
            raise
