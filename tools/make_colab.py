"""Generate render_colab.ipynb.   python3 tools/make_colab.py"""
import json, os

cells = []
def md(s): cells.append({"cell_type": "markdown", "metadata": {}, "source": s.strip("\n").splitlines(True)})
def code(s): cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                           "source": s.strip("\n").splitlines(True)})

md("""
# Render EEVEE (toon) di Colab GPU

1. **Runtime → Change runtime type → T4 GPU**.
2. Repo private → simpan GitHub token (fine-grained, *Contents: Read-only* untuk repo ini) di
   **Colab Secrets** (ikon kunci di sidebar kiri) dengan nama `GH_TOKEN`, nyalakan *Notebook access*.
3. Atur cell **Config**, lalu **Runtime → Run all**.
4. Sesi putus? Sambung lagi, *Run all* lagi — frame yang sudah ada di Google Drive di-skip.
""")
code("""
#@title Config
REPO       = "vietnamdripvd-oss/shorts3d"  #@param {type:"string"}
BRANCH     = "main"   #@param {type:"string"}
SLUG       = "test_e2e"            #@param {type:"string"}
BUILD_SCRIPT = "test_e2e/scene.py" #@param {type:"string"}
RES_PCT    = 50    #@param {type:"integer"}  50 = 540x960 (tes/preview), 100 = 1080x1920 (final)
SAMPLES    = 8     #@param {type:"integer"}  8 tes, 16 final
CHUNK      = 30    #@param {type:"integer"}
AUDIO      = ""    #@param {type:"string"}   wav relatif repo, kosong = bisu
USE_DRIVE  = True  #@param {type:"boolean"}
BLENDER_VER = "4.2.3"
""")
code("""
#@title 1. GPU + Google Drive
!nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
import os
if USE_DRIVE:
    from google.colab import drive
    drive.mount('/content/drive')
    WORK = '/content/drive/MyDrive/shorts3d_render'
else:
    WORK = '/content/shorts3d_render'
os.makedirs(WORK, exist_ok=True)
print('WORK =', WORK)
""")
code("""
#@title 2. Install dependency + EGL NVIDIA (biar EEVEE pakai GPU)
!apt-get -qq update > /dev/null
!apt-get -qq install -y libegl1 libgl1 libglvnd0 libxi6 libxkbcommon0 libxrender1 libsm6 libxxf86vm1 libxfixes3 ffmpeg > /dev/null
import os, glob, json
print('libEGL_nvidia:', glob.glob('/usr/lib64-nvidia/libEGL_nvidia.so*') + glob.glob('/usr/lib/x86_64-linux-gnu/libEGL_nvidia.so*'))
os.makedirs('/usr/share/glvnd/egl_vendor.d', exist_ok=True)
VENDOR = '/usr/share/glvnd/egl_vendor.d/10_nvidia.json'
with open(VENDOR, 'w') as f:
    json.dump({"file_format_version": "1.0.0", "ICD": {"library_path": "libEGL_nvidia.so.0"}}, f)
os.environ['LD_LIBRARY_PATH'] = '/usr/lib64-nvidia:' + os.environ.get('LD_LIBRARY_PATH', '')
os.environ['__EGL_VENDOR_LIBRARY_FILENAMES'] = VENDOR
""")
code("""
#@title 3. Install Blender portable (tarball di-cache di Drive)
mm = '.'.join(BLENDER_VER.split('.')[:2])
tar = f'{WORK}/blender-{BLENDER_VER}-linux-x64.tar.xz'
if not os.path.exists(tar):
    !wget -q -O "{tar}" https://download.blender.org/release/Blender{mm}/blender-{BLENDER_VER}-linux-x64.tar.xz
if not os.path.exists(f'/content/blender-{BLENDER_VER}-linux-x64'):
    !tar xf "{tar}" -C /content
BLENDER = f'/content/blender-{BLENDER_VER}-linux-x64/blender'
!{BLENDER} --version | head -1
""")
code("""
#@title 4. Clone repo (sparse: cuma folder kode, render lama nggak ikut di-download)
try:
    from google.colab import userdata
    TOKEN = userdata.get('GH_TOKEN')
except Exception:
    TOKEN = ''
url = f'https://{TOKEN}@github.com/{REPO}.git' if TOKEN else f'https://github.com/{REPO}.git'
R = '/content/repo'
if os.path.exists(f'{R}/.git'):
    !cd {R} && git fetch -q --depth 1 origin {BRANCH} && git reset -q --hard FETCH_HEAD
else:
    !git clone -q --depth 1 --filter=blob:none --sparse -b {BRANCH} "{url}" {R}
!cd {R} && git sparse-checkout set lib3d tools models rigs assets {SLUG} && git log --oneline -1
""")
code("""
#@title 5. Cek GPU dipakai EEVEE (harus NVIDIA/Tesla, BUKAN llvmpipe)
out = !{BLENDER} -b --factory-startup -P {R}/tools/gpu_info.py 2>&1 | grep -E "\\[gpu\\]|EGL"
print('\\n'.join(out))
if not any('NVIDIA' in l or 'Tesla' in l for l in out):
    print('\\n!! EEVEE TIDAK pakai GPU NVIDIA. Cek Runtime = GPU, restart runtime, Run all lagi.')
""")
code("""
#@title 6. Build scene (.blend) dari script
BLEND = f'{WORK}/{SLUG}/scene.blend'
os.makedirs(f'{WORK}/{SLUG}', exist_ok=True)
!cd {R} && {BLENDER} -b -P {BUILD_SCRIPT} -- --out "{BLEND}" 2>&1 | grep -E "TRIS|saved|Error|Traceback"
""")
code("""
#@title 7. Render per chunk (RESUMABLE) — frame di disk lokal, backup ke Drive
import subprocess, time, json, glob, statistics, shutil
FR = f'/content/frames/{SLUG}/frames_{RES_PCT}_s{SAMPLES}'          # lokal: cepat & stabil
FR_BAK = f'{WORK}/{SLUG}/frames_{RES_PCT}_s{SAMPLES}'               # Drive: cadangan buat resume
os.makedirs(FR, exist_ok=True)

def drive_ok():
    try:
        os.listdir(WORK); return True
    except OSError:
        if USE_DRIVE:
            try:
                drive.mount('/content/drive', force_remount=True); os.listdir(WORK); return True
            except Exception as e:
                print('  (Drive putus, lanjut tanpa backup:', e, ')')
        return False

def backup(names):
    if not USE_DRIVE or not drive_ok():
        return
    try:
        os.makedirs(FR_BAK, exist_ok=True)
        for n in names:
            if not os.path.exists(f'{FR_BAK}/{n}'):
                shutil.copy2(f'{FR}/{n}', f'{FR_BAK}/{n}')
        shutil.copy2(f'{FR}/timing.jsonl', f'{FR_BAK}/timing.jsonl')
    except OSError as e:
        print('  (backup Drive gagal, aman, lanjut:', e, ')')

# resume: tarik frame yang sudah ada di Drive ke lokal
if USE_DRIVE and drive_ok() and os.path.isdir(FR_BAK):
    got = 0
    for p in glob.glob(f'{FR_BAK}/*.png'):
        n = os.path.basename(p)
        if not os.path.exists(f'{FR}/{n}'):
            shutil.copy2(p, f'{FR}/{n}'); got += 1
    print(f'resume: {got} frame ditarik dari Drive')

info = subprocess.run([BLENDER, '-b', BLEND, '--python-expr',
    'import bpy;s=bpy.context.scene;print("RANGE",s.frame_start,s.frame_end)'], capture_output=True, text=True).stdout
fs, fe = [int(x) for x in [l for l in info.splitlines() if l.startswith('RANGE')][0].split()[1:]]
todo = [f for f in range(fs, fe + 1) if not os.path.exists(f'{FR}/{f:05d}.png')]
print(f'frame {fs}-{fe}: {fe-fs+1-len(todo)} sudah ada, {len(todo)} sisa')
t0 = time.time()
for a in range(fs, fe + 1, CHUNK):
    b = min(a + CHUNK - 1, fe)
    names = [f'{f:05d}.png' for f in range(a, b + 1)]
    if all(os.path.exists(f'{FR}/{n}') for n in names):
        continue
    p = subprocess.run([BLENDER, '-b', BLEND, '-P', f'{R}/tools/render_frames.py', '--',
                        '--out', FR, '--start', str(a), '--end', str(b),
                        '--pct', str(RES_PCT), '--samples', str(SAMPLES)], capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout[-2000:], p.stderr[-2000:]); raise SystemExit('render gagal')
    backup(names)
    done = len(glob.glob(f'{FR}/*.png'))
    print(f'  chunk {a}-{b} ok | {done}/{fe-fs+1} frame | {time.time()-t0:.0f}s')
secs = [json.loads(l)['sec'] for l in open(f'{FR}/timing.jsonl')]
if secs:
    print(f'\\nWAKTU/FRAME ({RES_PCT}%, {SAMPLES} samples): median {statistics.median(secs):.2f}s, '
          f'min {min(secs):.2f}s, max {max(secs):.2f}s ({len(secs)} frame)')
""")
code("""
#@title 8. Encode mp4 (lokal) + audio kalau ada, download, salin ke Drive
import shutil
MP4 = f'/content/{SLUG}_{RES_PCT}.mp4'
aud = f'{R}/{AUDIO}' if AUDIO else ''
!bash {R}/tools/encode.sh "{FR}" "{MP4}" {aud}
!ffprobe -v error -show_entries stream=width,height,r_frame_rate:format=duration -of compact "{MP4}"
try:
    if USE_DRIVE and drive_ok():
        os.makedirs(f'{WORK}/{SLUG}/render', exist_ok=True)
        shutil.copy2(MP4, f'{WORK}/{SLUG}/render/')
        print('disalin ke Drive:', f'{WORK}/{SLUG}/render/')
except OSError as e:
    print('(salin ke Drive gagal, file tetap di-download)', e)
from google.colab import files
files.download(MP4)
""")

nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"gpuType": "T4", "provenance": []},
      "kernelspec": {"display_name": "Python 3", "name": "python3"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "render_colab.ipynb")
json.dump(nb, open(out, "w"), indent=1)
print("->", out)
