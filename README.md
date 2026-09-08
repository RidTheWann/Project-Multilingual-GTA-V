# Proyek Terjemahan Bahasa Indonesia — Grand Theft Auto V

Selamat datang di repositori **GTA V Indonesian Localization Project** (Proyek Lokalisasi Bahasa Indonesia untuk Grand Theft Auto V).

Repositori ini bertujuan untuk menghadirkan lokalisasi bahasa Indonesia resmi, berkualitas tinggi, konsisten, dan alami untuk game Grand Theft Auto V, dengan memprioritaskan keselamatan format internal game Rockstar.

---

## Ringkasan Proyek

- **Bahasa Target**: Bahasa Indonesia (Indonesian)
- **Format File**: `.oxt` (OpenIV Text Format)
- **Encoding**: UTF-8 with BOM (`utf-8-sig`)
- **Format Baris**: Windows CRLF (`\r\n`)
- **Jumlah File**: 610 file teks
- **Jumlah Entri Sumber**: 284.927 baris terjemahan

---

## Aturan Utama (The Absolute Immutable Rule)

> [!CAUTION]
> **HANYA TEKS SETELAH TANDA SAMA DENGAN ("=") PERTAMA YANG BOLEH DITERJEMAHKAN.**
>
> Bagian sebelum tanda `=` (Key, Indentasi, Spasi, dan Format Sintaks) **TIDAK BOLEH DIUBAH SAMA SEKALI**.
> 
> ```ini
> # CONTOH SUMBER
> 	HUD_PAUSE = Resume Game
> 
> # CONTOH BENAR
> 	HUD_PAUSE = Lanjutkan Permainan
> 
> # CONTOH SALAH (Key diubah)
> 	HUD_PAUSE_ID = Lanjutkan Permainan
> ```

Setiap file `.oxt` harus mempertahankan token Rockstar (`~s~`, `~INPUT_...~`, `~HUD_COLOUR_...~`), placeholder argumen (`%s`, `%d`, `{0}`), dan tag gambar (`<img ... />`) secara utuh.

---

## Struktur Direktori

```
project_multilingual_gtav/
├── AGENTS.md                   # Panduan teknis & standar pengerjaan untuk Agen/Kontributor
├── PROGRESS.md                 # Pelacakan progres, status audit, & metrik terjemahan
├── README.md                   # Dokumentasi utama proyek
├── validate.py                 # Validasi integritas key, encoding, format, & token
├── translate.py                # Pipeline penerjemahan otomatis berbasis glossary & token shield
├── locales/
│   ├── original/               # 610 file .oxt asli bahasa Inggris (Pristine Source)
│   │   └── *.oxt
│   ├── id/                     # File .oxt hasil lokalisasi Bahasa Indonesia
│   │   └── *.oxt
│   └── cache/                  # Cache terjemahan (resumable)
├── tools/
│   ├── glossary.py             # Kamus istilah resmi & pola direktif misi GTA V
│   └── token_shield.py         # Ekstraktor & pelindung token/placeholder
└── reports/
    └── validation_report.json  # Hasil audit validasi berkala
```

---

## Panduan Penggunaan & Tooling

### Persyaratan
- Python 3.8 atau lebih baru (tidak memerlukan pustaka eksternal tambahan; menggunakan standard library).

### 1. Menjalankan Penerjemahan
Untuk memproses file tertentu:
```bash
python translate.py --files prolog.oxt abgail2.oxt snk_mnu.oxt --validate
```

Untuk memproses sekumpulan file berdasarkan pola:
```bash
python translate.py --pattern "*mnu*" --validate
```

Untuk menjalankan simulasi tanpa menulis file:
```bash
python translate.py --files prolog.oxt --dry-run
```

### 2. Menjalankan Validasi Kualitas
Untuk memverifikasi bahwa file di `locales/id/` 100% identik strukturnya dengan `locales/original/`:
```bash
python validate.py
```

Validator memeriksa:
1. Kesamaan identitas Key dan indentasi sebelum tanda `=`.
2. Kelengkapan dan kesesuaian token `~...~` serta placeholder.
3. Keberadaan UTF-8 BOM (`0xEF 0xBB 0xBF`).
4. Line endings Windows CRLF (`\r\n`).
5. Tidak ada baris atau entri yang hilang atau tertukar.

---

## Cara Pasang ke GTA V (OpenIV)

1. Buka aplikasi **OpenIV**.
2. Masuk ke **Edit Mode**.
3. Buka arsip teks bahasa game (contoh: `update/update.rpf/x64/data/lang/americangame.rpf` atau path teks DLC terkait).
4. Klik kanan pada file teks yang sesuai atau pilih **Import OpenIV Text (.oxt)**.
5. Pilih file dari folder `locales/id/`.
6. Jalankan GTA V dan nikmati permainan dalam Bahasa Indonesia!

---

## Alur Kontribusi & Git

1. Selalu buat cabang fitur baru dari cabang utama:
   ```bash
   git checkout -b localization/nama-fitur
   ```
2. Jalankan `python validate.py` sebelum melakukan commit.
3. Pastikan tidak ada kegagalan validasi (0 error).
4. Buat commit yang jelas dan deskriptif.
5. Kirim Pull Request (PR) untuk ditinjau.
