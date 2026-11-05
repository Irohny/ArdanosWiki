from __future__ import annotations

from pathlib import Path
from typing import Any

from scan_lore import (
    CATEGORY_SET,
    OUTPUT_FILE,
    load_scan_results,
    scan_lore,
    write_scan_results,
)

SCRIPT_ROOT = Path(__file__).resolve().parent
REPORT_FILE = SCRIPT_ROOT / "validation_report.md"


def validate_item(item: dict[str, Any]) -> list[str]:
    if not item["is_relevant"]:
        return []

    errors: list[str] = []
    primary_types = item["primary_types"]
    declared_categories = item["declared_categories"]
    categories = item["categories"]
    parsed_timespan = item["parsed_timespan"]

    if len(primary_types) != 1:
        errors.append("Genau ein Primaertyp-Tag erforderlich.")

    if item["timespan_line_count"] < 1:
        errors.append("Mindestens eine gueltige Zeitspanne-Quelle ist erforderlich.")
    elif parsed_timespan is None:
        errors.append("Zeitspanne hat kein gueltiges Standardformat.")

    if not categories:
        errors.append(
            "Mindestens eine gueltige Kategorie oder ein erkennbarer Pfad-Fallback ist erforderlich."
        )

    if any(category not in CATEGORY_SET for category in categories):
        errors.append("Unbekannte Kategorie gefunden.")

    if "Weltgeschichte" in declared_categories and len(declared_categories) > 1:
        errors.append(
            "#Weltgeschichte darf nicht mit lokalen Kategorien kombiniert werden."
        )

    if "Kaiserreich" in declared_categories and any(
        category in declared_categories
        for category in {"Elmrath", "Drakmora", "Mariven", "Schwarzklamm", "Vaylen"}
    ):
        errors.append(
            "#Kaiserreich darf nicht mit lokalen Kategorien kombiniert werden."
        )

    if len(set(primary_types)) != len(primary_types):
        errors.append("Primaertypen duerfen nicht doppelt vorkommen.")

    if len(set(declared_categories)) != len(declared_categories):
        errors.append("Kategorien duerfen nicht doppelt vorkommen.")

    if (
        primary_types
        and primary_types[0] == "Herrscher"
        and parsed_timespan
        and parsed_timespan["kind"] != "range"
    ):
        errors.append("Herrscher brauchen eine Zeitspanne und kein Punkt-Ereignis.")

    return errors


def validate_payload(
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    relevant_items: list[dict[str, Any]] = []
    items_with_errors: list[dict[str, Any]] = []

    for item in payload["items"]:
        item["validation_errors"] = validate_item(item)
        if item["is_relevant"]:
            relevant_items.append(item)
        if item["validation_errors"]:
            items_with_errors.append(item)

    return relevant_items, items_with_errors


def build_report(
    payload: dict[str, Any],
    relevant_items: list[dict[str, Any]],
    items_with_errors: list[dict[str, Any]],
) -> str:
    lines = [
        "# Validation Report",
        "",
        f"- Scanned files: {len(payload['items'])}",
        f"- Relevant files: {len(relevant_items)}",
        f"- Files with errors: {len(items_with_errors)}",
        "",
    ]

    if not items_with_errors:
        lines.append("Keine Validierungsfehler gefunden.")
        lines.append("")
        return "\n".join(lines)

    lines.extend(["## Fehler", ""])
    for item in items_with_errors:
        lines.append(f"### {item['path']}")
        lines.append("")
        for error in item["validation_errors"]:
            lines.append(f"- {error}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    if OUTPUT_FILE.exists():
        payload = load_scan_results()
    else:
        payload = scan_lore()
        write_scan_results(payload)

    relevant_items, items_with_errors = validate_payload(payload)
    REPORT_FILE.write_text(
        build_report(payload, relevant_items, items_with_errors), encoding="utf-8"
    )

    print(f"Validated {len(relevant_items)} relevant files.")
    print(f"Found {len(items_with_errors)} files with validation errors.")
    print(f"Wrote {REPORT_FILE.relative_to(SCRIPT_ROOT.parent.parent)}")

    if items_with_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
