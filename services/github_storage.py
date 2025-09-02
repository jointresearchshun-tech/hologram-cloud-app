import requests


if response.status_code == 404:
logger.warning(f"Folder '{folder}' not found")
return []
if response.status_code != 200:
logger.error(f"Failed to list files: {response.status_code} – {response.text}")
return []


files = response.json()
if not isinstance(files, list):
return []


files = [f for f in files if f.get("type") == "file"]
if extensions:
files = [
f for f in files if any(f["name"].lower().endswith(ext.lower()) for ext in extensions)
]


return [
{
"name": f["name"],
"size": f["size"],
"download_url": f["download_url"],
"sha": f.get("sha"),
}
for f in files
]
except requests.RequestException as e:
logger.error(f"Error listing files: {e}")
return []


def upload_file(
self, content: bytes, filename: str, folder: str = "results", message: Optional[str] = None
) -> bool:
try:
file_path = f"{folder}/{filename}"
url = f"{self.base_url}/contents/{file_path}"


# Check if file exists to include SHA for updates
existing_response = requests.get(url, headers=self.headers, timeout=10)
sha = existing_response.json().get("sha") if existing_response.status_code == 200 else None


# Base64 encode the content as required by GitHub API
content_b64 = base64.b64encode(content).decode("utf-8")


data = {
"message": message or f"Upload {filename} at {datetime.now().isoformat()}",
"content": content_b64,
}
if sha:
data["sha"] = sha
data["message"] = f"Update {filename} at {datetime.now().isoformat()}"


response = requests.put(url, json=data, headers=self.headers, timeout=30)
if response.status_code in [200, 201]:
logger.info(f"File uploaded successfully: {file_path}")
return True
logger.error(f"Upload failed: {response.status_code} – {response.text}")
return False
except requests.RequestException as e:
logger.error(f"Upload error: {e}")
return False


def download_file(self, file_info: Dict) -> Optional[bytes]:
try:
response = requests.get(file_info["download_url"], timeout=30)
if response.status_code == 200:
return response.content
logger.error(f"Download failed: {response.status_code} – {response.text}")
return None
except requests.RequestException as e:
logger.error(f"Download error: {e}")
return None
