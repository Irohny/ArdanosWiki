from dataclasses import dataclass


@dataclass(frozen=True)
class NavigationConfig:
    databases: tuple[str, ...] = (
        "Bestiarium",
        "Zauberarchiv",
        "Tranksammlung",
        "Zutatenarchiv",
        "Waffenkammer",
        "Schatzkammer",
    )
    ignored_paths: tuple[str, ...] = ("templates", "Images", ".obsidian")


@dataclass(frozen=True)
class FeatureConfig:
    toolbox_name: str = "Toolbox"

    @property
    def special_features(self) -> tuple[str, ...]:
        return (self.toolbox_name,)
