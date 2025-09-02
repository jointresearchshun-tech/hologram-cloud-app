import requests
import time
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from config.logging_config import logger




class ColabServerClient:
"""Client to manage multiple Colab-backed FastAPI servers via ngrok."""


def __init__(self):
self.servers: List[Dict] = []
self.current_server: Optional[Dict] = None


# ---- Server registry & health ----
def add_server(self, name: str, url: str) -> bool:
server = {"name": name, "url": url.rstrip("/"), "added_at": datetime.now().isoformat()}
try:
response = requests.get(f"{server['url']}/health", timeout=5)
if response.status_code == 200:
server["status"] = "healthy"
server["info"] = response.json()
self.servers.append(server)
if not self.current_server:
self.current_server = server
logger.info(f"Server added: {name}")
return True
else:
logger.warning(f"Server unhealthy: {response.status_code}")
except requests.RequestException as e:
logger.error(f"Server connection failed: {e}")
server["status"] = "unreachable"
return False


def remove_server(self, server_name: str) -> bool:
self.servers = [s for s in self.servers if s["name"] != server_name]
if self.current_server and self.current_server["name"] == server_name:
self.current_server = self.servers[0] if self.servers else None
return True


def switch_server(self, server_name: str) -> bool:
for s in self.servers:
if s["name"] == server_name:
self.current_server = s
return True
return False


def check_all_servers(self) -> None:
for server in self.servers:
try:
response = requests.get(f"{server['url']}/health", timeout=5)
server["status"] = "healthy" if response.status_code == 200 else "unhealthy"
if response.status_code == 200:
server["info"] = response.json()
except requests.RequestException:
server["status"] = "unreachable"


# ---- Job API ----
def submit_job(self, github_config: Dict, input_file: Dict, processing_config: Dict) -> Tuple[Optional[str], Optional[str]]:
if not self.current_server:
return None, "No available Colab server"
if self.current_server.get("status") != "healthy":
return None, f"Current server '{self.current_server['name']}' is not available"


try:
job_data = {
"job_id": f"job_{int(time.time())}_{hash(input_file['name']) % 10000}",
"github_repo": github_config["repo"],
"github_token": github_config["token"],
"input_file": input_file,
"processing_config": processing_config,
"timestamp": datetime.now().isoformat(),
"client_info": "Streamlit Cloud Processing System",
}
response = requests.post(f"{self.current_server['url']}/submit_job", json=job_data, timeout=30)
if response.status_code == 200:
