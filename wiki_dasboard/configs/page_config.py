from dataclasses import dataclass

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

@dataclass(frozen=True)
class DashboardLayoutConfig:
    default_emblems: tuple[str, ...] = (
        "Wappen Drakmora.png",
        "Wappen Elmrath.png",
        "Wappen Mariven.png",
        "Wappen Vaylen.png",
        "Wappen Schwarzklamm.png",
    )
    default_background: str = "Ardanos.jpg"
    views: tuple[DashboardViewConfig, ...] = (
        DashboardViewConfig(
            key="drakmora",
            path_prefix="Kaiserreich/Drakmora",
            mode="timeline",
            asset_path="World/Images/Timelines/drakmora_vertical_timeline.svg",
            caption="Chronik des Fürstentums Drakmora",
        ),
        DashboardViewConfig(
            key="elmrath",
            path_prefix="Kaiserreich/Elmrath",
            mode="timeline",
            asset_path="World/Images/Timelines/elmrath_vertical_timeline.svg",
            caption="Chronik des Fürstentums Elmrath",
        ),
        DashboardViewConfig(
            key="mariven",
            path_prefix="Kaiserreich/Mariven",
            mode="timeline",
            asset_path="World/Images/Timelines/mariven_vertical_timeline.svg",
            caption="Chronik des Fürstentums Mariven",
        ),
        DashboardViewConfig(
            key="schwarzklamm",
            path_prefix="Kaiserreich/Schwarzklamm",
            mode="timeline",
            asset_path="World/Images/Timelines/schwarzklamm_vertical_timeline.svg",
            caption="Chronik des Fürstentums Schwarzklamm",
        ),
        DashboardViewConfig(
            key="vaylen",
            path_prefix="Kaiserreich/Vaylen",
            mode="timeline",
            asset_path="World/Images/Timelines/vaylen_vertical_timeline.svg",
            caption="Chronik des Fürstentums Vaylen",
        ),
        DashboardViewConfig(
            key="ardanos",
            path_prefix="Kaiserreich",
            mode="timeline",
            asset_path="World/Images/Timelines/ardanos_vertical_timeline.svg",
            caption="Chronik des Kaiserreiches Ardanos",
        ),
    )