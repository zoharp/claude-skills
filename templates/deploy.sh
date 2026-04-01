#!/bin/bash
cd "$(dirname "$0")"

read -p "Commit message: " MSG
if [ -z "$MSG" ]; then
  echo "No message provided, aborting."
  exit 1
fi

echo "=== Staging changes ==="
git add -A
git status --short

echo "=== Committing ==="
git commit -m "$MSG"
if [ $? -ne 0 ]; then
  echo "Commit failed."
  exit 1
fi

echo "=== Pushing to GitHub ==="
git push
if [ $? -ne 0 ]; then
  echo "Push failed."
  exit 1
fi

echo "=== Done! Deployed successfully. ==="
