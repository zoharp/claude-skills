#!/bin/bash

SKILLS_REPO="https://github.com/zoharp/claude-skills"
CLONE_DIR="$HOME/claude-skills"
SKILLS_DIR="$HOME/.claude/skills"

echo "================================================"
echo " Claude Skills Installer"
echo "================================================"
echo ""

# Step 1 — Clone or update the skills repo
if [ -d "$CLONE_DIR/.git" ]; then
    echo "[1/3] Updating skills repo..."
    cd "$CLONE_DIR" && git pull
else
    echo "[1/3] Cloning skills repo..."
    git clone "$SKILLS_REPO" "$CLONE_DIR"
fi

if [ $? -ne 0 ]; then
    echo "ERROR: git failed. Make sure git is installed and you have internet access."
    exit 1
fi

# Step 2 — Create skills directory
echo ""
echo "[2/3] Creating skills directory..."
mkdir -p "$SKILLS_DIR"

# Step 3 — Copy all skills
echo ""
echo "[3/3] Installing skills..."
for dir in "$CLONE_DIR/skills"/*/; do
    skill=$(basename "$dir")
    if [ -f "$dir/SKILL.md" ]; then
        mkdir -p "$SKILLS_DIR/$skill"
        cp -r "$dir/." "$SKILLS_DIR/$skill/"
        echo "   Installed: $skill"
    fi
done

echo ""
echo "================================================"
echo " Done! Skills installed to: $SKILLS_DIR"
echo ""
echo " Next steps:"
echo "   1. Open your project folder in VS Code"
echo "   2. Open terminal and type: claude"
echo "   3. Say: use the new-project skill"
echo "================================================"
