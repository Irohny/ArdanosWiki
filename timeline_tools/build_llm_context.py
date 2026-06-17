from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from timeline_tools.metadata_extractor.scan_lore import (  # noqa: E402
    CATEGORY_ORDER,
    CURRENT_YEAR,
    leading_metadata_lines,
    scan_lore,
)


OUTPUT_DIR = REPO_ROOT / "context"
OUTPUT_FILE = OUTPUT_DIR / "llm_gm_context.md"
MONSTER_CATALOG_FILE = (
    REPO_ROOT / "timeline_tools" / "monster_catalog" / "monster_catalog.json"
)
REGION_OVERVIEW_FILES = {
    "Kaiserreich": "World/Kaiserreich/Ardanos.md",
    "Elmrath": "World/Kaiserreich/Elmrath/Elmrath.md",
    "Drakmora": "World/Kaiserreich/Drakmora/Drakmora.md",
    "Mariven": "World/Kaiserreich/Mariven/Mariven.md",
    "Schwarzklamm": "World/Kaiserreich/Schwarzklamm/Schwarzklamm.md",
    "Vaylen": "World/Kaiserreich/Vaylen/Vaylen.md",
}
PRIMARY_TYPE_ORDER = ("Herrscher", "Gruendung", "Krieg", "Konflikt", "Ereignis")
SECTION_ORDER = (
    ("Herrscher und Machttraeger", {"Herrscher"}),
    ("Gruendungen und Machtwechsel", {"Gruendung"}),
    ("Kriege und Konflikte", {"Krieg", "Konflikt"}),
    ("Schluesselereignisse", {"Ereignis"}),
)
MAX_SUMMARY_LENGTH = 240
MAX_MONSTER_ENTRIES = 8
MARKDOWN_PROPERTY_RE = re.compile(r"^\s*[-*]\s+\*\*.+?:\*\*\s*.*$")
WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass(frozen=True)
class ContextEntry:
    title: str
    primary_type: str
    categories: tuple[str, ...]
    timespan: str
    summary: str
    source_path: str
    sort_year: int
    is_current: bool


def compact_text(value: str, max_length: int = MAX_SUMMARY_LENGTH) -> str:
    normalized = re.sub(r"\s+", " ", value).strip(" -")
    if len(normalized) <= max_length:
        return normalized
    truncated = normalized[: max_length - 3].rsplit(" ", 1)[0].strip()
    if not truncated:
        truncated = normalized[: max_length - 3].strip()
    return f"{truncated}..."


def clean_markdown_inline(value: str) -> str:
    cleaned = HTML_COMMENT_RE.sub("", value)
    cleaned = WIKI_LINK_RE.sub(lambda match: match.group(2) or match.group(1), cleaned)
    cleaned = re.sub(r"!\[\[[^\]]+\]\]", "", cleaned)
    cleaned = re.sub(r"[*_`>#]", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip(" -")


def strip_frontmatter(content: str) -> str:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return content

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[index + 1 :])
    return content


def load_source_summary(source_path: str) -> str:
    file_path = REPO_ROOT / source_path
    if not file_path.exists():
        return ""

    content = strip_frontmatter(file_path.read_text(encoding="utf-8"))
    content = HTML_COMMENT_RE.sub("", content)

    metadata_lines = leading_metadata_lines(content)
    if metadata_lines:
        content_lines = content.splitlines()[len(metadata_lines) :]
        content = "\n".join(content_lines)

    for block in re.split(r"\n\s*\n", content):
        raw_lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not raw_lines:
            continue
        if all(line.startswith(("#", "![[")) for line in raw_lines):
            continue
        if all(MARKDOWN_PROPERTY_RE.match(line) for line in raw_lines):
            continue

        cleaned_lines: list[str] = []
        for line in raw_lines:
            if line.startswith(("#", "![[", "<!")):
                continue
            if MARKDOWN_PROPERTY_RE.match(line):
                continue
            cleaned = clean_markdown_inline(line)
            if cleaned:
                cleaned_lines.append(cleaned)

        if cleaned_lines:
            return compact_text(" ".join(cleaned_lines))

    return ""


def determine_primary_type(item: dict[str, Any]) -> str:
    types = item.get("primary_types") or []
    for primary_type in PRIMARY_TYPE_ORDER:
        if primary_type in types:
            return primary_type
    return "Lore"


def format_timespan(item: dict[str, Any]) -> str:
    parsed = item.get("parsed_timespan")
    if not parsed:
        raw = item.get("timespan_raw")
        return compact_text(raw, max_length=64) if raw else "unbekannt"

    start = parsed["start"]
    end = parsed["end"]
    if parsed["kind"] == "point":
        return f"{start} n.d.D."
    if parsed.get("is_open"):
        return f"{start}-heute n.d.D."
    return f"{start}-{end} n.d.D."


def timespan_sort_year(item: dict[str, Any]) -> int:
    parsed = item.get("parsed_timespan")
    if parsed:
        return int(parsed["start"])
    return CURRENT_YEAR + 1


def is_current_entry(item: dict[str, Any]) -> bool:
    parsed = item.get("parsed_timespan")
    if not parsed:
        return False
    return parsed["start"] <= CURRENT_YEAR <= parsed["end"]


def build_summary(item: dict[str, Any]) -> str:
    source_path = item["path"]
    parts: list[str] = []

    fields = item.get("structured_fields") or {}
    for key in ("Titel / Amt", "Bekannt fuer", "Status", "Herkunft"):
        value = compact_text(clean_markdown_inline(fields.get(key, "")), max_length=96)
        if value and value not in parts:
            parts.append(value)

    source_summary = load_source_summary(source_path)
    if source_summary and source_summary not in parts:
        parts.append(source_summary)

    if not parts:
        return "Keine kompakte Inhaltszusammenfassung verfuegbar."
    return " ".join(parts[:3])


def build_context_entries(payload: dict[str, Any]) -> list[ContextEntry]:
    entries: list[ContextEntry] = []
    for item in payload["items"]:
        if not item.get("is_relevant"):
            continue

        categories = tuple(item.get("categories") or item.get("fallback_categories") or ())
        entries.append(
            ContextEntry(
                title=item.get("title") or Path(item["path"]).stem,
                primary_type=determine_primary_type(item),
                categories=categories,
                timespan=format_timespan(item),
                summary=build_summary(item),
                source_path=item["path"],
                sort_year=timespan_sort_year(item),
                is_current=is_current_entry(item),
            )
        )
    return entries


def build_overview_lines(entries: list[ContextEntry]) -> list[str]:
    lines = [
        f"- Stand: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"- Aktuelles Jahr: {CURRENT_YEAR} n.d.D.",
        f"- Metadatengetaggte Lore-Eintraege: {len(entries)}",
    ]

    ardanos_summary = load_source_summary(REGION_OVERVIEW_FILES["Kaiserreich"])
    if ardanos_summary:
        lines.append(f"- Ardanos: {compact_text(ardanos_summary, max_length=320)}")

    return lines


def build_region_lines() -> list[str]:
    lines: list[str] = []
    for category in CATEGORY_ORDER:
        source_path = REGION_OVERVIEW_FILES.get(category)
        if not source_path:
            continue
        summary = load_source_summary(source_path)
        if not summary:
            continue
        lines.append(
            f"- {category}: {compact_text(summary, max_length=220)} "
            f"(Quelle: {source_path})"
        )
    return lines


def format_entry(entry: ContextEntry) -> str:
    category_label = ", ".join(entry.categories) if entry.categories else "ohne Kategorie"
    current_flag = " | aktuell" if entry.is_current else ""
    return (
        f"- {entry.title} | {entry.primary_type} | {category_label} | {entry.timespan}{current_flag} "
        f"| {entry.summary} | Quelle: {entry.source_path}"
    )


def build_section_lines(entries: list[ContextEntry], types: set[str]) -> list[str]:
    section_entries = [entry for entry in entries if entry.primary_type in types]
    if not section_entries:
        return ["- Keine Eintraege gefunden."]

    section_entries.sort(
        key=lambda entry: (
            0 if entry.is_current else 1,
            -entry.sort_year if entry.primary_type == "Herrscher" else entry.sort_year,
            entry.title.casefold(),
        )
    )
    return [format_entry(entry) for entry in section_entries]


def load_monster_lines() -> list[str]:
    if not MONSTER_CATALOG_FILE.exists():
        return ["- Monster-Katalog nicht gefunden."]

    payload = json.loads(MONSTER_CATALOG_FILE.read_text(encoding="utf-8"))
    profiles = payload.get("profiles") or []
    profiles.sort(key=lambda profile: (profile.get("cr") or 0, profile.get("name", "")), reverse=True)
    selected_profiles = profiles[:MAX_MONSTER_ENTRIES]
    if not selected_profiles:
        return ["- Keine Monsterprofile gefunden."]

    lines = []
    for profile in selected_profiles:
        tags = ", ".join(profile.get("tags") or []) or "keine Tags"
        hint = compact_text(profile.get("hint", ""), max_length=140)
        lines.append(
            f"- {profile.get('name', 'Unbekannt')} | HG {profile.get('cr', '?')} | "
            f"{profile.get('strategy', 'unbekannt')} | {tags} | {hint} | "
            f"Quelle: {profile.get('source_path', 'unbekannt')}"
        )
    return lines


def build_markdown(entries: list[ContextEntry]) -> str:
    sections: list[str] = [
        "# Ardanos GM Kontext",
        "",
        "Kompakter Lore- und Weltkontext fuer Session- und Kampagnendesign. "
        "Die Datei ist fuer LLM-Prompts gedacht und priorisiert knappe Fakten ueber Volltext.",
        "",
        "## Ueberblick",
        *build_overview_lines(entries),
        "",
        "## Regionen",
        *build_region_lines(),
        "",
    ]

    for section_title, types in SECTION_ORDER:
        sections.extend(
            [f"## {section_title}", *build_section_lines(entries, types), ""]
        )

    sections.extend(["## Monster-Kurzreferenz", *load_monster_lines(), ""])
    return "\n".join(sections).rstrip() + "\n"


def write_context(markdown: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(markdown, encoding="utf-8")


def main() -> None:
    payload = scan_lore()
    entries = build_context_entries(payload)
    markdown = build_markdown(entries)
    write_context(markdown)
    print(f"Scanned {len(payload['items'])} markdown files.")
    print(f"Collected {len(entries)} metadata-tagged lore entries.")
    print(f"Wrote {OUTPUT_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()