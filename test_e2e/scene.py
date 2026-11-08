"""TAHAP 0 — tes end-to-end 5 detik.
Maskot toon low-poly muter + kedip di atas planet kecil, outline (Solidify + Freestyle).

  blender -b -P test_e2e/scene.py -- [--out test_e2e/scene.blend]
"""
import bpy, sys, os, math, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from lib3d import core, toon, camera
from lib3d.core import DEG

# ---- PARAMETER -------------------------------------------------------------
BODY_COLOR = "#ff8a3d"
BELLY_COLOR = "#ffd9a8"
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

# ---- maskot (blob bulat) ---------------------------------------------------
body = core.sphere("body", r=0.7, seg=16, rings=10, loc=(0, 0, 0.72))
body.scale = (1.0, 0.92, 0.95)
core.subsurf(body, 1)
toon.apply_toon(body, BODY_COLOR, outline=0.025, rim=0.25)
belly = core.sphere("belly", r=0.45, seg=12, rings=8, loc=(0, -0.42, 0.6))
belly.scale = (1, 0.45, 0.9)
toon.apply_toon(belly, BELLY_COLOR, outline=0)

eyes = []
for side, x in (("L", 0.24), ("R", -0.24)):
    w = core.sphere(f"eye_{side}", r=0.16, seg=12, rings=8, loc=(x, -0.6, 0.95))
    w.scale = (1, 0.5, 1.25)
    w.data.materials.append(toon.flat_material("eye_white", "#ffffff"))
    toon.add_outline(w, 0.012)
    p = core.sphere(f"pupil_{side}", r=0.075, seg=10, rings=6, loc=(x, -0.68, 0.95))
    p.scale = (1, 0.5, 1.3)
    p.data.materials.append(toon.flat_material("pupil", "#1a1020"))
    eyes.append((side, w, p))
mouth = core.torus("mouth", R=0.1, r=0.03, maj=12, minr=6, loc=(0, -0.66, 0.66))
mouth.rotation_euler = (90 * DEG, 0, 0)
mouth.scale = (1.3, 0.6, 1)
mouth.data.materials.append(toon.flat_material("mouth", "#5a1a2a"))
feet = []
for side, x in (("L", 0.3), ("R", -0.3)):
    f = core.sphere(f"foot_{side}", r=0.18, seg=10, rings=6, loc=(x, -0.1, 0.1))
    f.scale = (1, 1.3, 0.6)
    toon.apply_toon(f, BODY_COLOR, outline=0.015)
    feet.append(f)
arms = []
for side, x in (("L", 0.72), ("R", -0.72)):
    a = core.sphere(f"arm_{side}", r=0.14, seg=10, rings=6, loc=(x, -0.05, 0.6))
    a.scale = (0.8, 0.8, 1.4)
    toon.apply_toon(a, BODY_COLOR, outline=0.015)
    arms.append((side, a))

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
bone("root", (0, 0, 0), (0, 0.3, 0))
bone("body", (0, 0, 0.1), (0, 0, 0.7), "root")
bone("head", (0, 0, 0.7), (0, 0, 1.3), "body")
for side, x in (("L", 0.24), ("R", -0.24)):
    bone(f"eye_{side}", (x, -0.6, 0.95), (x, -0.85, 0.95), "head")
    bone(f"arm_{side}", (x * 3, -0.05, 0.8), (x * 3, -0.05, 0.4), "body")
bone("mouth", (0, -0.66, 0.66), (0, -0.9, 0.66), "head")
bpy.ops.object.mode_set(mode="OBJECT")

def bone_parent(obj, bname):
    mw = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bname
    bpy.context.view_layer.update()
    obj.matrix_world = mw

for o in (body, belly):
    bone_parent(o, "body")
for side, w, p in eyes:
    bone_parent(w, f"eye_{side}"); bone_parent(p, f"eye_{side}")
for side, a in arms:
    bone_parent(a, f"arm_{side}")
bone_parent(mouth, "mouth")
for f in feet:
    bone_parent(f, "root")

# ---- animasi ---------------------------------------------------------------
pb = rig.pose.bones
for b in pb:
    b.rotation_mode = "XYZ"

def k(b, path, f, v, interp="BEZIER", ease="AUTO"):
    setattr(b, path, v)
    b.keyframe_insert(path, frame=f)

root = pb["root"]
# HOOK: pop-in overshoot (frame 1-12)
k(root, "scale", 1, (0.01, 0.01, 0.01))
k(root, "scale", 8, (1.25, 1.25, 0.85))
k(root, "scale", 12, (0.92, 0.92, 1.1))
k(root, "scale", 16, (1, 1, 1))
# muter 360 + squash tiap seperempat
k(root, "rotation_euler", 16, (0, 0, 0))
k(root, "rotation_euler", 120, (0, 0, 2 * math.pi))
k(root, "rotation_euler", 150, (0, 0, 2 * math.pi))
# hop kecil di tengah
for f, z in ((60, 0), (68, 0.35), (76, 0)):
    k(root, "location", f, (0, 0, z))
# kedip (scale Z eye bone -> head bone axis = Y lokal bone)
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
# mulut ngomong dikit
m = pb["mouth"]
for i, f in enumerate(range(20, 60, 5)):
    k(m, "scale", f, (1, 1, 1.0 + (0.9 if i % 2 else 0.0)))

# planet muter pelan
core.key(planet, "rotation_euler", 1, (0, 0, 0))
core.key(planet, "rotation_euler", 150, (40 * DEG, 0, 25 * DEG))
for fc in planet.animation_data.action.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"

# ---- kamera: zoom-in hook --------------------------------------------------
cam, tgt = camera.add_camera(loc=(1.4, -11, 1.6), target=(0, 0, -0.5), lens=38)
# hook: wide -> snap zoom in ke maskot, lalu pelan2 zoom terus
camera.key_lens(cam, 1, 24)
camera.key_lens(cam, 12, 40)
camera.key_lens(cam, 150, 44)

print("TRIS mascot:", core.tri_count([body, belly, mouth] + [x for _, w, p in eyes for x in (w, p)]
                                    + feet + [a for _, a in arms]))
print("TRIS total:", core.tri_count())
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--out" in argv:
    OUT = argv[argv.index("--out") + 1]
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
