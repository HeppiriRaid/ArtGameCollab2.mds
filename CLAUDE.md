# Rules for Claude (read every session)

This repo (`HeppiriRaid/ArtGameCollab2.mds`) holds all AI-related material for
the game repo `christopherlcollins/ArtGameCollab2`. Follow these rules always.

## 1. Game repo gets game files only
- In `christopherlcollins/ArtGameCollab2`, only add or change game files.
- Only create or edit files inside `Assets/Koki (HeppiriRaid)/` and
  `Assets/Public Assets/`. Every other folder (classmates' folders, scenes,
  `_SharedFiles`, `Settings`, `Packages/`, `ProjectSettings/`, etc.) belongs to
  classmates: read it if needed, never create, edit, move or delete there.
  Ask the user first if a change elsewhere seems necessary.
- Unity Pipeline authoring root stays at `Assets/Koki (HeppiriRaid)` (or
  `Assets/Public Assets` while working there). Never set it to `Assets`.
- The Pipeline package changes in `Packages/` are local only: don't commit
  them unless the user says so.
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
- Never create or push branches in the game repo. Commit and push straight to
  `main`, even if the session assigns a `claude/...` branch. Pull `main` first.
- Do not open PRs or post GitHub comments on the game repo unless asked, and
  then without Claude footers or attribution.
