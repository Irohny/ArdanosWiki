from pathlib import Path
import re
import unicodedata

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "World" / "Spielleiter" / "OneShots"
TEMPLATE_ROOT = REPO_ROOT / "World" / "templates"
BESTIARY_ROOT = REPO_ROOT / "World" / "Bestiarium"
RECORD_DIR_NAMES = {
    "scene": ("scenes", "Scenes"),
    "npc": ("NPCs", "npcs"),
    "monster": ("monsters", "Monsters"),
}


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or "eintrag"


def _split_frontmatter(content: str) -> tuple[dict, str]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, content

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            frontmatter_text = "\n".join(lines[1:index])
            body = "\n".join(lines[index + 1 :]).lstrip("\n")
            return (yaml.safe_load(frontmatter_text) or {}, body)

    return {}, content


def _with_frontmatter(frontmatter: dict, body: str = "") -> str:
    dumped = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    if body:
        return f"---\n{dumped}\n---\n\n{body.strip()}\n"
    return f"---\n{dumped}\n---\n"


def _resolve_dir(base_dir: Path, *names: str) -> Path:
    for name in names:
        candidate = base_dir / name
        if candidate.exists() and candidate.is_dir():
            return candidate
    return base_dir / names[0]


def _load_template(name: str) -> str:
    return (TEMPLATE_ROOT / name).read_text(encoding="utf-8")


def _replace_line(content: str, label: str, value: str) -> str:
    pattern = re.compile(rf"^(\s*-\s+\*\*{re.escape(label)}:\*\*).*?$", re.MULTILINE)
    replacement = rf"\1 {value}" if value else r"\1"
    return pattern.sub(replacement, content, count=1)


def _set_first_heading(content: str, title: str) -> str:
    return re.sub(r"^#\s+.+$", f"# {title}", content, count=1, flags=re.MULTILINE)


def _replace_section_text(content: str, heading: str, replacement_text: str) -> str:
    pattern = re.compile(
        rf"(^##\s+{re.escape(heading)}\s*$)(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )

    def replace(match):
        return f"{match.group(1)}\n\n{replacement_text.strip()}\n\n"

    return pattern.sub(replace, content, count=1)


def _ensure_unique_file(file_path: Path) -> None:
    if file_path.exists():
        raise FileExistsError(f"Datei existiert bereits: {file_path.name}")


def _update_session_scene_ids(session_file: Path, scene_id: str) -> None:
    content = session_file.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(content)
    scene_ids = list(frontmatter.get("scene_ids") or [])
    if scene_id not in scene_ids:
        scene_ids.append(scene_id)
    frontmatter["scene_ids"] = scene_ids
    if not frontmatter.get("current_scene"):
        frontmatter["current_scene"] = scene_id
    session_file.write_text(_with_frontmatter(frontmatter, body), encoding="utf-8")


def _session_file(session_dir: Path) -> Path:
    return session_dir / "session.md"


def read_session_content(session_dir: Path) -> str:
    return _session_file(session_dir).read_text(encoding="utf-8")


def update_session_content(session_dir: Path, content: str) -> Path:
    file_path = _session_file(session_dir)
    file_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return file_path


def list_bestiary_monsters() -> tuple[str, ...]:
    if not BESTIARY_ROOT.exists():
        return ()
    return tuple(sorted(path.stem for path in BESTIARY_ROOT.glob("*.md")))


def get_bestiary_monster_file(monster_name: str) -> Path:
    exact_match = BESTIARY_ROOT / f"{monster_name}.md"
    if exact_match.exists():
        return exact_match

    normalized_name = monster_name.casefold()
    for path in BESTIARY_ROOT.glob("*.md"):
        if path.stem.casefold() == normalized_name:
            return path

    raise FileNotFoundError(f"Bestiarium-Monster nicht gefunden: {monster_name}")


def read_bestiary_monster_content(monster_name: str) -> str:
    return get_bestiary_monster_file(monster_name).read_text(encoding="utf-8")


def update_bestiary_monster_content(monster_name: str, content: str) -> Path:
    file_path = get_bestiary_monster_file(monster_name)
    file_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return file_path


def link_bestiary_monster_to_scene(
    session_dir: Path,
    scene_name: str,
    monster_name: str,
    *,
    section_heading: str = "## Was auf dem Spiel steht",
) -> Path:
    get_bestiary_monster_file(monster_name)
    scene_file = get_record_file(session_dir, "scene", scene_name)
    content = scene_file.read_text(encoding="utf-8")
    monster_link = f"[[{monster_name}]]"
    if monster_link in content:
        raise ValueError(
            f"Monster {monster_name} ist in {scene_name} bereits verlinkt."
        )

    lines = content.splitlines()
    insert_index: int | None = None
    start_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == section_heading:
            start_index = index
            insert_index = index + 1
            break

    if start_index is None:
        raise ValueError(
            f"Abschnitt {section_heading} wurde in {scene_name} nicht gefunden."
        )

    for index in range(start_index + 1, len(lines)):
        if lines[index].startswith("## "):
            insert_index = index
            break
        insert_index = index + 1

    lines.insert(insert_index, f"- {monster_link}")
    scene_file.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return scene_file


def create_session(
    *,
    title: str,
    in_game_date: str,
    region: str,
    pacing: str,
    first_scene_title: str,
    first_scene_location: str,
    source_story: str = "",
) -> Path:
    session_dir = DATA_ROOT / title.strip()
    if session_dir.exists():
        raise FileExistsError(f"Session existiert bereits: {title}")

    (session_dir / "scenes").mkdir(parents=True, exist_ok=False)
    (session_dir / "NPCs").mkdir(parents=True, exist_ok=False)
    (session_dir / "monsters").mkdir(parents=True, exist_ok=False)

    first_scene_id = _slugify(first_scene_title)
    session_frontmatter = {
        "id": f"{_slugify(title)}-001",
        "session_title": title.strip(),
        "in_game_date": in_game_date.strip(),
        "region": region.strip(),
        "current_scene": first_scene_id,
        "pacing": pacing.strip(),
        "source_story": source_story.strip(),
        "scene_ids": [first_scene_id],
    }
    _session_file(session_dir).write_text(
        _with_frontmatter(session_frontmatter), encoding="utf-8"
    )

    create_scene(
        session_dir=session_dir,
        title=first_scene_title,
        location=first_scene_location,
        status="aktiv",
        update_session=False,
    )
    return session_dir


def create_scene(
    *,
    session_dir: Path,
    title: str,
    location: str,
    status: str,
    summary: str = "",
    atmosphere: str = "",
    pressure: str = "",
    update_session: bool = True,
) -> Path:
    scenes_dir = _resolve_dir(session_dir, "scenes", "Scenes")
    scenes_dir.mkdir(parents=True, exist_ok=True)
    scene_id = _slugify(title)
    file_path = scenes_dir / f"{scene_id}.md"
    _ensure_unique_file(file_path)

    frontmatter = {
        "id": scene_id,
        "title": title.strip(),
        "status": status.strip().lower(),
        "location": location.strip(),
    }
    body = "\n\n".join(
        section
        for section in (
            f"# {title.strip()}",
            f"## Atmosphäre\n{atmosphere.strip() or 'Stimmung und erste Eindruecke ergaenzen.'}",
            f"## Szenenbild\n{summary.strip() or 'Kurze Beschreibung der Szene.'}",
            f"## Druck\n{pressure.strip() or 'Welche Entwicklung droht, wenn die Gruppe zoegert?'}",
            "## Was auf dem Spiel steht\n- ",
            "## Was es zu entdecken gibt\n- ",
        )
    )
    file_path.write_text(_with_frontmatter(frontmatter, body), encoding="utf-8")

    if update_session:
        _update_session_scene_ids(_session_file(session_dir), scene_id)
    return file_path


def create_npc(
    *,
    session_dir: Path,
    name: str,
    title: str,
    species: str,
    origin: str,
    description: str,
) -> Path:
    npcs_dir = _resolve_dir(session_dir, "NPCs", "npcs")
    npcs_dir.mkdir(parents=True, exist_ok=True)
    file_path = npcs_dir / f"{name.strip()}.md"
    _ensure_unique_file(file_path)

    template = _load_template("nsc_template.md")
    content = f"# {name.strip()}\n\n{template.lstrip()}"
    content = _replace_line(content, "Rufname / Beiname", name.strip().split()[0])
    content = _replace_line(content, "Titel / Amt", title.strip())
    content = _replace_line(content, "Spezies / Volk", species.strip() or "Mensch")
    content = _replace_line(content, "Herkunft", origin.strip())
    content = _replace_section_text(
        content,
        "Beschreibung und Auftreten",
        description.strip()
        or "Kurze Einordnung, Auftreten und oeffentlich erkennbare Eigenheiten.",
    )
    file_path.write_text(content.strip() + "\n", encoding="utf-8")
    return file_path


def create_monster(
    *,
    session_dir: Path,
    name: str,
    challenge: str,
    species: str,
    origin: str,
    traits: str,
) -> Path:
    monsters_dir = _resolve_dir(session_dir, "monsters", "Monsters")
    monsters_dir.mkdir(parents=True, exist_ok=True)
    file_path = monsters_dir / f"{name.strip()}.md"
    _ensure_unique_file(file_path)

    content = _load_template("monster.md")
    content = _set_first_heading(content, name.strip())
    content = _replace_line(content, "Stufe/Herausfordungsgrad", challenge.strip())
    content = _replace_line(content, "Volk", species.strip())
    content = _replace_line(content, "Herkunft", origin.strip())
    content = _replace_line(content, "Merkmale", traits.strip())
    file_path.write_text(content.strip() + "\n", encoding="utf-8")
    return file_path


def list_session_records(session_dir: Path) -> dict[str, tuple[str, ...]]:
    record_dirs = {
        "Szenen": _resolve_dir(session_dir, *RECORD_DIR_NAMES["scene"]),
        "NSCs": _resolve_dir(session_dir, *RECORD_DIR_NAMES["npc"]),
        "Monster": _resolve_dir(session_dir, *RECORD_DIR_NAMES["monster"]),
    }
    records: dict[str, tuple[str, ...]] = {}
    for label, directory in record_dirs.items():
        if not directory.exists():
            records[label] = ()
            continue
        records[label] = tuple(sorted(path.stem for path in directory.glob("*.md")))
    return records


def get_record_file(session_dir: Path, record_type: str, record_name: str) -> Path:
    if record_type not in RECORD_DIR_NAMES:
        raise ValueError(f"Unbekannter Record-Typ: {record_type}")

    directory = _resolve_dir(session_dir, *RECORD_DIR_NAMES[record_type])
    if not directory.exists():
        raise FileNotFoundError(f"Kein Ordner fuer {record_type} gefunden.")

    exact_match = directory / f"{record_name}.md"
    if exact_match.exists():
        return exact_match

    normalized_name = record_name.casefold()
    for path in directory.glob("*.md"):
        if path.stem.casefold() == normalized_name:
            return path

    raise FileNotFoundError(f"Eintrag nicht gefunden: {record_name}")


def read_record_content(session_dir: Path, record_type: str, record_name: str) -> str:
    return get_record_file(session_dir, record_type, record_name).read_text(
        encoding="utf-8"
    )


def update_record_content(
    session_dir: Path,
    record_type: str,
    record_name: str,
    content: str,
) -> Path:
    file_path = get_record_file(session_dir, record_type, record_name)
    file_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return file_path
