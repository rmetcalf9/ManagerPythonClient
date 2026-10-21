#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

uv run --with pytest pytest

uv version --bump patch
VERSION=$(uv version --short)
uv lock

sed -i "s/^__version__ = .*/__version__ = \"${VERSION}\"/" \
  src/ManagerPythonClient/__init__.py

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