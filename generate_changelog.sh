#!/usr/bin/env bash
set -e

TYPES=("feat" "fix" "chore")
CHANGELOG_DIR="World"
CHANGELOG_FILE="$CHANGELOG_DIR/CHANGELOG.md"

# -----------------------------
# Ensure directory exists
# -----------------------------

mkdir -p "$CHANGELOG_DIR"

# -----------------------------
# Latest tag & base version
# -----------------------------

latest_tag=$(git tag --sort=-v:refname | head -n 1)

if [[ -z "$latest_tag" ]]; then
  BASE_MAJOR=0
  BASE_MINOR=0
  BASE_PATCH=0
  RANGE=""
else
  version=${latest_tag#v}
  IFS='.' read -r BASE_MAJOR BASE_MINOR BASE_PATCH <<< "$version"
  RANGE="$latest_tag..HEAD"
fi

# -----------------------------
# Detect bumps
# -----------------------------

major_bumps=$(git log $RANGE --grep='!:' --pretty=format:%s)

feat_count=$(git log $RANGE --grep='^feat:' --pretty=format:%s | wc -l)
fix_count=$(git log $RANGE --grep='^fix:' --pretty=format:%s | wc -l)

if [[ -n "$major_bumps" ]]; then
  MAJOR=$((BASE_MAJOR + 1))
  MINOR=0
  PATCH=0
else
  MAJOR=$BASE_MAJOR
  MINOR=$((BASE_MINOR + feat_count))
  PATCH=$((BASE_PATCH + fix_count))
fi

VERSION="$MAJOR.$MINOR.$PATCH"

# -----------------------------
# Write changelog
# -----------------------------

{
  echo "# Changelog $VERSION"
  echo

  for type in "${TYPES[@]}"; do
    commits=$(git log $RANGE \
      --pretty=format:"%s|%ad" \
      --date=short \
      --grep="^$type" \
      --no-merges)

    if [[ -n "$commits" ]]; then
      echo "### ${type^}"
      while IFS='|' read -r subject date; do
        if [[ "$subject" =~ ^($type)(!?)\:\ (.*)$ ]]; then
          t="${BASH_REMATCH[1]}${BASH_REMATCH[2]}"
          msg="${BASH_REMATCH[3]}"
          echo "* $t ($date): $msg"
        fi
      done <<< "$commits"
      echo
    fi
  done
} > "$CHANGELOG_FILE"

echo "✅ Changelog geschrieben nach: $CHANGELOG_FILE"
