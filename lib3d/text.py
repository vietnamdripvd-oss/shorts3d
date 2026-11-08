"""Teks yang MENEMPEL DI OBJEK (mis. tulisan "IJAZAH" di kertas).

Caption / angka / judul layar TIDAK di sini: itu overlay 2D setelah render 3D
(font yang sama: assets/fonts/Inter-ExtraBold.otf).
"""
import bpy, os
from . import toon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(ROOT, "assets", "fonts", "Inter-ExtraBold.otf")


def font():
    f = bpy.data.fonts.get("Inter-ExtraBold")
    if f is None:
        f = bpy.data.fonts.load(FONT_PATH) if os.path.exists(FONT_PATH) else bpy.data.fonts.get("Bfont")
    return f


def flat_text(name, body, size=0.2, color="#1e1e1e", extrude=0.0, loc=(0, 0, 0), rot=(0, 0, 0),
              align="CENTER", spacing=1.0):
    """Teks jadi MESH (bukan curve) dengan material flat. Default rebah di bidang XY menghadap +Z."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = font()
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.space_character = spacing
    obj = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    # convert ke mesh supaya bisa diperlakukan seperti objek biasa
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.clear()
    obj.data.materials.append(toon.flat_material(f"text_{color}", color))
    return obj
