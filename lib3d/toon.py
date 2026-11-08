"""Toon shading pipeline — WAJIB dipakai semua objek.

Isi:
  setup_render(scene, ...)   -> EEVEE, Standard view transform, Freestyle, flat look
  setup_world(scene, color)  -> world flat (kamera lihat warna penuh, ambient kecil)
  add_sun(...)               -> 1 sun light utama, shadow tegas
  toon_material(name, color) -> Diffuse -> ShaderToRGB -> ColorRamp(CONSTANT) -> Mix base -> Emission (+rim)
  outline_material()         -> material hitam, backface culling (dipakai Solidify inverted hull)
  add_outline(obj, ...)      -> Solidify flip normals + material outline
  apply_toon(obj, color)     -> shortcut: assign toon material + outline

Target Blender 4.2 LTS (EEVEE Next). Kode dijaga pakai hasattr supaya aman di 4.1/4.3+.
"""
import bpy

EEVEE = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in {
    e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
} else "BLENDER_EEVEE"

# Step default (posisi, nilai gelap-terang). 3 step: shadow / mid / light.
DEFAULT_STEPS = ((0.0, 0.45), (0.25, 0.75), (0.6, 1.0))


def _hex(c):
    """Terima '#RRGGBB' atau tuple 3/4 (sRGB 0..1). Return RGBA linear."""
    if isinstance(c, str):
        c = c.lstrip("#")
        c = tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
    c = tuple(c)

    def lin(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    rgb = tuple(lin(v) for v in c[:3])
    return (*rgb, c[3] if len(c) > 3 else 1.0)


def _set(obj, attr, val):
    if hasattr(obj, attr):
        try:
            setattr(obj, attr, val)
        except Exception:
            pass


# ---------------------------------------------------------------- render
def setup_render(scene=None, res=(1080, 1920), fps=30, samples=16,
                 freestyle=True, line_px=3.0, pct=100):
    scene = scene or bpy.context.scene
    r = scene.render
    r.engine = EEVEE
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = pct
    r.fps = fps
    r.film_transparent = False
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGB"

    ee = scene.eevee
    _set(ee, "taa_render_samples", samples)
    _set(ee, "taa_samples", 4)
    # flat ala kartun: matikan efek yang bikin "realistis"
    for a in ("use_bloom", "use_gtao", "use_ssr", "use_motion_blur",
              "use_raytracing", "use_volumetric_shadows", "use_shadow_jitter_viewport"):
        _set(ee, a, False)
    _set(ee, "use_shadows", True)
    _set(ee, "shadow_ray_count", 1)
    _set(ee, "shadow_step_count", 4)
    _set(ee, "shadow_cube_size", "1024")
    _set(ee, "shadow_cascade_size", "2048")
    _set(ee, "shadow_resolution_scale", 1.0)
    _set(ee, "shadow_pool_size", "1024")
    _set(ee, "use_soft_shadows", False)
    _set(r, "use_motion_blur", False)

    vs = scene.view_settings
    vs.view_transform = "Standard"
    vs.look = "None"
    vs.exposure = 0.0
    vs.gamma = 1.0
    scene.display_settings.display_device = "sRGB"

    r.use_freestyle = freestyle
    if freestyle:
        setup_freestyle(scene, line_px * (res[0] * pct / 100) / 1080)
    return scene


def setup_freestyle(scene, thickness=3.0, color=(0.03, 0.02, 0.04)):
    r = scene.render
    r.line_thickness_mode = "ABSOLUTE"
    r.line_thickness = 1.0
    vl = scene.view_layers[0]
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    fs.crease_angle = 1.75  # ~100 deg: crease cuma di sudut tajam
    if not fs.linesets:
        fs.linesets.new("toon_lines")
    ls = fs.linesets[0]
    ls.select_by_visibility = True
    ls.select_by_edge_types = True
    ls.select_by_collection = False
    ls.visibility = "VISIBLE"
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = True
    ls.select_contour = True
    ls.select_external_contour = True
    ls.exclude_border = False
    # objek dengan nama berawalan "nofs_" bisa di-exclude lewat collection kalau perlu
    style = ls.linestyle or bpy.data.linestyles.new("toon_ink")
    ls.linestyle = style
    style.color = color
    style.thickness = thickness
    style.thickness_position = "CENTER"
    style.caps = "ROUND"
    style.chaining = "PLAIN"
    return ls


# ---------------------------------------------------------------- world & light
def setup_world(scene=None, color="#9fd3ff", ambient=0.25):
    """Background flat. Kamera lihat `color` penuh; lighting cuma dapat `ambient`."""
    scene = scene or bpy.context.scene
    w = scene.world or bpy.data.worlds.new("World")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg_cam = nt.nodes.new("ShaderNodeBackground")
    bg_cam.inputs["Color"].default_value = _hex(color)
    bg_cam.inputs["Strength"].default_value = 1.0
    bg_amb = nt.nodes.new("ShaderNodeBackground")
    bg_amb.inputs["Color"].default_value = (1, 1, 1, 1)
    bg_amb.inputs["Strength"].default_value = ambient
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(bg_amb.outputs[0], mix.inputs[1])
    nt.links.new(bg_cam.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return w


def add_sun(rot=(0.75, 0.15, 0.6), energy=4.0, angle_deg=0.5, name="Sun"):
    data = bpy.data.lights.new(name, "SUN")
    data.energy = energy
    data.angle = angle_deg * 3.14159 / 180  # kecil = bayangan tegas
    _set(data, "use_shadow", True)
    _set(data, "use_contact_shadow", False)
    _set(data, "shadow_cascade_count", 2)
    _set(data, "shadow_maximum_resolution", 0.0008)  # EEVEE Next: lebih kecil = tepi bayangan lebih rapi
    _set(data, "shadow_filter_radius", 0.5)
    _set(data, "shadow_jitter", False)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.rotation_euler = rot
    return obj


# ---------------------------------------------------------------- materials
def toon_material(name, color, steps=DEFAULT_STEPS, rim=0.0, rim_color="#ffffff",
                  shadow_tint="#3a2a6a", tint_amt=0.35):
    """Material toon.

    color      : warna dasar (hex/sRGB)
    steps      : ((pos, value), ...) Color Ramp CONSTANT 2-3 step
    rim        : 0 = mati; 0.1-0.4 = rim light tipis
    shadow_tint: bayangan nggak cuma gelap, tapi agak ungu biar kartun
    """
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new

    out = N("ShaderNodeOutputMaterial"); out.location = (1200, 0)
    diff = N("ShaderNodeBsdfDiffuse"); diff.location = (-600, 0)
    diff.inputs["Color"].default_value = (1, 1, 1, 1)
    s2r = N("ShaderNodeShaderToRGB"); s2r.location = (-400, 0)
    ramp = N("ShaderNodeValToRGB"); ramp.location = (-200, 0)
    cr = ramp.color_ramp
    cr.interpolation = "CONSTANT"
    while len(cr.elements) < len(steps):
        cr.elements.new(0.5)
    for el, (pos, val) in zip(cr.elements, steps):
        el.position = pos
        el.color = (val, val, val, 1)

    base = _hex(color)
    tint = _hex(shadow_tint)
    # step gelap di-tint (bayangan agak ungu, bukan abu-abu kusam)
    for el, (pos, val) in zip(cr.elements, steps):
        k = (1 - val) * tint_amt * 2.0
        el.color = tuple(val * (1 - k) + val * t * 2.2 * k for t in tint[:3]) + (1,)

    # Mix (MULTIPLY): warna dasar x hasil ramp
    mul = N("ShaderNodeMix"); mul.location = (300, 0)
    mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
    mul.inputs[0].default_value = 1.0
    mul.inputs[6].default_value = base

    L(diff.outputs[0], s2r.inputs[0])
    L(s2r.outputs["Color"], ramp.inputs["Fac"])
    L(ramp.outputs["Color"], mul.inputs[7])
    last = mul.outputs[2]

    if rim > 0:
        lw = N("ShaderNodeLayerWeight"); lw.location = (-400, -300)
        lw.inputs["Blend"].default_value = 0.35
        rr = N("ShaderNodeValToRGB"); rr.location = (-200, -300)
        rr.color_ramp.interpolation = "CONSTANT"
        rr.color_ramp.elements[0].color = (0, 0, 0, 1)
        rr.color_ramp.elements[1].position = 0.55
        rr.color_ramp.elements[1].color = (rim, rim, rim, 1)
        rc = N("ShaderNodeMix"); rc.location = (300, -300)
        rc.data_type = "RGBA"; rc.blend_type = "MULTIPLY"; rc.inputs[0].default_value = 1
        rc.inputs[7].default_value = _hex(rim_color)
        add = N("ShaderNodeMix"); add.location = (500, 0)
        add.data_type = "RGBA"; add.blend_type = "ADD"; add.inputs[0].default_value = 1
        L(lw.outputs["Facing"], rr.inputs["Fac"])
        L(rr.outputs["Color"], rc.inputs[6])
        L(last, add.inputs[6]); L(rc.outputs[2], add.inputs[7])
        last = add.outputs[2]

    emi = N("ShaderNodeEmission"); emi.location = (900, 0)
    emi.inputs["Strength"].default_value = 1.0
    L(last, emi.inputs["Color"])
    L(emi.outputs[0], out.inputs["Surface"])
    mat.diffuse_color = base  # warna di viewport
    return mat


def flat_material(name, color, strength=1.0):
    """Emission polos (buat mata putih, pupil, teks, highlight) — tetap 'toon' tanpa gradasi."""
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = _hex(color)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    mat.diffuse_color = _hex(color)
    return mat


def outline_material(color=(0.03, 0.02, 0.04)):
    mat = bpy.data.materials.get("toon_outline")
    if mat:
        return mat
    mat = flat_material("toon_outline", color)
    mat.use_backface_culling = True
    _set(mat, "use_backface_culling_shadow", True)
    _set(mat, "shadow_method", "NONE")
    _set(mat, "surface_render_method", "DITHERED")
    return mat


def add_outline(obj, thickness=0.02):
    """Inverted hull: Solidify (flip normals, offset keluar) + material outline backface-cull."""
    if obj.type != "MESH" or "toon_outline" in obj.modifiers:
        return
    om = outline_material()
    if om.name not in obj.data.materials:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(None)
        obj.data.materials.append(om)
    idx = list(obj.data.materials).index(om)
    m = obj.modifiers.new("toon_outline", "SOLIDIFY")
    m.thickness = -abs(thickness)   # negatif + offset 1 -> keluar
    m.offset = 1.0
    m.use_flip_normals = True
    m.use_rim = False
    m.material_offset = idx
    m.use_quality_normals = True
    _set(obj, "visible_shadow", True)


def apply_toon(obj, color, outline=0.02, **kw):
    """Shortcut: material toon di slot 0 + outline."""
    mat = color if isinstance(color, bpy.types.Material) else toon_material(
        kw.pop("name", f"toon_{obj.name}"), color, **kw)
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    if outline:
        add_outline(obj, outline)
    return mat
