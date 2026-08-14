#!/bin/bash
# EvolvixOS — Push to GitHub
# Run this script to push EvolvixOS to github.com/Protremix/EvolvixOS
#
# Usage:
#   ./push_to_github.sh
#
# It will ask for your GitHub Personal Access Token once,
# then push everything. After that, use normal git commands.

set -e

REPO_URL="https://github.com/Protremix/EvolvixOS.git"

echo "🧬 Pushing EvolvixOS to GitHub..."
echo "   Repo: $REPO_URL"
echo ""

# Check if already has remote
if git remote get-url origin &>/dev/null; then
    echo "✅ Remote 'origin' already set to: $(git remote get-url origin)"
else
    git remote add origin "$REPO_URL"
    echo "✅ Added remote: $REPO_URL"
fi

# Ensure main branch
git branch -M main 2>/dev/null || true

# Try to push
echo ""
echo "Pushing to GitHub..."
echo "If asked, enter your GitHub username and Personal Access Token (PAT)."
echo "Get a token at: https://github.com/settings/tokens (scope: repo)"
echo ""

git push -u origin main

echo ""
echo "✅ EvolvixOS pushed to GitHub!"
echo "   https://github.com/Protremix/EvolvixOS"
