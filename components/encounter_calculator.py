import json
from dataclasses import dataclass, replace
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import cast

import streamlit as st
from components.login import Roles

MONSTER_CATALOG_PATH = (
    Path(__file__).resolve().parent.parent
    / "timeline_tools"
    / "monster_catalog"
    / "monster_catalog.json"
)

XP_THRESHOLDS = {
    1: (25, 50, 75, 100),
    2: (50, 100, 150, 200),
    3: (75, 150, 225, 400),
    4: (125, 250, 375, 500),
    5: (250, 500, 750, 1100),
    6: (300, 600, 900, 1400),
    7: (350, 750, 1100, 1700),
    8: (450, 900, 1400, 2100),
    9: (550, 1100, 1600, 2400),
    10: (600, 1200, 1900, 2800),
    11: (800, 1600, 2400, 3600),
    12: (1000, 2000, 3000, 4500),
    13: (1100, 2200, 3400, 5100),
    14: (1250, 2500, 3800, 5700),
    15: (1400, 2800, 4300, 6400),
    16: (1600, 3200, 4800, 7200),
    17: (2000, 3900, 5900, 8800),
    18: (2100, 4200, 6300, 9500),
    19: (2400, 4900, 7300, 10900),
    20: (2800, 5700, 8500, 12700),
}

CR_XP = {
    0: 10,
    0.125: 25,
    0.25: 50,
    0.5: 100,
    1: 200,
    2: 450,
    3: 700,
    4: 1100,
    5: 1800,
    6: 2300,
    7: 2900,
    8: 3900,
    9: 5000,
    10: 5900,
    11: 7200,
    12: 8400,
    13: 10000,
    14: 11500,
    15: 13000,
    16: 15000,
    17: 18000,
    18: 20000,
    19: 22000,
    20: 25000,
    21: 33000,
    22: 41000,
    23: 50000,
    24: 62000,
    25: 75000,
    26: 90000,
    27: 105000,
    28: 120000,
    29: 135000,
    30: 155000,
}

VALID_CRS = tuple(sorted(CR_XP.keys()))
MONSTER_COUNT_MULTIPLIERS = (
    (1, 1.0),
    (2, 1.5),
    (6, 2.0),
    (10, 2.5),
    (14, 3.0),
    (999, 4.0),
)

DIFFICULTY_SCALE = [
    ("⚪", "Trivial"),
    ("🟢", "Leicht"),
    ("🟡", "Mittel"),
    ("🟠", "Schwer"),
    ("🔴", "Tödlich"),
    ("☠️", "Jenseits tödlich"),
]

VOLATILITY_SCALE = [
    ("🟢", "Niedrig"),
    ("🟡", "Mittel"),
    ("🟠", "Hoch"),
    ("🔴", "Extrem"),
]


class FaktorEnum(Enum):
    def __new__(cls, label, factor):
        obj = object.__new__(cls)
        obj._value_ = (label, factor)
        return obj

    @property
    def label(self):
        return self.value[0]

    @property
    def factor(self):
        return self.value[1]


class ThreatTag(Enum):
    def __new__(cls, label, threat_bonus, volatility_bonus, action_bonus):
        obj = object.__new__(cls)
        obj._value_ = (label, threat_bonus, volatility_bonus, action_bonus)
        return obj

    @property
    def label(self):
        return self.value[0]

    @property
    def threat_bonus(self):
        return self.value[1]

    @property
    def volatility_bonus(self):
        return self.value[2]

    @property
    def action_bonus(self):
        return self.value[3]


class Schwierigkeit(Enum):
    LEICHT = "Leicht"
    MITTEL = "Mittel"
    SCHWER = "Schwer"
    TOEDLICH = "Tödlich"

    @property
    def key(self):
        return self.value.upper()


class PartyOptimierung(FaktorEnum):
    SCHWACH = ("Schwach optimiert", 0.85)
    NORMAL = ("Normal", 1.0)
    STARK = ("Stark optimiert", 1.15)
    SEHR_STARK = ("Sehr stark optimiert", 1.3)


class Ausruestungsniveau(FaktorEnum):
    ARM = ("Wenig magische Ausrüstung", 0.93)
    STANDARD = ("Normale magische Ausrüstung", 1.0)
    STARK = ("Starke magische Ausrüstung", 1.1)
    HEROISCH = ("Heroische Ausrüstung", 1.2)


class Ressourcenstand(FaktorEnum):
    FRISCH = ("Frisch", 1.0)
    LEICHT = ("Leicht angeschlagen", 0.93)
    AUSGEDUENNT = ("Ausgedünnt", 0.82)
    LETZTES = ("Letztes Gefecht", 0.7)


class Kontrollniveau(FaktorEnum):
    GERING = ("Kaum Kontrolle", 0.94)
    NORMAL = ("Normale Kontrolle", 1.0)
    HOCH = ("Starke Kontrolle", 1.1)


class Heilniveau(FaktorEnum):
    GERING = ("Wenig Heilung", 0.94)
    NORMAL = ("Normale Heilung", 1.0)
    HOCH = ("Starke Heilung", 1.08)


class FrontlineNiveau(FaktorEnum):
    BRUECHIG = ("Brüchige Frontline", 0.92)
    STABIL = ("Stabile Frontline", 1.0)
    MASSIV = ("Sehr stabile Frontline", 1.08)


class Fernkampfniveau(FaktorEnum):
    SCHWACH = ("Schwacher Fernkampf", 0.95)
    GEMISCHT = ("Gemischter Fernkampf", 1.0)
    STARK = ("Starker Fernkampf", 1.05)


class Terrainlage(FaktorEnum):
    SPIELERVORTEIL = ("Spielervorteil", 0.9)
    NEUTRAL = ("Neutral", 1.0)
    GEGNERVORTEIL = ("Gegnervorteil", 1.15)
    ENGPASS = ("Engpass gegen die Gruppe", 1.15)
    FERNKAMPF_GEGNER = ("Fernkampfvorteil der Gegner", 1.2)
    DECKUNG_SPIELER = ("Gute Deckung für die Spieler", 0.88)


class Ueberraschung(FaktorEnum):
    KEINE = ("Keine", 1.0)
    SPIELER = ("Spieler überraschen", 0.9)
    GEGNER = ("Gegner überraschen", 1.2)
    HINTERHALT = ("Starker Hinterhalt der Gegner", 1.35)


class MonsterTag(ThreatTag):
    BURST = ("Burst", 0.15, 0.25, 0.1)
    CONTROL = ("Control", 0.2, 0.35, 0.12)
    TANK = ("Tank", 0.08, 0.05, 0.05)
    MOBIL = ("Mobilität", 0.1, 0.12, 0.08)
    FERNKAMPF = ("Fernkampf", 0.08, 0.08, 0.05)
    BESCHWOERUNG = ("Beschwörung", 0.18, 0.28, 0.18)
    FLAECHE = ("Flächenschaden", 0.18, 0.3, 0.12)
    DEBUFF = ("Debuff", 0.12, 0.22, 0.08)
    HEIMLICH = ("Heimlich", 0.1, 0.24, 0.08)


@dataclass(frozen=True)
class Party:
    spieler: int
    stufe: int


@dataclass(frozen=True)
class PartyKontext:
    optimierung: PartyOptimierung
    ausruestung: Ausruestungsniveau
    ressourcen: Ressourcenstand
    kontrolle: Kontrollniveau
    heilung: Heilniveau
    frontline: FrontlineNiveau
    fernkampf: Fernkampfniveau


@dataclass(frozen=True)
class EncounterOptionen:
    terrain: Terrainlage
    ueberraschung: Ueberraschung
    legendare_aktionen: bool
    legendare_resistenzen: bool
    phasenwechsel: bool
    gegner_beschwoeren: bool
    wellen: int
    kurze_pause_zwischen_wellen: bool
    heilfenster_zwischen_wellen: bool
    gleiches_kampffeld: bool


@dataclass(frozen=True)
class MonsterEintrag:
    cr: float
    anzahl: int
    tags: tuple[MonsterTag, ...] = ()
    anzeigename: str | None = None
    profil_id: str | None = None
    profil_hinweis: str | None = None
    threat_modifier_bonus: float = 0.0
    action_weight_bonus: float = 0.0
    volatility_bonus: float = 0.0
    profil_legendare_aktionen: bool = False
    profil_legendare_resistenzen: bool = False
    profil_phasenwechsel: bool = False
    profil_beschwoerung: bool = False


@dataclass(frozen=True)
class MonsterProfil:
    key: str
    name: str
    cr: float
    tags: tuple[MonsterTag, ...]
    quelle: str = ""
    threat_modifier_bonus: float = 0.0
    action_weight_bonus: float = 0.0
    volatility_bonus: float = 0.0
    legendare_aktionen: bool = False
    legendare_resistenzen: bool = False
    phasenwechsel: bool = False
    beschwoerung: bool = False
    hinweis: str = ""


MONSTER_PROFILE_CATALOG = {
    "blutjaeger": MonsterProfil(
        key="blutjaeger",
        name="Blutjäger",
        cr=5,
        quelle="Bestiarium: Blutjäger",
        tags=(MonsterTag.BURST, MonsterTag.TANK, MonsterTag.DEBUFF),
        threat_modifier_bonus=0.08,
        action_weight_bonus=0.05,
        volatility_bonus=0.08,
        beschwoerung=True,
        hinweis="Mehrfachangriff, Bindungseffekt und Hex-artiger Zusatzdruck machen ihn stärker als einen reinen Frontkämpfer.",
    ),
    "soeldner": MonsterProfil(
        key="soeldner",
        name="Söldner",
        cr=5,
        quelle="Bestiarium: Söldner",
        tags=(MonsterTag.TANK, MonsterTag.DEBUFF),
        threat_modifier_bonus=0.06,
        action_weight_bonus=0.04,
        hinweis="Solider Nahkämpfer mit Blind-Effekt und guter Haltbarkeit, aber eher geringe Volatilität.",
    ),
    "schwarze_viper": MonsterProfil(
        key="schwarze_viper",
        name="Schwarze Viper",
        cr=5,
        quelle="Bestiarium: Schwarze Viper (Attentäter)",
        tags=(
            MonsterTag.HEIMLICH,
            MonsterTag.BURST,
            MonsterTag.MOBIL,
            MonsterTag.FERNKAMPF,
        ),
        threat_modifier_bonus=0.12,
        action_weight_bonus=0.1,
        volatility_bonus=0.18,
        hinweis="Hohe Mobilität, Hinterhältiger Angriff und Reaktionsschutz machen sie zu einem swingy Skirmisher.",
    ),
    "zerra_die_fluesterin": MonsterProfil(
        key="zerra_die_fluesterin",
        name="Zerra die Flüsterin",
        cr=6,
        quelle="Bestiarium: Zerra die Flüsterin",
        tags=(
            MonsterTag.CONTROL,
            MonsterTag.HEIMLICH,
            MonsterTag.MOBIL,
            MonsterTag.DEBUFF,
        ),
        threat_modifier_bonus=0.12,
        action_weight_bonus=0.08,
        volatility_bonus=0.18,
        hinweis="Kontrolllastige Schatten-Warlockin mit Teleport, Unsichtbarkeit und sozialer Manipulation.",
    ),
    "lord_vareth_nocthollow": MonsterProfil(
        key="lord_vareth_nocthollow",
        name="Lord Vareth Nocthollow",
        cr=16,
        quelle="Bestiarium: Lord Vareth Nocthollow",
        tags=(MonsterTag.TANK, MonsterTag.CONTROL, MonsterTag.MOBIL, MonsterTag.DEBUFF),
        threat_modifier_bonus=0.18,
        action_weight_bonus=0.16,
        volatility_bonus=0.2,
        legendare_aktionen=True,
        legendare_resistenzen=True,
        phasenwechsel=True,
        hinweis="Zeitverzerrung, Teleport und legendäre Rücksetzmechanik machen ihn zu einem harten Boss für fortgeschrittene Gruppen.",
    ),
    "ephazul": MonsterProfil(
        key="ephazul",
        name="Ephazul",
        cr=20,
        quelle="Bestiarium: Ephazul",
        tags=(
            MonsterTag.BURST,
            MonsterTag.CONTROL,
            MonsterTag.FLAECHE,
            MonsterTag.MOBIL,
            MonsterTag.DEBUFF,
        ),
        threat_modifier_bonus=0.22,
        action_weight_bonus=0.2,
        volatility_bonus=0.28,
        legendare_aktionen=True,
        legendare_resistenzen=True,
        phasenwechsel=True,
        beschwoerung=True,
        hinweis="Kampagnen-Endboss mit extremem Zeitkontroll-Druck, Flächeneffekten und mehrphasigem Design.",
    ),
    "goblin_plaenkler": MonsterProfil(
        key="goblin_plaenkler",
        name="Goblin-Plänkler",
        cr=0.25,
        tags=(MonsterTag.HEIMLICH, MonsterTag.MOBIL),
        action_weight_bonus=0.05,
        volatility_bonus=0.08,
        hinweis="Schwach einzeln, aber stark bei Hinterhalten, Fokusfeuer und Gelände.",
    ),
    "schildwache": MonsterProfil(
        key="schildwache",
        name="Schildwache",
        cr=0.5,
        tags=(MonsterTag.TANK,),
        threat_modifier_bonus=0.05,
        hinweis="Niedrige Volatilität, aber gut zum Binden der Frontline.",
    ),
    "skelettbogenschuetze": MonsterProfil(
        key="skelettbogenschuetze",
        name="Skelett-Bogenschütze",
        cr=0.25,
        tags=(MonsterTag.FERNKAMPF,),
        action_weight_bonus=0.03,
        hinweis="Skaliert stark mit Deckung und Engpässen.",
    ),
    "ork_brute": MonsterProfil(
        key="ork_brute",
        name="Ork-Brute",
        cr=1,
        tags=(MonsterTag.BURST, MonsterTag.TANK),
        threat_modifier_bonus=0.08,
        hinweis="Hoher Anfangsdruck, aber weniger gefährlich bei langem Kampf.",
    ),
    "kult_magier": MonsterProfil(
        key="kult_magier",
        name="Kult-Magier",
        cr=3,
        tags=(MonsterTag.CONTROL, MonsterTag.FLAECHE, MonsterTag.DEBUFF),
        threat_modifier_bonus=0.12,
        action_weight_bonus=0.08,
        volatility_bonus=0.18,
        hinweis="Swingy Gegner mit hoher Zauber-Volatilität.",
    ),
    "elite_ritter": MonsterProfil(
        key="elite_ritter",
        name="Elite-Ritter",
        cr=4,
        tags=(MonsterTag.TANK, MonsterTag.MOBIL, MonsterTag.BURST),
        threat_modifier_bonus=0.1,
        action_weight_bonus=0.06,
        hinweis="Konstanter Druck mit guter Haltbarkeit und starker Zielbindung.",
    ),
    "schattenassassine": MonsterProfil(
        key="schattenassassine",
        name="Schatten-Assassine",
        cr=8,
        tags=(MonsterTag.HEIMLICH, MonsterTag.BURST, MonsterTag.MOBIL),
        threat_modifier_bonus=0.12,
        action_weight_bonus=0.08,
        volatility_bonus=0.22,
        hinweis="Sehr hoher Eröffnungsdruck, vor allem gegen verwundbare Hinterreihen.",
    ),
    "nekromant": MonsterProfil(
        key="nekromant",
        name="Nekromant",
        cr=9,
        tags=(MonsterTag.CONTROL, MonsterTag.BESCHWOERUNG, MonsterTag.DEBUFF),
        threat_modifier_bonus=0.15,
        action_weight_bonus=0.14,
        volatility_bonus=0.18,
        beschwoerung=True,
        hinweis="Erzeugt über Adds und Debuffs überdurchschnittlichen Langzeitdruck.",
    ),
    "junger_drache": MonsterProfil(
        key="junger_drache",
        name="Junger Drache",
        cr=10,
        tags=(MonsterTag.BURST, MonsterTag.FLAECHE, MonsterTag.MOBIL),
        threat_modifier_bonus=0.15,
        action_weight_bonus=0.12,
        volatility_bonus=0.2,
        hinweis="Breath Weapon und Mobilität machen den Kampf deutlich swingy.",
    ),
    "uralter_waechter": MonsterProfil(
        key="uralter_waechter",
        name="Uralter Wächter",
        cr=15,
        tags=(MonsterTag.TANK, MonsterTag.BURST, MonsterTag.FLAECHE),
        threat_modifier_bonus=0.18,
        action_weight_bonus=0.18,
        volatility_bonus=0.16,
        legendare_aktionen=True,
        legendare_resistenzen=True,
        phasenwechsel=True,
        hinweis="Bossprofil mit Solo-Tauglichkeit durch legendäre Aktionen und Phasenwechsel.",
    ),
}

MONSTER_TAG_BY_NAME = {tag.name: tag for tag in MonsterTag}
MONSTER_PROFILE_ALIASES = {
    "blutjaeger": "blutjager",
    "soeldner": "soldner",
    "zerra_die_fluesterin": "zerra_die_flusterin",
}


@dataclass(frozen=True)
class EncounterAnalyse:
    basis_xp: int
    angepasst_xp: int
    bedrohungs_xp: int
    praxis_xp: int
    monster_anzahl: int
    multiplikator: float
    party_power: float
    encounter_faktor: float
    nominale_schwierigkeit: str
    praxis_schwierigkeit: str
    volatilitaet: str
    details: list[str]
    hinweise: list[str]
    wellen: int = 1
    ressourcendruck_xp: int | None = None
    ressourcendruck_schwierigkeit: str | None = None


@dataclass(frozen=True)
class EncounterVorschlag:
    name: str
    gegner: list[str]
    analyse: EncounterAnalyse
    monster_liste: list[MonsterEintrag]


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def unique_tags(tags):
    return tuple(dict.fromkeys(tags))


@lru_cache(maxsize=1)
def load_monster_profile_catalog():
    katalog = dict(MONSTER_PROFILE_CATALOG)

    if not MONSTER_CATALOG_PATH.exists():
        return katalog

    try:
        payload = json.loads(MONSTER_CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return katalog

    profiles = payload.get("profiles")
    if not isinstance(profiles, list):
        return katalog

    for entry in profiles:
        if not isinstance(entry, dict):
            continue

        key = entry.get("key")
        name = entry.get("name")
        cr = entry.get("cr")
        tags_raw = entry.get("tags", [])
        if (
            not isinstance(key, str)
            or not isinstance(name, str)
            or not isinstance(tags_raw, list)
        ):
            continue
        if not isinstance(cr, int | float):
            continue

        tags = tuple(
            MONSTER_TAG_BY_NAME[tag_name]
            for tag_name in tags_raw
            if isinstance(tag_name, str) and tag_name in MONSTER_TAG_BY_NAME
        )

        katalog[key] = MonsterProfil(
            key=key,
            name=name,
            cr=float(cr),
            tags=tags,
            quelle=str(entry.get("source_path", "")),
            threat_modifier_bonus=float(entry.get("threat_modifier_bonus", 0.0)),
            action_weight_bonus=float(entry.get("action_weight_bonus", 0.0)),
            volatility_bonus=float(entry.get("volatility_bonus", 0.0)),
            legendare_aktionen=bool(entry.get("legendary_actions", False)),
            legendare_resistenzen=bool(entry.get("legendary_resistances", False)),
            phasenwechsel=bool(entry.get("phase_change", False)),
            beschwoerung=bool(entry.get("summons", False)),
            hinweis=str(entry.get("hint", "")),
        )

    return katalog


def resolve_profile_key(profile_key):
    katalog = load_monster_profile_catalog()
    alias_key = MONSTER_PROFILE_ALIASES.get(profile_key)
    if alias_key in katalog:
        return alias_key
    if profile_key in katalog:
        return profile_key
    return alias_key or profile_key


def monster_profile_options():
    katalog = load_monster_profile_catalog()
    optionen = [
        key
        for key in katalog.keys()
        if not (
            key in MONSTER_PROFILE_ALIASES and MONSTER_PROFILE_ALIASES[key] in katalog
        )
    ]
    return tuple(
        sorted(optionen, key=lambda key: get_monster_profile(key).name.casefold())
    )


def get_monster_profile(profile_key):
    return load_monster_profile_catalog()[resolve_profile_key(profile_key)]


def profile_select_label(profile_key):
    profil = get_monster_profile(profile_key)
    return f"{profil.name} | CR {format_cr(profil.cr)}"


def monster_entry_from_profile(profil: MonsterProfil, anzahl: int, extra_tags=()):
    return MonsterEintrag(
        cr=profil.cr,
        anzahl=anzahl,
        tags=unique_tags(profil.tags + tuple(extra_tags)),
        anzeigename=profil.name,
        profil_id=profil.key,
        profil_hinweis=profil.hinweis,
        threat_modifier_bonus=profil.threat_modifier_bonus,
        action_weight_bonus=profil.action_weight_bonus,
        volatility_bonus=profil.volatility_bonus,
        profil_legendare_aktionen=profil.legendare_aktionen,
        profil_legendare_resistenzen=profil.legendare_resistenzen,
        profil_phasenwechsel=profil.phasenwechsel,
        profil_beschwoerung=profil.beschwoerung,
    )


def optionen_mit_profilen(optionen: EncounterOptionen, monster_liste):
    return replace(
        optionen,
        legendare_aktionen=optionen.legendare_aktionen
        or any(monster.profil_legendare_aktionen for monster in monster_liste),
        legendare_resistenzen=optionen.legendare_resistenzen
        or any(monster.profil_legendare_resistenzen for monster in monster_liste),
        phasenwechsel=optionen.phasenwechsel
        or any(monster.profil_phasenwechsel for monster in monster_liste),
        gegner_beschwoeren=optionen.gegner_beschwoeren
        or any(monster.profil_beschwoerung for monster in monster_liste),
    )


def xp_grenzen(party: Party):
    leicht, mittel, schwer, toedlich = XP_THRESHOLDS[party.stufe]
    return {
        "LEICHT": leicht * party.spieler,
        "MITTEL": mittel * party.spieler,
        "SCHWER": schwer * party.spieler,
        "TÖDLICH": toedlich * party.spieler,
    }


def format_cr(cr):
    if cr == 0.125:
        return "1/8"
    if cr == 0.25:
        return "1/4"
    if cr == 0.5:
        return "1/2"
    if float(cr).is_integer():
        return str(int(cr))
    return f"{cr:.1f}"


def difficulty_text(index):
    icon, label = DIFFICULTY_SCALE[index]
    return f"{icon} {label}"


def volatility_text(index):
    icon, label = VOLATILITY_SCALE[index]
    return f"{icon} {label}"


def difficulty_index_for_xp(xp, grenzen):
    if xp < grenzen["LEICHT"]:
        return 0
    if xp < grenzen["MITTEL"]:
        return 1
    if xp < grenzen["SCHWER"]:
        return 2
    if xp < grenzen["TÖDLICH"]:
        return 3
    if xp < int(grenzen["TÖDLICH"] * 1.5):
        return 4
    return 5


def difficulty_index_from_text(text):
    labels = [difficulty_text(index) for index in range(len(DIFFICULTY_SCALE))]
    return labels.index(text)


def target_index(schwierigkeit):
    return {
        Schwierigkeit.LEICHT: 1,
        Schwierigkeit.MITTEL: 2,
        Schwierigkeit.SCHWER: 3,
        Schwierigkeit.TOEDLICH: 4,
    }[schwierigkeit]


def target_xp(party, schwierigkeit, grenzen):
    if schwierigkeit == Schwierigkeit.LEICHT:
        return int((grenzen["LEICHT"] + grenzen["MITTEL"]) / 2)
    if schwierigkeit == Schwierigkeit.MITTEL:
        return int((grenzen["MITTEL"] + grenzen["SCHWER"]) / 2)
    if schwierigkeit == Schwierigkeit.SCHWER:
        return int((grenzen["SCHWER"] + grenzen["TÖDLICH"]) / 2)
    return int(grenzen["TÖDLICH"] * 1.15)


def xp_fuer(cr, anzahl):
    return CR_XP[cr] * anzahl


def xp_fuer_monsterliste(monster_liste):
    gesamt_xp = 0
    details = []
    for monster in monster_liste:
        xp = xp_fuer(monster.cr, monster.anzahl)
        gesamt_xp += xp
        monster_name = monster.anzeigename or f"CR {format_cr(monster.cr)}"
        tag_text = ""
        if monster.tags:
            tag_text = " | Tags: " + ", ".join(tag.label for tag in monster.tags)
        details.append(
            f"{monster.anzahl}× {monster_name} (CR {format_cr(monster.cr)}) -> {xp} XP{tag_text}"
        )
    return gesamt_xp, details


def encounter_multiplikator(monster_anzahl, spielerzahl):
    basis = 1.0
    for obergrenze, multiplikator in MONSTER_COUNT_MULTIPLIERS:
        if monster_anzahl <= obergrenze:
            basis = multiplikator
            break

    stufen = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
    index = stufen.index(basis)
    if spielerzahl <= 3:
        index = min(index + 1, len(stufen) - 1)
    elif spielerzahl >= 6:
        index = max(index - 1, 0)
    return stufen[index]


def party_power_factor(kontext: PartyKontext):
    faktor = (
        kontext.optimierung.factor
        * kontext.ausruestung.factor
        * kontext.ressourcen.factor
        * kontext.kontrolle.factor
        * kontext.heilung.factor
        * kontext.frontline.factor
        * kontext.fernkampf.factor
    )
    return clamp(faktor, 0.6, 1.6)


def threat_modifier_for_entry(monster: MonsterEintrag):
    modifier = (
        1.0
        + monster.threat_modifier_bonus
        + sum(tag.threat_bonus for tag in monster.tags)
    )
    if len(monster.tags) >= 3:
        modifier += 0.05 * (len(monster.tags) - 2)
    return clamp(modifier, 1.0, 1.9)


def action_weight_for_entry(monster: MonsterEintrag):
    gewicht = 1.0
    if monster.cr >= 5:
        gewicht += 0.15
    if monster.cr >= 11:
        gewicht += 0.1
    gewicht += monster.action_weight_bonus
    gewicht += sum(tag.action_bonus for tag in monster.tags)
    return gewicht


def action_economy_factor(party: Party, monster_liste):
    gegner_aktionen = sum(
        monster.anzahl * action_weight_for_entry(monster) for monster in monster_liste
    )
    spieler_aktionen = party.spieler * 1.35
    ratio = gegner_aktionen / max(1.0, spieler_aktionen)
    return clamp(1.0 + ((ratio - 1.0) * 0.45), 0.78, 1.35)


def focusfire_factor(party: Party, monster_liste):
    monster_anzahl = sum(monster.anzahl for monster in monster_liste)
    ranged_units = sum(
        monster.anzahl
        for monster in monster_liste
        if MonsterTag.FERNKAMPF in monster.tags or MonsterTag.MOBIL in monster.tags
    )
    factor = 1.0
    if monster_anzahl >= party.spieler * 2:
        factor += 0.08
    elif monster_anzahl >= party.spieler:
        factor += 0.04
    if ranged_units >= max(2, party.spieler // 2):
        factor += 0.05
    return clamp(factor, 0.95, 1.18)


def solo_boss_factor(party: Party, monster_liste, optionen: EncounterOptionen):
    del party
    monster_anzahl = sum(monster.anzahl for monster in monster_liste)
    factor = 0.78 if monster_anzahl == 1 else 1.0
    if optionen.legendare_aktionen:
        factor *= 1.22 if monster_anzahl == 1 else 1.08
    if optionen.legendare_resistenzen:
        factor *= 1.08 if monster_anzahl == 1 else 1.03
    if optionen.phasenwechsel:
        factor *= 1.12
    if optionen.gegner_beschwoeren:
        factor *= 1.12
    return clamp(factor, 0.65, 1.45)


def wave_pressure_factor(optionen: EncounterOptionen):
    if optionen.wellen <= 1:
        return 1.0

    factor = 1.0 + (optionen.wellen - 1) * 0.14
    if not optionen.kurze_pause_zwischen_wellen:
        factor += (optionen.wellen - 1) * 0.08
    if not optionen.heilfenster_zwischen_wellen:
        factor += (optionen.wellen - 1) * 0.05
    if optionen.gleiches_kampffeld:
        factor += (optionen.wellen - 1) * 0.04
    return clamp(factor, 1.0, 1.85)


def volatility_index(monster_liste, optionen: EncounterOptionen):
    score = 0.0
    monster_anzahl = sum(monster.anzahl for monster in monster_liste)

    for monster in monster_liste:
        entry_weight = 1 + (0.1 * min(monster.anzahl, 5))
        score += monster.volatility_bonus * entry_weight
        score += sum(tag.volatility_bonus for tag in monster.tags) * entry_weight

    if optionen.ueberraschung == Ueberraschung.GEGNER:
        score += 0.45
    elif optionen.ueberraschung == Ueberraschung.HINTERHALT:
        score += 0.8
    elif optionen.ueberraschung == Ueberraschung.SPIELER:
        score -= 0.15

    if optionen.terrain in (
        Terrainlage.GEGNERVORTEIL,
        Terrainlage.ENGPASS,
        Terrainlage.FERNKAMPF_GEGNER,
    ):
        score += 0.25
    if optionen.legendare_aktionen:
        score += 0.2
    if optionen.phasenwechsel:
        score += 0.35
    if optionen.gegner_beschwoeren:
        score += 0.25
    if monster_anzahl >= 8:
        score += 0.2
    if optionen.wellen > 1:
        score += min(0.5, 0.12 * optionen.wellen)

    if score < 0.8:
        return 0
    if score < 1.8:
        return 1
    if score < 3.0:
        return 2
    return 3


def analyse_encounter(
    party: Party,
    party_kontext: PartyKontext,
    optionen: EncounterOptionen,
    monster_liste,
):
    optionen = optionen_mit_profilen(optionen, monster_liste)
    grenzen = xp_grenzen(party)
    basis_xp, details = xp_fuer_monsterliste(monster_liste)
    monster_anzahl = sum(monster.anzahl for monster in monster_liste)
    multiplikator = encounter_multiplikator(monster_anzahl, party.spieler)
    angepasst_xp = int(round(basis_xp * multiplikator))

    bedrohungs_basis = 0
    for monster in monster_liste:
        entry_xp = xp_fuer(monster.cr, monster.anzahl)
        bedrohungs_basis += int(round(entry_xp * threat_modifier_for_entry(monster)))
    bedrohungs_xp = int(round(bedrohungs_basis * multiplikator))

    party_power = party_power_factor(party_kontext)
    action_factor = action_economy_factor(party, monster_liste)
    focus_factor = focusfire_factor(party, monster_liste)
    boss_factor = solo_boss_factor(party, monster_liste, optionen)
    encounter_faktor = (
        optionen.terrain.factor
        * optionen.ueberraschung.factor
        * action_factor
        * focus_factor
        * boss_factor
    )
    encounter_faktor = clamp(encounter_faktor, 0.65, 2.1)

    praxis_xp = int(round((bedrohungs_xp * encounter_faktor) / party_power))

    nominal_index = difficulty_index_for_xp(angepasst_xp, grenzen)
    praxis_index = difficulty_index_for_xp(praxis_xp, grenzen)
    volatilitaet = volatility_text(volatility_index(monster_liste, optionen))

    ressourcendruck_xp = None
    ressourcendruck_schwierigkeit = None
    if optionen.wellen > 1:
        wave_factor = wave_pressure_factor(optionen)
        ressourcendruck_xp = int(round(praxis_xp * wave_factor))
        ressourcendruck_schwierigkeit = difficulty_text(
            difficulty_index_for_xp(ressourcendruck_xp, grenzen)
        )

    hinweise = []
    if monster_anzahl == 1 and not optionen.legendare_aktionen and party.spieler >= 4:
        hinweise.append(
            "Solo-Boss ohne legendäre Aktionen bleibt trotz hoher XP oft kontrollierbar und damit leichter als der Zahlenwert vermuten lässt."
        )
    if optionen.legendare_aktionen or optionen.phasenwechsel:
        hinweise.append(
            "Boss-Mechaniken erhöhen die effektive Kampfdauer und machen Fokusfeuer der Gruppe weniger dominant."
        )
    if action_factor > 1.1:
        hinweise.append(
            "Die Gegner erzeugen überdurchschnittlich viele wirksame Aktionen pro Runde. Das hebt die Praxis-Schwierigkeit merklich an."
        )
    if focus_factor > 1.08:
        hinweise.append(
            "Viele oder mobile Gegner begünstigen Fokusfeuer, Flanken und das Blockieren von Räumen."
        )
    if optionen.terrain.factor > 1.1:
        hinweise.append(
            "Das Gelände liegt auf Gegnerseite und hebt die effektive Gefahr zusätzlich an."
        )
    if optionen.ueberraschung.factor > 1.1:
        hinweise.append(
            "Die Eröffnungsrunde liegt eher bei den Gegnern. Das erhöht Burst-Risiko und Kampfschwankung deutlich."
        )
    if optionen.wellen > 1:
        hinweise.append(
            f"Die Wellen werden pro Welle bewertet. Der kumulierte Ressourcendruck über {optionen.wellen} Wellen wird separat ausgewiesen."
        )
    if praxis_index > nominal_index:
        hinweise.append(
            "Die Praxis-Einstufung liegt über der nominalen DMG-Wertung. Ursache sind hier Rollen, Gelände, Überraschung oder Party-Kontext."
        )

    profil_hinweise = [
        monster.profil_hinweis for monster in monster_liste if monster.profil_hinweis
    ]
    if profil_hinweise:
        hinweise.extend(dict.fromkeys(profil_hinweise))

    if any(monster.profil_legendare_aktionen for monster in monster_liste):
        hinweise.append(
            "Mindestens ein Monsterprofil aktiviert legendäre Aktionen automatisch für die Analyse."
        )

    detail_liste = list(details)
    detail_liste.append(f"Party-Power: x{party_power:.2f}")
    detail_liste.append(f"Encounter-Faktor: x{encounter_faktor:.2f}")
    detail_liste.append(f"Action-Economy-Faktor: x{action_factor:.2f}")
    detail_liste.append(f"Fokusfeuer-Faktor: x{focus_factor:.2f}")
    detail_liste.append(f"Boss-Faktor: x{boss_factor:.2f}")

    return EncounterAnalyse(
        basis_xp=basis_xp,
        angepasst_xp=angepasst_xp,
        bedrohungs_xp=bedrohungs_xp,
        praxis_xp=praxis_xp,
        monster_anzahl=monster_anzahl,
        multiplikator=multiplikator,
        party_power=party_power,
        encounter_faktor=encounter_faktor,
        nominale_schwierigkeit=difficulty_text(nominal_index),
        praxis_schwierigkeit=difficulty_text(praxis_index),
        volatilitaet=volatilitaet,
        details=detail_liste,
        hinweise=hinweise,
        wellen=optionen.wellen,
        ressourcendruck_xp=ressourcendruck_xp,
        ressourcendruck_schwierigkeit=ressourcendruck_schwierigkeit,
    )


def score_vorschlag(analyse: EncounterAnalyse, target_index_value, target_xp_value):
    praxis_index = difficulty_index_from_text(analyse.praxis_schwierigkeit)
    return abs(analyse.praxis_xp - target_xp_value) + (
        abs(praxis_index - target_index_value) * int(target_xp_value * 0.35)
    )


def cr_auswahl(min_cr=0.125, max_cr=None):
    if max_cr is None:
        max_cr = VALID_CRS[-1]
    return [cr for cr in VALID_CRS if min_cr <= cr <= max_cr]


def finde_besten_vorschlag(
    name, kandidaten, party, party_kontext, optionen, schwierigkeit
):
    del optionen
    grenzen = xp_grenzen(party)
    target_index_value = target_index(schwierigkeit)
    target_xp_value = target_xp(party, schwierigkeit, grenzen)
    bester_vorschlag = None
    bester_score = None

    for gegner, monster_liste, encounter_override in kandidaten:
        analyse = analyse_encounter(
            party, party_kontext, encounter_override, monster_liste
        )
        score = score_vorschlag(analyse, target_index_value, target_xp_value)
        if bester_score is None or score < bester_score:
            bester_score = score
            bester_vorschlag = EncounterVorschlag(
                name=name,
                gegner=gegner,
                analyse=analyse,
                monster_liste=list(monster_liste),
            )

    return bester_vorschlag


def boss_minions_beispiel(party, party_kontext, optionen, schwierigkeit):
    kandidaten = []
    boss_min = max(1, party.stufe - 1)
    boss_max = min(
        VALID_CRS[-1],
        party.stufe + (3 if schwierigkeit == Schwierigkeit.TOEDLICH else 2),
    )

    for boss_cr in cr_auswahl(min_cr=boss_min, max_cr=boss_max):
        for minion_cr in cr_auswahl(
            min_cr=0.125, max_cr=max(0.5, min(boss_cr, party.stufe))
        ):
            if minion_cr >= boss_cr:
                continue
            for minions in range(1, party.spieler * 3 + 1):
                monster_liste = [
                    MonsterEintrag(boss_cr, 1, (MonsterTag.BURST, MonsterTag.TANK)),
                    MonsterEintrag(minion_cr, minions, (MonsterTag.MOBIL,)),
                ]
                encounter_override = replace(optionen, wellen=1)
                gegner = [
                    f"1× CR {format_cr(boss_cr)}",
                    f"{minions}× CR {format_cr(minion_cr)}",
                ]
                kandidaten.append((gegner, monster_liste, encounter_override))

    return finde_besten_vorschlag(
        "Boss + Minions", kandidaten, party, party_kontext, optionen, schwierigkeit
    )


def elite_trupp_beispiel(party, party_kontext, optionen, schwierigkeit):
    kandidaten = []
    elite_min = max(0.5, party.stufe - 3)
    elite_max = min(VALID_CRS[-1], party.stufe + 1)

    for elite_cr in cr_auswahl(min_cr=elite_min, max_cr=elite_max):
        for elites in range(2, party.spieler + 3):
            monster_liste = [
                MonsterEintrag(elite_cr, elites, (MonsterTag.TANK, MonsterTag.MOBIL))
            ]
            encounter_override = replace(optionen, wellen=1)
            gegner = [f"{elites}× CR {format_cr(elite_cr)}"]
            kandidaten.append((gegner, monster_liste, encounter_override))

    return finde_besten_vorschlag(
        "Elite-Trupp", kandidaten, party, party_kontext, optionen, schwierigkeit
    )


def ueberzahl_beispiel(party, party_kontext, optionen, schwierigkeit):
    kandidaten = []
    swarm_max = max(0.5, min(VALID_CRS[-1], party.stufe / 2))

    for swarm_cr in cr_auswahl(min_cr=0.125, max_cr=swarm_max):
        for swarm in range(max(4, party.spieler), party.spieler * 5 + 1):
            tags = (MonsterTag.MOBIL,)
            if schwierigkeit in (Schwierigkeit.SCHWER, Schwierigkeit.TOEDLICH):
                tags = (MonsterTag.MOBIL, MonsterTag.FERNKAMPF)
            monster_liste = [MonsterEintrag(swarm_cr, swarm, tags)]
            encounter_override = replace(optionen, wellen=1)
            gegner = [f"{swarm}× CR {format_cr(swarm_cr)}"]
            kandidaten.append((gegner, monster_liste, encounter_override))

    return finde_besten_vorschlag(
        "Überzahl", kandidaten, party, party_kontext, optionen, schwierigkeit
    )


def wellen_beispiel(party, party_kontext, optionen, schwierigkeit):
    kandidaten = []
    waves = max(2, optionen.wellen)
    per_wave_target = {
        Schwierigkeit.LEICHT: Schwierigkeit.LEICHT,
        Schwierigkeit.MITTEL: Schwierigkeit.LEICHT,
        Schwierigkeit.SCHWER: Schwierigkeit.MITTEL,
        Schwierigkeit.TOEDLICH: Schwierigkeit.SCHWER,
    }[schwierigkeit]

    grenzen = xp_grenzen(party)
    target_index_value = target_index(per_wave_target)
    target_xp_value = target_xp(party, per_wave_target, grenzen)

    for minion_cr in cr_auswahl(
        min_cr=0.125, max_cr=max(0.5, min(VALID_CRS[-1], party.stufe / 3))
    ):
        for anzahl in range(max(3, party.spieler), party.spieler * 3 + 3):
            monster_liste = [MonsterEintrag(minion_cr, anzahl, (MonsterTag.MOBIL,))]
            encounter_override = replace(optionen, wellen=waves)
            analyse = analyse_encounter(
                party, party_kontext, encounter_override, monster_liste
            )
            score = abs(analyse.praxis_xp - target_xp_value) + (
                abs(
                    difficulty_index_for_xp(analyse.praxis_xp, grenzen)
                    - target_index_value
                )
                * int(target_xp_value * 0.35)
            )
            gegner = [
                f"{anzahl}× CR {format_cr(minion_cr)} pro Welle",
                f"{waves} Wellen insgesamt",
            ]
            kandidaten.append((score, gegner, analyse, list(monster_liste)))

    if not kandidaten:
        return EncounterVorschlag(
            name="🌊 Wellenkampf",
            gegner=["Kein passender Wellenkampf gefunden"],
            analyse=analyse_encounter(party, party_kontext, optionen, []),
            monster_liste=[],
        )

    _, gegner, analyse, monster_liste = min(kandidaten, key=lambda entry: entry[0])
    return EncounterVorschlag(
        name="🌊 Wellenkampf",
        gegner=gegner,
        analyse=analyse,
        monster_liste=list(monster_liste),
    )


def beispiele(party, party_kontext, optionen, schwierigkeit):
    return [
        boss_minions_beispiel(party, party_kontext, optionen, schwierigkeit),
        elite_trupp_beispiel(party, party_kontext, optionen, schwierigkeit),
        ueberzahl_beispiel(party, party_kontext, optionen, schwierigkeit),
        wellen_beispiel(party, party_kontext, optionen, schwierigkeit),
    ]


def render_hinweisbox(text):
    if text.startswith("Solo-Boss"):
        st.warning(text)
    elif text.startswith("Die Praxis-Einstufung") or text.startswith(
        "Die Gegner erzeugen"
    ):
        st.info(text)
    else:
        st.caption(text)


def render_legend_content(grenzen):
    st.markdown(
        "- **Nominale Schwierigkeit**: reine DMG-Einstufung aus Basis-XP und Gegnerzahl.\n"
        "- **Bedrohungs-XP**: DMG-XP plus Monsterrollen wie Burst, Control, Beschwörung oder Flächenschaden.\n"
        "- **Praxis-XP**: Bedrohungs-XP korrigiert um Action Economy, Fokusfeuer, Gelände, Überraschung, Boss-Mechaniken und Party-Stärke.\n"
        "- **Volatilität**: Wie swingy der Kampf ist. Hohe Volatilität bedeutet mehr Risiko für extreme Verläufe.\n"
        "- **Ressourcendruck**: Nur bei Wellenkämpfen. Zeigt, wie stark mehrere Wellen die Gruppe über Zeit zermürben."
    )
    st.caption(
        f"Aktuelle Schwellen: Leicht {grenzen['LEICHT']} | Mittel {grenzen['MITTEL']} | Schwer {grenzen['SCHWER']} | Tödlich {grenzen['TÖDLICH']}"
    )


def render_party_context_summary(party_kontext):
    st.caption(
        " | ".join(
            (
                party_kontext.optimierung.label,
                party_kontext.ausruestung.label,
                party_kontext.ressourcen.label,
                party_kontext.kontrolle.label,
                party_kontext.heilung.label,
                party_kontext.frontline.label,
                party_kontext.fernkampf.label,
            )
        )
    )


def render_encounter_context_summary(optionen):
    teile = [
        optionen.terrain.label,
        optionen.ueberraschung.label,
        f"{optionen.wellen} Wellen",
    ]
    if optionen.legendare_aktionen:
        teile.append("Leg. Aktionen")
    if optionen.legendare_resistenzen:
        teile.append("Resistenzen")
    if optionen.phasenwechsel:
        teile.append("Phase")
    if optionen.gegner_beschwoeren:
        teile.append("Beschwörung")
    st.caption(" | ".join(teile))


def render_party_context_inputs():
    cols = st.columns(4)
    optimierung = cols[0].selectbox(
        "Optimierung",
        list(PartyOptimierung),
        format_func=lambda item: item.label,
        key="enc_party_optimierung",
    )
    ausruestung = cols[1].selectbox(
        "Ausrüstung",
        list(Ausruestungsniveau),
        format_func=lambda item: item.label,
        key="enc_party_ausruestung",
    )
    ressourcen = cols[2].selectbox(
        "Ressourcen",
        list(Ressourcenstand),
        format_func=lambda item: item.label,
        key="enc_party_ressourcen",
    )
    kontrolle = cols[3].selectbox(
        "Kontrolle",
        list(Kontrollniveau),
        format_func=lambda item: item.label,
        key="enc_party_kontrolle",
    )

    cols = st.columns(3)
    heilung = cols[1].selectbox(
        "Heilung",
        list(Heilniveau),
        format_func=lambda item: item.label,
        key="enc_party_heilung",
    )
    frontline = cols[0].selectbox(
        "Frontline",
        list(FrontlineNiveau),
        format_func=lambda item: item.label,
        key="enc_party_frontline",
    )
    fernkampf = cols[2].selectbox(
        "Fernkampf",
        list(Fernkampfniveau),
        format_func=lambda item: item.label,
        key="enc_party_fernkampf",
    )

    return PartyKontext(
        optimierung=optimierung,
        ausruestung=ausruestung,
        ressourcen=ressourcen,
        kontrolle=kontrolle,
        heilung=heilung,
        frontline=frontline,
        fernkampf=fernkampf,
    )


def render_encounter_context_inputs():
    cols = st.columns(3)
    terrain = cols[0].selectbox(
        "Terrain",
        list(Terrainlage),
        format_func=lambda item: item.label,
        key="enc_terrain",
    )
    ueberraschung = cols[1].selectbox(
        "Überraschung",
        list(Ueberraschung),
        format_func=lambda item: item.label,
        key="enc_surprise",
    )
    wellen = cols[2].number_input(
        "Wellen", min_value=1, max_value=6, value=1, step=1, key="enc_waves"
    )

    cols = st.columns(4)
    legendare_aktionen = cols[0].checkbox(
        "Legendäre Aktionen", key="enc_legend_actions"
    )
    legendare_resistenzen = cols[1].checkbox("Resistenzen", key="enc_legend_res")
    phasenwechsel = cols[2].checkbox("Phase", key="enc_phase")
    gegner_beschwoeren = cols[3].checkbox("Beschwörung", key="enc_summons")
    kurze_pause = False
    heilfenster = False
    gleiches_feld = True
    if int(wellen) > 1:
        cols = st.columns(3)
        kurze_pause = cols[0].checkbox("Kurze Pause", value=False, key="enc_wave_rest")
        heilfenster = cols[1].checkbox("Heilfenster", value=False, key="enc_wave_heal")
        gleiches_feld = cols[2].checkbox(
            "Gleiches Feld", value=True, key="enc_same_field"
        )

    return EncounterOptionen(
        terrain=terrain,
        ueberraschung=ueberraschung,
        legendare_aktionen=legendare_aktionen,
        legendare_resistenzen=legendare_resistenzen,
        phasenwechsel=phasenwechsel,
        gegner_beschwoeren=gegner_beschwoeren,
        wellen=int(wellen),
        kurze_pause_zwischen_wellen=kurze_pause,
        heilfenster_zwischen_wellen=heilfenster,
        gleiches_kampffeld=gleiches_feld,
    )


def render_advanced_settings(grenzen):
    with st.expander("Umgebungsdetails", expanded=False):
        optionen = render_encounter_context_inputs()
        with st.expander("Legende", expanded=False):
            render_legend_content(grenzen)
    return optionen


def load_example_into_custom_builder(beispiel: EncounterVorschlag):
    st.session_state["custom_monster_types"] = len(beispiel.monster_liste)

    for index, monster in enumerate(beispiel.monster_liste):
        st.session_state[f"anzahl_custom_{index}"] = int(monster.anzahl)
        if monster.profil_id:
            profil = get_monster_profile(monster.profil_id)
            extra_tags = tuple(tag for tag in monster.tags if tag not in profil.tags)
            st.session_state[f"monster_mode_{index}"] = "Profil"
            st.session_state[f"profile_custom_{index}"] = monster.profil_id
            st.session_state[f"profile_tags_custom_{index}"] = list(extra_tags)
        else:
            st.session_state[f"monster_mode_{index}"] = "Frei"
            st.session_state[f"cr_custom_{index}"] = monster.cr
            st.session_state[f"tags_custom_{index}"] = list(monster.tags)

    for index in range(len(beispiel.monster_liste), 6):
        st.session_state.pop(f"profile_tags_custom_{index}", None)
        st.session_state.pop(f"tags_custom_{index}", None)

    st.session_state["encounter_layout_segment_pending"] = "Eigene Monster"


def render_beispielkarte(spalte, beispiel: EncounterVorschlag):
    analyse = beispiel.analyse
    with spalte.container(border=False):
        spalte.markdown(f"### {beispiel.name}")
        spalte.caption(" | ".join(beispiel.gegner))
        kennzahlen = spalte.columns(2)
        kennzahlen[0].markdown(
            f"**Praxis**<br>{analyse.praxis_schwierigkeit}",
            unsafe_allow_html=True,
        )
        kennzahlen[1].markdown(
            f"**Nominal**<br>{analyse.nominale_schwierigkeit}",
            unsafe_allow_html=True,
        )
        spalte.caption(
            f"Volatilität: {analyse.volatilitaet} | Praxis-XP: {analyse.praxis_xp}"
        )
        ressourcendruck = analyse.ressourcendruck_schwierigkeit or "-"
        if analyse.ressourcendruck_xp is None:
            ressourcendruck = "-"
        spalte.caption(f"Ressourcendruck: {ressourcendruck}")
        with spalte.expander("Details", expanded=False):
            st.markdown(f"**Basis-XP:** {analyse.basis_xp}")
            st.markdown(
                f"**DMG-XP:** {analyse.angepasst_xp} (x{analyse.multiplikator:g})"
            )
            st.markdown(f"**Bedrohungs-XP:** {analyse.bedrohungs_xp}")
            st.markdown(f"**Praxis-XP:** {analyse.praxis_xp}")
            for hinweis in analyse.hinweise[1:3]:
                st.markdown(f"- {hinweis}")
        if spalte.button(
            "Als Startpunkt nutzen",
            key=f"encounter_example_load_{beispiel.name}",
            use_container_width=True,
        ):
            load_example_into_custom_builder(beispiel)
            st.rerun()
        if analyse.hinweise:
            spalte.caption(analyse.hinweise[0])
        else:
            spalte.caption("Keine besonderen Treiber.")


def monster_flag_text(profil: MonsterProfil):
    flags = []
    if profil.legendare_aktionen:
        flags.append("Legendäre Aktionen")
    if profil.legendare_resistenzen:
        flags.append("Legendäre Resistenzen")
    if profil.phasenwechsel:
        flags.append("Phasenwechsel")
    if profil.beschwoerung:
        flags.append("Beschwörung")
    return " | ".join(flags)


def render_profile_monster_inputs(index, anzahl, spalte):
    profile_state_key = f"profile_custom_{index}"
    if profile_state_key in st.session_state:
        st.session_state[profile_state_key] = resolve_profile_key(
            st.session_state[profile_state_key]
        )

    profil_key = spalte.selectbox(
        "Profil",
        monster_profile_options(),
        format_func=profile_select_label,
        key=profile_state_key,
    )
    profil = get_monster_profile(profil_key)
    st.caption(f"CR {format_cr(profil.cr)} | {profil.name}")

    with st.expander("Details", expanded=False):
        if profil.quelle:
            st.caption(profil.quelle)
        if profil.hinweis:
            st.caption(profil.hinweis)
        st.caption("Standard-Tags: " + ", ".join(tag.label for tag in profil.tags))
        flag_text = monster_flag_text(profil)
        if flag_text:
            st.caption("Sondermerkmale: " + flag_text)

    return monster_entry_from_profile(
        profil,
        int(anzahl),
        extra_tags=tuple(st.session_state.get(f"profile_tags_custom_{index}", ())),
    )


def render_free_monster_inputs_inline(index, anzahl, spalte):
    cr = spalte.selectbox(
        "CR",
        VALID_CRS,
        format_func=format_cr,
        key=f"cr_custom_{index}",
    )
    cr_wert = cast(float, cr)
    aktive_tags = st.session_state.get(f"tags_custom_{index}", ())
    if aktive_tags:
        st.caption("Tags: " + ", ".join(tag.label for tag in aktive_tags))

    with st.expander("Tags", expanded=False):
        tags = st.multiselect(
            "Tags",
            list(MonsterTag),
            format_func=lambda item: item.label,
            key=f"tags_custom_{index}",
        )

    return MonsterEintrag(cr=cr_wert, anzahl=int(anzahl), tags=tuple(tags))


def render_monster_card(index):
    with st.container(border=True):
        st.markdown(f"**Monster {index + 1}**")
        modus = st.radio(
            f"Eingabemodus Monster {index + 1}",
            ("Profil", "Frei"),
            horizontal=True,
            label_visibility="collapsed",
            key=f"monster_mode_{index}",
        )
        kopf_spalten = st.columns((3, 2))
        anzahl = kopf_spalten[1].number_input(
            "Anzahl",
            min_value=1,
            max_value=30,
            value=1,
            step=1,
            format="%d",
            key=f"anzahl_custom_{index}",
        )
        anzahl = int(anzahl)

        if modus == "Profil":
            monster = render_profile_monster_inputs(index, anzahl, kopf_spalten[0])
        else:
            monster = render_free_monster_inputs_inline(index, anzahl, kopf_spalten[0])

        st.caption(
            f"{monster.anzahl}× {monster.anzeigename or f'CR {format_cr(monster.cr)}'}"
        )
        return monster


def render_monster_builder():
    monster_anzahl = st.number_input(
        "Wie viele unterschiedliche Monster-Typen?",
        min_value=1,
        max_value=6,
        value=2,
        step=1,
        format="%d",
        key="custom_monster_types",
    )
    monster_anzahl = int(monster_anzahl)

    monster_liste = []
    spalten = st.columns(2)
    for index in range(monster_anzahl):
        with spalten[index % 2]:
            monster_liste.append(render_monster_card(index))

    return monster_liste


def render_analysis_summary(analyse: EncounterAnalyse):
    st.subheader("Auswertung")
    st.markdown(f"### {analyse.praxis_schwierigkeit}")
    kennzahlen = st.columns(3)
    kennzahlen[0].metric("Nominal", analyse.nominale_schwierigkeit)
    kennzahlen[1].metric("Volatilität", analyse.volatilitaet)
    if analyse.ressourcendruck_xp is not None:
        kennzahlen[2].metric("Ressourcendruck", analyse.ressourcendruck_schwierigkeit)
    else:
        kennzahlen[2].metric("Monster", str(analyse.monster_anzahl))

    wichtigste_hinweise = analyse.hinweise[:3]
    if wichtigste_hinweise:
        st.caption("Wichtigste Treiber")
        for hinweis in wichtigste_hinweise:
            render_hinweisbox(hinweis)


def render_analysis_details(analyse: EncounterAnalyse, grenzen):
    with st.expander("Rechendetails", expanded=False):
        xp_spalten = st.columns(2)
        xp_spalten[0].markdown(f"**Monster gesamt:** {analyse.monster_anzahl}")
        xp_spalten[1].markdown(f"**Basis-XP:** {analyse.basis_xp}")
        xp_spalten[0].markdown(
            f"**DMG-XP:** {analyse.angepasst_xp} (x{analyse.multiplikator:g})"
        )
        xp_spalten[1].markdown(f"**Bedrohungs-XP:** {analyse.bedrohungs_xp}")
        xp_spalten[0].markdown(f"**Praxis-XP:** {analyse.praxis_xp}")
        xp_spalten[1].markdown(f"**Party-Power:** x{analyse.party_power:.2f}")
        st.markdown(f"**Encounter-Faktor:** x{analyse.encounter_faktor:.2f}")
        if analyse.ressourcendruck_xp is not None:
            st.markdown(
                f"**Ressourcendruck über {analyse.wellen} Wellen:** {analyse.ressourcendruck_xp} | {analyse.ressourcendruck_schwierigkeit}"
            )
        st.caption(
            f"Schwellen für diese Gruppe: Leicht {grenzen['LEICHT']} | Mittel {grenzen['MITTEL']} | Schwer {grenzen['SCHWER']} | Tödlich {grenzen['TÖDLICH']}"
        )
        for detail in analyse.details:
            st.markdown(f"- {detail}")


def render_beispiel_section(beispiel_liste):
    spalten = st.columns(len(beispiel_liste), border=True)
    for index, beispiel in enumerate(beispiel_liste):
        render_beispielkarte(spalten[index], beispiel)


def render_examples_panel(party, grenzen):
    beispiel_liste = beispiele(
        party,
        party_kontext_from_state(),
        encounter_optionen_from_state(),
        st.session_state["cr_input"],
    )
    render_beispiel_section(beispiel_liste)


def render_group_primary_inputs(party):
    primar = st.columns(3)
    primar[0].number_input("Spieler", 1, 8, party.spieler, key="player_input")
    primar[1].number_input("Level", 1, 20, party.stufe, key="level_input")
    primar[2].selectbox(
        "Ziel",
        list(Schwierigkeit),
        format_func=lambda item: item.value,
        key="cr_input",
    )


def render_group_header_panel(party):
    with st.container(border=True):
        render_group_primary_inputs(party)
        render_party_context_summary(party_kontext_from_state())
        with st.expander("Gruppendetails", expanded=False):
            return render_party_context_inputs()


def render_environment_header_panel(grenzen):
    with st.container(border=True):
        render_encounter_context_summary(encounter_optionen_from_state())
        return render_advanced_settings(grenzen)


def render_group_overview_header(party, grenzen):
    cols = st.columns((1, 1), vertical_alignment="top")
    with cols[0]:
        party_kontext = render_group_header_panel(party)
    with cols[1]:
        optionen = render_environment_header_panel(grenzen)
    return party_kontext, optionen


def render_group_and_examples_segment(party, grenzen):
    render_examples_panel(party, grenzen)


def render_monster_builder_panel():
    return render_monster_builder()


def render_analysis_panel(analyse, grenzen):
    render_analysis_summary(analyse)
    render_analysis_details(analyse, grenzen)


def render_custom_workspace(party, party_kontext, optionen, grenzen):
    arbeitsbereich = st.columns((3, 2), vertical_alignment="top")
    with arbeitsbereich[0]:
        monster_liste = render_monster_builder_panel()
    analyse = analyse_encounter(party, party_kontext, optionen, monster_liste)
    with arbeitsbereich[1]:
        render_analysis_panel(analyse, grenzen)
    return analyse


def render_custom_monster_segment(party, party_kontext, optionen, grenzen):
    st.subheader("Eigene Monster")
    return render_custom_workspace(party, party_kontext, optionen, grenzen)


def party_kontext_from_state():
    return PartyKontext(
        optimierung=st.session_state.get(
            "enc_party_optimierung", PartyOptimierung.NORMAL
        ),
        ausruestung=st.session_state.get(
            "enc_party_ausruestung", Ausruestungsniveau.STANDARD
        ),
        ressourcen=st.session_state.get("enc_party_ressourcen", Ressourcenstand.FRISCH),
        kontrolle=st.session_state.get("enc_party_kontrolle", Kontrollniveau.NORMAL),
        heilung=st.session_state.get("enc_party_heilung", Heilniveau.NORMAL),
        frontline=st.session_state.get("enc_party_frontline", FrontlineNiveau.STABIL),
        fernkampf=st.session_state.get("enc_party_fernkampf", Fernkampfniveau.GEMISCHT),
    )


def encounter_optionen_from_state():
    return EncounterOptionen(
        terrain=st.session_state.get("enc_terrain", Terrainlage.NEUTRAL),
        ueberraschung=st.session_state.get("enc_surprise", Ueberraschung.KEINE),
        legendare_aktionen=st.session_state.get("enc_legend_actions", False),
        legendare_resistenzen=st.session_state.get("enc_legend_res", False),
        phasenwechsel=st.session_state.get("enc_phase", False),
        gegner_beschwoeren=st.session_state.get("enc_summons", False),
        wellen=int(st.session_state.get("enc_waves", 1)),
        kurze_pause_zwischen_wellen=st.session_state.get("enc_wave_rest", False),
        heilfenster_zwischen_wellen=st.session_state.get("enc_wave_heal", False),
        gleiches_kampffeld=st.session_state.get("enc_same_field", True),
    )


def set_to_encounter_calculator_view():
    st.session_state["db_flag"] = True
    st.session_state["db"] = "Encounter Rechner"


def encounter_calculator_is_admin():
    user = st.session_state.get("user")
    return bool(user and user.role.value == Roles.GameMaster.value)


def encounter_calculator_view():
    set_to_encounter_calculator_view()
    if "player_input" not in st.session_state:
        st.session_state["player_input"] = 4
    if "level_input" not in st.session_state:
        st.session_state["level_input"] = 5
    if "cr_input" not in st.session_state:
        st.session_state["cr_input"] = Schwierigkeit.MITTEL
    is_admin = encounter_calculator_is_admin()
    if is_admin and "encounter_layout_segment_pending" in st.session_state:
        st.session_state["encounter_layout_segment"] = st.session_state.pop(
            "encounter_layout_segment_pending"
        )
    elif not is_admin:
        st.session_state.pop("encounter_layout_segment_pending", None)
        st.session_state.pop("encounter_layout_segment", None)

    party = Party(
        spieler=st.session_state["player_input"],
        stufe=st.session_state["level_input"],
    )
    grenzen = xp_grenzen(party)
    party_kontext, optionen = render_group_overview_header(party, grenzen)

    party = Party(
        spieler=st.session_state["player_input"],
        stufe=st.session_state["level_input"],
    )
    grenzen = xp_grenzen(party)

    if not is_admin:
        render_group_and_examples_segment(party, grenzen)
        return

    segment = st.segmented_control(
        "Ansicht",
        options=("Gruppe & Beispiele", "Eigene Monster"),
        default="Gruppe & Beispiele",
        key="encounter_layout_segment",
    )

    if segment == "Gruppe & Beispiele":
        render_group_and_examples_segment(party, grenzen)
    else:
        render_custom_monster_segment(party, party_kontext, optionen, grenzen)
