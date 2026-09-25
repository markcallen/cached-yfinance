#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <original-commit>" >&2
  exit 2
fi

original_commit="$1"
matching_tags=()

while IFS= read -r tag; do
  tag_commit="$(git rev-list -n 1 "$tag")"
  tag_parent="$(git rev-parse "${tag_commit}^" 2>/dev/null || true)"
  if [ "$tag_parent" = "$original_commit" ]; then
    matching_tags+=("$tag")
  fi
done < <(git tag --list 'v*')

case "${#matching_tags[@]}" in
  0)
    ;;
  1)
    echo "${matching_tags[0]}"
    ;;
  *)
    echo "Multiple release tags were created from ${original_commit}: ${matching_tags[*]}" >&2
    exit 1
    ;;
esac
