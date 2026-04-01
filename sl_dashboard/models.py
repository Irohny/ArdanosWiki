from dataclasses import dataclass, field


@dataclass(frozen=True)
class DashboardScene:
    title: str
    status: str
    summary: str
    location: str
    source_file: str = ""
    source_heading: str = ""
    image_files: tuple[str, ...] = ()
    goal: str = ""
    atmosphere: str = ""
    pressure: str = ""
    stakes: tuple[str, ...] = ()
    discoveries: tuple[str, ...] = ()
    likely_player_actions: tuple[str, ...] = ()
    hidden_truths: tuple[str, ...] = ()


@dataclass(frozen=True)
class DashboardNpc:
    name: str
    role: str
    motivation: str
    tension: str
    species: str = ""
    title: str = ""
    voice: str = ""
    reason: str = ""
    source_file: str = ""
    source_heading: str = ""
    image_file: str = ""


@dataclass(frozen=True)
class DashboardLink:
    title: str
    context: str
    reason: str = ""
    source_file: str = ""
    source_heading: str = ""
    image_file: str = ""


@dataclass(frozen=True)
class DashboardTool:
    title: str
    description: str
    status: str = "geplant"
    emphasis: str = "normal"


@dataclass(frozen=True)
class SessionStatus:
    session_title: str
    in_game_date: str
    region: str
    current_scene: str
    current_goal: str = ""
    pacing: str = ""
    open_threads: tuple[str, ...] = ()


@dataclass(frozen=True)
class DashboardData:
    status: SessionStatus
    current_scene: DashboardScene
    next_scenes: tuple[DashboardScene, ...] = ()
    npcs: tuple[DashboardNpc, ...] = ()
    quick_links: tuple[DashboardLink, ...] = ()
    tools: tuple[DashboardTool, ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)
    alerts: tuple[str, ...] = field(default_factory=tuple)
