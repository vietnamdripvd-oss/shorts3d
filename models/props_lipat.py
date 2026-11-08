"""Showcase props video lipat-ijazah-3d: tiap props turntable 360° bergantian.

  blender -b -P models/props_lipat.py -- --out /path/scene.blend      (lalu render pakai tools/render_frames.py)
  blender -b -P models/props_lipat.py -- --stills models/preview      (render 1 still per props, buat cek cepat)

Di Colab: SLUG = "lipat-props", BUILD_SCRIPT = "models/props_lipat.py".
"""
import bpy, sys, os, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from lib3d import core, toon, camera, props
from lib3d.core import DEG
from mathutils import Vector

# ---- PARAMETER -------------------------------------------------------------
SEG = 45                 # frame per props (1,5 s)
LENS = 40
ELEV = 22 * DEG          # kamera agak dari atas
SKY = "#9fd3ff"
SPACE = "#0b1a3a"
# ---------------------------------------------------------------------------

LIST = [
    # (nama, builder, tilt_x_deg, space?)
    ("ijazah", lambda: props.ijazah(), 0, False),
    ("tumpukan_lipat", lambda: props.paper_stack(layers=8), 0, False),
    ("kolom_kertas", lambda: props.paper_column(height=3.0, ticks=10), 0, False),
    ("meja", lambda: props.desk(), 0, False),
    ("hp", lambda: props.phone(), 0, False),
    ("gedung_4_lantai", lambda: props.building(floors=4), 0, False),
    ("tugu", lambda: props.tugu(height=7.0), 0, False),
    ("gunung", lambda: props.mountain(), 0, False),
    ("awan", lambda: props.cloud(), 0, False),
    ("lup", lambda: props.magnifier(), 0, False),
    ("grafik_batang", lambda: props.bars([1.35 ** n for n in range(14)], max_h=4.0), 0, False),
    ("bumi", lambda: props.earth(r=1.5), 0, True),
    ("garis_karman", lambda: props.karman_ring(r=1.6, thick=0.02), 60, True),
    ("roket", lambda: props.rocket(size=1.0), 0, True),
    ("bulan", lambda: props.moon(r=1.2), 0, True),
    ("bintang", lambda: (lambda o: (o, [o]))(props.starfield(n=300, r_min=2.5, r_max=3.0, size=0.03)), 0, True),
]


def all_parts(root):
    out = []
    for o in root.children_recursive if hasattr(root, "children_recursive") else root.children:
        if o.type == "MESH":
            out.append(o)
    if root.type == "MESH":
        out.append(root)
    return out


def bounds(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        pts += [mw @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    r = max(math.hypot(p.x, p.y) for p in pts)
    zmin, zmax = min(p.z for p in pts), max(p.z for p in pts)
    return r, zmin, zmax


def key_vis(objs, f0, f1):
    for o in objs:
        for f, hide in ((1, True), (f0, False), (f1 + 1, True)):
            if f < 1:
                continue
            o.hide_render = hide
            o.hide_viewport = hide
            o.keyframe_insert("hide_render", frame=f)
            o.keyframe_insert("hide_viewport", frame=f)


def const_interp(idblock):
    ad = idblock.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sc = core.reset_scene()
    toon.setup_render(sc, res=(1080, 1920), fps=30, samples=16)
    world = toon.setup_world(sc, SKY, ambient=0.3)
    toon.add_sun(rot=(50 * DEG, 0, 30 * DEG), energy=4.0)
    cam, tgt = camera.add_camera(loc=(0, -10, 2), target=(0, 0, 1), lens=LENS)
    bg = [n for n in world.node_tree.nodes if n.type == "BACKGROUND"]
    bg_cam = max(bg, key=lambda n: n.inputs["Strength"].default_value)  # strength 1 = yang dilihat kamera

    vh = 2 * math.atan(cam.data.sensor_height / 2 / LENS)
    hh = 2 * math.atan(cam.data.sensor_height * 9 / 16 / 2 / LENS)

    stills = []
    for i, (name, build, tilt, space) in enumerate(LIST):
        f0, f1 = i * SEG + 1, (i + 1) * SEG
        root, parts = build()
        if tilt:
            root.rotation_euler.x = tilt * DEG
        bpy.context.view_layer.update()
        objs = all_parts(root)
        r, zmin, zmax = bounds(objs)
        zc, half_h = (zmin + zmax) / 2, (zmax - zmin) / 2
        d = max(half_h / math.tan(vh / 2), r / math.tan(hh / 2)) * 1.2 + r
        cam.location = (0, -d * math.cos(ELEV), zc + d * math.sin(ELEV))
        tgt.location = (0, 0, zc)
        cam.keyframe_insert("location", frame=f0)
        tgt.keyframe_insert("location", frame=f0)
        bg_cam.inputs["Color"].default_value = toon._hex(SPACE if space else SKY)
        bg_cam.inputs["Color"].keyframe_insert("default_value", frame=f0)
        # turntable: root muter 360 (rotasi z global lewat empty pemutar)
        spin = bpy.data.objects.new(f"spin_{name}", None)
        sc.collection.objects.link(spin)
        root.parent = spin
        spin.rotation_euler = (0, 0, 0)
        spin.keyframe_insert("rotation_euler", frame=f0, index=2)
        spin.rotation_euler = (0, 0, 2 * math.pi)
        spin.keyframe_insert("rotation_euler", frame=f1, index=2)
        for fc in spin.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
        key_vis(objs, f0, f1)
        stills.append((name, f0 + SEG // 8))
        print(f"[props] {name}: frame {f0}-{f1}, tris {core.tri_count(objs)}", flush=True)

    const_interp(cam); const_interp(tgt)
    if world.node_tree.animation_data:
        const_interp(world.node_tree)
    sc.frame_start, sc.frame_end = 1, len(LIST) * SEG

    if "--out" in argv:
        bpy.ops.wm.save_as_mainfile(filepath=argv[argv.index("--out") + 1])
        print("saved", argv[argv.index("--out") + 1])
    if "--stills" in argv:
        out = argv[argv.index("--stills") + 1]
        os.makedirs(out, exist_ok=True)
        sc.render.resolution_percentage = 25
        for ls in sc.view_layers[0].freestyle_settings.linesets:
            ls.linestyle.thickness *= 0.25
        sc.eevee.taa_render_samples = 4
        for name, f in stills:
            sc.frame_set(f)
            sc.render.filepath = os.path.join(out, f"prop_{name}.png")
            bpy.ops.render.render(write_still=True)
            print("still", name, flush=True)


main()
