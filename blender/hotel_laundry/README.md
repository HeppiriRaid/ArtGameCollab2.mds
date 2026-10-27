# Hotel laundry: Blender sources

Scripts that build the laundry props procedurally in Blender 5.2 via the
Blender MCP (`execute_blender_code` + `runpy.run_path`).

- `laundry_lib.py`  shared helpers: materials, box/cylinder/lathe/rounded-plate
  meshes, world-scale UVs, bevel + weighted normals, flat text, GLB export.
- `textures.py`     tileable PBR textures generated with numpy (brushed steel,
  powder-coat paint, perforated drum, plastic, rubber).
- `washer.py`       washer-extractor (reference: docs/references/washer.md).

Working files (not in any repo): `~/Documents/Blender/HotelLaundry/`
(`blend/`, `textures/`, `renders/`, `references/`).
Exports go to `Assets/Koki (HeppiriRaid)/Models/<Prop>.glb` in the game repo.
