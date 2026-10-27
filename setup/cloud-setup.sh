#!/bin/bash
# Claude Code cloud environment setup script.
# Clones the AI docs repo and loads its CLAUDE.md as user-level memory, so the
# rules apply in every session without adding files to the game repo.
set -e
DOCS=/home/user/artgamecollab2.mds
if [ ! -d "$DOCS/.git" ]; then
  git clone --depth 1 https://github.com/HeppiriRaid/ArtGameCollab2.mds "$DOCS"
fi
# Commit as the user, not as Claude.
git config --global user.name HeppiriRaid
git config --global user.email koukixieben@gmail.com
mkdir -p ~/.claude
# No Co-Authored-By / attribution lines in commits or PRs.
cat > ~/.claude/settings.json <<'SETTINGS'
{
  "includeCoAuthoredBy": false,
  "attribution": { "commit": "", "pr": "" }
}
SETTINGS
cat > ~/.claude/CLAUDE.md <<RULES
The AI docs repo is cloned at $DOCS. Its rules apply to every session:

@$DOCS/CLAUDE.md
RULES
