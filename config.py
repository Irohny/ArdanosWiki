from pathlib import Path


class Config:
    MARKDOWN_DIR = Path("World")
    IMAGE_DIR = Path("World/Images")
    IMAGE_TYPES = {".png", ".jpeg", ".jpg", ".svg"}
    ROLE_MAPPING = {
        "Gnodomir": "gn_",
        "Vishuda": "vs_",
        "Hector": "he_",
        "Marcus": "mc_",
        "Nyssara": "ny_",
        "Admin": "sl ",
    }


cfg = Config()
