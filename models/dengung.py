"""Maskot 'dengung' — anak chibi berkostum lebah, low-poly, toon shaded. ORIGINAL (bukan karakter yang sudah ada).

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
HOOD = "#ffc83d"      # tudung & baju kuning madu
STRIPE = "#4a2c16"    # coklat belang / trim
SKIN = "#ffd9c2"
BLUSH = "#ff9a9a"
WING = "#eaf6ff"
TEAR = "#8fd8ff"
EYE = "#1e1420"
HEAD_Z = 1.35         # tinggi pusat kepala (kaki di z=0)
HEAD_R = 0.72         # kepala gede = chibi
# ---------------------------------------------------------------------------


# ellipsoid muka (muka nongol dari lubang tudung)
FACE_C = Vector((0, -0.33, HEAD_Z - 0.06))
FACE_R = Vector((0.56, 0.36, 0.50))


def face_y(x, z, lift=0.0):
    """y permukaan depan muka di titik (x, z)."""
    u = 1 - (x / FACE_R.x) ** 2 - ((z - FACE_C.z) / FACE_R.z) ** 2
    return FACE_C.y - FACE_R.y * math.sqrt(max(u, 0.0)) - lift


def stripes(obj, bands, mat_name="toon_stripe"):
    """Belang = material per face berdasarkan z lokal (band = (zmin, zmax))."""
    m = toon.toon_material(mat_name, STRIPE)
    obj.data.materials.append(m)
    si = list(obj.data.materials).index(m)
    for poly in obj.data.polygons:
        if any(lo <= poly.center.z <= hi for lo, hi in bands):
            poly.material_index = si
    # outline material harus terakhir (material_offset Solidify)
    om = toon.outline_material()
    mats = obj.data.materials
    if om.name in [x.name for x in mats if x]:
        mats.pop(index=[x.name if x else "" for x in mats].index(om.name))
        mats.append(om)
        obj.modifiers["toon_outline"].material_offset = len(mats) - 1


def build():
    root = bpy.data.objects.new("dengung_root", None)
    bpy.context.scene.collection.objects.link(root)
    P = []

    # ---- kepala: tudung + muka --------------------------------------------
    hood = core.sphere("hood", r=HEAD_R, seg=16, rings=10, loc=(0, 0, HEAD_Z))
    hood.scale = (1.05, 0.88, 0.95)
    toon.apply_toon(hood, HOOD, outline=0.025, rim=0.2)
    face = core.sphere("face", r=1.0, seg=16, rings=10, loc=tuple(FACE_C))
    face.scale = tuple(FACE_R)
    toon.apply_toon(face, SKIN, outline=0.015)
    # trim tudung di sekeliling muka
    trim = core.torus("hood_trim", R=0.47, r=0.07, maj=18, minr=5,
                      loc=(0, face_y(0.47, FACE_C.z) + 0.04, FACE_C.z))
    trim.rotation_euler = (90 * DEG, 0, 0)
    trim.scale = (1.0, 0.98, 1.0)
    toon.apply_toon(trim, STRIPE, outline=0.012)
    P += [hood, face, trim]

    # telinga tudung: bola kecil coklat di samping
    for sd in (1, -1):
        ear = core.sphere(f"hood_puff_{sd}", r=0.17, seg=8, rings=6,
                          loc=(0.68 * sd, -0.05, HEAD_Z - 0.18))
        ear.scale = (0.7, 1.0, 1.0)
        toon.apply_toon(ear, STRIPE, outline=0.012)
        P.append(ear)

    # ---- muka -------------------------------------------------------------
    ez = FACE_C.z + 0.04
    for sd in (1, -1):
        x = 0.2 * sd
        # mata: oval hitam tegak + highlight
        e = core.sphere(f"eye_{sd}", r=0.075, seg=8, rings=6, loc=(x, face_y(x, ez, -0.01), ez))
        e.scale = (0.85, 0.4, 1.25)
        e.data.materials.append(toon.flat_material("eye", EYE))
        hl = core.sphere(f"eye_hl_{sd}", r=0.024, seg=6, rings=4,
                         loc=(x + 0.025, face_y(x, ez + 0.04) - 0.04, ez + 0.04))
        hl.data.materials.append(toon.flat_material("eye_hl", "#ffffff"))
        # alis sedih (ujung dalam naik)
        bz = ez + 0.17
        brow = core.cube(f"brow_{sd}", size=1.0, loc=(x, face_y(x, bz, 0.005), bz), bevel=0.3, seg=2)
        brow.scale = (0.12, 0.03, 0.025)
        brow.rotation_euler = (0, sd * 20 * DEG, 0)
        toon.apply_toon(brow, STRIPE, outline=0)
        # pipi merah
        cx, cz = 0.33 * sd, FACE_C.z - 0.12
        bl = core.sphere(f"blush_{sd}", r=0.08, seg=10, rings=6, loc=(cx, face_y(cx, cz, -0.02), cz))
        bl.scale = (1.0, 0.3, 0.6)
        bl.data.materials.append(toon.flat_material("blush", BLUSH))
        # air mata: 2 tetes di bawah mata
        tears = []
        for i, (dz, r) in enumerate(((-0.12, 0.04), (-0.24, 0.032))):
            tx, tz = x + 0.03 * sd, ez + dz
            t = core.sphere(f"tear_{sd}_{i}", r=r, seg=8, rings=6, loc=(tx, face_y(tx, tz, 0.005), tz))
            t.scale = (0.8, 0.4, 1.4)
            t.data.materials.append(toon.flat_material("tear", TEAR))
            tears.append(t)
        P += [e, hl, brow, bl] + tears

    # mulut: cemberut kecil (torus gepeng)
    mz = FACE_C.z - 0.2
    m = core.torus("mouth", R=0.05, r=0.018, maj=12, minr=6, loc=(0, face_y(0, mz, 0.0), mz))
    m.rotation_euler = (90 * DEG, 0, 0)
    m.scale = (1.2, 1.0, 0.7)
    m.data.materials.append(toon.flat_material("mouth", "#7a2a22"))
    P.append(m)

    # ---- antena dari puncak tudung -----------------------------------------
    top = HEAD_Z + HEAD_R * 0.95 - 0.05
    for sd in (1, -1):
        tilt = 25 * DEG * sd
        base = Vector((0.22 * sd, 0.0, top - 0.06))
        L = 0.38
        d = Vector((math.sin(tilt), 0, math.cos(tilt)))
        a = core.cylinder(f"antenna_{sd}", r=0.03, depth=L, verts=6, loc=tuple(base + d * (L / 2)))
        a.rotation_euler = (0, tilt, 0)
        toon.apply_toon(a, STRIPE, outline=0)
        ball = core.sphere(f"antenna_tip_{sd}", r=0.11, seg=8, rings=6, loc=tuple(base + d * (L + 0.07)))
        toon.apply_toon(ball, HOOD, outline=0.012)
        P += [a, ball]

    # ---- badan kecil belang -----------------------------------------------
    body = core.sphere("body", r=0.42, seg=14, rings=10, loc=(0, 0, 0.5))
    body.scale = (1.0, 0.9, 1.05)
    toon.apply_toon(body, HOOD, outline=0.02)
    stripes(body, ((-0.2, -0.06), (0.1, 0.24)))
    P.append(body)

    # tangan pendek
    for sd in (1, -1):
        arm = core.sphere(f"arm_{sd}", r=0.12, seg=8, rings=6, loc=(0.44 * sd, -0.04, 0.58))
        arm.scale = (0.9, 0.9, 1.5)
        arm.rotation_euler = (0, sd * 25 * DEG, 0)
        toon.apply_toon(arm, HOOD, outline=0.012)
        P.append(arm)

    # kaki gendut
    for sd in (1, -1):
        leg = core.sphere(f"leg_{sd}", r=0.15, seg=8, rings=6, loc=(0.17 * sd, -0.04, 0.13))
        leg.scale = (1.0, 1.1, 1.0)
        toon.apply_toon(leg, HOOD, outline=0.012)
        P.append(leg)

    # sayap di punggung
    for sd in (1, -1):
        w = core.sphere(f"wing_{sd}", r=1.0, seg=10, rings=6, loc=(0.42 * sd, 0.42, 0.78))
        w.scale = (0.34, 0.04, 0.26)
        w.rotation_euler = (0, -sd * 25 * DEG, -sd * 25 * DEG)
        toon.apply_toon(w, WING, outline=0.01)
        P.append(w)

    # sengat
    st = core.cone("stinger", r1=0.08, r2=0.0, depth=0.18, verts=8, loc=(0, 0.42, 0.33))
    st.rotation_euler = (-90 * DEG, 0, 0)
    toon.apply_toon(st, STRIPE, outline=0.008)
    P.append(st)

    for o in P:
        o.parent = root
    return root, P


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sc = core.reset_scene()
    toon.setup_render(sc, res=(540, 960), fps=30, samples=8, freestyle=True)
    toon.setup_world(sc, "#7cc4ff", ambient=0.3)
    toon.add_sun(rot=(50 * DEG, 0, 30 * DEG), energy=4.0)
    root, parts = build()
    cam, tgt = camera.add_camera(loc=(0, -7.0, 1.4), target=(0, 0, 1.0), lens=40)

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
