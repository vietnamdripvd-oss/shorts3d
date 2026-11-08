"""Props low-poly toon dari primitive. Semua material lewat lib3d/toon.py.

Setiap builder return (root, parts):
  root  = Empty di pivot props (biasanya alas / bawah tengah), parts ter-parent ke root
  parts = list object mesh
Ukuran dalam "unit scene" (bukan meter asli) — skala dunia nyata diatur di anim.py.
Parameter warna di PALETTE.
"""
import bpy, bmesh, math, random
from mathutils import Vector, noise
from . import core, toon, text
from .core import DEG

PALETTE = {
    "paper": "#fbf7ea", "paper_edge": "#e6dfc8", "ink": "#2a2a35", "gold": "#e8b84a",
    "seal": "#e0484d", "line": "#b9b4a2",
    "wood": "#b9773f", "wood_dark": "#8a5428",
    "phone": "#2b2d42", "screen": "#7fd3ff",
    "bldg": "#ff8a5c", "bldg_trim": "#e8e2d6", "window": "#9fd8ff", "door": "#6b4a3a",
    "tugu": "#f1ece0", "tugu_base": "#d9d2c0", "flame": "#ffcc33",
    "rock": "#8f8aa3", "rock_dark": "#6e6985", "snow": "#ffffff", "flag": "#e0484d",
    "cloud": "#ffffff",
    "ocean": "#2f86e8", "land": "#4cbf63", "ice": "#f4fbff",
    "moon": "#e9e3c9", "crater": "#c9c1a2",
    "karman": "#ffd23f",
    "rocket": "#f4f4f4", "rocket_red": "#e0484d", "rocket_win": "#7fd3ff", "fire": "#ff8a1f",
    "star": "#ffffff",
    "glass": "#cdeeff", "lup_rim": "#2b2d42",
    "bar": "#ffc83d",
}


# ------------------------------------------------------------------ util
def _group(name, parts, loc=(0, 0, 0)):
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root.empty_display_size = 0.3
    for p in parts:
        p.parent = root
    root.location = loc
    return root, parts


def box(name, dims, loc=(0, 0, 0), bottom=False, bevel=0.0, seg=2):
    """Cube dengan dimensi (x, y, z). bottom=True -> pivot di alas."""
    o = core.cube(name, size=1.0, loc=(0, 0, 0))
    me = o.data
    for v in me.vertices:
        v.co.x *= dims[0]; v.co.y *= dims[1]; v.co.z *= dims[2]
        if bottom:
            v.co.z += dims[2] / 2
    o.location = loc
    if bevel:
        m = o.modifiers.new("bevel", "BEVEL")
        m.width = bevel
        m.segments = seg
        m.limit_method = "ANGLE"
    return o


def mesh_obj(name, verts, faces, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    for p in me.polygons:
        p.use_smooth = smooth
    return o


def face_mats(obj, rule, mat):
    """Assign `mat` ke face yang rule(poly_center)==True, outline tetap material terakhir."""
    obj.data.materials.append(mat)
    idx = len(obj.data.materials) - 1
    for p in obj.data.polygons:
        if rule(p.center):
            p.material_index = idx
    om = toon.outline_material()
    names = [m.name if m else "" for m in obj.data.materials]
    if om.name in names and names[-1] != om.name:
        obj.data.materials.pop(index=names.index(om.name))
        obj.data.materials.append(om)
        # face yang tadinya indeks > outline turun 1
        oi = names.index(om.name)
        for p in obj.data.polygons:
            if p.material_index > oi:
                p.material_index -= 1
        if "toon_outline" in obj.modifiers:
            obj.modifiers["toon_outline"].material_offset = len(obj.data.materials) - 1


def T(name):
    return toon.toon_material(f"toon_{name}", PALETTE[name])


def F(name):
    return toon.flat_material(f"flat_{name}", PALETTE[name])


# ------------------------------------------------------------------ kertas
def ijazah(w=1.4, h=1.0, t=0.012, name="ijazah"):
    """Ijazah rebah di bidang XY (muka ke +Z), pivot di tengah bawah kertas."""
    P = []
    paper = box(f"{name}_paper", (w, h, t), bottom=True)
    toon.apply_toon(paper, T("paper"), outline=0.008)
    P.append(paper)
    zt = t + 0.002
    # bingkai emas
    bw = 0.035
    for i, (dx, dy, sx, sy) in enumerate(((0, h / 2 - 0.08, w - 0.16, bw), (0, -h / 2 + 0.08, w - 0.16, bw),
                                         (w / 2 - 0.08, 0, bw, h - 0.16), (-w / 2 + 0.08, 0, bw, h - 0.16))):
        b = box(f"{name}_frame{i}", (sx, sy, 0.004), loc=(dx, dy, zt), bottom=True)
        b.data.materials.append(F("gold"))
        P.append(b)
    # judul (teks yang menempel di objek)
    ttl = text.flat_text(f"{name}_title", "IJAZAH", size=0.16, color=PALETTE["ink"],
                         loc=(0, h * 0.27, zt + 0.005), spacing=1.15)
    P.append(ttl)
    # garis-garis isi
    for i, (ln, y) in enumerate(((0.75, 0.10), (0.6, -0.0), (0.7, -0.1), (0.45, -0.2))):
        l = box(f"{name}_line{i}", (w * ln * 0.75, 0.022, 0.003), loc=(0, y * h, zt), bottom=True)
        l.data.materials.append(F("line"))
        P.append(l)
    # segel merah + pita
    seal = core.cylinder(f"{name}_seal", r=0.1, depth=0.01, verts=16, loc=(w * 0.3, -h * 0.3, zt + 0.006))
    seal.data.materials.append(F("seal"))
    s2 = core.cylinder(f"{name}_seal_in", r=0.065, depth=0.012, verts=16, loc=(w * 0.3, -h * 0.3, zt + 0.008))
    s2.data.materials.append(F("gold"))
    toon.add_outline(seal, 0.006)
    P += [seal, s2]
    return _group(name, P)


def paper_slab(w=1.4, h=1.0, t=0.012, name="paper", color="paper"):
    o = box(name, (w, h, t), bottom=True)
    toon.apply_toon(o, T(color), outline=0.006)
    return o


def paper_stack(layers=8, w=0.7, h=1.0, t=0.03, name="stack"):
    """Tumpukan beberapa lapis (keliatan lapisannya) — buat lipatan awal."""
    P = []
    for i in range(layers):
        c = "paper" if i % 2 == 0 else "paper_edge"
        P.append(paper_slab(w, h, t * 0.92, f"{name}_{i}", c))
        P[-1].location.z = i * t
    return _group(name, P)


def paper_column(height=1.0, w=0.35, d=0.25, ticks=0, name="column"):
    """Tumpukan tinggi = 1 balok (pivot di alas). ticks>0: tanda penggaris di sisi depan."""
    P = []
    col = box(name + "_body", (w, d, height), bottom=True)
    toon.apply_toon(col, T("paper"), outline=0.012)
    P.append(col)
    for i in range(1, ticks):
        tk = box(f"{name}_tick{i}", (w * 0.35, 0.01, height * 0.004), loc=(-w * 0.32, -d / 2 - 0.004, height * i / ticks))
        tk.data.materials.append(F("line"))
        P.append(tk)
    return _group(name, P)


# ------------------------------------------------------------------ rumah tangga
def desk(w=3.0, d=1.8, h=1.2, name="desk"):
    P = []
    top = box(f"{name}_top", (w, d, 0.14), loc=(0, 0, h - 0.14), bottom=True, bevel=0.03)
    toon.apply_toon(top, T("wood"), outline=0.015)
    P.append(top)
    for i, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        leg = core.cylinder(f"{name}_leg{i}", r=0.07, depth=h - 0.14, verts=8,
                            loc=(sx * (w / 2 - 0.2), sy * (d / 2 - 0.2), (h - 0.14) / 2))
        toon.apply_toon(leg, T("wood_dark"), outline=0.01)
        P.append(leg)
    return _group(name, P)


def phone(w=0.72, h=1.5, t=0.08, name="phone"):
    """HP berdiri tegak menghadap -Y, pivot di alas."""
    P = []
    body = box(f"{name}_body", (w, t, h), bottom=True, bevel=0.06, seg=3)
    toon.apply_toon(body, T("phone"), outline=0.012)
    scr = box(f"{name}_screen", (w - 0.1, 0.01, h - 0.2), loc=(0, -t / 2 - 0.003, 0.1), bottom=True, bevel=0.03)
    scr.data.materials.append(toon.toon_material("toon_screen", PALETTE["screen"], rim=0.0))
    cam = core.cylinder(f"{name}_cam", r=0.025, depth=0.01, verts=10, loc=(0, -t / 2 - 0.006, h - 0.06))
    cam.rotation_euler = (90 * DEG, 0, 0)
    cam.data.materials.append(F("phone"))
    P += [body, scr, cam]
    return _group(name, P)


# ------------------------------------------------------------------ kota & alam
def building(floors=4, w=3.0, d=2.4, floor_h=1.0, name="building"):
    """Gedung kotak, pivot di alas tengah, jendela pakai Array modifier."""
    P = []
    H = floors * floor_h
    body = box(f"{name}_body", (w, d, H), bottom=True)
    toon.apply_toon(body, T("bldg"), outline=0.02)
    roof = box(f"{name}_roof", (w + 0.2, d + 0.2, 0.18), loc=(0, 0, H), bottom=True, bevel=0.02)
    toon.apply_toon(roof, T("bldg_trim"), outline=0.012)
    P += [body, roof]
    cols = 3
    win = box(f"{name}_win", (0.5, 0.05, 0.55), loc=(-w / 2 + 0.55, -d / 2 - 0.01, floor_h * 0.3 + floor_h), bottom=True)
    win.data.materials.append(toon.toon_material("toon_window", PALETTE["window"]))
    a1 = win.modifiers.new("ax", "ARRAY"); a1.use_relative_offset = False; a1.use_constant_offset = True
    a1.constant_offset_displace = ((w - 1.1) / (cols - 1), 0, 0); a1.count = cols
    a2 = win.modifiers.new("az", "ARRAY"); a2.use_relative_offset = False; a2.use_constant_offset = True
    a2.constant_offset_displace = (0, 0, floor_h); a2.count = floors - 1
    toon.add_outline(win, 0.01)  # setelah array, biar tiap jendela ber-outline
    door = box(f"{name}_door", (0.6, 0.05, 0.8), loc=(0, -d / 2 - 0.01, 0), bottom=True)
    toon.apply_toon(door, T("door"), outline=0.01)
    # jendela lantai dasar kiri-kanan pintu
    for i, x in enumerate((-w / 2 + 0.55, w / 2 - 0.55)):
        gw = box(f"{name}_gwin{i}", (0.5, 0.05, 0.5), loc=(x, -d / 2 - 0.01, floor_h * 0.3), bottom=True)
        gw.data.materials.append(toon.toon_material("toon_window", PALETTE["window"]))
        toon.add_outline(gw, 0.01)
        P.append(gw)
    P += [win, door]
    return _group(name, P)


def tugu(height=7.0, name="tugu"):
    """Tugu/monumen generik: pelataran berundak, obelisk meruncing, cawan, api emas. Pivot di alas."""
    P = []
    base_h = height * 0.12
    for i, (s, hh) in enumerate(((3.2, 0.35), (2.5, 0.3), (1.8, 0.35))):
        z = sum(x for _, x in ((3.2, 0.35), (2.5, 0.3), (1.8, 0.35))[:i]) * height / 7
        st = box(f"{name}_step{i}", (s * height / 7, s * height / 7, hh * height / 7), loc=(0, 0, z), bottom=True)
        toon.apply_toon(st, T("tugu_base"), outline=0.015)
        P.append(st)
    z0 = 1.0 * height / 7
    shaft_h = height * 0.72
    shaft = core.cone(f"{name}_shaft", r1=0.42 * height / 7, r2=0.24 * height / 7, depth=shaft_h, verts=4,
                      loc=(0, 0, z0 + shaft_h / 2))
    shaft.rotation_euler = (0, 0, 45 * DEG)
    toon.apply_toon(shaft, T("tugu"), outline=0.015)
    ztop = z0 + shaft_h
    cup = core.cone(f"{name}_cup", r1=0.22 * height / 7, r2=0.42 * height / 7, depth=0.25 * height / 7, verts=4,
                    loc=(0, 0, ztop + 0.12 * height / 7))
    cup.rotation_euler = (0, 0, 45 * DEG)
    toon.apply_toon(cup, T("tugu"), outline=0.012)
    fl = core.sphere(f"{name}_flame", r=0.2 * height / 7, seg=10, rings=7, loc=(0, 0, ztop + 0.42 * height / 7))
    fl.scale = (1, 1, 1.5)
    toon.apply_toon(fl, T("flame"), outline=0.01, rim=0.3)
    tip = core.cone(f"{name}_flame_tip", r1=0.14 * height / 7, depth=0.35 * height / 7, verts=8,
                    loc=(0, 0, ztop + 0.68 * height / 7))
    toon.apply_toon(tip, T("flame"), outline=0.01)
    P += [shaft, cup, fl, tip]
    return _group(name, P)


def mountain(R=4.0, H=4.5, sides=9, seed=3, flag=True, name="mountain"):
    """Gunung low-poly bergerigi (2 cincin + puncak), salju di atas. Pivot di alas tengah."""
    rnd = random.Random(seed)
    verts, faces = [], []
    rings = ((R, 0.0), (R * 0.55, H * 0.45), (R * 0.22, H * 0.78))
    for ri, (r, z) in enumerate(rings):
        for i in range(sides):
            a = 2 * math.pi * i / sides + ri * 0.3
            rr = r * rnd.uniform(0.82, 1.12)
            verts.append((rr * math.cos(a), rr * math.sin(a), z + (rnd.uniform(-0.12, 0.12) * H if ri else 0)))
    verts.append((rnd.uniform(-0.1, 0.1) * R, rnd.uniform(-0.1, 0.1) * R, H))
    apex = len(verts) - 1
    for ri in range(len(rings) - 1):
        for i in range(sides):
            a, b = ri * sides + i, ri * sides + (i + 1) % sides
            c, d = (ri + 1) * sides + (i + 1) % sides, (ri + 1) * sides + i
            faces += [(a, b, c), (a, c, d)]
    top = (len(rings) - 1) * sides
    for i in range(sides):
        faces.append((top + i, top + (i + 1) % sides, apex))
    faces.append(tuple(reversed(range(sides))))
    m = mesh_obj(f"{name}_body", verts, faces)
    toon.apply_toon(m, T("rock"), outline=0.03)
    face_mats(m, lambda c: c.z > H * 0.62, T("snow"))
    P = [m]
    if flag:
        pole = core.cylinder(f"{name}_pole", r=0.03 * H / 4.5, depth=0.7 * H / 4.5, verts=6,
                             loc=(verts[apex][0], verts[apex][1], H + 0.3 * H / 4.5))
        toon.apply_toon(pole, T("rock_dark"), outline=0)
        fl = box(f"{name}_flag", (0.4 * H / 4.5, 0.02, 0.25 * H / 4.5),
                 loc=(verts[apex][0] + 0.2 * H / 4.5, verts[apex][1], H + 0.45 * H / 4.5))
        fl.data.materials.append(F("flag"))
        toon.add_outline(fl, 0.008)
        P += [pole, fl]
    return _group(name, P)


def cloud(size=1.0, seed=1, name="cloud"):
    rnd = random.Random(seed)
    P = []
    blobs = ((0, 0, 0, 0.55), (0.55, 0, -0.1, 0.42), (-0.55, 0, -0.12, 0.4), (0.25, 0.05, 0.28, 0.38), (-0.25, -0.05, 0.22, 0.36))
    for i, (x, y, z, r) in enumerate(blobs):
        b = core.sphere(f"{name}_{i}", r=r * size * rnd.uniform(0.9, 1.1), seg=10, rings=7, loc=(x * size, y * size, z * size))
        b.scale = (1, 0.8, 0.85)
        toon.apply_toon(b, T("cloud"), outline=0.012 * size)
        P.append(b)
    return _group(name, P)


# ------------------------------------------------------------------ angkasa
def earth(r=1.0, sub=4, seed=7, name="earth"):
    """Bumi: ico low-poly, benua dari noise per face, es kutub."""
    e = core.ico(f"{name}_body", r=r, sub=sub, smooth=False)
    toon.apply_toon(e, T("ocean"), outline=0.012 * r, rim=0.25)
    off = Vector((seed * 1.7, seed * 0.3, -seed))
    face_mats(e, lambda c: noise.noise(c / r * 1.6 + off) > 0.08 and abs(c.z) < 0.82 * r, T("land"))
    face_mats(e, lambda c: abs(c.z) > 0.86 * r, T("ice"))
    return _group(name, [e])


def moon(r=1.0, seed=5, name="moon"):
    rnd = random.Random(seed)
    m = core.ico(f"{name}_body", r=r, sub=2, smooth=False)
    toon.apply_toon(m, T("moon"), outline=0.012 * r)
    P = [m]
    for i in range(9):
        th, ph = rnd.uniform(0, 2 * math.pi), math.acos(rnd.uniform(-1, 1))
        n = Vector((math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph)))
        cr = rnd.uniform(0.1, 0.24) * r
        c = core.sphere(f"{name}_crater{i}", r=cr, seg=10, rings=6, loc=tuple(n * r * 0.93))
        c.scale = (1, 1, 0.12)
        c.rotation_mode = "QUATERNION"
        c.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(n)
        toon.apply_toon(c, T("crater"), outline=0)
        P.append(c)
    return _group(name, P)


def karman_ring(r=1.0, thick=0.01, dashes=48, name="karman"):
    """Cincin putus-putus (garis batas angkasa) di bidang XY."""
    bm = bmesh.new()
    seg = dashes * 2
    rows = 4
    # torus manual, segmen ganjil dilewati -> putus-putus
    verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for j in range(rows):
            b = 2 * math.pi * j / rows
            rr = r + thick * math.cos(b)
            verts.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), thick * math.sin(b))))
    for i in range(seg):
        if i % 2:
            continue
        for j in range(rows):
            a0, a1 = i * rows + j, i * rows + (j + 1) % rows
            b0, b1 = ((i + 1) % seg) * rows + j, ((i + 1) % seg) * rows + (j + 1) % rows
            bm.faces.new((verts[a0], verts[b0], verts[b1], verts[a1]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(F("karman"))
    return _group(name + "_root", [o])


def rocket(size=1.0, name="rocket"):
    """Roket menghadap +Z, pivot di tengah badan. Api = part '<name>_fire'."""
    s = size
    P = []
    body = core.cylinder(f"{name}_body", r=0.25 * s, depth=1.0 * s, verts=12, loc=(0, 0, 0), smooth=True)
    toon.apply_toon(body, T("rocket"), outline=0.012 * s, rim=0.2)
    nose = core.cone(f"{name}_nose", r1=0.25 * s, depth=0.5 * s, verts=12, loc=(0, 0, 0.75 * s))
    for p in nose.data.polygons:
        p.use_smooth = True
    toon.apply_toon(nose, T("rocket_red"), outline=0.012 * s)
    win = core.cylinder(f"{name}_win", r=0.1 * s, depth=0.06 * s, verts=12, loc=(0, -0.24 * s, 0.15 * s))
    win.rotation_euler = (90 * DEG, 0, 0)
    toon.apply_toon(win, T("rocket_win"), outline=0.008 * s)
    P += [body, nose, win]
    for i in range(3):
        a = i * 2 * math.pi / 3 + math.pi / 2
        fin = box(f"{name}_fin{i}", (0.05 * s, 0.3 * s, 0.4 * s),
                  loc=(math.cos(a) * 0.3 * s, math.sin(a) * 0.3 * s, -0.4 * s))
        fin.rotation_euler = (0, 0, a - math.pi / 2)
        toon.apply_toon(fin, T("rocket_red"), outline=0.008 * s)
        P.append(fin)
    noz = core.cone(f"{name}_nozzle", r1=0.2 * s, r2=0.12 * s, depth=0.15 * s, verts=12, loc=(0, 0, -0.55 * s))
    toon.apply_toon(noz, T("rock_dark"), outline=0.008 * s)
    fire = core.cone(f"{name}_fire", r1=0.16 * s, depth=0.6 * s, verts=8, loc=(0, 0, -0.92 * s))
    fire.rotation_euler = (math.pi, 0, 0)
    fire.data.materials.append(F("fire"))
    P += [noz, fire]
    return _group(name, P)


def starfield(n=1200, r_min=40.0, r_max=60.0, size=0.08, seed=11, name="stars"):
    """Bintang = oktahedron kecil emission, satu mesh (ringan). Kulit bola r_min..r_max."""
    rnd = random.Random(seed)
    verts, faces = [], []
    oct_v = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    oct_f = ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5))
    for i in range(n):
        th, ph = rnd.uniform(0, 2 * math.pi), math.acos(rnd.uniform(-1, 1))
        rr = rnd.uniform(r_min, r_max)
        c = (rr * math.sin(ph) * math.cos(th), rr * math.sin(ph) * math.sin(th), rr * math.cos(ph))
        sz = size * rnd.uniform(0.5, 1.6) * rr / r_min
        b = len(verts)
        verts += [(c[0] + x * sz, c[1] + y * sz, c[2] + z * sz) for x, y, z in oct_v]
        faces += [tuple(b + k for k in f) for f in oct_f]
    o = mesh_obj(name, verts, faces)
    o.data.materials.append(F("star"))
    o.visible_shadow = False
    return o


# ------------------------------------------------------------------ alat bantu
def magnifier(r=0.6, name="lup"):
    """Kaca pembesar menghadap -Y, pivot di tengah kaca."""
    rim = core.torus(f"{name}_rim", R=r, r=0.06 * r / 0.6, maj=24, minr=6)
    rim.rotation_euler = (90 * DEG, 0, 0)
    toon.apply_toon(rim, T("lup_rim"), outline=0.01)
    glass = core.cylinder(f"{name}_glass", r=r, depth=0.02, verts=24)
    glass.rotation_euler = (90 * DEG, 0, 0)
    glass.data.materials.append(toon.toon_material("toon_glass", PALETTE["glass"], rim=0.3))
    handle = core.cylinder(f"{name}_handle", r=0.07 * r / 0.6, depth=0.8 * r / 0.6, verts=8,
                           loc=(r * 0.85, 0, -r * 0.85 - 0.25))
    handle.rotation_euler = (0, -45 * DEG, 0)
    toon.apply_toon(handle, T("lup_rim"), outline=0.01)
    return _group(name, [rim, glass, handle])


def bars(values, width=0.3, gap=0.08, max_h=6.0, name="bars", color="bar"):
    """Grafik batang 3D. values -> tinggi dinormalisasi ke max_h. Pivot tengah bawah. Return (root, [bar...])."""
    vmax = max(values) or 1
    P = []
    for i, v in enumerate(values):
        hh = max(v / vmax * max_h, 0.002)
        x = (i - (len(values) - 1) / 2) * (width + gap)
        b = box(f"{name}_{i}", (width, width, 1.0), loc=(x, 0, 0), bottom=True)
        b.scale.z = hh
        toon.apply_toon(b, T(color), outline=0.008)
        P.append(b)
    return _group(name, P)
