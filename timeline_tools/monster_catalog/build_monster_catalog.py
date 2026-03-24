from __future__ import annotations

import json
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCRIPT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_ROOT.parent.parent
SCAN_FILE = SCRIPT_ROOT / "extracted_monsters.json"
OUTPUT_FILE = SCRIPT_ROOT / "monster_catalog.json"
RULES_VERSION = 1

TAG_ORDER = [
    "BURST",
    "CONTROL",
    "TANK",
    "MOBIL",
    "FERNKAMPF",
    "BESCHWOERUNG",
    "FLAECHE",
    "DEBUFF",
    "HEIMLICH",
]
STRATEGY_ORDER = [
    "boss",
    "controller",
    "summoner",
    "assassin",
    "artillery",
    "defender",
    "skirmisher",
    "brute",
]

TAG_OVERRIDE_MAP = {
    "burst": "BURST",
    "control": "CONTROL",
    "tank": "TANK",
    "mobil": "MOBIL",
    "beweglich": "MOBIL",
    "fernkampf": "FERNKAMPF",
    "beschwoerung": "BESCHWOERUNG",
    "beschworung": "BESCHWOERUNG",
    "beschwörung": "BESCHWOERUNG",
    "flaeche": "FLAECHE",
    "flaechenschaden": "FLAECHE",
    "debuff": "DEBUFF",
    "heimlich": "HEIMLICH",
}
STRATEGY_OVERRIDE_MAP = {
    "brute": "brute",
    "skirmisher": "skirmisher",
    "controller": "controller",
    "artillery": "artillery",
    "assassin": "assassin",
    "summoner": "summoner",
    "defender": "defender",
    "boss": "boss",
}


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower()


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def load_scan_results() -> dict[str, Any]:
    return json.loads(SCAN_FILE.read_text(encoding="utf-8"))


def load_source_text(source_path: str) -> str:
    path = REPO_ROOT / source_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def contains_any(text: str, patterns: tuple[str, ...] | list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def unique_in_order(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def ordered_tags(tags: list[str]) -> list[str]:
    tag_set = set(tags)
    return [tag for tag in TAG_ORDER if tag in tag_set]


def normalize_tag_override(tag: str) -> str | None:
    return TAG_OVERRIDE_MAP.get(normalize_text(tag).strip())


def normalize_strategy_override(strategy: str) -> str | None:
    return STRATEGY_OVERRIDE_MAP.get(normalize_text(strategy).strip())


def infer_flags(signals: dict[str, Any], normalized_source: str) -> dict[str, bool]:
    return {
        "legendary_actions": bool(signals.get("has_legend_actions_section"))
        or "legendenaktion" in normalized_source,
        "legendary_resistances": bool(signals.get("has_legendary_resistances_text"))
        or "legendare resistenz" in normalized_source
        or "legendare resistenzen" in normalized_source,
        "phase_change": bool(signals.get("has_phase_markers"))
        or contains_any(
            normalized_source,
            ["## phase 2", "## phase 3", "phasenwechsel", "wahre gestalt", "bei 0 hp"],
        ),
        "summons": bool(signals.get("has_summon_markers"))
        or contains_any(
            normalized_source,
            ["beschwort", "beschwoert", "ruft", "adds", "diener", "erschafft"],
        ),
    }


def infer_tags(entry: dict[str, Any], normalized_source: str) -> list[str]:
    signals = entry["signals"]
    name_text = normalize_text(entry["name"])
    matched_keywords = {
        normalize_text(keyword) for keyword in signals.get("matched_keywords", [])
    }
    tags: list[str] = []

    if signals.get("has_control_effects") or matched_keywords & {
        "furcht",
        "betaubung",
        "verlangsamung",
        "blind",
    }:
        tags.append("CONTROL")

    if matched_keywords & {
        "furcht",
        "betaubung",
        "verlangsamung",
        "blind",
    } or contains_any(
        normalized_source,
        ["nachteil", "verstumm", "blind", "furcht", "verlangsam", "paralys"],
    ):
        tags.append("DEBUFF")

    if (
        signals.get("has_teleport")
        or signals.get("has_flight")
        or signals.get("has_bonus_action")
        or contains_any(
            normalized_source,
            [
                "ruckzug",
                "zuruckzieh",
                "verstecken als bonusaktion",
                "fliegend",
                "teleport",
            ],
        )
    ):
        tags.append("MOBIL")

    if (
        signals.get("has_invisibility")
        or contains_any(
            normalized_source,
            [
                "heimlichkeit",
                "versteck",
                "unsichtbarkeit",
                "assassine",
                "spion",
                "schurke",
            ],
        )
        or contains_any(name_text, ["viper", "assass", "spion"])
    ):
        tags.append("HEIMLICH")

    if signals.get("has_summon_markers") or contains_any(
        normalized_source,
        ["beschwor", "beschwoer", "ruft", "herbeiruf", "adds", "diener"],
    ):
        tags.append("BESCHWOERUNG")

    if signals.get("has_aoe") or contains_any(
        normalized_source,
        [
            "umkreis",
            "radius",
            "kegel",
            "linie",
            "wolke",
            "alle kreaturen",
            "feuerball",
            "meteorschwarm",
        ],
    ):
        tags.append("FLAECHE")

    if contains_any(
        normalized_source,
        [
            "fernkampf",
            "langbogen",
            "handarmbrust",
            "wurf",
            "strahl",
            "reichweite",
            "feuerball",
        ],
    ):
        tags.append("FERNKAMPF")

    multiattack_count = int(signals.get("multiattack_count_estimate") or 0)
    parsed_cr = float(signals.get("parsed_cr") or 0)
    if (
        multiattack_count >= 3
        or contains_any(
            normalized_source,
            [
                "kritisch",
                "kritischen",
                "hinterhaltiger angriff",
                "bonus schaden",
                "verdoppelt",
                "machtwort",
            ],
        )
        or (multiattack_count >= 2 and parsed_cr >= 10)
    ):
        tags.append("BURST")

    if (
        signals.get("has_resistances") or signals.get("has_immunities")
    ) and parsed_cr >= 5:
        tags.append("TANK")
    elif contains_any(
        normalized_source,
        [
            "halber schaden",
            "resistent",
            "vorteil auf rettungswurfe",
            "wiederherstellen",
            "negieren",
        ],
    ):
        tags.append("TANK")

    if not tags and signals.get("has_spells"):
        tags.append("CONTROL")

    return ordered_tags(unique_in_order(tags))


def infer_strategy(
    tags: list[str],
    flags: dict[str, bool],
    signals: dict[str, Any],
    normalized_source: str,
) -> str:
    scores = {strategy: 0.0 for strategy in STRATEGY_ORDER}

    if (
        flags["legendary_actions"]
        or flags["legendary_resistances"]
        or flags["phase_change"]
    ):
        scores["boss"] += 4.0

    if "CONTROL" in tags:
        scores["controller"] += 3.0
    if "DEBUFF" in tags:
        scores["controller"] += 1.0
    if "MOBIL" in tags:
        scores["skirmisher"] += 2.0
    if "HEIMLICH" in tags:
        scores["assassin"] += 2.0
        scores["skirmisher"] += 1.0
    if "FERNKAMPF" in tags:
        scores["artillery"] += 2.0
    if "FLAECHE" in tags:
        scores["artillery"] += 2.0
    if "BESCHWOERUNG" in tags:
        scores["summoner"] += 3.0
    if "TANK" in tags:
        scores["defender"] += 2.0
        scores["brute"] += 1.0
    if "BURST" in tags:
        scores["assassin"] += 2.0
        scores["brute"] += 2.0

    if signals.get("has_spells") and "FLAECHE" in tags:
        scores["artillery"] += 1.0
    if signals.get("has_spells") and "CONTROL" in tags:
        scores["controller"] += 1.0
    if (
        signals.get("multiattack_count_estimate") or 0
    ) >= 2 and "FERNKAMPF" not in tags:
        scores["brute"] += 1.0
    if "MOBIL" in tags and "HEIMLICH" in tags:
        scores["assassin"] += 1.0
    if "TANK" in tags and "CONTROL" in tags:
        scores["defender"] += 1.0
    if contains_any(normalized_source, ["hinterhalt", "backline", "assassin"]):
        scores["assassin"] += 1.0

    best_score = max(scores.values())
    for strategy in STRATEGY_ORDER:
        if scores[strategy] == best_score:
            return strategy
    return "brute"


def calculate_action_weight_bonus(
    signals: dict[str, Any],
    flags: dict[str, bool],
    tags: list[str],
    normalized_source: str,
) -> float:
    bonus = 0.0
    multiattack_count = int(signals.get("multiattack_count_estimate") or 0)
    if multiattack_count >= 2:
        bonus += 0.04
    if multiattack_count >= 3:
        bonus += 0.04
    if signals.get("has_bonus_action"):
        bonus += 0.04
    if signals.get("has_reaction"):
        bonus += 0.04
    if flags["legendary_actions"]:
        bonus += 0.12
    if "FLAECHE" in tags:
        bonus += 0.06
    if flags["summons"]:
        bonus += 0.08
    if "CONTROL" in tags:
        bonus += 0.05
    if "MOBIL" in tags and contains_any(
        normalized_source, ["bonusaktion", "teleport", "schritt"]
    ):
        bonus += 0.03
    return round(clamp(bonus, 0.0, 0.35), 2)


def calculate_threat_modifier_bonus(
    signals: dict[str, Any],
    flags: dict[str, bool],
    tags: list[str],
    strategy: str,
    normalized_source: str,
) -> float:
    bonus = 0.0
    if "CONTROL" in tags:
        bonus += 0.08
    if "DEBUFF" in tags:
        bonus += 0.04
    if "BURST" in tags:
        bonus += 0.06
    if "MOBIL" in tags and ("HEIMLICH" in tags or signals.get("has_teleport")):
        bonus += 0.06
    if signals.get("has_resistances"):
        bonus += 0.04
    if signals.get("has_immunities"):
        bonus += 0.03
    if flags["legendary_resistances"]:
        bonus += 0.08
    if flags["legendary_actions"]:
        bonus += 0.06
    if flags["summons"]:
        bonus += 0.06
    if "FLAECHE" in tags:
        bonus += 0.05
    if strategy == "boss":
        bonus += 0.04
    if contains_any(
        normalized_source, ["gegenzauber", "aktion verlieren", "zeitstop", "labyrinth"]
    ):
        bonus += 0.04
    return round(clamp(bonus, 0.0, 0.35), 2)


def calculate_volatility_bonus(
    signals: dict[str, Any],
    flags: dict[str, bool],
    tags: list[str],
    normalized_source: str,
) -> float:
    bonus = 0.0
    if signals.get("has_invisibility") or "HEIMLICH" in tags:
        bonus += 0.06
    if signals.get("has_teleport") or signals.get("has_flight"):
        bonus += 0.05
    if contains_any(
        normalized_source, ["recharge", "reload", "1/tag", "kritischen", "verdoppelt"]
    ):
        bonus += 0.05
    if "CONTROL" in tags:
        bonus += 0.05
    if flags["phase_change"]:
        bonus += 0.08
    if flags["summons"]:
        bonus += 0.05
    if "FLAECHE" in tags:
        bonus += 0.05
    if "BURST" in tags:
        bonus += 0.04
    if flags["legendary_actions"]:
        bonus += 0.04
    return round(clamp(bonus, 0.0, 0.30), 2)


def calculate_confidence(
    entry: dict[str, Any],
    tags: list[str],
    strategy: str,
    override_conflict: bool,
    normalized_source: str,
) -> float:
    signals = entry["signals"]
    sections = entry["sections"]
    confidence = 0.0

    if isinstance(signals.get("parsed_cr"), (int, float)):
        confidence += 0.20
    if entry.get("name") and entry.get("key"):
        confidence += 0.10
    if sections.get("has_actions_section"):
        confidence += 0.10
    if "## taktik" in normalized_source:
        confidence += 0.05

    keyword_count = len(signals.get("matched_keywords", []))
    if keyword_count >= 3:
        confidence += 0.10
    elif keyword_count >= 1:
        confidence += 0.05

    if len(tags) >= 2:
        confidence += 0.10
    elif tags:
        confidence += 0.05

    if strategy:
        confidence += 0.10

    if signals.get("has_spells") == (signals.get("spell_count", 0) > 0):
        confidence += 0.05

    if entry.get("parse_status") == "ok":
        confidence += 0.05
    elif entry.get("parse_status") == "warning":
        confidence -= 0.10

    if "noch nicht ausgearbeitet" in normalized_source:
        confidence -= 0.20
    if override_conflict:
        confidence -= 0.10

    return round(clamp(confidence, 0.0, 1.0), 2)


def strategy_label(strategy: str) -> str:
    return {
        "brute": "Direkter Frontkaempfer",
        "skirmisher": "Mobiler Stoerer",
        "controller": "Kontrollkaempfer",
        "artillery": "Fernkampf- oder Flaechenkaempfer",
        "assassin": "Assassinenprofil",
        "summoner": "Beschwoererprofil",
        "defender": "Zaeher Linienhalter",
        "boss": "Bossprofil",
    }[strategy]


def generate_hint(strategy: str, tags: list[str], flags: dict[str, bool]) -> str:
    feature_parts: list[str] = []
    if flags["legendary_actions"]:
        feature_parts.append("legendaeren Aktionen")
    if flags["legendary_resistances"]:
        feature_parts.append("legendaeren Resistenzen")
    if flags["phase_change"]:
        feature_parts.append("Phasenwechsel")
    if flags["summons"]:
        feature_parts.append("Beschwoerung")
    if "CONTROL" in tags:
        feature_parts.append("Kontrolleffekten")
    if "HEIMLICH" in tags:
        feature_parts.append("Heimlichkeit")
    if "MOBIL" in tags:
        feature_parts.append("Mobilitaet")
    if "FLAECHE" in tags:
        feature_parts.append("Flaechendruck")
    if "BURST" in tags:
        feature_parts.append("Burst-Schaden")
    if "TANK" in tags:
        feature_parts.append("hoher Haltbarkeit")

    descriptor = strategy_label(strategy)
    if not feature_parts:
        return f"{descriptor} mit aus Kampfsignalen abgeleitetem Profil."
    if len(feature_parts) == 1:
        return f"{descriptor} mit {feature_parts[0]}."
    return f"{descriptor} mit {', '.join(feature_parts[:-1])} und {feature_parts[-1]}."


def apply_overrides(
    profile: dict[str, Any],
    metadata: dict[str, Any],
) -> tuple[dict[str, Any], list[str], bool]:
    overrides_applied: list[str] = []
    override_conflict = False

    strategy_override = metadata.get("strategy_override")
    normalized_strategy = (
        normalize_strategy_override(strategy_override) if strategy_override else None
    )
    if normalized_strategy:
        if normalized_strategy != profile["strategy"]:
            override_conflict = True
        profile["strategy"] = normalized_strategy
        overrides_applied.append("strategy_override")

    tags_override = metadata.get("tags_override")
    if isinstance(tags_override, list) and tags_override:
        normalized_tags = [normalize_tag_override(tag) for tag in tags_override]
        cleaned_tags = ordered_tags([tag for tag in normalized_tags if tag])
        if cleaned_tags:
            if cleaned_tags != profile["tags"]:
                override_conflict = True
            profile["tags"] = cleaned_tags
            overrides_applied.append("tags_override")

    for field_name, profile_key in (
        ("threat_override", "threat_modifier_bonus"),
        ("action_override", "action_weight_bonus"),
        ("volatility_override", "volatility_bonus"),
    ):
        value = metadata.get(field_name)
        if isinstance(value, (int, float)):
            if float(value) != profile[profile_key]:
                override_conflict = True
            maximum = 0.35 if profile_key != "volatility_bonus" else 0.30
            profile[profile_key] = round(clamp(float(value), 0.0, maximum), 2)
            overrides_applied.append(field_name)

    for field_name, profile_key in (
        ("legendary_actions_override", "legendary_actions"),
        ("legendary_resistances_override", "legendary_resistances"),
        ("phase_change_override", "phase_change"),
        ("summons_override", "summons"),
    ):
        value = metadata.get(field_name)
        if isinstance(value, bool):
            if value != profile[profile_key]:
                override_conflict = True
            profile[profile_key] = value
            overrides_applied.append(field_name)

    hint = metadata.get("hint")
    if isinstance(hint, str) and hint.strip():
        profile["hint"] = hint.strip()
        overrides_applied.append("hint")

    return profile, overrides_applied, override_conflict


def build_profile(entry: dict[str, Any]) -> dict[str, Any] | None:
    if entry.get("parse_status") == "error":
        return None

    normalized_source = normalize_text(load_source_text(entry["source_path"]))
    signals = dict(entry["signals"])
    metadata = entry["raw_fields"]["catalog_metadata"]
    flags = infer_flags(signals, normalized_source)
    inferred_tags = infer_tags(entry, normalized_source)
    inferred_strategy = infer_strategy(inferred_tags, flags, signals, normalized_source)

    profile = {
        "key": entry["key"],
        "name": entry["name"],
        "source_path": entry["source_path"],
        "cr": signals["parsed_cr"],
        "strategy": inferred_strategy,
        "tags": inferred_tags,
        "threat_modifier_bonus": calculate_threat_modifier_bonus(
            signals, flags, inferred_tags, inferred_strategy, normalized_source
        ),
        "action_weight_bonus": calculate_action_weight_bonus(
            signals, flags, inferred_tags, normalized_source
        ),
        "volatility_bonus": calculate_volatility_bonus(
            signals, flags, inferred_tags, normalized_source
        ),
        "legendary_actions": flags["legendary_actions"],
        "legendary_resistances": flags["legendary_resistances"],
        "phase_change": flags["phase_change"],
        "summons": flags["summons"],
        "confidence": 0.0,
        "hint": generate_hint(inferred_strategy, inferred_tags, flags),
        "notes": [],
        "overrides_applied": [],
    }

    profile, overrides_applied, override_conflict = apply_overrides(profile, metadata)
    profile["overrides_applied"] = overrides_applied
    profile["confidence"] = calculate_confidence(
        entry,
        profile["tags"],
        profile["strategy"],
        override_conflict,
        normalized_source,
    )

    notes = []
    if entry.get("parse_status") == "warning":
        notes.extend(
            f"Scan warning: {warning}" for warning in entry.get("warnings", [])
        )
    if override_conflict:
        notes.append("Overrides weichen von der automatischen Herleitung ab.")
    if not profile["tags"]:
        notes.append("Kaum extrahierbare Kampfsignale vorhanden.")
    profile["notes"] = notes

    profile["derived_from"] = {
        "challenge_rating_raw": entry["raw_fields"].get("challenge_rating_raw"),
        "challenge_rating_parsed": signals.get("parsed_cr"),
        "has_spells": signals.get("has_spells"),
        "spell_count": signals.get("spell_count"),
        "has_multiattack": signals.get("has_multiattack"),
        "multiattack_count_estimate": signals.get("multiattack_count_estimate"),
        "has_bonus_action": signals.get("has_bonus_action"),
        "has_reaction": signals.get("has_reaction"),
        "has_legend_actions_section": signals.get("has_legend_actions_section"),
        "has_legendary_resistances_text": signals.get("has_legendary_resistances_text"),
        "has_teleport": signals.get("has_teleport"),
        "has_invisibility": signals.get("has_invisibility"),
        "has_flight": signals.get("has_flight"),
        "has_aoe": signals.get("has_aoe"),
        "has_control_effects": signals.get("has_control_effects"),
        "has_summon_markers": signals.get("has_summon_markers"),
        "has_phase_markers": signals.get("has_phase_markers"),
        "has_resistances": signals.get("has_resistances"),
        "has_immunities": signals.get("has_immunities"),
        "matched_keywords": signals.get("matched_keywords", []),
        "inferred_tags": inferred_tags,
        "inferred_strategy": inferred_strategy,
    }
    return profile


def build_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    profiles: list[dict[str, Any]] = []
    for entry in payload.get("entries", []):
        if not isinstance(entry, dict):
            continue
        profile = build_profile(entry)
        if profile is not None:
            profiles.append(profile)

    profiles.sort(key=lambda item: str(item["name"]))
    return {
        "version": 1,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source_root": payload.get("source_root", "World/Bestiarium"),
        "builder": {
            "name": "build_monster_catalog.py",
            "rules_version": RULES_VERSION,
        },
        "profiles": profiles,
    }


def write_catalog(payload: dict[str, Any]) -> None:
    OUTPUT_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    if not SCAN_FILE.exists():
        raise SystemExit(
            "extracted_monsters.json fehlt. Bitte zuerst scan_bestiary.py ausfuehren."
        )

    scan_payload = load_scan_results()
    catalog_payload = build_catalog(scan_payload)
    write_catalog(catalog_payload)

    print(f"Built {len(catalog_payload['profiles'])} monster profiles.")
    print(f"Wrote {OUTPUT_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
