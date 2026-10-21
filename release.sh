#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

GITHUB_USER=$(gh api user --jq .login 2>/dev/null || true)
if [[ "$GITHUB_USER" != "rmetcalf9" ]]; then
echo "ERROR: GitHub CLI must be logged in as rmetcalf9."
echo "Currently logged in as: ${GITHUB_USER:-unknown}"
echo "Switch accounts with: gh auth switch --hostname github.com --user rmetcalf9"
exit 1
fi

uv run --with pytest pytest

uv version --bump patch
VERSION=$(uv version --short)
uv lock

sed -i "s/^__version__ = .*/__version__ = \"${VERSION}\"/" \
  src/MangerPythonClient/__init__.py

uv build

git add .
git commit -m "release: v${VERSION}"
git push origin main

git tag -a v${VERSION} -m "Release v${VERSION}"
git push origin v${VERSION}

gh release create v${VERSION} \
--title "v${VERSION}" \
--notes "New Release" \
--verify-tag

exit 0