"""Cetak renderer OpenGL/EGL yang dipakai Blender. 'llvmpipe' = software (CPU), 'NVIDIA'/'Tesla' = GPU."""
import bpy, gpu
bpy.ops.render.render()  # paksa init konteks GPU
try:
    print("[gpu] vendor  :", gpu.platform.vendor_get())
    print("[gpu] renderer:", gpu.platform.renderer_get())
    print("[gpu] version :", gpu.platform.version_get())
except Exception as e:
    print("[gpu] tidak bisa baca info:", e)
