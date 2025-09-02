import torch
import io
from services.github_storage import GithubStorage

def load_model_from_pth(model_bytes):
    buffer = io.BytesIO(model_bytes)
    model = torch.load(buffer, map_location="cpu")
    model.eval()
    return model

def decompress_file(model, compressed_bytes):
    buffer = io.BytesIO(compressed_bytes)
    compressed_obj = torch.load(buffer, map_location="cpu")
    output = model.decompress(compressed_obj["strings"], compressed_obj["shape"])
    return output["x_hat"]
