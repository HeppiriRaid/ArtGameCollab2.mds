---
name: blender-to-unity
description: Build realistic, game-ready props in Blender via the Blender MCP and bring them into Koki's Unity folder. Use when modelling any new object or room piece for the hotel laundry (or similar), or when re-exporting existing ones.
---

# Blender -> Unity prop pipeline (hotel laundry)

Code lives in `~/Documents/GitHub/ArtGameCollab2.mds/blender/hotel_laundry/`
(`laundry_lib.py` helpers, `textures.py`, one builder script per prop).
Working files: `~/Documents/Blender/HotelLaundry/` (blend, textures, renders, references).

## 1. References first (CLAUDE.md rule 5)
- Find a spec sheet / dimension drawing + photos; save to
  `~/Documents/Blender/HotelLaundry/references/<object>/`.
- Note key dimensions and visual details in `docs/references/<object>.md`.

## 2. Model by script
- Run builders with `runpy.run_path(...)` through `execute_blender_code`.
- Metres, Z up, front faces -Y, origin at the floor. Parts that must move in
  Unity (doors) hang under an empty named e.g. "Door"; markers for Unity are
  empties named `*Slot*` / `*Trigger*`.
- Materials: image textures only (procedural nodes don't export). Generated
  textures via `textures.py`; scanned ones from Poly Haven (CC0) 1K JPG with
  the `nor_gl` normal map. Grime = "Col" vertex colours (`L.grime`).
- Bevel + weighted normals on hard edges; text is flat (`L.text_mesh`).
  Budgets: hero machine <= 30k tris, props <= 12k.

## 3. Check
- Render with EEVEE (product shot + close-up), compare with the references,
  fix differences before exporting.

## 4. Export
- `L.export_glb(name, Models/<name>.glb, keep_separate=("Door",))` merges each
  prop into one mesh (+ separate movable parts), JPEG textures, vertex colours.
- Output: `ArtGameCollab2/Assets/Koki (HeppiriRaid)/Models/`.

## 5. Unity
- `unity command editor invoke_menu --path "Assets/Refresh"` (Unity doesn't see
  files while unfocused), then `console status`.
- Place via scripts / `eval` (`PrefabUtility.InstantiatePrefab`); Pipeline
  `instantiate` rejects .glb.
- glTF import drops KHR emissive strength: scale emission in code.
- Captures: `game_view source=screen` shows the real HDR + bloom result; a
  RenderTexture capture does not. Use small sizes and decode the saved base64.
- Enable `set_auto_tick` so play mode advances while the editor is unfocused.

## Known traps (fixed, don't reintroduce)
- `box_bm` face keys: vertex index = 4x + 2y + z; check `skip=` removes the
  intended face.
- Objects in a viewport-hidden collection have stale `matrix_world`;
  `merged_copy` unhides and updates first.
- Joined meshes fill missing vertex-colour layers with black; give every part
  a white "Col" layer before joining.
- Slot `matrix_world` is stale right after creation: `view_layer.update()`.
