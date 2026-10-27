# Reusable Spawner + SpawnButton (shared asset)

Built 2026-10-27. Goal: an object spawner classmates (little Unity knowledge) can
reuse; a vending machine is just the example.

## Where things live (game repo)
- Shared, in `Assets/Public Assets/`:
  - `Scripts/Spawner/Spawner.cs`: `objectToSpawn`, optional `spawnPoint`,
    `amountPerSpawn`, `randomOffset`, `addPhysicsIfMissing` (adds Rigidbody +
    BoxCollider from renderer bounds), `pushForce` (along spawn point +Z),
    `randomSpin`, `cooldown`, `maxObjects` (removes oldest), `destroyAfterSeconds`,
    `spawnSound`, `onSpawned`. Public `Spawn()` (UnityEvent-callable) and context
    menu "Spawn (test)". Gizmo: green sphere + blue push line.
  - `Scripts/Spawner/SpawnButton.cs`: `spawner` slot + `onPressed` UnityEvent;
    click (raycast from `Camera.main`, screen center when cursor locked) and/or
    key (default E) within `reach` of `Camera.main`; OnGUI hint (`{key}`
    placeholder); `movingPart` presses in along -Z; `pressSound`.
    Uses legacy `Input` (project Active Input Handling = Both).
  - `Prefab/Spawner/Spawner.prefab`, `SpawnButton.prefab` (+ `Materials/`),
    `README_Spawner.txt` (student guide).
- Example, in `Assets/Koki (HeppiriRaid)/`:
  - `Scenes/VendingMachine.unity`: floor, light, shared FPSController,
    `VendingMachine` prefab, and "Example2" pedestal (button on top, spawner
    launching 3 cans with push + spin, destroy after 15 s).
  - `VendingMachine/Prefabs/VendingMachine.prefab` (primitive blockout,
    0.95 x 1.83 x 0.85 m, glass front, shelves of display cans, delivery bin,
    button on control column), `VendingMachine/Prefabs/SodaCan.prefab`
    (cylinder 66 x 122 mm, convex MeshCollider, Rigidbody 0.37 kg),
    `VendingMachine/Materials/VM_*.mat`.
- Vending machine is a blockout, not a reference-based model. If it is to be
  modelled properly, follow rule 5 (references first).

## Verified
- Compiles clean. Edit-mode physics test in a preview scene: can drops into the
  bin and rests lying down; a plain model with no physics gets a collider and
  lands. Not yet play-tested in Play mode (avoided while another session used
  the editor).

## Working alongside another session in the same Unity editor
- Don't change the Pipeline root, don't `save_all`, don't open scenes in Single
  mode, don't enter Play mode.
- Build scenes additively: `EditorSceneManager.NewScene(..., Additive)`, set it
  active, build, `SaveScene`, restore the previous active scene, `CloseScene`.
- Physics tests in edit mode: spawn into a temp additive scene, move objects into
  `EditorSceneManager.NewPreviewScene()` and call `GetPhysicsScene().Simulate`.
  `SceneManager.CreateScene` with local physics only works in Play mode.
- `eval` / `eval_file` wrap code in a method: no `using` lines, fully qualify
  `UnityEngine.SceneManagement.*` and `UnityEngine.Object`.
- Write new scripts with plain file writes, then `AssetDatabase.Refresh()` +
  `CompilationPipeline.RequestScriptCompilation()` (Unity doesn't refresh
  while unfocused).
- UnityEvent fields need `= new UnityEvent()` or `AddComponent` + call throws.
