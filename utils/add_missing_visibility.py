from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from typing import Any

import yaml

from wiki_dasboard.config import cfg


FRONTMATTER_PATTERN = re.compile(
    r"\A(?P<opening>---[ \t]*(?P<eol>\r?\n))"
    r"(?P<metadata>.*?)(?P<closing>\r?\n---[ \t]*(?:\r?\n|\Z))",
    re.DOTALL,
)


class FrontmatterError(ValueError):
    pass


def add_visibility_if_missing(content: str) -> tuple[str, str]:
    match = FRONTMATTER_PATTERN.match(content)
    if match is None:
        return content, "no-frontmatter"

    try:
        metadata: Any = yaml.safe_load(match.group("metadata"))
    except yaml.YAMLError as error:
        raise FrontmatterError(f"invalid YAML frontmatter: {error}") from error

    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise FrontmatterError("frontmatter must be a mapping")
    if "sichtbarkeit" in metadata:
        return content, "already-present"

    raw_metadata = match.group("metadata")
    separator = "" if not raw_metadata or raw_metadata.endswith(("\n", "\r")) else match.group("eol")
    updated = (
        content[: match.start("metadata")]
        + raw_metadata
        + separator
        + "sichtbarkeit: []"
        + content[match.end("metadata") :]
    )
    return updated, "added"


def add_missing_visibility(world_root: Path, *, apply: bool) -> dict[str, int]:
    plans: list[tuple[Path, str]] = []
    errors: list[str] = []
    summary = {"added": 0, "already-present": 0, "no-frontmatter": 0}

    for path in sorted(world_root.rglob("*.md")):
        try:
            with path.open("r", encoding="utf-8", newline="") as source:
                original = source.read()
            updated, result = add_visibility_if_missing(original)
        except (OSError, UnicodeError, FrontmatterError) as error:
            errors.append(f"{path.relative_to(world_root)}: {error}")
            continue

        summary[result] += 1
        if result == "added":
            plans.append((path, updated))

    if errors:
        raise FrontmatterError("\n".join(errors))

    if apply:
        for path, updated in plans:
            with path.open("w", encoding="utf-8", newline="") as destination:
                destination.write(updated)

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add an explicit empty visibility list to Markdown frontmatter"
    )
    parser.add_argument("--world-root", type=Path, default=cfg.paths.world_dir)
    parser.add_argument("--apply", action="store_true", help="write the updates")
    args = parser.parse_args()

    try:
        summary = add_missing_visibility(args.world_root, apply=args.apply)
    except FrontmatterError as error:
        print(error, file=sys.stderr)
        return 1

    mode = "Applied" if args.apply else "Dry run"
    print(
        f"{mode}: {summary['added']} files to update, "
        f"{summary['already-present']} already have sichtbarkeit, "
        f"{summary['no-frontmatter']} have no frontmatter"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())