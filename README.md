# shorts3d — pipeline YouTube Shorts edukasi 3D (100% kode)

Semua visual dibikin pakai **Blender Python API headless** (`blender -b -P`) + **ffmpeg**.
Tanpa generative video/3D, tanpa sculpting manual, tanpa download model.

- Gaya: low-poly / maskot bulat, **toon shaded** (dari primitive + modifier).
- Engine: **EEVEE** selalu (Blender 4.2 LTS = EEVEE Next). Bukan Workbench/Cycles.
- Output: 1080x1920, 30 fps, ≤ 60 detik.

## Struktur

```
lib3d/            helper umum
  toon.py         render setup (EEVEE, Standard, Freestyle), world flat, sun, toon material, outline
  core.py         reset scene, primitive low-poly, keyframe helper, hitung tris
  camera.py       kamera vertikal + track target + zoom lens
  materials.py    (TAHAP 4) palet & material tambahan
  mascot.py       (TAHAP 4) builder maskot + rig dasar
  props.py        (TAHAP 4) props dari primitive
  actions.py      (TAHAP 6) library aksi: idle, talk, blink, point, wave, kaget, dst
  text.py         (TAHAP 6) teks di layar
models/           model + rig dasar (.py, .blend, .glb, preview/)
rigs/             rig turunan per video
tools/
  render_frames.py  render per frame, RESUMABLE, --chunk i/n, log timing.jsonl
  encode.sh         PNG -> mp4 (h264 yuv420p, + audio opsional)
  blender_run.sh    wrapper: pakai display kalau ada, kalau nggak xvfb
  gpu_info.py       cek renderer GL yang dipakai (NVIDIA vs llvmpipe)
  install_local.sh  install Blender 4.2.3 + ffmpeg + EGL di Ubuntu
render_colab.ipynb  render EEVEE di Colab GPU (resume via Google Drive)
test_e2e/         tes TAHAP 0 (scene.py, render.sh, render/test_e2e.mp4)
<slug>/           per video: idea.md, script.md, storyboard.md, timeline.json, vo/, anim.py, render.sh, render/
```

## Toon shader (`lib3d/toon.py`)

```
Diffuse BSDF ─► Shader to RGB ─► Color Ramp (CONSTANT, 3 step: shadow/mid/light, step gelap di-tint ungu)
                                        └─► Mix MULTIPLY × warna dasar ─► (+ rim) ─► Emission ─► Output
Rim (opsional): Layer Weight.Facing ─► Color Ramp CONSTANT ─► × rim color ─► Mix ADD
Outline: Solidify (thickness negatif, flip normals, material_offset → "toon_outline" hitam, backface culling)
       + Freestyle (silhouette/border/crease/contour, round caps, tebal skala resolusi)
Lighting: 1 Sun (angle 0.5°, shadow tegas, shadow map resolusi tinggi) + world flat
          (Light Path: kamera lihat warna langit penuh, ambient cuma 0.25)
Flat look: bloom/AO/SSR/raytracing/motion blur OFF. View Transform = Standard, Look = None.
```

Pakai: `toon.apply_toon(obj, "#ff8a3d", outline=0.02, rim=0.25)`; benda tanpa gradasi (mata, pupil): `toon.flat_material(...)`.

## Instalasi

**Opsi 1 — Colab GPU (utama, buat final):** buka `render_colab.ipynb` di Colab, Runtime = T4 GPU,
isi `REPO_URL` (+ `GH_TOKEN` kalau private), *Run all*. Frame disimpan di Google Drive →
kalau sesi putus, *Run all* lagi, frame yang sudah ada di-skip. Cell 5 mengecek EEVEE beneran pakai GPU
(harus muncul NVIDIA/Tesla, bukan `llvmpipe`).

**Opsi 2 — PC lokal dengan GPU (Linux):** `tools/install_local.sh`, lalu `test_e2e/render.sh`.
Windows/Mac: install Blender 4.2 LTS biasa, jalankan perintah `blender -b ...` yang sama.

**Opsi 3 — cloud CPU (cuma buat tes):** sama dengan opsi 2; tanpa GPU, Blender 4.2 jalan pakai
Mesa EGL **llvmpipe** (software OpenGL). Perlu paket `libegl1 libegl-mesa0`.
Catatan: Blender 4.2 mode `-b` selalu pakai EGL, jadi `xvfb` sebenarnya nggak wajib — yang wajib libEGL.

## Tes end-to-end (TAHAP 0)

```bash
test_e2e/render.sh 100     # build scene + render 150 frame + encode
```
Scene: maskot oranye bulat (armature: root/body/head/eye_L/R/arm_L/R/mouth, rigid parenting) di atas
planet low-poly (ico sub 2) + pohon kerucut + batu. Hook: pop-in overshoot + snap zoom di 0,4 detik pertama,
lalu muter 360°, kedip 3x, lompat, lambai, mulut gerak. Maskot ≈ 4,4k tris (termasuk hull outline).

### Waktu render per frame (EEVEE, 1080x1920, 16 samples, Freestyle ON)

| Mesin | Renderer GL | Detik/frame | 5 detik (150 fr) | 60 detik (1800 fr) |
|---|---|---|---|---|
| Cloud CPU 4 vCPU (session ini) | Mesa llvmpipe | ~20 (median 20,4; min 16,4; frame-1 incl. compile 21–45) | ~50 menit | ~10 jam |
| Colab T4 GPU | NVIDIA EGL | belum diukur — jalankan notebook, angka keluar di cell 7 | | |

Frame pertama tiap proses lebih lama (compile shader), jadi `CHUNK` di notebook dibuat 30 frame.
