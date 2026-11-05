from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EncounterCondition:
    name: str
    duration: str = ""
    source: str = ""
    notes: str = ""


@dataclass(frozen=True)
class EncounterCombatant:
    id: str
    name: str
    side: str
    source_type: str = ""
    source_key: str = ""
    max_hp: int | None = None
    current_hp: int | None = None
    initiative: int | None = None
    armor_class: int | None = None
    immunities: tuple[str, ...] = ()
    resistances: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    conditions: tuple[EncounterCondition, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class EncounterPreparation:
    target_difficulty: str = ""
    predicted_difficulty: str = ""
    monster_source_keys: tuple[str, ...] = ()
    analysis_summary: str = ""
    analysis_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class EncounterRuntime:
    round_number: int = 1
    active_combatant_id: str = ""
    combatants: tuple[EncounterCombatant, ...] = ()


@dataclass(frozen=True)
class DashboardEncounter:
    scene_id: str
    status: str = "draft"
    preparation: EncounterPreparation = field(default_factory=EncounterPreparation)
    runtime: EncounterRuntime = field(default_factory=EncounterRuntime)
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class DashboardScene:
    title: str
    status: str
    summary: str
    location: str
    id: str = ""
    encounter: DashboardEncounter | None = None
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
    location: str = ""
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
