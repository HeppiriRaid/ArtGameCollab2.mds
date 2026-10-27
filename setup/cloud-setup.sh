#!/bin/bash
# Claude Code cloud environment setup script.
# Clones the AI docs repo and loads its CLAUDE.md as user-level memory, so the
# rules apply in every session without adding files to the game repo.
set -e
DOCS=/home/user/artgamecollab2.mds
if [ ! -d "$DOCS/.git" ]; then
  git clone --depth 1 https://github.com/HeppiriRaid/ArtGameCollab2.mds "$DOCS"
fi
mkdir -p ~/.claude
cat > ~/.claude/CLAUDE.md <<RULES
The AI docs repo is cloned at $DOCS. Its rules apply to every session:

@$DOCS/CLAUDE.md
RULES
