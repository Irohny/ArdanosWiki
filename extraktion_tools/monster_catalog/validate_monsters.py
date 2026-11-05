from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCRIPT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_ROOT.parent.parent
SCAN_FILE = SCRIPT_ROOT / "extracted_monsters.json"
REPORT_FILE = SCRIPT_ROOT / "validation_report.md"

ALLOWED_PARSE_STATUS = {"ok", "warning", "error"}
ALLOWED_TAGS = {
    "BURST",
    "CONTROL",
    "TANK",
    "MOBIL",
    "FERNKAMPF",
    "BESCHWOERUNG",
    "FLAECHE",
    "DEBUFF",
    "HEIMLICH",
}
ALLOWED_STRATEGIES = {
    "brute",
    "skirmisher",
    "controller",
    "artillery",
    "assassin",
    "summoner",
    "defender",
    "boss",
}


def load_scan_results() -> dict[str, Any]:
    return json.loads(SCAN_FILE.read_text(encoding="utf-8"))


def has_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_top_level(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("version") != 1:
        errors.append("Top-Level version muss 1 sein.")
    if not has_non_empty_string(payload.get("generated_at")):
        errors.append("Top-Level generated_at fehlt.")
    if payload.get("source_root") != "World/Bestiarium":
        errors.append("Top-Level source_root muss World/Bestiarium sein.")

    scanner = payload.get("scanner")
    if not isinstance(scanner, dict):
        errors.append("Top-Level scanner fehlt oder ist kein Objekt.")
    else:
        if scanner.get("name") != "scan_bestiary.py":
            errors.append("scanner.name muss scan_bestiary.py sein.")
        if not isinstance(scanner.get("rules_version"), int):
            errors.append("scanner.rules_version muss eine Ganzzahl sein.")

    if not isinstance(payload.get("entries"), list):
        errors.append("Top-Level entries fehlt oder ist keine Liste.")

    return errors


def validate_catalog_metadata(metadata: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    key_override = metadata.get("key_override")
    strategy_override = metadata.get("strategy_override")
    tags_override = metadata.get("tags_override")

    if key_override is not None and not has_non_empty_string(key_override):
        errors.append("catalog_metadata.key_override ist leer.")

    if strategy_override is not None:
        if not has_non_empty_string(strategy_override):
            errors.append("catalog_metadata.strategy_override ist leer.")
        elif str(strategy_override).strip().lower() not in ALLOWED_STRATEGIES:
            errors.append("catalog_metadata.strategy_override ist ungueltig.")

    if tags_override is not None:
        if not isinstance(tags_override, list) or not tags_override:
            errors.append(
                "catalog_metadata.tags_override muss eine nicht-leere Liste sein."
            )
        else:
            invalid_tags = [
                tag
                for tag in tags_override
                if str(tag).strip().upper() not in ALLOWED_TAGS
            ]
            if invalid_tags:
                errors.append(
                    "catalog_metadata.tags_override enthaelt ungueltige Tags: "
                    + ", ".join(str(tag) for tag in invalid_tags)
                )

    for field in ("threat_override", "action_override", "volatility_override"):
        value = metadata.get(field)
        if value is not None and not isinstance(value, (int, float)):
            errors.append(f"catalog_metadata.{field} muss numerisch sein.")

    for field in (
        "legendary_actions_override",
        "legendary_resistances_override",
        "phase_change_override",
        "summons_override",
    ):
        value = metadata.get(field)
        if value is not None and not isinstance(value, bool):
            errors.append(f"catalog_metadata.{field} muss boolesch sein.")

    hint = metadata.get("hint")
    if hint is not None and not has_non_empty_string(hint):
        errors.append("catalog_metadata.hint ist leer.")

    return errors


def validate_signals(signals: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    warnings: list[str] = []

    parsed_cr = signals.get("parsed_cr")
    if not isinstance(parsed_cr, (int, float)):
        errors.append("signals.parsed_cr fehlt oder ist nicht numerisch.")
    elif parsed_cr < 0:
        errors.append("signals.parsed_cr darf nicht negativ sein.")

    spell_count = signals.get("spell_count")
    if not isinstance(spell_count, int) or spell_count < 0:
        errors.append("signals.spell_count muss eine nicht-negative Ganzzahl sein.")

    multiattack_count = signals.get("multiattack_count_estimate")
    if not isinstance(multiattack_count, int) or multiattack_count < 0:
        errors.append(
            "signals.multiattack_count_estimate muss eine nicht-negative Ganzzahl sein."
        )

    for field in (
        "has_spells",
        "has_multiattack",
        "has_bonus_action",
        "has_reaction",
        "has_legend_actions_section",
        "has_legendary_resistances_text",
        "has_teleport",
        "has_invisibility",
        "has_flight",
        "has_aoe",
        "has_control_effects",
        "has_summon_markers",
        "has_phase_markers",
        "has_resistances",
        "has_immunities",
    ):
        if not isinstance(signals.get(field), bool):
            errors.append(f"signals.{field} muss boolesch sein.")

    matched_keywords = signals.get("matched_keywords")
    if not isinstance(matched_keywords, list):
        errors.append("signals.matched_keywords muss eine Liste sein.")
    elif any(not has_non_empty_string(value) for value in matched_keywords):
        errors.append("signals.matched_keywords darf keine leeren Eintraege enthalten.")
    elif not matched_keywords:
        warnings.append("Keine relevanten Kampfschluesselwoerter erkannt.")

    if signals.get("has_spells") and spell_count == 0:
        warnings.append("Zauber-Sektion erkannt, aber spell_count ist 0.")

    if signals.get("has_multiattack") and multiattack_count == 0:
        warnings.append(
            "Mehrfachangriff erkannt, aber multiattack_count_estimate ist 0."
        )

    if signals.get("has_legend_actions_section") and not matched_keywords:
        warnings.append(
            "Legendenaktionen-Sektion erkannt, aber keine Kampfkeywords gematcht."
        )

    return errors + warnings


def validate_sections(sections: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "has_actions_section",
        "has_spellcasting_section",
        "has_legendary_actions_section",
        "has_reactions_section",
        "has_bonus_actions_section",
    ):
        if not isinstance(sections.get(field), bool):
            errors.append(f"sections.{field} muss boolesch sein.")
    return errors


def validate_source_excerpt(source_excerpt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    cr_line = source_excerpt.get("cr_line")
    if cr_line is not None and not has_non_empty_string(cr_line):
        errors.append("source_excerpt.cr_line darf nicht leer sein.")
    matched_lines = source_excerpt.get("matched_lines")
    if not isinstance(matched_lines, list):
        errors.append("source_excerpt.matched_lines muss eine Liste sein.")
    elif any(not has_non_empty_string(value) for value in matched_lines):
        errors.append(
            "source_excerpt.matched_lines darf keine leeren Eintraege enthalten."
        )
    return errors


def validate_entry(
    entry: dict[str, Any], seen_keys: set[str]
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    source_path = entry.get("source_path")
    key = entry.get("key")
    parse_status = entry.get("parse_status")

    if not has_non_empty_string(source_path):
        errors.append("source_path fehlt.")
    elif not str(source_path).startswith("World/Bestiarium/"):
        errors.append("source_path muss unter World/Bestiarium liegen.")

    if not has_non_empty_string(entry.get("file_name")):
        errors.append("file_name fehlt.")

    if not has_non_empty_string(entry.get("name")):
        errors.append("name fehlt.")

    if not has_non_empty_string(key):
        errors.append("key fehlt.")
    else:
        key_text = str(key)
        if key_text in seen_keys:
            errors.append("key ist nicht eindeutig.")
        seen_keys.add(key_text)

    if parse_status not in ALLOWED_PARSE_STATUS:
        errors.append("parse_status ist ungueltig.")

    entry_warnings = entry.get("warnings")
    if not isinstance(entry_warnings, list):
        errors.append("warnings muss eine Liste sein.")
    elif any(not has_non_empty_string(value) for value in entry_warnings):
        errors.append("warnings darf keine leeren Eintraege enthalten.")

    entry_errors = entry.get("errors")
    if not isinstance(entry_errors, list):
        errors.append("errors muss eine Liste sein.")
    elif any(not has_non_empty_string(value) for value in entry_errors):
        errors.append("errors darf keine leeren Eintraege enthalten.")

    raw_fields = entry.get("raw_fields")
    if not isinstance(raw_fields, dict):
        errors.append("raw_fields fehlt oder ist kein Objekt.")
    else:
        metadata = raw_fields.get("catalog_metadata")
        if not isinstance(metadata, dict):
            errors.append("raw_fields.catalog_metadata fehlt oder ist kein Objekt.")
        else:
            errors.extend(validate_catalog_metadata(metadata))

    signals = entry.get("signals")
    if not isinstance(signals, dict):
        errors.append("signals fehlt oder ist kein Objekt.")
    else:
        signal_messages = validate_signals(signals)
        for message in signal_messages:
            if message.startswith("signals."):
                errors.append(message)
            elif message.startswith("Keine ") or " ist 0." in message:
                warnings.append(message)
            else:
                warnings.append(message)

    sections = entry.get("sections")
    if not isinstance(sections, dict):
        errors.append("sections fehlt oder ist kein Objekt.")
    else:
        errors.extend(validate_sections(sections))

    source_excerpt = entry.get("source_excerpt")
    if not isinstance(source_excerpt, dict):
        errors.append("source_excerpt fehlt oder ist kein Objekt.")
    else:
        errors.extend(validate_source_excerpt(source_excerpt))

    if parse_status == "error" and not entry_errors:
        errors.append("parse_status error ohne errors-Eintrag.")
    if parse_status == "warning" and not entry_warnings and not warnings:
        warnings.append("parse_status warning ohne dokumentierte Warnung.")

    return errors, warnings


def build_report(
    payload: dict[str, Any],
    top_level_errors: list[str],
    validation_results: list[dict[str, Any]],
) -> str:
    total_entries = (
        len(payload.get("entries", []))
        if isinstance(payload.get("entries"), list)
        else 0
    )
    entries_with_errors = [
        result for result in validation_results if result["validation_errors"]
    ]
    entries_with_warnings = [
        result for result in validation_results if result["validation_warnings"]
    ]

    lines = [
        "# Validation Report",
        "",
        f"- Scanned files: {total_entries}",
        f"- Top-level errors: {len(top_level_errors)}",
        f"- Files with validation errors: {len(entries_with_errors)}",
        f"- Files with validation warnings: {len(entries_with_warnings)}",
        "",
    ]

    if top_level_errors:
        lines.extend(["## Top-Level Fehler", ""])
        for error in top_level_errors:
            lines.append(f"- {error}")
        lines.append("")

    if entries_with_errors:
        lines.extend(["## Fehler", ""])
        for result in entries_with_errors:
            lines.append(f"### {result['source_path']}")
            lines.append("")
            for error in result["validation_errors"]:
                lines.append(f"- {error}")
            lines.append("")
    else:
        lines.extend(["## Fehler", "", "Keine Validierungsfehler gefunden.", ""])

    if entries_with_warnings:
        lines.extend(["## Warnungen", ""])
        for result in entries_with_warnings:
            lines.append(f"### {result['source_path']}")
            lines.append("")
            for warning in result["validation_warnings"]:
                lines.append(f"- {warning}")
            lines.append("")

    return "\n".join(lines)


def main() -> None:
    if not SCAN_FILE.exists():
        raise SystemExit(
            "extracted_monsters.json fehlt. Bitte zuerst scan_bestiary.py ausfuehren."
        )

    payload = load_scan_results()
    top_level_errors = validate_top_level(payload)
    validation_results: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    entries = payload.get("entries", [])
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                validation_results.append(
                    {
                        "source_path": "<invalid-entry>",
                        "validation_errors": ["Entry ist kein Objekt."],
                        "validation_warnings": [],
                    }
                )
                continue
            errors, warnings = validate_entry(entry, seen_keys)
            validation_results.append(
                {
                    "source_path": entry.get("source_path", "<unknown>"),
                    "validation_errors": errors,
                    "validation_warnings": warnings,
                }
            )

    REPORT_FILE.write_text(
        build_report(payload, top_level_errors, validation_results),
        encoding="utf-8",
    )

    error_count = len(top_level_errors) + sum(
        1 for result in validation_results if result["validation_errors"]
    )
    warning_count = sum(
        1 for result in validation_results if result["validation_warnings"]
    )

    print(f"Validated {len(validation_results)} monster entries.")
    print(f"Files with validation warnings: {warning_count}")
    print(f"Files with validation errors: {error_count}")
    print(f"Wrote {REPORT_FILE.relative_to(REPO_ROOT)}")

    if error_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
