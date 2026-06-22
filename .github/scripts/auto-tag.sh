#!/usr/bin/env bash
# Compute the next version tag and push it.
# Usage: auto-tag.sh <ref-name>
#
# Tag format: vX.Y.Z on main, derived from the previous v* tag plus the
# conventional-commit type of new commits since.
#
# Bump precedence (highest first):
#   1. Manual footer in any new commit body:
#        [release: major] [release: minor] [release: patch]
#   2. Conventional-commit auto-detection:
#        - any subject ending in `!:` or any body containing `BREAKING CHANGE:` -> major
#        - any subject matching `^feat:` or `^feat(...):` -> minor
#        - otherwise -> patch
#   3. Skip markers in any new commit body suppress tagging entirely:
#        [skip release] [skip ci]
#
# Idempotent: if the computed tag already exists on the remote, exits cleanly.

set -euo pipefail

ref_name="${1:?ref name required}"

if [ "$ref_name" != "main" ]; then
  echo "Ref ${ref_name} is not main; skipping tag."
  exit 0
fi

# Most recent ancestor tag matching v*. Falls back to 0.0.0 if no tag exists yet.
latest=$(git describe --tags --abbrev=0 --match 'v*' 2>/dev/null | sed 's/^v//' || true)
if [ -z "$latest" ]; then latest="0.0.0"; fi

# All commit subjects + bodies since the previous tag. `%b` is the body, the
# trailing `---` is a separator so we can grep across commit boundaries.
if [ "$latest" = "0.0.0" ]; then
  commits=$(git log --pretty=format:"%s%n%b---")
else
  commits=$(git log "v${latest}..HEAD" --pretty=format:"%s%n%b---")
fi

# Skip markers win outright.
if echo "$commits" | grep -qE '\[skip release\]|\[skip ci\]'; then
  echo "Skip marker found in a new commit body; not tagging."
  exit 0
fi

# Manual override footer (highest precedence for the bump type).
bump=""
if echo "$commits" | grep -qE '^\[release: major\]'; then
  bump="major"
elif echo "$commits" | grep -qE '^\[release: minor\]'; then
  bump="minor"
elif echo "$commits" | grep -qE '^\[release: patch\]'; then
  bump="patch"
fi

# Fall back to conventional-commit auto-detection.
if [ -z "$bump" ]; then
  subjects=$(echo "$commits" | grep -v '^---$' || true)
  if echo "$commits" | grep -qE '^[a-z]+(\([^)]+\))?!:|BREAKING CHANGE'; then
    bump="major"
  elif echo "$subjects" | grep -qE '^feat(\([^)]+\))?:'; then
    bump="minor"
  else
    bump="patch"
  fi
fi

# Compute the next version.
IFS='.' read -r major minor patch <<< "$latest"
case "$bump" in
  major) major=$((major + 1)); minor=0; patch=0 ;;
  minor) minor=$((minor + 1)); patch=0 ;;
  patch) patch=$((patch + 1)) ;;
esac
version="${major}.${minor}.${patch}"
tag="v${version}"

# Idempotency: skip if the tag already exists on the remote.
if git ls-remote --tags origin | grep -qF "refs/tags/${tag}"; then
  echo "Tag ${tag} already exists on remote; skipping."
  exit 0
fi

# Create the tag locally and push it. The push fires the `push: tags: v*`
# trigger on .github/workflows/release.yaml, which builds the wheel and
# attaches it to the GitHub Release. hatch-vcs reads the version from this
# tag at build time.
sha=$(git rev-parse HEAD)
git tag "${tag}" "${sha}"
git push origin "refs/tags/${tag}"

echo "Tagged: ${tag} (bump: ${bump}, base: ${latest})"
