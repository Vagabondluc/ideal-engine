#!/usr/bin/env bash
# Interactive script to prepare a local branch and open a PR using GitHub CLI (optional)
set -e

echo "This script will:"
echo "  - initialize git repository if none exists"
echo "  - create branch: stitch-world-editor-ui-001"
echo "  - add and commit candidate files"
echo "  - optionally push and open a PR via 'gh' CLI"

read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted by user."
  exit 1
fi

if [ ! -d .git ]; then
  git init
  echo "Initialized empty git repository."
else
  echo "Git repository already exists."
fi

BRANCH=stitch-world-editor-ui-001

# Create branch
git checkout -b $BRANCH || git checkout $BRANCH

# Stage files
git add src/ui.py scripts/world_builder.py openspec/ tests/ e2e/playwright/ scripts/start_test_app.py .github/workflows/e2e-playwright.yml pr_draft/ || true

# Commit
git commit -m "feat: restore world builder UI, add toasts, gutter, versioning, tests, and Playwright E2E scaffold" || echo "No changes to commit."

read -p "Push branch to remote 'origin' and open PR using 'gh'? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  git remote -v | grep origin || (read -p "Provide remote URL (e.g., git@github.com:org/repo.git): " remote && git remote add origin "$remote")
  git push -u origin $BRANCH
  if command -v gh >/dev/null 2>&1; then
    gh pr create --title "Restore & Enhance World Builder UI" --body-file pr_draft/PR_BODY.md --base main --head $BRANCH
  else
    echo "gh CLI not found. Please create a PR using the GitHub web UI or install 'gh' and re-run this script."
  fi
else
  echo "Skipping push/PR creation. Branch created locally: $BRANCH"
fi

echo "Done."