# UE5 Import Notes

## Basic import

For the first test, drag `MedievalDoor_Animated.fbx` into the Content Browser.

Suggested settings:

- Skeletal Mesh: Enabled
- Import Mesh: Enabled
- Import Animations: Enabled
- Convert Scene: Enabled
- Force Front XAxis: try Disabled first

After import, open the generated Animation Sequence and scrub the timeline.

## Expected animation

The door rotates around its left-side hinge.

Timeline at 24 FPS:

| Frame | State |
|---:|---|
| 1 | Closed |
| 24 | Open 90° |
| 48 | Closed |
| 72 | Closed hold |

## Rig structure

The generated door is a rigid Skeletal Mesh. All door vertices are weighted 100% to `DoorBone`. This keeps the asset simple while using the same UE5 skeletal-animation pipeline that can later support multi-part animated props.

## If the facing direction is wrong

FBX axis conventions can differ depending on Blender / UE version and export settings.
The script uses Blender FBX export with:

- Forward: `-Y`
- Up: `Z`

If your project convention differs, adjust those two values in the export block.

## Why skeletal animation for a door?

UE5 can animate a door in several ways (Blueprint transform, Sequencer, skeletal animation).
This sample intentionally uses a bone so the same pipeline can later support:

- windmills
- drawbridges
- traps
- chests
- mechanical props
- multi-part animated medieval assets
