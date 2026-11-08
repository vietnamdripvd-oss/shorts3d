"""TAHAP 0 — tes end-to-end 5 detik.
Maskot lebah 'dengung' muter + kedip di atas planet kecil, outline (Solidify + Freestyle).

  blender -b -P test_e2e/scene.py -- [--out test_e2e/scene.blend]
"""
import bpy, sys, os, math, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from lib3d import core, toon, camera
from lib3d.core import DEG

# ---- PARAMETER -------------------------------------------------------------
PLANET_COLOR = "#5cc96b"
ROCK_COLOR = "#8a7f9e"
TREE_COLOR = "#2f9e57"
SKY = "#7cc4ff"
FPS, SECONDS = 30, 5
OUT = os.path.join(ROOT, "test_e2e", "scene.blend")
# ---------------------------------------------------------------------------

sc = core.reset_scene()
toon.setup_render(sc, res=(1080, 1920), fps=FPS, samples=16)
toon.setup_world(sc, SKY, ambient=0.25)
toon.add_sun(rot=(50 * DEG, 10 * DEG, 35 * DEG), energy=4.0)
sc.frame_start, sc.frame_end = 1, FPS * SECONDS

# ---- planet ----------------------------------------------------------------
planet = core.ico("planet", r=2.0, sub=2, loc=(0, 0, -2.0))
toon.apply_toon(planet, PLANET_COLOR, outline=0.03)
random.seed(4)
for i in range(9):
    th, ph = random.uniform(0, 2 * math.pi), random.uniform(35, 150) * DEG
    n = (math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph))
    if i % 3 == 0:
        o = core.ico(f"rock{i}", r=0.18, sub=1)
        toon.apply_toon(o, ROCK_COLOR, outline=0.015, name="toon_rock")
        off = 1.95
    else:
        o = core.cone(f"tree{i}", r1=0.22, depth=0.6, verts=6)
        toon.apply_toon(o, TREE_COLOR, outline=0.015, name="toon_tree")
        off = 2.2
    o.location = (n[0] * off, n[1] * off, n[2] * off)
    o.rotation_mode = "QUATERNION"
    from mathutils import Vector
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(n))
    o.location = Vector(o.location)
    o.parent = planet
    o.location = (Vector(o.location) - Vector((0, 0, 0)))  # relatif pusat planet

# ---- maskot: lebah 'dengung' dari models/dengung.py ------------------------
sys.path.insert(0, os.path.join(ROOT, "models"))
import dengung
m_root, parts = dengung.build()
O = {o.name: o for o in parts}

# ---- rig sederhana (rigid parenting ke bone) -------------------------------
arm_data = bpy.data.armatures.new("rig")
rig = bpy.data.objects.new("rig", arm_data)
sc.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones
def bone(name, h, t, parent=None):
    b = eb.new(name); b.head, b.tail = h, t
    if parent: b.parent = eb[parent]
    return b
HZ = dengung.HEAD_Z
EZ = dengung.FACE_C.z + 0.04
bone("root", (0, 0, 0), (0, 0.3, 0))
bone("body", (0, 0, 0.1), (0, 0, 0.8), "root")
bone("head", (0, 0, 0.8), (0, 0, 2.0), "body")
for side, sd in (("L", 1), ("R", -1)):
    ey = dengung.face_y(0.2 * sd, EZ)
    bone(f"eye_{side}", (0.2 * sd, ey, EZ), (0.2 * sd, ey - 0.25, EZ), "head")
    bone(f"arm_{side}", (0.38 * sd, 0, 0.74), (0.46 * sd, 0, 0.42), "body")
MZ = dengung.FACE_C.z - 0.2
bone("mouth", (0, dengung.face_y(0, MZ), MZ), (0, dengung.face_y(0, MZ) - 0.25, MZ), "head")
bpy.ops.object.mode_set(mode="OBJECT")

def bone_parent(obj, bname):
    mw = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bname
    bpy.context.view_layer.update()
    obj.matrix_world = mw

for o in parts:
    n = o.name
    if n.startswith(("eye_1", "eye_hl_1")):
        bone_parent(o, "eye_L")
    elif n.startswith(("eye_-1", "eye_hl_-1")):
        bone_parent(o, "eye_R")
    elif n == "arm_1":
        bone_parent(o, "arm_L")
    elif n == "arm_-1":
        bone_parent(o, "arm_R")
    elif n == "mouth":
        bone_parent(o, "mouth")
    elif n.startswith("leg_"):
        bone_parent(o, "root")
    elif n.startswith(("body", "wing_", "stinger")):
        bone_parent(o, "body")
    else:
        bone_parent(o, "head")
bpy.data.objects.remove(m_root)

# ---- animasi ---------------------------------------------------------------
pb = rig.pose.bones
for b in pb:
    b.rotation_mode = "XYZ"

def k(b, path, f, v):
    setattr(b, path, v)
    b.keyframe_insert(path, frame=f)

root = pb["root"]
# HOOK: pop-in overshoot (frame 1-16)
k(root, "scale", 1, (0.01, 0.01, 0.01))
k(root, "scale", 8, (1.25, 1.25, 0.85))
k(root, "scale", 12, (0.92, 0.92, 1.1))
k(root, "scale", 16, (1, 1, 1))
# muter 360
k(root, "rotation_euler", 16, (0, 0, 0))
k(root, "rotation_euler", 120, (0, 0, 2 * math.pi))
k(root, "rotation_euler", 150, (0, 0, 2 * math.pi))
# hop kecil
for f, z in ((60, 0), (68, 0.35), (76, 0)):
    k(root, "location", f, (0, 0, z))
# kepala goyang dikit (nangis sesenggukan)
hd = pb["head"]
for i, f in enumerate(range(16, 150, 8)):
    k(hd, "rotation_euler", f, (0, (4 if i % 2 else -4) * DEG, 0))
# kedip
for side in "LR":
    e = pb[f"eye_{side}"]
    for f0 in (40, 100, 135):
        k(e, "scale", f0 - 3, (1, 1, 1))
        k(e, "scale", f0, (1, 1, 0.08))
        k(e, "scale", f0 + 3, (1, 1, 1))
# lambai tangan kanan
aR = pb["arm_R"]
for f, r in ((80, 0), (86, -120), (92, -90), (98, -120), (104, -90), (112, 0)):
    k(aR, "rotation_euler", f, (0, 0, r * DEG))
# mulut merengek
mo = pb["mouth"]
for i, f in enumerate(range(20, 60, 5)):
    k(mo, "scale", f, (1, 1, 1.0 + (0.8 if i % 2 else 0.0)))

# planet muter pelan
core.key(planet, "rotation_euler", 1, (0, 0, 0))
core.key(planet, "rotation_euler", 150, (40 * DEG, 0, 25 * DEG))
for fc in planet.animation_data.action.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"

# ---- kamera: zoom-in hook --------------------------------------------------
cam, tgt = camera.add_camera(loc=(1.4, -11, 1.9), target=(0, 0, 0.5), lens=38)
# hook: wide -> snap zoom in ke maskot, lalu pelan2 zoom terus
camera.key_lens(cam, 1, 24)
camera.key_lens(cam, 12, 40)
camera.key_lens(cam, 150, 44)

print("TRIS mascot:", core.tri_count(parts))
print("TRIS total:", core.tri_count())
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--out" in argv:
    OUT = argv[argv.index("--out") + 1]
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
