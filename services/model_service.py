import torch
import io
from services.github_storage import GithubStorage

def load_model_from_pth(pth_bytes: bytes):
    """Load model object directly from .pth file bytes"""
    buffer = io.BytesIO(pth_bytes)
    model = torch.load(buffer, map_location="cpu")
    model.eval()
    return model

def decompress_file(model, compressed_bytes: bytes, output_path: str, github_client: GithubStorage):
    """Decompress compressed .pt using the provided model and save result to GitHub"""
    buffer = io.BytesIO(compressed_bytes)
    checkpoint = torch.load(buffer, map_location="cpu")

    # decompress using model
    x_hat = model.decompress(checkpoint["strings"], checkpoint["shape"])["x_hat"]

    # save as tensor file
    output_buffer = io.BytesIO()
    torch.save({"x_hat": x_hat}, output_buffer)

    github_client.upload_file(output_path, output_buffer.getvalue())
    return output_path
