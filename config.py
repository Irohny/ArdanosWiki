from pathlib import Path


class Config:
    MARKDOWN_DIR = Path("World/Ardanos")
    IMAGE_DIR = Path("World/Images")
    IMAGE_TYPES = {".png", ".jpeg", ".jpg", ".svg"}


cfg = Config()
