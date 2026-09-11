# UE5 Animation Generator

A minimal Blender-to-Unreal Engine 5 animation generation sample.

This repository starts with a procedural medieval wooden door that:
- is generated entirely from Blender Python
- uses a hinge pivot suitable for game animation
- animates Closed -> Open -> Closed
- exports to FBX for Unreal Engine 5
- saves a `.blend` scene for inspection

## Ready-made model

`models/MedievalDoor_Animated.glb` is included in the repository.

It contains:
- medieval wooden door
- stone frame / threshold
- iron straps, hinges, and handle
- three basic PBR materials: Wood / Iron / Stone
- `Door_OpenClose` animation
- hinge-centered opening motion: Closed -> 90 degrees Open -> Closed -> Hold
- 3 second animation duration

The GLB uses meter units. In UE5, use/enable the glTF importer for the `.glb` route.

## Quick start

### Use the included model

Import `models/MedievalDoor_Animated.glb` into Unreal Engine 5.

### Generate the Blender / FBX version

1. Install Blender 4.x.
2. Open Blender.
3. Go to **Scripting**.
4. Open `blender/medieval_door_animation.py`.
5. Run the script.

By default, outputs are written next to the current `.blend` file, or to Blender's temporary directory if the file has not been saved.

Generated files:
- `MedievalDoor_Animated.blend`
- `MedievalDoor_Animated.fbx`

## UE5 FBX import

Import `MedievalDoor_Animated.fbx` into Unreal Engine 5.

Recommended first test:
- Import as a skeletal mesh if you want the bone animation as an Animation Sequence.
- Enable animation import.
- Keep unit conversion enabled.
- Verify the `DoorBone` animation from frame 1 to 72.

The Blender sample uses 24 FPS:
- Frame 1: closed
- Frame 24: fully open (90 degrees)
- Frame 48: closed
- Frame 72: closed hold / loop-friendly end

## Repository layout

```text
ue5-animation-generator/
├─ blender/
│  └─ medieval_door_animation.py
├─ docs/
│  └─ UE5_IMPORT.md
├─ models/
│  └─ MedievalDoor_Animated.glb
├─ .gitignore
└─ README.md
```

## Next planned features

- configurable open angle / speed / easing
- windmill rotation animation
- chest open / close animation
- drawbridge animation
- generic object-to-bone animation helper
- batch FBX export
- integration with a parametric medieval asset generator
