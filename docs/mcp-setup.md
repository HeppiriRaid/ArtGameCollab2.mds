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
- Do NOT use `~/.unity/bin/unity mcp` (what `unity mcp configure claude-code`
  suggests): it only exposes commands from Unity's separate Pipeline package,
  which this project doesn't have, so it shows 0 tools.
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
