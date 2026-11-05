#!/usr/bin/env python3
"""
Ergänzt in allen Markdown-Dateien eines Obsidian-Vaults einen leeren
Metadaten-Block (YAML-Frontmatter), sofern die Datei noch keinen hat.

- Der Dateiinhalt wird nicht verändert, der Block wird nur vorangestellt.
- Dateien mit vorhandenem Frontmatter werden übersprungen (mehrfach ausführbar).
- Standardmäßig ist es ein Trockenlauf: es wird nur aufgelistet, was passieren würde.

Aufruf:
    python add_frontmatter.py "C:/Pfad/zum/Vault"            # Trockenlauf
    python add_frontmatter.py "C:/Pfad/zum/Vault" --apply    # wirklich schreiben
"""

import argparse
import re
import sys
from pathlib import Path

# Felder und Reihenfolge wie in templates/nsc_template.md
FIELDS = [
    "typ:",
    "status:",
    "kampagne:",
    "geschichten:",
    "region:",
    "tags: []",
    "zeit_text:",
    "zeit_von_jahr:",
    "zeit_bis_jahr:",
    "erstellt:",
    "geaendert:",
]

# Ordner, die nie angefasst werden (Templates bleiben, wie sie sind)
SKIP_DIRS = {".obsidian", ".git", ".trash", "templates"}

BOM = "\ufeff"

# Erste Zeile im Block sieht nach YAML aus ("schluessel: ...")
# (Zeilen mit # am Anfang zählen bewusst nicht: das sind Markdown-Überschriften)
YAML_LINE = re.compile(r"^[^\s:#\-][^:]*:.*$")


def has_frontmatter(text: str) -> bool:
    """True, wenn die Datei mit einem echten YAML-Frontmatter beginnt."""
    if text.startswith(BOM):
        text = text[1:]
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            inner = [ln for ln in lines[1:i] if ln.strip()]
            # leerer Block (---/---) oder erste Zeile wie "schluessel: ..." -> echtes Frontmatter
            return not inner or bool(YAML_LINE.match(inner[0]))
    return False  # kein schließendes --- gefunden: war nur eine Trennlinie


def build_block(newline: str) -> str:
    return newline.join(["---", *FIELDS, "---"]) + newline


def process(path: Path, apply: bool) -> str:
    # newline="" erhält vorhandene Zeilenenden (LF oder CRLF) unverändert
    with open(path, "r", encoding="utf-8", newline="") as f:
        text = f.read()

    if has_frontmatter(text):
        return "skip"

    newline = "\r\n" if "\r\n" in text else "\n"
    block = build_block(newline)

    if text.startswith(BOM):
        new_text = BOM + block + text[1:]
    else:
        new_text = block + text

    if apply:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new_text)
    return "add"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("vault", help="Pfad zum Obsidian-Vault")
    parser.add_argument("--apply", action="store_true", help="Änderungen wirklich schreiben (ohne: Trockenlauf)")
    args = parser.parse_args()

    root = Path(args.vault).expanduser().resolve()
    if not root.is_dir():
        print(f"Ordner nicht gefunden: {root}", file=sys.stderr)
        return 1

    added, skipped, errors = [], 0, []

    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        try:
            result = process(path, args.apply)
        except (UnicodeDecodeError, OSError) as e:
            errors.append((rel, e))
            continue
        if result == "add":
            added.append(rel)
        else:
            skipped += 1

    mode = "ERGÄNZT" if args.apply else "WÜRDE ERGÄNZEN (Trockenlauf)"
    for rel in added:
        print(f"{mode}: {rel}")
    for rel, e in errors:
        print(f"FEHLER:  {rel} ({e})", file=sys.stderr)

    print()
    print(f"{'Ergänzt' if args.apply else 'Zu ergänzen'}: {len(added)}")
    print(f"Übersprungen (hatten schon Frontmatter): {skipped}")
    print(f"Fehler: {len(errors)}")
    if not args.apply and added:
        print("Zum Schreiben erneut mit --apply starten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())