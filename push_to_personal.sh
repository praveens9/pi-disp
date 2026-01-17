#!/bin/bash

# Script to push to Personal GitHub (github.com)
# Enforces github.com usage and asks for strict confirmation.

set -e

# 1. Get Repo Name from folder name
REPO_NAME=$(basename "$PWD")

echo "================================================================"
echo "      🚀  PUSH TO PERSONAL GITHUB.COM (PUBLIC)  🚀"
echo "================================================================"
echo "Current Folder: $PWD"
echo "Target Repo:    $REPO_NAME"
echo "Target Host:    github.com (Hardcoded)"
echo "================================================================"

# 2. Prompt for Credentials
read -p "Enter your GitHub.com Username: " GITHUB_USER
if [ -z "$GITHUB_USER" ]; then echo "❌ Username cannot be empty."; exit 1; fi

echo -n "Enter your GitHub.com Personal Access Token (PAT): "
read -s GITHUB_PAT
echo ""
if [ -z "$GITHUB_PAT" ]; then echo "❌ Token cannot be empty."; exit 1; fi

echo ""
echo "⚠️  WARNING: This will perform the following actions:"
echo "  1. Create a PUBLIC repository '$REPO_NAME' on github.com."
echo "  2. Initialize a local Git repository (if one doesn't exist)."
echo "  3. Stage and Commit ALL current files."
echo "  4. OVERWRITE/SET remote 'origin' to point to the new github.com repo."
echo "  5. Push the 'main' branch to github.com."
echo ""
read -p "Are you strictly sure you want to proceed? (Type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "🚫 Operation cancelled. You must type 'yes' to proceed."
    exit 0
fi

# 3. Create Repository using GitHub API
echo "----------------------------------------------------------------"
echo "Creating repository '$REPO_NAME' on github.com..."
RESPONSE=$(curl -s -w "%{http_code}" -o response.json -u "$GITHUB_USER:$GITHUB_PAT" \
  -d "{\"name\":\"$REPO_NAME\", \"private\":false}" \
  https://api.github.com/user/repos)

HTTP_CODE=$(tail -n1 <<< "$RESPONSE")

if [ "$HTTP_CODE" -eq 201 ]; then
    echo "✅ Repository created successfully."
elif [ "$HTTP_CODE" -eq 422 ]; then
    echo "ℹ️  Repository '$REPO_NAME' already exists on github.com. Proceeding..."
else
    echo "❌ Failed to create repository. HTTP Code: $HTTP_CODE"
    cat response.json
    rm response.json
    exit 1
fi
rm -f response.json

# 4. Initialize Git and Commit
if [ ! -d ".git" ]; then
    echo "Initializing Git..."
    git init
    git branch -M main
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "Committing changes..."
    git add .
    git commit -m "Initial commit to public repo" || echo "Nothing to commit, proceeding..."
fi

# 5. Handle Remote 'origin'
REMOTE_URL="https://$GITHUB_USER:$GITHUB_PAT@github.com/$GITHUB_USER/$REPO_NAME.git"

if git remote | grep -q "^origin$"; then
    CURRENT_ORIGIN=$(git remote get-url origin)
    echo "⚠️  Remote 'origin' already exists: $CURRENT_ORIGIN"
    echo "Updating 'origin' to point to: $REMOTE_URL"
    git remote set-url origin "$REMOTE_URL"
else
    echo "Adding remote 'origin': $REMOTE_URL"
    git remote add origin "$REMOTE_URL"
fi

# 6. Push
echo "----------------------------------------------------------------"
echo "Pushing code to $GITHUB_USER/$REPO_NAME..."
git push -u origin main

echo "================================================================