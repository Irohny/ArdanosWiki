#!/usr/bin/env bash
set -euo pipefail

TYPES=("feat" "fix" "chore")

# -----------------------------
# Latest tag & base version
# -----------------------------

latest_tag=$(git tag --sort=-v:refname | sed -n '1p')
RANGE="HEAD"

if [[ -z "$latest_tag" ]]; then
  BASE_MAJOR=0
  BASE_MINOR=0
  BASE_PATCH=0
else
  version=${latest_tag#v}
  if [[ ! "$version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    echo "Unsupported version tag: $latest_tag" >&2
    exit 1
  fi
  BASE_MAJOR=${BASH_REMATCH[1]}
  BASE_MINOR=${BASH_REMATCH[2]}
  BASE_PATCH=${BASH_REMATCH[3]}
  RANGE="$latest_tag..HEAD"
fi

# -----------------------------
# Collect conventional commits
# -----------------------------

commit_lines=()
while IFS= read -r commit; do
  commit_lines+=("$commit")
done < <(
  git log "$RANGE" --no-merges --date=short --format='%s%x09%ad'
)

commit_pattern='^(feat|fix|chore)(\([^)]*\))?(!)?:[[:space:]](.+)$'
feat_count=0
fix_count=0
major_bump=false
for commit in "${commit_lines[@]}"; do
  IFS=$'\t' read -r subject _ <<< "$commit"
  if [[ "$subject" =~ $commit_pattern ]]; then
    commit_type=${BASH_REMATCH[1]}
    breaking_marker=${BASH_REMATCH[3]}
    if [[ "$breaking_marker" == "!" ]]; then
      major_bump=true
    fi
    case "$commit_type" in
      feat) ((feat_count += 1)) ;;
      fix) ((fix_count += 1)) ;;
    esac
  fi
done

# -----------------------------
# Calculate version
# -----------------------------

if [[ "$major_bump" == true ]]; then
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
# Write changelog to stdout
# -----------------------------

{
  printf '%s\n' \
    '---' \
    'typ:' \
    'status:' \
    'kampagne:' \
    'region:' \
    'tags: []' \
    'zeit_text:' \
    'zeit_von_jahr:' \
    'zeit_bis_jahr:' \
    'erstellt:' \
    '---'
  printf '\n'
  printf '# Changelog %s\n\n' "$VERSION"

  for type in "${TYPES[@]}"; do
    entries=()
    for commit in "${commit_lines[@]}"; do
      IFS=$'\t' read -r subject date <<< "$commit"
      if [[ "$subject" =~ $commit_pattern ]]; then
        commit_type=${BASH_REMATCH[1]}
        scope=${BASH_REMATCH[2]}
        breaking_marker=${BASH_REMATCH[3]}
        message=${BASH_REMATCH[4]}
        if [[ "$commit_type" == "$type" ]]; then
          entries+=("* ${commit_type}${scope}${breaking_marker} ($date): $message")
        fi
      fi
    done

    if (( ${#entries[@]} > 0 )); then
      case "$type" in
        feat) section_title="Feat" ;;
        fix) section_title="Fix" ;;
        chore) section_title="Chore" ;;
      esac
      printf '### %s\n' "$section_title"
      printf '%s\n' "${entries[@]}"
      printf '\n'
    fi
  done
}
