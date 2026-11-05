from dataclasses import dataclass, field
import os
from pathlib import Path

from wiki_dasboard.configs import (
    DashboardLayoutConfig,
    DashboardViewConfig,
    FeatureConfig,
    NavigationConfig,
    PlayerAccessRegistryConfig,
    load_player_access_registry,
)




@dataclass(frozen=True)
class PathsConfig:
    repo_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1])
    wiki_app_base_url: str = field(
        default_factory=lambda: os.getenv(
            "ARDANOS_WIKI_APP_BASE_URL", "http://localhost:8501"
        )
    )

    @property
    def world_dir(self) -> Path:
        return self.repo_root / "World"

    @property
    def image_dir(self) -> Path:
        return self.world_dir / "Images"


@dataclass(frozen=True)
class MediaConfig:
    image_types: frozenset[str] = frozenset({".png", ".jpeg", ".jpg", ".svg"})


@dataclass(frozen=True)
class Config:
    paths: PathsConfig = field(default_factory=PathsConfig)
    player_access: PlayerAccessRegistryConfig = field(init=False)
    navigation: NavigationConfig = field(default_factory=NavigationConfig)
    media: MediaConfig = field(default_factory=MediaConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    layout: DashboardLayoutConfig = field(default_factory=DashboardLayoutConfig)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "player_access",
            load_player_access_registry(self.paths.world_dir),
        )

    @property
    def REPO_ROOT(self) -> Path:
        return self.paths.repo_root

    @property
    def WIKI_APP_BASE_URL(self) -> str:
        return self.paths.wiki_app_base_url

    @property
    def MARKDOWN_DIR(self) -> Path:
        return self.paths.world_dir

    @property
    def IMAGE_DIR(self) -> Path:
        return self.paths.image_dir

    @property
    def IMAGE_TYPES(self) -> frozenset[str]:
        return self.media.image_types

    @property
    def CAMPAIGN_LABELS(self) -> dict[str, str]:
        return self.player_access.campaign_labels

    @property
    def CAMPAIGN_ALIASES(self) -> dict[str, str]:
        return self.player_access.campaign_aliases

    @property
    def DATABASE_LIST(self) -> tuple[str, ...]:
        return self.navigation.databases

    @property
    def IGNORE_LIST(self) -> tuple[str, ...]:
        return self.navigation.ignored_paths

    @property
    def SPECIAL_FEATURE(self) -> tuple[str, ...]:
        return self.features.special_features

    @property
    def TOOLBOX_FEATURE_NAME(self) -> str:
        return self.features.toolbox_name

    @property
    def DEFAULT_DASHBOARD_EMBLEMS(self) -> tuple[str, ...]:
        return self.layout.default_emblems

    @property
    def DEFAULT_DASHBOARD_BACKGROUND(self) -> str:
        return self.layout.default_background

    @property
    def DASHBOARD_VIEWS(self) -> tuple[DashboardViewConfig, ...]:
        return self.layout.views


cfg = Config()




