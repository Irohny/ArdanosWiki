from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DashboardViewConfig:
    key: str
    path_prefix: str
    mode: str
    asset_path: str | None = None
    use_container_width: bool = True
    layout_columns: tuple[int, int, int] | None = (1, 10, 1)
    top_spacing_rem: float = 0.5
    caption: str | None = None


class Config:
    REPO_ROOT: Path = Path(__file__).resolve().parent
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
    SPECIAL_FEATURE: list[str] = ["Encounter Rechner"]
    IGNORE_LIST: list[str] = ["templates", "Images", ".obsidian"]
    DEFAULT_DASHBOARD_EMBLEMS: list[str] = [
        "Wappen Drakmora.png",
        "Wappen Elmrath.png",
        "Wappen Mariven.png",
        "Wappen Vaylen.png",
        "Wappen Schwarzklamm.png",
    ]
    DEFAULT_DASHBOARD_BACKGROUND: str = "Ardanos.jpg"
    DASHBOARD_VIEWS: tuple[DashboardViewConfig, ...] = (
        DashboardViewConfig(
            key="drakmora",
            path_prefix="Kaiserreich/Drakmora",
            mode="timeline",
            asset_path="World/Images/drakmora_vertical_timeline.svg",
            caption="Chronik des Fürstentums Drakmora",
        ),
        DashboardViewConfig(
            key="elmrath",
            path_prefix="Kaiserreich/Elmrath",
            mode="timeline",
            asset_path="World/Images/elmrath_vertical_timeline.svg",
            caption="Chronik des Fürstentums Elmrath",
        ),
        DashboardViewConfig(
            key="mariven",
            path_prefix="Kaiserreich/Mariven",
            mode="timeline",
            asset_path="World/Images/mariven_vertical_timeline.svg",
            caption="Chronik des Fürstentums Mariven",
        ),
        DashboardViewConfig(
            key="schwarzklamm",
            path_prefix="Kaiserreich/Schwarzklamm",
            mode="timeline",
            asset_path="World/Images/schwarzklamm_vertical_timeline.svg",
            caption="Chronik des Fürstentums Schwarzklamm",
        ),
        DashboardViewConfig(
            key="vaylen",
            path_prefix="Kaiserreich/Vaylen",
            mode="timeline",
            asset_path="World/Images/vaylen_vertical_timeline.svg",
            caption="Chronik des Fürstentums Vaylen",
        ),
    )


cfg = Config()
