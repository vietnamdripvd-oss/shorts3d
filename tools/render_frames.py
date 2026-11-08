"""Render frame-per-frame, RESUMABLE (skip frame yang PNG-nya udah ada).

Pakai:
  blender -b scene.blend -P tools/render_frames.py -- \
      --out render/frames --start 1 --end 150 [--pct 50] [--samples 8] [--chunk 0/4]

--chunk i/n : render cuma frame ke-i dari tiap n (buat bagi kerja ke beberapa sesi/GPU).
Log waktu per frame -> <out>/timing.jsonl
"""
import bpy, sys, os, time, json, argparse

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--start", type=int)
ap.add_argument("--end", type=int)
ap.add_argument("--pct", type=int)
ap.add_argument("--samples", type=int)
ap.add_argument("--chunk", default="0/1")
ap.add_argument("--no-freestyle", action="store_true")
a = ap.parse_args(argv)

sc = bpy.context.scene
start = a.start or sc.frame_start
end = a.end or sc.frame_end
if a.pct:
    sc.render.resolution_percentage = a.pct
    if sc.render.use_freestyle:  # garis ikut skala resolusi
        for ls in sc.view_layers[0].freestyle_settings.linesets:
            ls.linestyle.thickness *= a.pct / 100
if a.samples:
    sc.eevee.taa_render_samples = a.samples
if a.no_freestyle:
    sc.render.use_freestyle = False
ci, cn = map(int, a.chunk.split("/"))
os.makedirs(a.out, exist_ok=True)
log = open(os.path.join(a.out, "timing.jsonl"), "a")
print(f"[render] engine={sc.render.engine} {sc.render.resolution_x}x{sc.render.resolution_y}@{sc.render.resolution_percentage}% "
      f"frames {start}-{end} chunk {ci}/{cn}", flush=True)
for f in range(start, end + 1):
    if (f - start) % cn != ci:
        continue
    path = os.path.join(a.out, f"{f:05d}.png")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        continue
    sc.frame_set(f)
    sc.render.filepath = path + ".tmp.png"
    t = time.time()
    bpy.ops.render.render(write_still=True)
    os.replace(path + ".tmp.png", path)   # atomic: frame setengah jadi nggak dianggap selesai
    dt = time.time() - t
    log.write(json.dumps({"frame": f, "sec": round(dt, 3)}) + "\n"); log.flush()
    print(f"[render] frame {f} {dt:.2f}s", flush=True)
print("[render] done", flush=True)
