# Panduan Presenter BidSentry AI

**Acuan:** PowerPoint BidSentry AI versi v3, 10 slide. Naskah ini mengikuti urutan deck tersebut dan tidak menambahkan hasil pilot atau angka baru.

## Pesan utama

BidSentry membantu reviewer menelusuri dokumen pengadaan dan memprioritaskan hal yang perlu diperiksa. Rules engine lokal memberi sinyal yang dapat dijelaskan; reviewer tetap memeriksa dokumen asli dan mengambil keputusan.

## Intermezo pembuka: satu situasi yang akrab

Sampaikan sebelum masuk ke Slide 1. Ini **skenario ilustratif**, bukan kasus nyata atau hasil wawancara:

> “Bayangkan menjelang rapat evaluasi. Satu persyaratan ada di dokumen pemilihan, redaksinya berubah di adendum, lalu buktinya tersimpan di berkas lain. Reviewer harus memastikan versi mana yang berlaku dan menunjukkan dasar pemeriksaannya. Di tengah banyaknya dokumen, pertanyaan praktisnya: bagaimana membantu reviewer menemukan bagian yang perlu diperiksa tanpa menyerahkan keputusan kepada mesin?”

Berhenti sejenak setelah pertanyaan. Lalu lanjutkan dengan kalimat ini:

> “Itulah ruang kerja yang ingin kami bantu. BidSentry menyusun sinyal dan rujukannya agar reviewer bisa memeriksa lebih terarah.”

Jangan menyebut skenario ini sebagai pengalaman pengguna yang sudah tervalidasi.

## Kenapa pitch ini dibawa ke Komdigi

Framing yang aman dan relevan:

> “Kami membawa BidSentry ke Komdigi sebagai prototipe use case transformasi digital pemerintah, bukan sebagai sistem pengadaan resmi atau produk yang sudah diadopsi. Siaran pers Komdigi tentang transformasi digital pemerintah menyebut peran kementerian pada infrastruktur digital, aplikasi digital, koordinasi data, dan keamanan siber, dengan cakupan transformasi dari perencanaan dan pengadaan sampai implementasi. Karena itu, kami ingin meminta masukan Komdigi tentang kecocokan use case ini, tata kelola datanya, dan syarat sebelum pilot. Mesin utama prototype kami saat ini adalah aturan lokal deterministik; analisis AI eksternal masih opsional.”


## Siapa yang dibantu

- **Pengguna utama:** reviewer pengadaan yang membaca silang dokumen pemilihan, adendum, dan bukti. Slide 7 menyebut PPK/ULP sebagai calon peserta validasi berikutnya.
- **Pengguna pendukung:** reviewer teknis atau hukum yang perlu menelusuri klausul dan bukti sebelum memberi masukan.
- **Pihak yang berpotensi menerima manfaat tidak langsung:** penyedia, jika proses review menjadi lebih mudah ditelusuri dan konsisten. Ini masih hipotesis, belum divalidasi lewat pilot.
- **Peran Komdigi dalam pitch ini:** calon pemberi masukan atau mentor untuk kecocokan teknologi pemerintah, tata kelola data, keamanan, serta jalur pilot. Jangan menyebut Komdigi sebagai pengguna atau mitra resmi tanpa persetujuan nyata.

## Pitch singkat untuk Komdigi
> “BidSentry membantu reviewer pengadaan menelusuri dokumen pemilihan, adendum, dan bukti dalam satu alur. Rules engine lokal menampilkan sinyal beserta sumbernya; reviewer tetap memverifikasi dokumen asli dan mengambil keputusan. Kami belum mengklaim penghematan waktu atau akurasi. Kami ingin meminta masukan Komdigi untuk memvalidasi kebutuhan pengguna, tata kelola data, dan rancangan pilot yang aman.”

## Naskah per slide

### Slide 1 — BidSentry AI

“Halo, Saya dari BidSentry AI. BidSentry membantu reviewer pengadaan memeriksa dokumen dan menemukan sinyal yang perlu ditinjau. Sistem memberi indeks triase 0 sampai 100 sebagai penunjuk prioritas. Reviewer tetap memeriksa sumber dan memutuskan tindak lanjut; skor ini bukan probabilitas fraud atau keputusan pengadaan.”

**Jembatan:** “Kenapa alur ini dibutuhkan? Karena bahan review biasanya tersebar di beberapa dokumen.”

### Slide 2 — Masalah audit pengadaan

“Pengguna utama yang kami tuju adalah reviewer pengadaan, termasuk calon peserta validasi dari PPK atau ULP. Mereka perlu membaca silang dokumen pemilihan, adendum, dan bukti perusahaan. Konteks dan perubahan klausul bisa berada di berkas yang berbeda, sementara reviewer teknis dan hukum mungkin perlu menelusuri sumber yang sama. BidSentry mencoba membuat sinyal dan rujukan lebih mudah ditinjau. Kami belum menganggap masalah ini tervalidasi; wawancara dan pilot akan menguji apakah alur ini benar-benar membantu.”

**Jembatan:** “Kami merancang satu alur yang membawa reviewer dari dokumen ke bukti dan keputusan.”

### Slide 3 — Solusi dan nilai

“Reviewer memasukkan dokumen pemilihan, adendum, dan pustaka bukti. Rules engine lokal memeriksa pola tertentu, lalu menampilkan skor triase beserta pendorongnya. Reviewer membuka sumber, memeriksa dokumen asli, dan memutuskan tindak lanjut. Mesin bisa menandai hal seperti klausul yang perlu ditinjau atau bukti yang perlu diperiksa. Indeksnya belum dikalibrasi, jadi sistem tidak menyatakan penyedia patuh atau tidak patuh.”

**Jembatan:** “Alur ini sengaja tetap berjalan tanpa layanan AI eksternal.”

### Slide 4 — Arsitektur dan stack IBM

“Aplikasi menggunakan browser, API tervalidasi, controller, dan service rules lokal sebagai jalur utama. Ini penting untuk posisi kami di hadapan Komdigi: kami ingin menguji use case digital government yang bisa ditelusuri, dengan data lokal sebagai default dan manusia tetap mengambil keputusan. Langflow hanya memberi analisis tambahan bila diaktifkan dan disetujui untuk audit itu. Composio dapat berada dalam mode simulasi, dan koneksi IBM Bob/MCP belum diverifikasi live. Kami tidak mengklaim kemitraan atau adopsi Komdigi.”

**Jembatan:** “Berikut tampilan portofolio. Angkanya perlu dibaca dengan konteks.”

### Slide 5 — Executive overview

“Dashboard merangkum tiga paket contoh, distribusi risiko, dan nilai HPS pada fixture. Seluruh angka di layar ini sintetis dari repo, bukan data tender eksternal dan bukan hasil benchmark. Dashboard membantu menunjukkan bentuk register dan cara reviewer memilih paket untuk diperiksa.”

**Jembatan:** “Saya buka satu contoh agar terlihat alasan skor dan temuan.”

### Slide 6 — Risk deep-dive

“Contoh sintetis ini memiliki skor triase 97 dari 100 dan empat temuan, termasuk persyaratan klasifikasi, personel teknis, sanksi keterlambatan, dan klausul denda tanpa batas eksplisit. Skor berasal dari heuristik deterministik yang belum dikalibrasi. Angka 97 tidak berarti kemungkinan fraud 97 persen. Reviewer harus membuka dokumen asli dan memeriksa konteks klausul.”

**Jembatan:** “Kami juga membedakan apa yang sudah diuji secara internal dari apa yang belum divalidasi pengguna.”

### Slide 7 — Bukti awal dan validasi pengguna

“Deck mencatat QA internal: 7 dari 7 API contract tests lulus, pencarian dan filter diuji, audit scan serta tampilan temuan diperiksa, ekspor register dan dispatch simulasi dicoba, dan tampilan ponsel diperiksa. Namun feedback pengguna riil, waktu review, dan acceptance rate belum tersedia. Langkah berikutnya adalah task-based test dengan PPK atau ULP menggunakan dokumen berizin. Kami ingin mengetahui aturan mana yang relevan, bukti apa yang reviewer perlukan, dan bagaimana mengukur false positive dengan aman.”

**Catatan presenter:** Jika juri meminta bukti QA, tampilkan hasil pengujian yang mendukung klaim 7/7. Jangan menyamakan QA internal dengan validasi pengguna.

**Jembatan:** “Sekarang saya tunjukkan alur produk dari dashboard sampai tindak lanjut.”

### Slide 9 — Impact, feasibility, roadmap

“Kami belum mengklaim penghematan waktu atau peningkatan akurasi. Pada pilot, kami akan mengukur waktu review per paket, temuan yang diterima reviewer, serta false positive dan koreksi. Rencana berikutnya adalah meninjau aturan bersama ahli pengadaan dan legal, menguji dokumen berizin, lalu menyiapkan kalibrasi, keamanan data, dan verifikasi IBM Bob live.”

**Jembatan:** “Untuk menjalankan pilot dengan baik, kami membutuhkan masukan yang spesifik.”

### Slide 10 — Penutup

“Kami meminta masukan Komdigi dan calon reviewer pada tiga hal: apakah sinyal yang ditampilkan relevan, bukti apa yang harus menyertai setiap alert, dan syarat tata kelola data sebelum pilot. Jika use case ini cocok, langkah berikutnya adalah validasi dengan reviewer dan dokumen yang pengguna berhak proses. Kami belum mengklaim adopsi atau dampak sebelum pengujian itu selesai. Terima kasih.”

## Jawaban singkat untuk pertanyaan juri

**Kenapa dipresentasikan ke Komdigi?**

“Kami mencari masukan tentang kecocokan use case digital government, pemilihan teknologi, dan tata kelola data. Kami tidak menganggap Komdigi sebagai operator harian atau menyatakan produk ini sudah didukung kementerian. Pengguna langsung yang perlu kami validasi adalah reviewer pengadaan, termasuk PPK/ULP.”

**Siapa yang paling dibantu BidSentry?**

“Yang paling langsung adalah reviewer pengadaan yang harus membaca silang dokumen dan bukti. Reviewer teknis atau hukum bisa menjadi pengguna pendukung. Penyedia mungkin menerima manfaat tidak langsung dari proses yang lebih mudah ditelusuri, tetapi itu masih hipotesis yang perlu diuji.”

**Apakah BidSentry memakai AI generatif untuk mengambil keputusan?**

“Tidak. Jalur utama prototype saat ini adalah rules engine lokal yang deterministik. Langflow hanya opsional untuk analisis tambahan dengan persetujuan. Semua hasil tetap memerlukan verifikasi dan keputusan manusia.”

**Apakah skor 97 berarti probabilitas fraud 97%?**

“Tidak. Itu indeks triase dari heuristik deterministik yang belum dikalibrasi. Reviewer harus memeriksa dokumen asli.”

**Apakah sudah terbukti menghemat waktu atau meningkatkan akurasi?**

“Belum. Feedback pengguna dan metrik waktu review belum tersedia. Itu yang akan kami ukur dalam pilot.”

**Apakah dokumen dikirim ke layanan eksternal?**

“Rules engine lokal adalah jalur utama. Langflow hanya digunakan bila dikonfigurasi dan disetujui untuk audit tersebut. Status konektor lain kami jelaskan sesuai hasil verifikasi; Bob/MCP belum diverifikasi live.”

**Apakah angka dashboard berasal dari data tender nyata?**

“Tidak. Paket dan nilai pada dashboard berasal dari fixture sintetis.”

## Persiapan sebelum presentasi

- Isi atau hapus placeholder tautan video pada slide 8.
- Pastikan demo berjalan pada perangkat presentasi dan gunakan fixture sintetis.
- Siapkan bukti yang mendukung klaim QA internal 7/7 bila akan menyebutkannya.
- Jangan mengklaim feedback pengguna, penghematan waktu, acceptance rate, atau integrasi live yang belum dibuktikan.
- Slide 10 menyebut roster anggota belum tercantum di repositori. Lengkapi nama tim bila diperlukan untuk presentasi.
- Deck yang diberikan memuat bobot matriks sebesar 95%. Minta penyelenggara menjelaskan perlakuan terhadap sisa 5% bila skor dibahas.
