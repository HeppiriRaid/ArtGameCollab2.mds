# Design: "The Laundry" (Koki's scene)

Back-of-house laundry of a massive Las Vegas casino hotel, but wrong:
liminal / backrooms horror. Endless fluorescent-lit bays of washers and
dryers that hum, the same room again and again, slightly worse each time.

## Mood
- Fluorescent troffers (some dead, some flickering), 60 Hz hum.
- Yellowed walls: dirty white tile wainscot, stained paint above, water-stained
  drop ceiling, sealed concrete floor with drains and wet patches.
- Hotel-scale industrial: rows of washer-extractors and tumble dryers, linen
  carts, folding tables, wire shelving with towels, pipes and ducts overhead.
- Fog so the far end of a bay is never fully visible. No music, only machines.

## Space (non-Euclidean, all via seamless teleports)
- One repeating **bay** module: 24 m long (Z) x 10 m wide x 3.2 m high.
  Washers on one wall, dryers on the other, centre aisle, columns every 6 m,
  double swing doors with portholes at each end.
- Three live bays in a line; crossing into the next bay shifts the player
  back one bay length -> the corridor never ends.
- The room is longer inside than out: the teleport distance is shorter than
  the walked distance.
- Side door: leads back into the far end, facing the other way, so retracing
  your steps does not return you.
- Per-loop variation from a loop counter: lights fail, washer doors stand
  open, screens show wrong text, ceiling slowly lowers, carts move.

## Tech
- Scripts in `Assets/Koki (HeppiriRaid)/Scripts/`: FirstPersonController
  (Input System device reads), LaundryLoop (bays + teleport + variation),
  FluorescentFlicker, ProceduralHum. No new tags/layers (ProjectSettings is shared).
- Models: Blender scripts in this repo, export merged per prop (door parts
  kept separate), 1K textures, Poly Haven CC0 for room surfaces.
- Post: URP Volume profile in Koki's folder (bloom, grain, vignette, colour).

## Status (2026-10-27, end of session)
- Machines: laundromat stainless washers (Dexter T-450 size) and stack dryers,
  aged materials, layered door assemblies, stickers baked into geometry,
  LOD0/LOD1/LOD2 (+ culled in fog). No TextMeshPro on machines.
- Scene is built in the Hierarchy by "Koki > Laundry > Build Scene" (prefabs in
  Prefabs/), then "Bake Reflections", then "Build Scene" again.
- Player: copy of the Standard Assets FPSController prefab in StandardFPS/
  (scripts copied with namespace KokiLaundry.FirstPerson, still using the
  original CrossPlatformInputManager; Teleport() added for the loop). Scene
  overrides only: post-processing on, far clip 55, fog-coloured background, hum.
- Performance (standalone build, 30 s walk): 99% of frames <= 6 ms, avg 83 fps.
  Some one-off hitches (likely first-time shader compiles) pull the average
  down: worth a shader warmup pass later.

## Git notes
- Classmates have pushed merges with unresolved conflict markers before
  (ProjectSettings.asset, Demo_WallpaperGallery.unity.meta). Scan for
  `<<<<<<<` after pulling.
- Unity re-saves ProjectSettings/Packages/com.unity.probuilder/Settings.json on
  Koki's Mac; it's noise: discard it, don't commit it.
- A GitHub Desktop stash of auto-changed shared render settings was dropped;
  backup at ~/Documents/ArtGameCollab2-stash-backup-2026-10-27.patch.
