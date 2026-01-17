from pathlib import Path


class Config:
    MARKDOWN_DIR: Path = Path("World")
    IMAGE_DIR: Path = Path("World/Images")
    IMAGE_TYPES: set[str] = {".png", ".jpeg", ".jpg", ".svg"}
    ROLE_MAPPING: dict = {
        "Gnodomir": "gn_",
        "Vishuda": "vs_",
        "Hector": "he_",
        "Marcus": "mc_",
        "Nyssara": "ny_",
        "Admin": "sl ",
    }
    DATABASE_LIST: list[str] = [
        "Bestiarium",
        "Zauberarchiv",
        "Tranksammlung",
        "Zutatenarchiv",
    ]


cfg = Config()
