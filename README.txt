YTMP3 Downloader - Windows EXE
==============================
Cara pakai:
  1. Jalankan YTMP3.exe di komputer tujuan (tidak perlu install Python).
  2. Masukkan link YouTube/Playlist, pilih folder output, kualitas, lalu Download MP3.
  3. ffmpeg.exe sudah tersedia di folder bin/ (digunakan untuk konversi MP3).

Aplikasi akan secara otomatis memeriksa kebutuhan saat dibuka (yt-dlp, ffmpeg, tkinter).
Jika ada yang hilang, muncul pesan error yang menjelaskan apa yang harus dipasang.

Untuk membangun ulang:
  python build_exe.py

Catatan: build manual (tanpa PyInstaller) agar tidak terdeteksi sebagai virus oleh AV.
