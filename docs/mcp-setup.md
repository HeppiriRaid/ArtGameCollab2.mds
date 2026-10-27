# MCP setup: Unity editor + Blender (Koki's Mac)

Both servers are registered at **user scope** in `~/.claude.json`, never with a
`.mcp.json` in the game repo. Check with `claude mcp list`.

## Local Mac setup (done 2026-10-27)
- Docs repo cloned at `~/Documents/GitHub/ArtGameCollab2.mds`.
- `~/.claude/CLAUDE.md` imports this repo's `CLAUDE.md`.
- `~/.claude/settings.json`: `includeCoAuthoredBy: false`, blank `attribution`
  (backup of the old file: `settings.json.bak`).
- Do not run `setup/cloud-setup.sh` on the Mac: it overwrites
  `~/.claude/settings.json` and `~/.claude/CLAUDE.md`. It is for cloud sessions only.

## Unity: connected (relay)
- Package `com.unity.ai.assistant` 2.21.0-pre.2 is already in the game repo.
- Uses the AI Assistant relay. Registered with:
  `claude mcp add --scope user --transport stdio unity -- ~/.unity/relay/relay_mac_arm64.app/Contents/MacOS/relay_mac_arm64 --mcp`
- The connection must be approved once in Unity: Edit > Project Settings > AI >
  Unity MCP (done 2026-10-27).
- Tools (7): `Unity_RunCommand`, `Unity_GetConsoleLogs`, `Unity_Camera_Capture`,
  `Unity_SceneView_Capture2DScene`, `Unity_SceneView_CaptureMultiAngleSceneView`,
  `Unity_AssetGeneration_GenerateAsset`, `Unity_AssetGeneration_GetModels`.

## Unity: Pipeline tools (`unity-editor-mcp`)
- `~/.unity/bin/unity mcp` serves the tools of the `com.unity.pipeline`
  package (~120 tools: scenes, prefabs, components, assets, animation,
  timeline, builds, captures, console, play mode). Without that package it
  shows 0 tools.
- Installed 2026-10-27 with `unity pipeline install` (0.9.1-exp.1). This edits
  `Packages/manifest.json` and `Packages/packages-lock.json`, which are shared
  with classmates: NOT committed. Only commit them if the user says so.
- Registered with:
  `claude mcp add --scope user --transport stdio unity-editor-mcp -- ~/.unity/bin/unity mcp --project-path ~/Documents/GitHub/ArtGameCollab2`
- Authoring root (`get_root` / `set_root`) is set to
  `Assets/Koki (HeppiriRaid)`, so Pipeline file tools stay in Koki's folder.
  Switch to `Assets/Public Assets` only while working there, then switch back.
  Never set it to `Assets`. The setting is not stored in tracked files.
- Unity must be open with the project for it to connect.

## Blender: official Blender Lab MCP
- Blender 5.2.3 LTS installed with `brew install --cask blender`.
- Add-on "MCP" 1.0.3 (Blender Lab) from
  `https://projects.blender.org/lab/blender_mcp/releases/download/v1.0.3/mcp-1.0.3.zip`,
  installed with
  `Blender --command extension install-file -r user_default --enable mcp-1.0.3.zip`.
  Its bridge auto-starts when Blender opens (Preferences > Add-ons > MCP) and
  listens on `localhost:9876`.
- The bridge only starts if Preferences > System > **Allow Online Access** is
  on (off by default). Turned on and saved to user prefs. If it stops working,
  check that setting first: `lsof -nP -iTCP:9876 -sTCP:LISTEN`.
- MCP server (`blender-mcp` from the same project, NOT the PyPI package of the
  same name, which is the community one):
  `claude mcp add --scope user --transport stdio blender -- /opt/homebrew/bin/uvx --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.3#subdirectory=mcp" blender-mcp`
- Registered and verified 2026-10-27: `claude mcp list` shows it connected
  and Blender listens on 9876. Blender must be open for it to work.
- Warning from Blender: the server runs LLM-generated Python in Blender with
  no guards. Save work before using it.

## Workflow for models made in Blender
- Export `.glb`/`.fbx` into `Assets/Koki (HeppiriRaid)/Models/` (or
  `Assets/Public Assets/` if shared); let Unity generate the `.meta`.
- No `.blend` scratch files or AI notes in the game repo unless asked.

## Unity CLI gotchas
- Don't pipe `unity command ...` output into `head`/`grep -m`: closing the
  pipe early resets the connection and Pipeline logs two Console errors
  ("Cannot be changed after headers are sent" / "Connection reset by peer").
  Write the output to a file first, then read it.
- Read the Console with
  `unity command console get --tail 60 --level error --result-only`
  and check health with `unity command console status --result-only`
  (`groundTruth.compilationFailed`, `consoleErrors`).
- Several MCP tools share names (`get`, `create`, `list`...); when the right
  one is unclear, use the CLI (`unity command <group> <name> ...`).
- "Build asset version error" / "Import Error Code:(4)" in `Logs/Editor.log`
  means files changed on disk while Unity was importing (e.g. a `git pull`).
  Unity rescans them on its own; not a real problem.
- Pipeline `instantiate` only takes prefab assets. An imported `.glb` (glTFast)
  is not one and logs a Console error. Place models with `eval`:
  `PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(path))`,
  or make a prefab from it first.
- `game_view` / `scene_view` with `save_path` save under the authoring root
  (e.g. `Assets/Koki (HeppiriRaid)/Temp/`), i.e. inside the game repo. Don't use
  `save_path`; decode the inline image instead.
