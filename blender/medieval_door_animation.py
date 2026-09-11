"""
Procedural UE5-ready medieval door animation sample.

Target: Blender 4.x
Run inside Blender:
    Scripting -> Open -> Run Script

Outputs:
    MedievalDoor_Animated.blend
    MedievalDoor_Animated.fbx

The FBX contains one rigidly-skinned door mesh and one armature bone.
Every door vertex is weighted 100% to DoorBone so Unreal Engine can import
it as a Skeletal Mesh with an Animation Sequence.
"""

from __future__ import annotations

import bpy
import math
import os
import tempfile
from mathutils import Vector


FPS = 24
FRAME_START = 1
FRAME_OPEN = 24
FRAME_CLOSE = 48
FRAME_END = 72

DOOR_WIDTH = 2.0
DOOR_HEIGHT = 3.2
DOOR_THICKNESS = 0.18
OPEN_DEGREES = 90.0


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.armatures,
    ):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def make_material(name: str, base_color, roughness=0.6, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_box(name: str, location, scale, material=None):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        obj.data.materials.append(material)
    return obj


def join_meshes(objects, active, name):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = active
    bpy.ops.object.join()
    active.name = name
    return active


def create_door_mesh():
    wood = make_material("M_Wood", (0.23, 0.085, 0.025), roughness=0.72)
    iron = make_material("M_Iron", (0.045, 0.05, 0.055), roughness=0.38, metallic=0.8)

    parts = []

    # Door is centered at x = width/2 so its left edge sits on x = 0,
    # which is also the hinge / DoorBone axis.
    door = add_box(
        "DoorPanel",
        (DOOR_WIDTH / 2.0, 0.0, DOOR_HEIGHT / 2.0),
        (DOOR_WIDTH / 2.0, DOOR_THICKNESS / 2.0, DOOR_HEIGHT / 2.0),
        wood,
    )
    parts.append(door)

    brace_depth = -(DOOR_THICKNESS / 2.0 + 0.035)

    for index, z in enumerate((0.55, DOOR_HEIGHT - 0.55), start=1):
        brace = add_box(
            f"Brace_{index}",
            (DOOR_WIDTH / 2.0, brace_depth, z),
            (DOOR_WIDTH / 2.0 - 0.08, 0.035, 0.075),
            iron,
        )
        parts.append(brace)

    hinge_strip = add_box(
        "HingeStrip",
        (0.12, brace_depth, DOOR_HEIGHT / 2.0),
        (0.07, 0.035, DOOR_HEIGHT / 2.0 - 0.12),
        iron,
    )
    parts.append(hinge_strip)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=0.07,
        depth=0.18,
        location=(DOOR_WIDTH - 0.25, -0.19, DOOR_HEIGHT * 0.52),
        rotation=(math.radians(90), 0.0, 0.0),
    )
    handle = bpy.context.object
    handle.name = "Handle"
    handle.data.materials.append(iron)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(handle)

    return join_meshes(parts, door, "SK_Door")


def create_armature():
    arm_data = bpy.data.armatures.new("DoorRig")
    arm_obj = bpy.data.objects.new("DoorRig", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    arm_obj.show_in_front = True

    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    bone = arm_data.edit_bones.new("DoorBone")
    bone.head = Vector((0.0, 0.0, 0.0))
    bone.tail = Vector((0.0, 0.0, DOOR_HEIGHT))

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def skin_door_to_bone(door, rig):
    # Rigid skinning: every vertex follows DoorBone at weight 1.0.
    group = door.vertex_groups.new(name="DoorBone")
    group.add(list(range(len(door.data.vertices))), 1.0, "REPLACE")

    modifier = door.modifiers.new(name="Armature", type="ARMATURE")
    modifier.object = rig

    # Parenting to the armature keeps the export hierarchy straightforward.
    door.parent = rig
    door.matrix_parent_inverse = rig.matrix_world.inverted()


def animate_rig(rig):
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END

    bone = rig.pose.bones["DoorBone"]
    bone.rotation_mode = "XYZ"

    keys = [
        (FRAME_START, 0.0),
        (FRAME_OPEN, math.radians(OPEN_DEGREES)),
        (FRAME_CLOSE, 0.0),
        (FRAME_END, 0.0),
    ]

    for frame, angle in keys:
        scene.frame_set(frame)
        bone.rotation_euler = (0.0, 0.0, angle)
        bone.keyframe_insert(data_path="rotation_euler", frame=frame)

    if rig.animation_data and rig.animation_data.action:
        action = rig.animation_data.action
        action.name = "Door_OpenClose"

        # Blender 4.x versions differ in Action internals. fcurves is available
        # on the common 4.x path; if it is not, animation still exports with
        # Blender's default interpolation.
        fcurves = getattr(action, "fcurves", None)
        if fcurves is not None:
            for fcurve in fcurves:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = "BEZIER"
                    kp.handle_left_type = "AUTO_CLAMPED"
                    kp.handle_right_type = "AUTO_CLAMPED"

    scene.frame_set(FRAME_START)


def add_preview_frame():
    """Add a non-exported stone frame so the motion is easy to inspect in Blender."""
    stone = make_material("M_Stone", (0.16, 0.15, 0.13), roughness=0.9)

    post_w = 0.25
    post_d = 0.30

    add_box(
        "Preview_FrameLeft",
        (-post_w / 2.0, 0.10, DOOR_HEIGHT / 2.0),
        (post_w / 2.0, post_d / 2.0, DOOR_HEIGHT / 2.0 + 0.15),
        stone,
    )
    add_box(
        "Preview_FrameRight",
        (DOOR_WIDTH + post_w / 2.0, 0.10, DOOR_HEIGHT / 2.0),
        (post_w / 2.0, post_d / 2.0, DOOR_HEIGHT / 2.0 + 0.15),
        stone,
    )
    add_box(
        "Preview_FrameTop",
        (DOOR_WIDTH / 2.0, 0.10, DOOR_HEIGHT + 0.20),
        (DOOR_WIDTH / 2.0 + post_w, post_d / 2.0, 0.20),
        stone,
    )


def set_scene_units():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0


def output_dir():
    if bpy.data.filepath:
        return os.path.dirname(bpy.data.filepath)
    return tempfile.gettempdir()


def save_and_export(door, rig):
    out_dir = output_dir()
    blend_path = os.path.join(out_dir, "MedievalDoor_Animated.blend")
    fbx_path = os.path.join(out_dir, "MedievalDoor_Animated.fbx")

    bpy.ops.wm.save_as_mainfile(filepath=blend_path)

    bpy.ops.object.select_all(action="DESELECT")
    door.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig

    bpy.ops.export_scene.fbx(
        filepath=fbx_path,
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS",
        use_space_transform=True,
        bake_space_transform=False,
        axis_forward="-Y",
        axis_up="Z",
        add_leaf_bones=False,
        use_armature_deform_only=True,
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=0.0,
    )

    print("=" * 60)
    print("Generated UE5 animation sample")
    print("BLEND:", blend_path)
    print("FBX:  ", fbx_path)
    print("=" * 60)


def main():
    clear_scene()
    set_scene_units()
    add_preview_frame()

    door = create_door_mesh()
    rig = create_armature()
    skin_door_to_bone(door, rig)
    animate_rig(rig)
    save_and_export(door, rig)


if __name__ == "__main__":
    main()
