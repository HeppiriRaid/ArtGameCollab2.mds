# MCP setup: Unity editor + Blender

Unity and Blender run on the user's own computer, so their MCP servers only
work with a Claude Code session that runs on that computer too (Claude Desktop
app, or the `claude` CLI). A cloud session cannot reach them.

To keep the game repo clean, register both servers at **user scope**
(`--scope user`), never with a `.mcp.json` in the game repo.

## Unity (official: Unity AI Assistant package)
- Requires Unity 6+ (project is 6000.6.7f1) and package `com.unity.ai.assistant`.
- Installing the package changes `Packages/manifest.json` and
  `packages-lock.json` in the game repo. That affects every collaborator, so
  agree with the team before committing those two files.
- In the editor: Edit > Project Settings > AI > Unity MCP. "Unity Bridge"
  should say Running. The relay binary installs itself to `~/.unity/relay/`.
- Connect Claude Code from that settings page (client integration), or follow
  the "Step 2" of the official guide:
  https://docs.unity3d.com/Packages/com.unity.ai.assistant@2.0/manual/unity-mcp-get-started.html
- Check: run `claude mcp list` and confirm the Unity server is connected.

## Blender
Official (Blender Lab, Blender 5.1+), preferred:
1. Install the MCP add-on from the Blender Lab extensions page
   (adds the Blender Lab repo, then the "MCP" add-on).
2. In Blender, open the add-on's N-panel > Client Config and copy the Claude
   Code command/JSON; run it with `--scope user`.

Community fallback (older Blender): `ahujasid/blender-mcp`
1. Install `uv`.
2. Install `addon.py` from https://github.com/ahujasid/blender-mcp in Blender
   (Edit > Preferences > Add-ons > Install from Disk), enable it.
3. `claude mcp add --scope user blender -- uvx blender-mcp`
4. In Blender: N-panel > BlenderMCP > Connect (port 9876).

Note: Blender MCP can run arbitrary Python in Blender. Save before using it.

## Workflow for models made in Blender
- Export to `.glb`/`.fbx` into the right folder under `Assets/` (e.g.
  `Assets/Koki (HeppiriRaid)/Models/`) and let Unity generate the `.meta`.
- Only the exported model files go in the game repo; no `.blend` scratch
  files or AI notes unless the user asks.
