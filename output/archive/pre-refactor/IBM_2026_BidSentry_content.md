# IBM_2026_BidSentry: Analisis repo dan konten deck

## Analisis repo singkat

- **Frontend:** index.html berisi dashboard skenario, input audit kustom tiga tab, matriks kepatuhan, kategori risiko, register klausul kontrak, kalkulator eksposur, dan export JSON.
- **Backend:** server.py menyajikan UI, menangani /api/audit dengan rules engine lokal, mencatat audit_log.jsonl, serta mem-proxy rute API lain ke Langflow pada port 7860.
- **IBM Bob dan Langflow:** bob/mcp.json memuat konfigurasi server MCP untuk Langflow. Folder langflow/ kosong pada checkout ini, sehingga flow belum bisa diverifikasi. Repo tidak membuktikan koneksi end-to-end Bob ke Langflow.
- **Risk engine:** hasil UI berupa kategori seperti RENDAH, TINGGI, atau KRITIS. Audit kustom memberi kategori berdasarkan jumlah GAP. Tidak tampak model risiko numerik terkalibrasi atau detektor fraud khusus.
- **Integrasi workspace:** composio_dispatcher.py berisi builder aksi dokumen, kalender, dan email. Kode menyediakan mode simulasi bila kredensial eksternal tidak tersedia.
- **Bukti pengujian:** sample-data/tender-sample.json memuat tiga skenario tender fiktif. Satu event LOCAL_ENGINE pada audit_log.jsonl mencatat verdict GO-WITH-CAUTION dan panjang input, bukan isi dokumen.
- **Validasi pengguna:** repo tidak mencatat peserta, kutipan feedback, atau metrik usability. Karena itu deck tidak mengklaim user validation ataupun angka akurasi benchmark.
- **Klaim yang sengaja tidak dipakai:** README menyebut 31%, akurasi >94%, review <90 detik, dan penghematan biaya. Tidak ditemukan sumber atau runner benchmark yang cukup untuk mengonfirmasi klaim tersebut.

## Asset screenshot yang ditangkap

| Asset | Isi | Lokasi |
|---|---|---|
| Dashboard dan risk category | Verdict, Risk Score TINGGI, drivers, KPI, dan awal risk register | output/assets/ui_dashboard.png |
| Risk register | Alert termin pembayaran bersyarat dan denda tanpa batas | output/assets/ui_risk_register.png |
| Matriks kepatuhan | Klausul, sumber, status, dan bukti | output/assets/ui_compliance_matrix.png |
| Audit dokumen kustom | Tab input dan contoh dokumen sintetis | output/assets/ui_custom_audit.png |
| Audit log | Satu baris event lokal yang tersimpan | output/assets/ui_audit_log.png |

Semua layar berasal dari UI lokal proyek. Contoh pada dashboard adalah skenario demo, bukan data tender riil.

## Konten slide 16:9

### Slide 1: BidSentry AI

**Key takeaway:** Audit kepatuhan pengadaan dan risiko kontrak sebelum penawaran dikirim.

**Isi slide:**
- Track IBM SkillsBuild 2026
- Tim BidSentry AI
- Pitch deck · 2026

**Layout & visual:** Sampul minimal dengan latar navy, judul besar di kiri, tagline, track, dan nama tim.

**Speaker notes:** Durasi 0:20. BidSentry AI membantu tim vendor membaca syarat pengadaan dan sinyal risiko kontrak lebih terarah. Hari ini kami akan menunjukkan prototipe lokal, status integrasi IBM, dan bukti validasi yang tersedia. Kami juga akan jujur tentang apa yang belum diuji.

### Slide 2: Audit pengadaan melelahkan karena bukti tersebar

**Key takeaway:** Satu gap administratif atau klausul yang luput dapat menggugurkan peluang atau menambah eksposur biaya.

**Isi slide:**
- **Bukti tersebar:** Syarat pemilihan, adendum, dan kredensial perusahaan hidup di dokumen berbeda. Pemeriksa perlu mencocokkan ketiganya satu per satu.
- **Perubahan luput:** Adendum dapat mengubah ambang atau bentuk persyaratan. Review manual mudah membandingkan versi yang salah.
- **Eksposur tersembunyi:** Dokumen kedaluwarsa, pembayaran bersyarat, dan denda tanpa batas dapat menambah risiko gugur atau beban kas. Anomali menjadi sinyal review, bukan bukti fraud.

**Layout & visual:** Tiga kolom editorial tanpa kartu. Tiap kolom menamai satu sumber pekerjaan ulang dan memberi contoh konkret.

**Speaker notes:** Durasi 0:40. Tim pengadaan vendor harus membaca persyaratan, adendum, dan bukti perusahaan secara bersamaan. Perubahan klausul mudah tertukar, sementara isu kontrak seperti termin pembayaran atau denda dapat memengaruhi kelayakan dan arus kas. Sistem kami hanya menandai sinyal dokumen. Pemeriksa tetap menentukan apakah ada masalah atau indikasi fraud.

### Slide 3: Satu alur mengubah dokumen menjadi sinyal audit

**Key takeaway:** Temuan terhubung ke klausul, bukti, status, dan jalur review manusia.

**Isi slide:**
- **INPUT:** RKS/KAK, adendum, kredensial
- **RULES LOKAL:** Pencocokan kata kunci dan baris bukti
- **MATRIKS:** Terpenuhi, GAP, expiring, superseded
- **REVIEW MANUSIA:** Klarifikasi, lengkapi, atau minta review legal

**Layout & visual:** Diagram editable empat langkah dari input dokumen menuju pemeriksaan manusia. Nilai prop di bawah diagram.

**Speaker notes:** Durasi 0:40. Pengguna memasukkan isi dokumen pemilihan, adendum, dan daftar kredensial. Parser lokal mengelompokkan klausul dan memetakan status ke bukti yang diberikan. Hasilnya berupa matriks kepatuhan dan kategori risiko untuk membantu pemeriksa memprioritaskan tindak lanjut. Kode saat ini memakai aturan kata kunci sederhana, bukan model risiko yang sudah dikalibrasi.

### Slide 4: Arsitektur IBM dan status integrasi

**Key takeaway:** Jalur audit lokal tersedia. Koneksi IBM Bob dan Langflow masih perlu pembuktian end-to-end.

**Isi slide:**
- **index.html:** Dashboard dan audit kustom
- **server.py:** /api/audit lokal dan proxy Langflow
- **RULES ENGINE:** Parser lokal dan pencatatan JSONL
- **HASIL:** Verdict, matriks, dan export

**Layout & visual:** Baris pertama memetakan demo lokal dengan koneksi solid. Baris kedua menjelaskan jalur Langflow, MCP/IBM Bob, dan Composio beserta statusnya.

**Speaker notes:** Durasi 0:50. Jalur yang dapat ditunjukkan dari repo adalah UI, bridge Python, rules engine lokal, matriks hasil, dan log JSONL. Server juga memiliki proxy menuju Langflow pada port 7860. File bob/mcp.json mendefinisikan server MCP Langflow, dan dispatcher Composio membangun aksi workspace. Namun folder flow Langflow kosong, dan tidak ada bukti koneksi langsung IBM Bob atau eksekusi Composio yang berhasil. Karena itu kami menyebutnya jalur integrasi yang disiapkan, bukan integrasi produksi.

### Slide 5: Dashboard membuat risiko mudah dipindai

**Key takeaway:** Skenario demo menampilkan kategori TINGGI beserta alasan sebelum keputusan manusia.

**Isi slide:**
- TINGGI
- GO-WITH-CAUTION
- Sinyal demo: perubahan adendum, kredensial yang segera kedaluwarsa, dan klausul kontrak yang dapat menunda pembayaran atau memperbesar eksposur denda.
- Label risiko bersifat kategorikal dan berasal dari skenario UI statis. Pengguna tetap memeriksa klausul sumber sebelum bertindak.

**Layout & visual:** Screenshot dashboard besar di sisi kanan. Ringkasan verdict dan catatan bahwa skenario bersifat statis di sisi kiri.

**Speaker notes:** Durasi 0:45. Dashboard menggabungkan verdict, kategori risiko, dan alasan utama. Skenario contoh menampilkan perubahan ambang melalui adendum, masa berlaku kredensial, serta dua klausul kontrak yang perlu diperiksa. Label TINGGI bukan angka probabilitas atau skor terkalibrasi. Ini adalah kategori triage dalam demo yang membantu mengarahkan perhatian reviewer.

### Slide 6: Audit kustom menautkan persyaratan ke bukti

**Key takeaway:** Tiga input dokumen menghasilkan matriks klausul dengan status dan bukti.

**Isi slide:**
- Pengguna menempel RKS/KAK, adendum, dan pustaka kredensial melalui tiga tab.
- Parser lokal menghasilkan status klausul dan teks bukti pada matriks audit.
- Skenario finansial menandai termin bersyarat atau denda tanpa batas untuk review manusia.
- MVP belum memiliki model risiko numerik terkalibrasi atau penetapan fraud.

**Layout & visual:** Screenshot input audit kustom dan matriks kepatuhan diletakkan berdampingan. Satu baris ringkas menjelaskan batas engine.

**Speaker notes:** Durasi 0:50. Alur kustom menerima dokumen pemilihan, adendum, dan kredensial perusahaan. Parser sisi browser serta endpoint audit lokal memakai aturan kata kunci untuk menghasilkan status dan bukti. Matriks memberi reviewer titik awal untuk meninjau GAP atau masa berlaku. Tampilan finansial dalam skenario demo memberi sinyal kontrak, bukan rekomendasi hukum. Belum ada model angka risiko yang divalidasi atau keputusan fraud otomatis.

### Slide 7: Validasi awal belum mencatat feedback pengguna

**Key takeaway:** Repo memuat tiga kasus sintetis dan satu audit lokal, tanpa catatan uji pengguna riil.

**Isi slide:**
- **3:** kasus sintetis dalam fixture, bukan peserta uji
- **1:** event audit LOCAL_ENGINE tercatat
- **0:** peserta atau kutipan feedback terdokumentasi

**Layout & visual:** Tiga angka besar meringkas bukti yang ada. Screenshot satu baris audit log menjadi strip bukti di bawahnya. Bagian akhir memuat metrik pilot yang perlu dicatat.

**Speaker notes:** Durasi 1:00. Dataset repo berisi tiga skenario tender fiktif. Satu baris audit lokal pada 2 Oktober 2026 mencatat hasil GO-WITH-CAUTION dan panjang input, bukan isi dokumen. Repo tidak mencatat peserta, kutipan, atau metrik respons pengguna. Maka kami tidak mengklaim validasi pengguna atau akurasi 94 persen. Untuk diskusi Komdigi, kami ingin menguji waktu tugas, kejelasan bukti, temuan salah, temuan terlewat, dan tingkat kepercayaan reviewer.

### Slide 8: Tautan demo video

**Key takeaway:** Gunakan YouTube Unlisted dan jaga durasi maksimal tujuh menit.

**Isi slide:**
- Tautan YouTube Unlisted: https://youtu.be/[VIDEO_ID]
- Target durasi: 6 menit 30 detik
- 0:00 masalah dan dashboard · 1:00 audit kustom · 2:30 bukti klausul · 4:00 risiko kontrak · 5:10 log dan status IBM · 6:10 permintaan pilot

**Layout & visual:** Slot tautan demo menonjol di tengah. Garis waktu sederhana di bawah merinci skenario rekaman 6:30.

**Speaker notes:** Durasi 0:30. Tautan ini sengaja masih menjadi slot pengisian. Sebelum submission, unggah rekaman ke YouTube dengan status Unlisted dan ganti VIDEO_ID. Rekam alur yang benar-benar berjalan: buka dashboard, audit dokumen sampel, tunjukkan bukti dan risk bucket, lalu buka audit log. Jelaskan bahwa integrasi Bob dan Langflow belum dibuktikan end-to-end.

### Slide 9: Impact dapat diuji dalam pilot terbatas

**Key takeaway:** Manfaat yang diharapkan adalah menemukan gap lebih awal dan membuat review lebih terukur.

**Isi slide:**
- **DAMPAK YANG DIUJI:** Temukan gap sebelum submit. Tampilkan sinyal eksposur kontrak. Simpan status dan bukti untuk tindak lanjut. Belum ada pengukuran dampak.
- **KELAYAKAN SAAT INI:** UI, bridge Python, parser lokal, dan audit log tersedia. Contoh data bersifat sintetis. Integrasi eksternal belum terverifikasi.
- **ROADMAP USULAN:** 0-30 hari: uji 5 pengguna dan 5-10 paket. 31-60 hari: demo alur Bob-Langflow MCP dan dokumentasi guardrail. 61-90 hari: pilot terawasi setelah review legal dan keamanan.

**Layout & visual:** Tiga kolom untuk hipotesis dampak, kesiapan repo, dan roadmap 90 hari yang jelas berstatus usulan.

**Speaker notes:** Durasi 0:55. Nilai yang ingin kami ukur adalah apakah vendor menemukan gap lebih cepat, memahami risiko finansial, dan dapat menelusuri bukti. Prototype lokal membuat uji terkontrol cukup realistis, tetapi data contoh belum mewakili operasi pengguna. Roadmap ini adalah usulan: mulai dengan uji tugas bersama pengguna procurement dan paket yang dianonimkan, buktikan alur Bob dengan Langflow, lalu jalankan pilot kecil setelah peninjauan legal dan keamanan.

### Slide 10: Tim BidSentry AI

**Key takeaway:** Kami mencari arahan untuk memvalidasi alur dengan vendor dan mengukur false positive sejak awal.

**Isi slide:**
- Track IBM SkillsBuild 2026
- Fokus: audit kepatuhan tender Indonesia dan risk triage kontrak.
- Profil repo: dashboard frontend, Python audit bridge, rules engine lokal, dan konfigurasi MCP untuk Langflow.
- Nama anggota individu belum tercantum di repo. Tim tampil dengan nama BidSentry AI.
- Masukan yang kami cari: desain uji pengguna, batas sinyal fraud, dan gerbang integrasi sebelum pilot.

**Layout & visual:** Closing sederhana dengan nama tim, fokus produk, profil kemampuan yang terlihat di repo, dan permintaan mentoring.

**Speaker notes:** Durasi 0:20. Kami adalah Tim BidSentry AI pada track IBM SkillsBuild 2026. Fokus kami adalah membantu vendor membaca risiko pengadaan lebih awal. Langkah berikutnya bukan membesarkan klaim, melainkan menguji alur dengan pengguna, mengukur salah tandai dan temuan terlewat, lalu membuktikan integrasi IBM secara terbatas. Kami mohon arahan untuk merancang pilot tersebut.

## Catatan sebelum submission

Slide validasi secara sengaja menyatakan bahwa user testing belum terdokumentasi. Ganti metrik n=0 dengan hasil uji riil hanya setelah sesi pengguna dilakukan dan catatan feedback disimpan. Tautan video pada slide 8 adalah placeholder YouTube Unlisted yang harus diganti.
