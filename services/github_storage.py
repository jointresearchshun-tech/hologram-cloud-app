from github import Github
import base64
import logging

class GithubStorage:
    def __init__(self, token: str, repo_name: str):
        self.github = Github(token)
        self.repo = self.github.get_repo(repo_name)
        self.logger = logging.getLogger(__name__)

    def upload_file(self, file_path: str, content: bytes, branch: str = "main"):
        try:
            self.repo.create_file(
                path=file_path,
                message=f"Upload {file_path}",
                content=content.decode("utf-8", errors="ignore"),
                branch=branch
            )
            self.logger.info(f"Uploaded file: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to upload {file_path}: {e}")
            raise

    def list_files(self, path: str = "", branch: str = "main"):
        try:
            contents = self.repo.get_contents(path, ref=branch)
            return [c.path for c in contents]
        except Exception as e:
            self.logger.error(f"Failed to list files in {path}: {e}")
            return []

    def download_file(self, file_path: str, branch: str = "main") -> bytes:
        try:
            file_content = self.repo.get_contents(file_path, ref=branch)
            return base64.b64decode(file_content.content)
        except Exception as e:
            self.logger.error(f"Failed to download {file_path}: {e}")
            raise

    def delete_file(self, file_path: str, branch: str = "main"):
        try:
            file_content = self.repo.get_contents(file_path, ref=branch)
            self.repo.delete_file(
                path=file_path,
                message=f"Delete {file_path}",
                sha=file_content.sha,
                branch=branch
            )
            self.logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to delete {file_path}: {e}")
            raise


def connect_github(token: str, repo_name: str):
    """
    Simple connection test to GitHub repository.
    Returns (success: bool, message: str)
    """
    try:
        storage = GithubStorage(token, repo_name)
        storage.list_files("")  # connection test
        return True, f"Connected to {repo_name}"
    except Exception as e:
        return False, str(e)
