# IBM 2026 · BidSentry AI

Pitch deck 16:9 · naskah untuk video maksimal 7 menit. Angka portofolio dan hasil scan berasal dari fixture/uji internal; repo tidak memuat feedback pengguna riil.

## Slide 1: BidSentry AI

**Header & key takeaway**  
Audit pengadaan yang tertata. Risiko lebih cepat terlihat.

**Body copy**
- Screening dokumen kepatuhan dan sinyal risiko finansial dalam satu alur review.
- Track IBM SkillsBuild 2026
- Tim: BidSentry AI

**Layout & visual instruction**  
Cover editorial: judul besar di kiri; skor triage abstrak dan label risk band di kanan; tanpa klaim data eksternal.

**Speaker notes (0:25)**  
BidSentry AI membantu reviewer menata pemeriksaan dokumen pengadaan. Kami menggabungkan aturan kepatuhan yang dapat dijelaskan dengan triage risiko finansial, agar perhatian reviewer jatuh lebih dulu pada bagian yang perlu dicek. Produk ini berada pada track IBM SkillsBuild 2026.

## Slide 2: Masalah audit pengadaan

**Header & key takeaway**  
Berkas yang tersebar membuat pemeriksaan silang lambat dan sulit diulang.

**Body copy**
- Dokumen pemilihan, adendum, dan bukti perusahaan harus dibaca silang.
- Pemeriksaan manual berulang menyulitkan konsistensi antar paket.
- Sinyal seperti syarat kabur, kredensial kedaluwarsa, atau denda tanpa batas mudah terlewat.
- Reviewer membutuhkan alasan yang jelas, bukan sekadar label risiko.

**Layout & visual instruction**  
Pernyataan editorial di kiri; tiga pain point bernomor dan dipisahkan garis tipis di kanan; tanpa statistik yang tidak tersedia.

**Speaker notes (0:40)**  
Masalah yang kami bidik bukan ketiadaan dokumen, melainkan beban membaca dan membandingkannya. Reviewer perlu menyilangkan dokumen pemilihan, adendum, dan bukti perusahaan. Pemeriksaan manual berulang juga membuat sinyal risiko sulit dibaca dengan cara yang konsisten. Sistem harus menunjukkan alasan dan sumber untuk ditinjau manusia.

## Slide 3: Solusi dan nilai

**Header & key takeaway**  
BidSentry mengubah dokumen menjadi temuan yang dapat ditinjau, bukan keputusan otomatis.

**Body copy**
- 1 · Masukkan teks dokumen pemilihan, adendum, atau pustaka.
- 2 · Rules engine mencari gap, kredensial kedaluwarsa, klausul terganti, dan sinyal kontrak.
- 3 · Risk engine memberi skor triage 0–100 dengan pendorong yang terlihat.
- 4 · Reviewer memeriksa dokumen asli dan menentukan tindak lanjut.
- Nilai: satu register audit, sinyal yang lebih mudah diprioritaskan, dan alasan yang dapat dijelaskan.

**Layout & visual instruction**  
Alur 4 langkah mendatar di tengah; dua pernyataan di bawah untuk cakupan otomasi dan kewenangan reviewer.

**Speaker notes (0:40)**  
Reviewer memasukkan dokumen yang akan diperiksa. Rules engine menandai gap dan pola kontrak, lalu risk engine menyusun indeks triage beserta pendorongnya. Hasilnya membantu mengurutkan pemeriksaan, tetapi keputusan tetap pada reviewer yang memeriksa dokumen asli.

## Slide 4: Arsitektur dan stack IBM

**Header & key takeaway**  
Rules lokal menjadi jalur utama; layanan eksternal bersifat opt-in dan punya fallback.

**Body copy**
- Browser: web/app.js, state.js, dan api.js.
- API: routes + schema validation → controllers → audit, portfolio, dan risk services.
- Langflow: advisory opsional; hanya dipanggil dengan persetujuan reviewer per audit.
- Composio: tindak lanjut Docs/Calendar/Gmail; simulasi jika API key tidak tersedia.
- IBM Bob: bob/mcp.json berisi konfigurasi MCP untuk Langflow; sesi Bob live belum diverifikasi.

**Layout & visual instruction**  
Diagram pipeline 4 lapis dari browser ke risk services; baris integrasi opsional di bawah dengan status yang jujur.

**Speaker notes (0:50)**  
UI mengirim request ke API yang tervalidasi. Controller mengatur alur ke audit dan risk service, lalu hasil kembali dalam envelope respons yang konsisten. Langflow hanya menjadi advisory jika diaktifkan dan reviewer menyetujui pemrosesan eksternal. Composio punya mode simulasi. File Bob yang ditemukan adalah konfigurasi MCP; repositori belum membuktikan koneksi IBM Bob berjalan end-to-end.

## Slide 5: Executive overview

**Header & key takeaway**  
Dashboard menyatukan ringkasan portofolio, register kepatuhan, dan detail risiko.

**Body copy**
- 3 paket contoh sintetis.
- 33% kasus demo berstatus low pada fixture.
- 1 kasus high atau critical pada fixture.
- Rp6,965 miliar total HPS pada fixture.
- Angka layar berasal dari sample-data proyek dan audit lokal; bukan data tender eksternal.

**Layout & visual instruction**  
Screenshot dashboard lokal mengisi sisi kiri; empat metrik dan batas data sintetis di sisi kanan.

**Speaker notes (0:40)**  
Di halaman ringkasan, reviewer melihat jumlah paket, indikator risiko, register, dan rincian paket terpilih. Angka tiga paket, rasio 33 persen, satu kasus tinggi atau kritis, dan total HPS berasal dari fixture sintetis di repo. Screenshot ini menunjukkan bentuk produk, bukan hasil implementasi pada tender nyata.

## Slide 6: Risk deep-dive

**Header & key takeaway**  
Skor 97/100 menunjukkan prioritas review pada scan uji; bukan probabilitas fraud.

**Body copy**
- Contoh audit lokal: 4 temuan pada input sintetis.
- KBLI/SBU · Personel dan SKK · Sanksi keterlambatan · Denda tanpa batas eksplisit.
- Band: LOW 0–19 · MEDIUM 20–39 · HIGH 40–69 · CRITICAL 70–100.
- Skor adalah heuristik deterministik yang belum dikalibrasi; reviewer wajib memeriksa sumber asli.

**Layout & visual instruction**  
Screenshot panel risk detail di kiri; skor triage dan daftar temuan berukuran besar di kanan; band risiko di bagian bawah.

**Speaker notes (0:55)**  
Pada contoh scan sintetis, empat aturan terpicu dan skor mencapai 97 dari 100, sehingga masuk band kritis. Temuannya mencakup klasifikasi usaha, persyaratan personel, sanksi keterlambatan, dan denda. Angka ini adalah heuristik triage yang belum dikalibrasi. Ia bukan probabilitas fraud atau verdict; reviewer tetap harus membuka dokumen asli.

## Slide 7: Bukti awal dan validasi pengguna

**Header & key takeaway**  
Alur produk lolos uji internal; feedback pengguna riil belum tercatat di repo.

**Body copy**
- Uji API: 7/7 unit tests lulus.
- Uji browser: pencarian, filter risiko, audit scan, ekspor JSON, dan dispatch simulasi berhasil.
- Tidak ada error JavaScript; viewport ponsel 390 px tidak mengalami overflow horizontal.
- Belum ditemukan sesi pengujian pengguna riil, feedback, atau metrik waktu respons.
- Bahan mentoring Komdigi: aturan mana yang paling berguna, bukti apa yang perlu ditampilkan, dan bagaimana mengukur false positive?

**Layout & visual instruction**  
Dua kolom: bukti QA yang sudah ada dan gap validasi pengguna; strip bawah berisi tiga pertanyaan mentoring.

**Speaker notes (0:50)**  
Yang sudah kami buktikan adalah kelayakan teknis awal: tujuh uji API lulus dan lima alur UI berhasil dijalankan, tanpa error browser dan tanpa overflow pada viewport ponsel. Kami belum menemukan feedback pengguna riil di repositori, jadi kami tidak mengklaim validasi pasar. Untuk diskusi Komdigi, kami ingin menguji kegunaan aturan, bukti yang dibutuhkan, dan cara mengukur false positive.

## Slide 8: Demo produk · maksimal 7 menit

**Header & key takeaway**  
Slot tautan demo YouTube Unlisted; video belum diunggah.

**Body copy**
- Tautan: tempel URL YouTube Unlisted setelah video diunggah.
- 00:00–00:45 · Ringkasan dashboard dan peringatan data sintetis.
- 00:45–02:15 · Jalankan audit dan lihat daftar temuan.
- 02:15–04:30 · Jelaskan skor, band risiko, dan bukti sumber.
- 04:30–05:45 · Cari paket, filter risiko, ekspor register.
- 05:45–06:30 · Siapkan tindak lanjut simulasi dan tutup dengan keputusan reviewer.

**Layout & visual instruction**  
Slot video besar di kiri dengan instruksi tautan; rundown 6:30 di kanan agar tetap di bawah batas 7 menit.

**Speaker notes (0:25)**  
Video demo akan menggunakan fixture sintetis dan tidak lebih dari tujuh menit. Tampilkan audit scan, cara membaca skor dan temuan, pencarian, filter, ekspor, lalu fallback tindak lanjut. Ganti teks slot ini dengan tautan YouTube Unlisted setelah video tersedia.

## Slide 9: Impact, feasibility, roadmap

**Header & key takeaway**  
Dampak harus diukur lewat pilot; fondasi lokal sudah dapat dijalankan tanpa kredensial eksternal.

**Body copy**
- Ukur pada pilot: waktu review per paket, temuan yang diterima reviewer, dan false positive.
- Feasibility: Python stdlib, frontend tanpa build step, API kontrak stabil, fallback Langflow/Composio.
- Roadmap usulan: (1) validasi aturan dengan ahli pengadaan; (2) pilot dengan dokumen berizin dan anotasi; (3) kalibrasi skor, keamanan, dan verifikasi integrasi IBM Bob.
- Target dampak belum diklaim sebelum baseline dan hasil pilot tersedia.

**Layout & visual instruction**  
Satu kolom metrik pilot di kiri; tiga fase roadmap mendatar di kanan/bawah; label jelas bahwa rencana bersifat usulan.

**Speaker notes (0:45)**  
Dampak belum bisa disimpulkan dari fixture demo. Pilot perlu mengukur waktu review, kesesuaian temuan dengan reviewer, serta false positive. Aplikasi saat ini bisa berjalan lokal tanpa layanan eksternal. Roadmap yang kami usulkan dimulai dari validasi aturan, dilanjutkan pilot dengan dokumen berizin, lalu kalibrasi skor, penguatan keamanan, dan verifikasi integrasi IBM Bob.

## Slide 10: Tim dan penutup

**Header & key takeaway**  
BidSentry AI meminta masukan untuk menguji aturan, bukti, dan tata kelola data.

**Body copy**
- Tim: BidSentry AI · nama anggota belum tercantum di repositori.
- Track IBM SkillsBuild 2026.
- Diskusi yang dibutuhkan: dokumen prioritas, alur review, governance data, dan desain pilot.
- Terima kasih.

**Layout & visual instruction**  
Penutup editorial dengan nama tim besar; tiga permintaan masukan di bawah dan track di footer.

**Speaker notes (0:30)**  
Kami adalah Tim BidSentry AI pada track IBM SkillsBuild 2026. Repo belum memuat roster anggota, jadi kami tidak mencantumkan nama yang belum terverifikasi. Kami mengundang masukan Komdigi untuk menentukan dokumen prioritas, alur review, tata kelola data, dan desain pilot yang bisa menghasilkan bukti pengguna nyata. Terima kasih.
