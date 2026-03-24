from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCRIPT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_ROOT.parent.parent
BESTIARY_ROOT = REPO_ROOT / "World" / "Bestiarium"
OUTPUT_FILE = SCRIPT_ROOT / "extracted_monsters.json"
RULES_VERSION = 1

CR_LINE_RE = re.compile(
    r"^\s*-\s*\*\*Stufe/Herausfordungsgrad:\*\*\s*(?P<value>.+?)\s*$"
)
H1_RE = re.compile(r"^#\s+(?P<value>.+?)\s*$")
HEADING_RE = re.compile(r"^(?P<level>#{2,6})\s*(?P<title>.+?)\s*$")
LIST_FIELD_RE = re.compile(r"^\s*-\s*\*\*(?P<label>.+?):\*\*\s*(?P<value>.*?)\s*$")
NUMBER_PREFIX_RE = re.compile(r"^(?P<number>\d+)\s*/\s*(?P<denominator>\d+)$")
INTEGER_PREFIX_RE = re.compile(r"^(?P<number>\d+)")
INDENTED_BULLET_RE = re.compile(r"^\s*-\s+(?P<value>.+?)\s*$")

CATALOG_OVERRIDE_FIELDS = {
    "katalog-key": "key_override",
    "strategie-override": "strategy_override",
    "tags-override": "tags_override",
    "threat-override": "threat_override",
    "action-override": "action_override",
    "volatilitat-override": "volatility_override",
    "volatilität-override": "volatility_override",
    "legendare aktionen-override": "legendary_actions_override",
    "legendäre aktionen-override": "legendary_actions_override",
    "legendare resistenzen-override": "legendary_resistances_override",
    "legendäre resistenzen-override": "legendary_resistances_override",
    "phasenwechsel-override": "phase_change_override",
    "beschworung-override": "summons_override",
    "beschwörung-override": "summons_override",
    "katalog-hinweis": "hint",
}

SIGNAL_PATTERNS: dict[str, tuple[str, ...]] = {
    "teleport": (
        "teleport",
        "dimensionstur",
        "dimensionstür",
        "schattenschritt",
        "nebelschritt",
    ),
    "invisibility": (
        "unsichtbarkeit",
        "grossere unsichtbarkeit",
        "größere unsichtbarkeit",
        "versteck",
        "heimlich",
    ),
    "flight": ("fliegend", "flug", "schwebend", "fliegen"),
    "aoe": (
        "alle kreaturen",
        "im umkreis",
        "aura",
        "flachenschaden",
        "flächenschaden",
        "kegel",
        "radius",
        "6 m radius",
        "9 m radius",
    ),
    "control": (
        "furcht",
        "betaub",
        "betäub",
        "verlangsam",
        "nachteil",
        "verstummen",
        "lähmung",
        "paralys",
        "blind",
    ),
    "summons": (
        "beschwort",
        "beschwört",
        "beschworung",
        "beschwörung",
        "ruft",
        "herbeiruf",
        "adds",
        "diener",
        "erschafft",
    ),
    "phase": (
        "phase 2",
        "phase 3",
        "phasenwechsel",
        "verwandelt",
        "zweite form",
        "wahre gestalt",
        "unter 50",
        "bei 0 hp",
        "auf 0 hp",
    ),
    "spells": (
        "## zauber",
        "### zauber",
        "zauberplätze",
        "zaubertricks",
        "vorbereitete zauber",
        "gegenzauber",
    ),
}

KEYWORD_PATTERNS: dict[str, tuple[str, ...]] = {
    "Teleport": ("teleport", "dimensionstur", "dimensionstür", "schattenschritt"),
    "Unsichtbarkeit": (
        "unsichtbarkeit",
        "grossere unsichtbarkeit",
        "größere unsichtbarkeit",
    ),
    "Furcht": ("furcht",),
    "Betäubung": ("betäub", "betaub"),
    "Blind": ("blind",),
    "Verlangsamung": ("verlangsam",),
    "Beschwörung": (
        "beschwort",
        "beschwört",
        "beschworung",
        "beschwörung",
        "ruft",
        "adds",
    ),
    "Legendäre Resistenz": (
        "legendäre resistenz",
        "legendare resistenz",
        "legendäre resistenzen",
        "legendare resistenzen",
    ),
    "Flug": ("fliegend", "flug", "schwebend"),
    "Mehrfachangriff": ("mehrfachangriff",),
    "Gegenzauber": ("gegenzauber",),
}


@dataclass(slots=True)
class ScanEntry:
    source_path: str
    file_name: str
    name: str
    key: str
    parse_status: str
    warnings: list[str]
    errors: list[str]
    raw_fields: dict[str, Any]
    signals: dict[str, Any]
    sections: dict[str, Any]
    source_excerpt: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "file_name": self.file_name,
            "name": self.name,
            "key": self.key,
            "parse_status": self.parse_status,
            "warnings": self.warnings,
            "errors": self.errors,
            "raw_fields": self.raw_fields,
            "signals": self.signals,
            "sections": self.sections,
            "source_excerpt": self.source_excerpt,
        }


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower()


def normalize_heading_title(text: str) -> str:
    normalized = normalize_text(text)
    normalized = normalized.replace("*", " ")
    normalized = normalized.replace(":", " ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def slugify_ascii(value: str) -> str:
    normalized = normalize_text(value)
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_") or "monster"


def parse_bool(value: str) -> bool | None:
    normalized = normalize_text(value.strip())
    if normalized in {"ja", "true", "wahr", "yes"}:
        return True
    if normalized in {"nein", "false", "falsch", "no"}:
        return False
    return None


def parse_float(value: str) -> float | None:
    normalized = value.strip().replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def parse_cr(raw: str) -> float | int | None:
    value = raw.strip()
    fraction_match = NUMBER_PREFIX_RE.match(value)
    if fraction_match:
        numerator = int(fraction_match.group("number"))
        denominator = int(fraction_match.group("denominator"))
        if denominator == 0:
            return None
        return numerator / denominator
    integer_match = INTEGER_PREFIX_RE.match(value)
    if integer_match:
        return int(integer_match.group("number"))
    return None


def find_first_heading_name(lines: list[str]) -> str | None:
    for line in lines:
        match = H1_RE.match(line.strip())
        if match:
            return match.group("value").strip()
    return None


def extract_cr_line(lines: list[str]) -> tuple[str | None, str | None]:
    for line in lines:
        match = CR_LINE_RE.match(line)
        if match:
            return match.group("value").strip(), line.strip()
    return None, None


def extract_catalog_metadata(lines: list[str]) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "key_override": None,
        "strategy_override": None,
        "tags_override": None,
        "threat_override": None,
        "action_override": None,
        "volatility_override": None,
        "legendary_actions_override": None,
        "legendary_resistances_override": None,
        "phase_change_override": None,
        "summons_override": None,
        "hint": None,
    }
    in_section = False
    for line in lines:
        stripped = line.strip()
        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            title = normalize_text(heading_match.group("title"))
            if title == "katalog-metadaten":
                in_section = True
                continue
            if in_section and len(heading_match.group("level")) <= 2:
                break
        if not in_section:
            continue
        field_match = LIST_FIELD_RE.match(line)
        if not field_match:
            continue
        label = normalize_text(field_match.group("label"))
        value = field_match.group("value").strip()
        field_name = CATALOG_OVERRIDE_FIELDS.get(label)
        if not field_name:
            continue
        if field_name in {
            "legendary_actions_override",
            "legendary_resistances_override",
            "phase_change_override",
            "summons_override",
        }:
            metadata[field_name] = parse_bool(value)
        elif field_name in {
            "threat_override",
            "action_override",
            "volatility_override",
        }:
            metadata[field_name] = parse_float(value)
        elif field_name == "tags_override":
            metadata[field_name] = [
                token.strip() for token in value.split(",") if token.strip()
            ]
        else:
            metadata[field_name] = value or None
    return metadata


def extract_heading_blocks(lines: list[str]) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    current_titles: list[str] = []
    current_level = 0

    for line in lines:
        stripped = line.strip()
        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            title = normalize_heading_title(heading_match.group("title"))
            level = len(heading_match.group("level"))
            while current_titles and current_level >= level:
                current_titles.pop()
                current_level -= 1
            current_titles.append(title)
            current_level = level
            blocks.setdefault(" / ".join(current_titles), [])
            continue

        if current_titles:
            blocks.setdefault(" / ".join(current_titles), []).append(line)

    return blocks


def block_has_content(lines: list[str]) -> bool:
    for line in lines:
        stripped = line.strip()
        if stripped and stripped != "---":
            return True
    return False


def detect_sections(
    lines: list[str], heading_blocks: dict[str, list[str]]
) -> dict[str, bool]:
    def has_named_block(keyword: str) -> bool:
        return any(
            keyword in title and block_has_content(content)
            for title, content in heading_blocks.items()
        )

    return {
        "has_actions_section": has_named_block("aktionen"),
        "has_spellcasting_section": has_named_block("zauber"),
        "has_legendary_actions_section": has_named_block("legendenaktionen"),
        "has_reactions_section": has_named_block("reaktionen"),
        "has_bonus_actions_section": has_named_block("bonusaktionen"),
    }


def count_spell_lines(lines: list[str], heading_blocks: dict[str, list[str]]) -> int:
    count = 0
    in_spell_ability = False

    for title, block_lines in heading_blocks.items():
        if "zauber" not in title:
            continue
        for line in block_lines:
            stripped = line.strip()
            if stripped.startswith("- "):
                count += 1

    for line in lines:
        field_match = LIST_FIELD_RE.match(line)
        if field_match:
            label = normalize_heading_title(field_match.group("label"))
            in_spell_ability = "zauber" in label and "legendenaktionen" not in label
            continue

        if not in_spell_ability:
            continue

        if HEADING_RE.match(line.strip()):
            in_spell_ability = False
            continue

        bullet_match = INDENTED_BULLET_RE.match(line)
        if bullet_match and bullet_match.group("value").strip():
            count += 1

    return count


def estimate_multiattack_count(lines: list[str]) -> int:
    for line in lines:
        normalized = normalize_text(line)
        if "mehrfachangriff" not in normalized:
            continue
        numeric_match = re.search(r"(\d+)", normalized)
        if numeric_match:
            return int(numeric_match.group(1))
        return 2
    return 0


def gather_matched_keywords(lines: list[str]) -> tuple[list[str], list[str]]:
    normalized_lines = [normalize_text(line) for line in lines]
    matched_keywords: list[str] = []
    matched_lines: list[str] = []
    for label, patterns in KEYWORD_PATTERNS.items():
        for raw_line, normalized_line in zip(lines, normalized_lines, strict=False):
            if any(pattern in normalized_line for pattern in patterns):
                matched_keywords.append(label)
                excerpt = raw_line.strip()
                if excerpt and excerpt not in matched_lines:
                    matched_lines.append(excerpt)
                break
    return matched_keywords, matched_lines[:8]


def signal_from_patterns(lines: list[str], pattern_names: tuple[str, ...]) -> bool:
    normalized_lines = [normalize_text(line) for line in lines]
    return any(
        any(pattern in line for pattern in pattern_names) for line in normalized_lines
    )


def extract_signals(
    lines: list[str], sections: dict[str, bool], heading_blocks: dict[str, list[str]]
) -> dict[str, Any]:
    matched_keywords, matched_lines = gather_matched_keywords(lines)
    cr_raw, _ = extract_cr_line(lines)
    spell_count = count_spell_lines(lines, heading_blocks)
    multiattack_count = estimate_multiattack_count(lines)
    signals = {
        "parsed_cr": parse_cr(cr_raw) if cr_raw else None,
        "has_spells": spell_count > 0
        or signal_from_patterns(lines, SIGNAL_PATTERNS["spells"]),
        "spell_count": spell_count,
        "has_multiattack": multiattack_count > 0,
        "multiattack_count_estimate": multiattack_count,
        "has_bonus_action": any(
            "bonusaktion" in normalize_text(line) for line in lines
        ),
        "has_reaction": any("reaktion" in normalize_text(line) for line in lines),
        "has_legend_actions_section": sections["has_legendary_actions_section"],
        "has_legendary_resistances_text": signal_from_patterns(
            lines, KEYWORD_PATTERNS["Legendäre Resistenz"]
        ),
        "has_teleport": signal_from_patterns(lines, SIGNAL_PATTERNS["teleport"]),
        "has_invisibility": signal_from_patterns(
            lines, SIGNAL_PATTERNS["invisibility"]
        ),
        "has_flight": signal_from_patterns(lines, SIGNAL_PATTERNS["flight"]),
        "has_aoe": signal_from_patterns(lines, SIGNAL_PATTERNS["aoe"]),
        "has_control_effects": signal_from_patterns(lines, SIGNAL_PATTERNS["control"]),
        "has_summon_markers": signal_from_patterns(lines, SIGNAL_PATTERNS["summons"]),
        "has_phase_markers": signal_from_patterns(lines, SIGNAL_PATTERNS["phase"]),
        "has_resistances": any(
            normalize_text(line).startswith("- **resistenzen:") for line in lines
        ),
        "has_immunities": any(
            normalize_text(line).startswith("- **immunitaten:")
            or normalize_text(line).startswith("- **immunitäten:")
            for line in lines
        ),
        "matched_keywords": matched_keywords,
        "matched_lines": matched_lines,
    }
    return signals


def build_source_excerpt(
    cr_line: str | None, matched_lines: list[str]
) -> dict[str, Any]:
    return {
        "cr_line": cr_line,
        "matched_lines": matched_lines,
    }


def build_warnings(
    name: str, key: str, cr_raw: str | None, signals: dict[str, Any]
) -> list[str]:
    warnings: list[str] = []
    if not cr_raw:
        warnings.append("Keine CR-Zeile gefunden.")
    elif signals["parsed_cr"] is None:
        warnings.append(f"CR konnte nicht geparst werden: {cr_raw}")
    if not name:
        warnings.append("Kein Name ermittelt.")
    if not key:
        warnings.append("Kein Key ermittelt.")
    if not signals["matched_keywords"]:
        warnings.append("Keine relevanten Kampfschluesselwoerter erkannt.")
    return warnings


def build_errors(name: str, key: str, signals: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not name:
        errors.append("Monstername fehlt.")
    if not key:
        errors.append("Monster-Key fehlt.")
    if signals["parsed_cr"] is None:
        errors.append("CR fehlt oder ist nicht parsebar.")
    return errors


def scan_file(path: Path) -> ScanEntry:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    name = find_first_heading_name(lines) or path.stem
    key = slugify_ascii(name)
    cr_raw, cr_line = extract_cr_line(lines)
    catalog_metadata = extract_catalog_metadata(lines)
    if catalog_metadata.get("key_override"):
        key = slugify_ascii(str(catalog_metadata["key_override"]))

    heading_blocks = extract_heading_blocks(lines)
    sections = detect_sections(lines, heading_blocks)
    signals = extract_signals(lines, sections, heading_blocks)
    warnings = build_warnings(name, key, cr_raw, signals)
    errors = build_errors(name, key, signals)
    parse_status = "error" if errors else "warning" if warnings else "ok"

    raw_fields = {
        "challenge_rating_raw": cr_raw,
        "alias_raw": None,
        "catalog_metadata": catalog_metadata,
    }
    for line in lines:
        field_match = LIST_FIELD_RE.match(line)
        if not field_match:
            continue
        label = normalize_text(field_match.group("label"))
        if label == "alias":
            raw_fields["alias_raw"] = field_match.group("value").strip() or None
            break

    source_excerpt = build_source_excerpt(cr_line, signals.pop("matched_lines"))

    return ScanEntry(
        source_path=str(path.relative_to(REPO_ROOT)),
        file_name=path.name,
        name=name,
        key=key,
        parse_status=parse_status,
        warnings=warnings,
        errors=errors,
        raw_fields=raw_fields,
        signals=signals,
        sections=sections,
        source_excerpt=source_excerpt,
    )


def scan_bestiary() -> dict[str, Any]:
    entries = [scan_file(path).to_dict() for path in sorted(BESTIARY_ROOT.glob("*.md"))]
    return {
        "version": 1,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source_root": str(BESTIARY_ROOT.relative_to(REPO_ROOT)),
        "scanner": {
            "name": "scan_bestiary.py",
            "rules_version": RULES_VERSION,
        },
        "entries": entries,
    }


def write_scan_results(payload: dict[str, Any]) -> None:
    OUTPUT_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    payload = scan_bestiary()
    write_scan_results(payload)
    total = len(payload["entries"])
    warnings = sum(
        1 for entry in payload["entries"] if entry["parse_status"] == "warning"
    )
    errors = sum(1 for entry in payload["entries"] if entry["parse_status"] == "error")
    print(f"Scanned {total} monster files.")
    print(f"Warnings: {warnings}")
    print(f"Errors: {errors}")
    print(f"Wrote {OUTPUT_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
