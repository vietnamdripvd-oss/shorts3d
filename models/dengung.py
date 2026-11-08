"""Maskot 'dengung' — lebah bulat low-poly, toon shaded. ORIGINAL (bukan karakter yang sudah ada).

Jalan sendiri:
  blender -b -P models/dengung.py -- --preview            # build + render turnaround 4 sudut
  blender -b -P models/dengung.py -- --out models/dengung.blend --glb models/dengung.glb

Parameter di bawah. Semua material lewat lib3d/toon.py. Tanpa rig dulu (rig dasar = tahap berikutnya).
"""
import bpy, sys, os, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from lib3d import core, toon, camera
from lib3d.core import DEG
from mathutils import Vector

# ---- PARAMETER -------------------------------------------------------------
BODY = "#ffc83d"      # kuning madu
STRIPE = "#3a2412"    # coklat gelap
WING = "#e8f7ff"      # biru pucat transparan-ish (opaque di toon)
TEAR = "#9fe0ff"
ANTENNA = "#3a2412"
BODY_R = 0.8
# ---------------------------------------------------------------------------


def build():
    root = bpy.data.objects.new("dengung_root", None)
    bpy.context.scene.collection.objects.link(root)
    parts = []

    body = core.sphere("body", r=BODY_R, seg=16, rings=10, loc=(0, 0, 0))
    body.scale = (1.0, 0.95, 0.95)
    core.subsurf(body, 1)
    toon.apply_toon(body, BODY, outline=0.025, rim=0.2)
    parts.append(body)

    # 2 belang (torus melingkar di badan)
    for z, R in ((0.28, 0.76), (-0.18, 0.79)):
        s = core.torus(f"stripe_{z}", R=R, r=0.085, maj=20, minr=6, loc=(0, 0, z))
        s.scale = (1.0, 0.95, 1.0)
        toon.apply_toon(s, STRIPE, outline=0)
        parts.append(s)

    # mata sedih: oval gepeng + alis miring ke dalam
    for side in (1, -1):
        x = 0.28 * side
        e = core.sphere(f"eye_{side}", r=0.12, seg=12, rings=8, loc=(x, -0.68, 0.12))
        e.scale = (1.0, 0.5, 1.1)
        e.data.materials.append(toon.flat_material("eye_white", "#ffffff"))
        toon.add_outline(e, 0.012)
        p = core.sphere(f"pupil_{side}", r=0.06, seg=8, rings=5, loc=(x, -0.72, 0.10))
        p.scale = (1, 0.5, 1.2)
        p.data.materials.append(toon.flat_material("pupil", "#1a1020"))
        brow = core.cube(f"brow_{side}", size=1.0, loc=(x, -0.7, 0.32))
        brow.scale = (0.2, 0.05, 0.035)
        brow.rotation_euler = (0, 0, -side * 20 * DEG)  # dalam naik = sedih
        toon.apply_toon(brow, STRIPE, outline=0)
        parts += [e, p, brow]

        # air mata: bulatan + ujung lancip ke bawah
        t = core.sphere(f"tear_{side}", r=0.055, seg=8, rings=5, loc=(x, -0.76, -0.04))
        tip = core.cone(f"tear_tip_{side}", r1=0.055, r2=0.0, depth=0.16, verts=8, loc=(x, -0.76, -0.16))
        tip.rotation_euler = (math.pi, 0, 0)
        toon.apply_toon(t, TEAR, outline=0)
        toon.apply_toon(tip, TEAR, outline=0)
        parts += [t, tip]

    # mulut: bulat cemberut kecil
    m = core.torus("mouth", R=0.06, r=0.025, maj=12, minr=6, loc=(0, -0.76, -0.28))
    m.rotation_euler = (90 * DEG, 0, 0)
    m.data.materials.append(toon.flat_material("mouth", "#8a3a2a"))
    parts.append(m)

    # antena
    for side in (1, -1):
        a = core.cylinder(f"antenna_{side}", r=0.025, depth=0.35, verts=6,
                          loc=(0.22 * side, 0, 1.0))
        a.rotation_euler = (0, -side * 18 * DEG, 0)
        toon.apply_toon(a, ANTENNA, outline=0)
        ball = core.sphere(f"antenna_tip_{side}", r=0.08, seg=8, rings=5,
                           loc=(0.29 * side, 0, 1.17))
        toon.apply_toon(ball, ANTENNA, outline=0.01)
        parts += [a, ball]

    # sayap
    for side in (1, -1):
        w = core.sphere(f"wing_{side}", r=0.5, seg=12, rings=8, loc=(0.6 * side, 0.1, 0.05))
        w.scale = (0.18, 0.6, 0.85)
        w.rotation_euler = (0, side * 12 * DEG, 0)
        toon.apply_toon(w, WING, outline=0.012)
        parts.append(w)

    # kaki
    for side in (1, -1):
        f = core.sphere(f"foot_{side}", r=0.2, seg=10, rings=6, loc=(0.3 * side, -0.1, -0.78))
        f.scale = (1, 1.2, 0.6)
        toon.apply_toon(f, BODY, outline=0.015)
        parts.append(f)

    for o in parts:
        o.parent = root
    return root, parts


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sc = core.reset_scene()
    toon.setup_render(sc, res=(540, 960), fps=30, samples=8, freestyle=True)
    toon.setup_world(sc, "#7cc4ff", ambient=0.3)
    toon.add_sun(rot=(55 * DEG, 10 * DEG, 35 * DEG), energy=4.0)
    root, parts = build()
    cam, tgt = camera.add_camera(loc=(0, -6.2, 0.6), target=(0, 0, 0.1), lens=50)

    print("TRIS:", core.tri_count(parts))

    if "--preview" in argv or not argv:
        out_dir = os.path.join(ROOT, "models", "preview")
        os.makedirs(out_dir, exist_ok=True)
        for name, ang in (("front", 0), ("three_quarter", 45), ("side", 90), ("back", 180)):
            root.rotation_euler = (0, 0, ang * DEG)
            sc.render.filepath = os.path.join(out_dir, f"dengung_{name}.png")
            bpy.ops.render.render(write_still=True)
            print("preview:", sc.render.filepath, flush=True)
    if "--out" in argv:
        bpy.ops.wm.save_as_mainfile(filepath=argv[argv.index("--out") + 1])
    if "--glb" in argv:
        bpy.ops.export_scene.gltf(filepath=argv[argv.index("--glb") + 1], export_format="GLB",
                                  use_selection=False)
        print("glb saved")


if __name__ == "__main__":
    main()
