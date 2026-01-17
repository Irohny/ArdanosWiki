import re
from pathlib import Path
import pandas as pd

BESTIARIUM_PATTERNS = {
    "Stufe": r"\*\*Stufe/Herausfordungsgrad:\*\*\s*(.+)",
    "Volk": r"\*\*Volk:\*\*\s*(.+)",
    "Gesinnung": r"\*\*Gesinnung:\*\*\s*(.+)",
    "Rüstungsklasse": r"\*\*Rüstungsklasse.*?:\*\*\s*(\d+)",
    "Grundlage": r"\*\*Grundlage:\*\*\s*(.+)",
}

ZAUBER_PATTERNS = {
    "Grad": r"\*\*Grad:\*\*\s*(.+)",
    "Schule": r"\*\*Schule:\*\*\s*(.+)",
    "Konzentration": r"\*\*Konzentration:\*\*\s*(.+)",
    "Komponenten": r"\*\*Komponenten:\*\*\s*(.+)",
    "Materialien": r"\*\*Materialien:\*\*\s*(.+)",
}

TRANK_PATTERNS = {
    "Tags": r"-\s*Tag:\s*(.+)",
    "Wert": r"\*\*Wert:\*\*\s*(.+)",
    "Komponenten": r"\*\*Komponenten:\*\*\s*(.+)",
    "Seltenheit": r"\*\*Seltenheit:\*\*\s*(.+)",
}

ZUTATEN_PATTERNS = {
    "Seltenheit": r"\*\*Seltenheit:\*\*\s*(.+)",
    "Wert": r"\*\*Wert:\*\*\s*(.+)",
    "Fundort": r"\*\*Fundort:\*\*\s*(.+)",
}


def get_dict(root: str, name: str, path: str) -> list[dict, dict]:
    data, pattern = {}, {}
    if "Bestiarium" in root:
        data = {
            "Name": name,
            "Pfad": path,
            "Stufe": None,
            "Volk": None,
            "Gesinnung": None,
            "Rüstungsklasse": None,
            "Grundlage": None,
        }
        pattern = BESTIARIUM_PATTERNS
    elif "Zauberarchiv" in root:
        pattern = ZAUBER_PATTERNS
        data = {
            "Name": name,
            "Pfad": path,
            "Grad": None,
            "Schule": None,
            "Komponenten": None,
            "Konzentration": None,
        }
    elif "Trank" in root:
        data = {
            "Name": name,
            "Pfad": path,
            "Tags": None,
            "Wert": None,
            "Seltenheit": None,
        }
        pattern = TRANK_PATTERNS
    elif "Zutaten" in root:
        data = {
            "Name": name,
            "Pfad": path,
            "Wert": None,
            "Seltenheit": None,
            "Fundort": None,
        }
        pattern = ZUTATEN_PATTERNS
    return data, pattern


def parse_markdown_file(path: Path, root: str) -> dict:
    """
    Parsed eine einzelne Markdown-Datei und extrahiert relevante Felder.
    """
    text = path.read_text(encoding="utf-8", errors="ignore")

    data, field_pattern = get_dict(root, path.stem, str(path.resolve()))

    for field, pattern in field_pattern.items():
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            if field == "Rüstungsklasse":
                data[field] = int(value)
            else:
                data[field] = value

    return data


def build_markdown_database(root_path: str) -> pd.DataFrame:
    """
    Durchsucht rekursiv root_path nach Markdown-Dateien
    und erstellt einen DataFrame mit den extrahierten Daten.
    """
    root = Path(root_path)
    records = []

    for md_file in root.rglob("*.md"):
        try:
            record = parse_markdown_file(md_file, root_path)
            records.append(record)
        except Exception as e:
            print(f"⚠️ Fehler beim Parsen von {md_file}: {e}")

    return pd.DataFrame(records)
