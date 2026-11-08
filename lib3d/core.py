"""Util umum: reset scene, primitive low-poly, keyframe helper."""
import bpy
import math


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def _finish(obj, name, smooth, loc):
    obj.name = name
    obj.data.name = name
    obj.location = loc
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def _new_mesh(op, name, smooth, loc, **kw):
    op(**kw)
    return _finish(bpy.context.active_object, name, smooth, loc)


def sphere(name, r=1.0, seg=16, rings=10, loc=(0, 0, 0), smooth=True):
    return _new_mesh(bpy.ops.mesh.primitive_uv_sphere_add, name, smooth, loc,
                     radius=r, segments=seg, ring_count=rings)


def ico(name, r=1.0, sub=2, loc=(0, 0, 0), smooth=False):
    return _new_mesh(bpy.ops.mesh.primitive_ico_sphere_add, name, smooth, loc,
                     radius=r, subdivisions=sub)


def cube(name, size=1.0, loc=(0, 0, 0), bevel=0.0, seg=2):
    o = _new_mesh(bpy.ops.mesh.primitive_cube_add, name, False, loc, size=size)
    if bevel:
        m = o.modifiers.new("bevel", "BEVEL")
        m.width = bevel
        m.segments = seg
    return o


def cylinder(name, r=0.5, depth=1.0, verts=12, loc=(0, 0, 0), smooth=False):
    return _new_mesh(bpy.ops.mesh.primitive_cylinder_add, name, smooth, loc,
                     radius=r, depth=depth, vertices=verts)


def cone(name, r1=0.5, r2=0.0, depth=1.0, verts=8, loc=(0, 0, 0), smooth=False):
    return _new_mesh(bpy.ops.mesh.primitive_cone_add, name, smooth, loc,
                     radius1=r1, radius2=r2, depth=depth, vertices=verts)


def torus(name, R=1.0, r=0.25, maj=16, minr=8, loc=(0, 0, 0), smooth=True):
    return _new_mesh(bpy.ops.mesh.primitive_torus_add, name, smooth, loc,
                     major_radius=R, minor_radius=r, major_segments=maj, minor_segments=minr)


def subsurf(obj, levels=1):
    m = obj.modifiers.new("subsurf", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    return m


def key(obj, path, frame, value, interp="BEZIER", easing="AUTO", index=-1):
    """Set value + keyframe. path bisa 'location', 'rotation_euler', 'scale', dsb."""
    if index >= 0:
        getattr(obj, path)[index] = value
    else:
        setattr(obj, path, value)
    obj.keyframe_insert(path, frame=frame, index=index)
    ad = obj.animation_data or obj.id_data.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            if fc.data_path.endswith(path.split(".")[-1]) and (index < 0 or fc.array_index == index):
                for kp in fc.keyframe_points:
                    if int(kp.co[0]) == frame:
                        kp.interpolation = interp
                        kp.easing = easing


def tri_count(objs=None):
    dg = bpy.context.evaluated_depsgraph_get()
    total = 0
    for o in objs or bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        total += len(me.loop_triangles)
        o.evaluated_get(dg).to_mesh_clear()
    return total


DEG = math.pi / 180
