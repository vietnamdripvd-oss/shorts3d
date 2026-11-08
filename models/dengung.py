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


def _on_surface(x, z, r=BODY_R, sy=0.95):
    """y permukaan depan badan (ellipsoid) di titik x,z."""
    return -sy * math.sqrt(max(r * r - x * x - z * z, 0.0))


def build():
    root = bpy.data.objects.new("dengung_root", None)
    bpy.context.scene.collection.objects.link(root)
    parts = []

    # badan: sphere smooth (tanpa subsurf biar < 5k tris), belang = material per face
    body = core.sphere("body", r=BODY_R, seg=20, rings=18, loc=(0, 0, 0))
    body.scale = (1.0, 0.95, 0.95)
    toon.apply_toon(body, BODY, outline=0.025, rim=0.2)
    stripe_mat = toon.toon_material("toon_stripe", STRIPE)
    body.data.materials.append(stripe_mat)
    si = list(body.data.materials).index(stripe_mat)
    for poly in body.data.polygons:
        z = poly.center.z
        if -0.44 <= z <= -0.26 or -0.70 <= z <= -0.54:
            poly.material_index = si
    # outline material tetap paling akhir (material_offset solidify)
    om = toon.outline_material()
    mats = body.data.materials
    if mats[len(mats) - 1] != om:
        oi = list(mats).index(om)
        mats.pop(index=oi)
        mats.append(om)
        body.modifiers["toon_outline"].material_offset = len(mats) - 1
    parts.append(body)

    # mata sedih + alis miring
    for side in (1, -1):
        x = 0.27 * side
        y = _on_surface(x, 0.15)
        e = core.sphere(f"eye_{side}", r=0.13, seg=12, rings=8, loc=(x, y + 0.03, 0.15))
        e.scale = (1.0, 0.45, 1.15)
        e.data.materials.append(toon.flat_material("eye_white", "#ffffff"))
        toon.add_outline(e, 0.012)
        p = core.sphere(f"pupil_{side}", r=0.065, seg=10, rings=6, loc=(x - 0.02 * side, y - 0.03, 0.12))
        p.scale = (1, 0.45, 1.2)
        p.data.materials.append(toon.flat_material("pupil", "#1a1020"))
        hl = core.sphere(f"eye_hl_{side}", r=0.022, seg=6, rings=4, loc=(x + 0.02, y - 0.06, 0.17))
        hl.data.materials.append(toon.flat_material("eye_hl", "#ffffff"))
        by = _on_surface(x, 0.36)
        brow = core.cube(f"brow_{side}", size=1.0, loc=(x, by - 0.01, 0.36), bevel=0.3, seg=2)
        brow.scale = (0.17, 0.04, 0.035)
        brow.rotation_euler = (0, 0, 0)
        brow.rotation_euler = (0, side * 18 * DEG, 0)   # ujung dalam naik = sedih
        toon.apply_toon(brow, STRIPE, outline=0)
        parts += [e, p, hl, brow]

        # air mata: tetesan gepeng nempel di pipi
        tx = 0.29 * side
        t = core.sphere(f"tear_{side}", r=0.07, seg=10, rings=6, loc=(tx, _on_surface(tx, -0.04) - 0.01, -0.04))
        t.scale = (0.8, 0.35, 1.6)
        t.data.materials.append(toon.flat_material("tear", TEAR))
        toon.add_outline(t, 0.008)
        parts.append(t)

    # mulut: bulat cemberut kecil
    m = core.torus("mouth", R=0.055, r=0.022, maj=12, minr=6, loc=(0, _on_surface(0, -0.12) - 0.005, -0.12))
    m.rotation_euler = (90 * DEG, 0, 0)
    m.scale = (1.0, 1.0, 0.8)
    m.data.materials.append(toon.flat_material("mouth", "#7a2a22"))
    parts.append(m)

    # antena: batang nancep di ubun-ubun, condong keluar, bola di ujung
    for side in (1, -1):
        tilt = 22 * DEG * side
        base = Vector((0.18 * side, 0.0, 0.70))
        L = 0.42
        d = Vector((math.sin(tilt), 0, math.cos(tilt)))
        mid = base + d * (L / 2)
        a = core.cylinder(f"antenna_{side}", r=0.028, depth=L, verts=6, loc=tuple(mid))
        a.rotation_euler = (0, tilt, 0)
        toon.apply_toon(a, ANTENNA, outline=0.008)
        tip = base + d * (L + 0.06)
        ball = core.sphere(f"antenna_tip_{side}", r=0.09, seg=10, rings=6, loc=tuple(tip))
        toon.apply_toon(ball, BODY, outline=0.012)
        parts += [a, ball]

    # sayap: elips tipis di belakang, nongol ke samping & atas
    for side in (1, -1):
        w = core.sphere(f"wing_{side}", r=1.0, seg=14, rings=8, loc=(0.78 * side, 0.35, 0.3))
        w.scale = (0.42, 0.05, 0.3)
        w.rotation_euler = (0, -side * 30 * DEG, side * 20 * DEG)
        toon.apply_toon(w, WING, outline=0.012)
        parts.append(w)

    # kaki
    for side in (1, -1):
        f = core.sphere(f"foot_{side}", r=0.2, seg=10, rings=6, loc=(0.3 * side, -0.1, -0.76))
        f.scale = (1, 1.2, 0.6)
        toon.apply_toon(f, STRIPE, outline=0.015)
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
    cam, tgt = camera.add_camera(loc=(0, -6.2, 0.6), target=(0, 0, 0.15), lens=36)

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
