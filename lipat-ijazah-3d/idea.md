# Lipat Ijazah 42x — remake 3D

Remake 3D dari video 2D `youtube-shorts-explainer/lipat-kertas/ijazah` (versi ElevenLabs).
**VO dan durasi tidak berubah:** VO `vo/vo.mp3` (54,1 s), video 56 s, timing per baris di `timeline.json`.

## Hook (0–2,5 s, tipe: angka + pertanyaan)
"Ijazah ini dilipet empat puluh dua kali... nyampe BULAN?!"
Visual detik 0: ijazah pop-in + teks 3D "42×" nge-slam, snap zoom, Bulan nongol di langit.

## Cek fakta (tebal awal 0,1 mm, tebal = 0,1 mm × 2^n)
| Lipatan | Hitungan | Di VO | Pembanding |
|---|---|---|---|
| 10 | 102 mm | 10 senti | HP ±15 cm ✓ |
| 17 | 13,1 m | 13 meter | gedung 4 lantai (±3,3 m/lantai) ✓ |
| 21 | 209,7 m | 210 meter | Monas 132 m ✓ |
| 27 | 13,4 km | 13 kilo | Everest 8.849 m ✓ |
| 30 | 107,4 km | 107 kilo | garis Kármán 100 km ✓ |
| 42 | 439.805 km | 440 ribu kilo | jarak rata-rata Bulan 384.400 km ✓ |
| — | — | rekor 12 kali | Britney Gallivan, 2002 ✓ |

## Kenapa 3D lebih jelas
- **Lipatan beneran:** separuh kertas muter di engsel, dan tumpukannya kelihatan makin tebal dari samping. Versi 2D cuma bisa niru pakai perspektif palsu.
- **Skala vertikal:** kamera *crane* naik ngikutin tumpukan, ngelewatin gedung, tugu, gunung, sampai lengkung Bumi. Rasa tingginya dapet, bukan cuma garis di layar.
- **Ruang angkasa:** Bumi dan Bulan beneran bola, jaraknya ditunjukin pakai *dolly out* panjang. Tumpukan nembus lewat samping Bulan.
- **Grafik eksponensial 3D:** 42 batang naik, kamera nyapu dari depan ke samping.

## Pemain
- **Dengung** (maskot lebah, sudah di-approve) — reaksi: panik ijazahnya dilipet, kaget, nangis, sombong, mentok di CTA.

## Objek (semua primitive)
ijazah (cube tipis + border + teks), tumpukan kertas (cube bertingkat), meja, HP (cube bevel),
gedung 4 lantai (cube + jendela array), tugu ala Monas (cylinder/cone + api), gunung (cone/ico low-poly + salju),
awan (sphere cluster), Bumi (ico + benua sphere gepeng), garis Kármán (torus tipis), roket (cylinder + cone),
Bulan (ico + kawah sphere), bintang (instanced ico kecil), batang grafik (cube array), teks 3D (FONT object).

## Estimasi
56 s = 1.680 frame. Colab T4 final 1080x1920: ±1–2 s/frame → ±30–60 menit. Preview 540x960: ±10 menit.
Berat: **sedang** (banyak ganti setting, teks 3D, ribuan bintang di-instance).
