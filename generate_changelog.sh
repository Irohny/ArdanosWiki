#!/usr/bin/env bash

LOG_RANGE=""

echo "# Changelog"
echo

for type in feat fix docs refactor perf chore; do
  commits=$(git log $LOG_RANGE \
    --pretty=format:"* %s (%ad)" \
    --date=short \
    --grep="^$type" \
    --no-merges)

  if [[ -n "$commits" ]]; then
    echo "### ${type^}"
    echo "$commits"
    echo
  fi
done