# Rules for Claude (read every session)

This repo (`HeppiriRaid/ArtGameCollab2.mds`) holds all AI-related material for
the game repo `christopherlcollins/ArtGameCollab2`. Follow these rules always.

## 1. Game repo gets game files only
- In `christopherlcollins/ArtGameCollab2`, only add or change game files:
  `Assets/`, `Packages/`, `ProjectSettings/`, and the project/solution files.
- Never put `CLAUDE.md`, `.claude/`, AI notes, plans, memories, prompts or other
  AI docs in the game repo.

## 2. All AI material goes here
- Rules, notes, plans, decisions and anything worth remembering between
  sessions go in this repo (`docs/` for notes, `CLAUDE.md` for rules).
- When you learn something about the game project that a later session needs,
  write it to `docs/` here and commit + push it.
- Read `docs/` at the start of work on the game.

## 3. Commits
- Do not add `Co-Authored-By` or `Claude-Session` lines to commit messages in
  either repo.
- Do not commit or push to the game repo unless the user asks for it.

## 4. No trace of Claude in the game repo
- Commits in the game repo are authored as `HeppiriRaid <koukixieben@gmail.com>`,
  never as Claude. Check `git config user.name` before committing.
- Commit messages, code comments, file names and branch names in the game repo
  must not mention Claude, Anthropic, AI or session links.
- Do not push `claude/...` branches to the game repo. If the session assigns a
  `claude/` branch, ask the user for a plain branch name (or use `main` if they
  say so) before pushing.
- Do not open PRs or post GitHub comments on the game repo unless asked, and
  then without Claude footers or attribution.
