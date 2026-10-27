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
- Exception (user-approved): TextMesh Pro may be used, and importing its
  resources may create `Assets/TextMesh Pro/` outside Koki's folder.
- Unity Pipeline authoring root stays at `Assets/Koki (HeppiriRaid)` (or
  `Assets/Public Assets` while working there). Never set it to `Assets`.
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

## 5. Modelling: references first
- Before modelling or refining any object, gather real references instead of
  working from memory: manufacturer spec sheets and dimension drawings, product
  photos from several angles, close-ups of details (controls, hinges, seams,
  labels, fasteners, wear). Note real dimensions and materials.
- Save reference images and notes outside the repos, in
  `~/Documents/Blender/HotelLaundry/references/<object>/`, and write a short
  summary (sources + key dimensions/details) to `docs/references/<object>.md`
  in this repo. Never put reference images in the game repo.
- Compare renders side by side with the references and list what differs
  before calling a model done.
- Use real products only as reference; models use fictional branding.

## 6. Scenes are built like a human would build them
- Place everything in the scene at edit time so it is visible and editable in
  the Hierarchy: level geometry, machines, props, lights, reflection probes,
  post-processing volumes, UI canvases, audio sources, triggers.
- Use prefabs (in Koki's `Prefabs/`) for repeated things, placed as prefab
  instances. Runtime scripts may move, enable/disable and vary objects that
  already exist, but must not spawn the level at Start.
- Every scene gets reflection probes and a sensible lighting setup, and is
  saved after each build step.

## 7. No rendering artifacts (z-fighting)
- Never leave two surfaces in the same plane overlapping (coplanar walls,
  backing panels, trims ending flush on another face). Offset or embed them.
- Where pieces meet at a corner, run one piece past the corner so its end is
  hidden inside/behind the other, instead of ending exactly on its face.
- Decals, stickers, printed text and thin plates sit >= 1.5 mm off their
  surface (text >= 2.5 mm), so depth precision at game distances can't flicker.
- Before calling a scene done, look for flicker at corners, wall joins, floor
  edges and on decals from a few metres away.

## 8. No implausible shadows
- Lighting must make physical sense in Play mode, not just in the editor.
- Don't toggle shadow casting on/off at runtime by distance (shadows pop and
  smear), and don't cast shadows from very wide spot lights (shadow maps stretch
  into blobs). Many soft overhead sources (fluorescent troffers) cast no
  realtime shadows; ground objects with soft contact shadows instead.
- Check shadows by walking around in Play mode before calling it done.

## 9. Craftsmanship: never simplify a part into one shape
- Model objects the way they are manufactured: break every component into its
  real sub-parts (trims, bezels, retainers, gaskets, fasteners, seams, folds,
  vents, hinges, latches, labels) at their real proportions.
- Study references close up for each sub-part before modelling it; if a detail
  is visible in the reference at gameplay distance, it must exist in the model.
- Small accurate details accumulated everywhere are the goal ("master work, not
  slop"). Budget triangles by merging/LOD, not by skipping detail.

## 10. Performance: steady 60 fps on Koki's Mac (M1 Pro)
- No TextMeshPro on repeated objects (machines, props). Labels are baked into
  the model geometry; TMP only for a few unique signs and the HUD.
- Every repeated object gets an LODGroup (detail up close, simplified mid,
  stand-in far, culled in the fog). The project's LOD Bias is 2: set
  thresholds with that in mind.
- No realtime shadows from the many fluorescent lights; contact shadows instead.
- Verify with "Koki > Laundry > Performance Build" + the -perfprobe run, not
  with editor Play-mode stats (the editor adds its own overhead).
