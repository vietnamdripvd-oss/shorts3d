"""Kamera vertikal 9:16 + helper zoom/dolly."""
import bpy
from mathutils import Vector


def add_camera(loc=(0, -10, 2), target=(0, 0, 1), lens=50, name="Cam"):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_fit = "VERTICAL"
    data.clip_start = 0.05
    data.clip_end = 500
    cam = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    tgt = bpy.data.objects.new(name + "_target", None)
    bpy.context.scene.collection.objects.link(tgt)
    tgt.location = target
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    bpy.context.scene.camera = cam
    return cam, tgt


def key_lens(cam, frame, lens):
    cam.data.lens = lens
    cam.data.keyframe_insert("lens", frame=frame)


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
