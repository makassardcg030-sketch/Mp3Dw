"""Cek kebutuhan aplikasi ketika dijalankan."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys


def app_dir() -> Path:
    """Folder tempat aplikasi (dist saat exe, root proyek saat source)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def find_ffmpeg(base: Path | None = None) -> Path | None:
    base = base or app_dir()
    candidates = [base / "bin" / "ffmpeg.exe", base / "bin" / "ffmpeg"]
    found = shutil.which("ffmpeg")
    if found:
        candidates.append(Path(found))
    for item in candidates:
        if item.is_file():
            return item.resolve()
    return None


def prepare_path(base: Path | None = None) -> Path | None:
    """Pastikan ffmpeg bundled ditemukan yt-dlp lewat PATH."""
    base = base or app_dir()
    bundled = base / "bin"
    if bundled.is_dir():
        os.environ["PATH"] = str(bundled) + os.pathsep + os.environ.get("PATH", "")
    return find_ffmpeg(base)


def check_requirements(base: Path | None = None) -> tuple[list[str], dict[str, str]]:
    """Kembalikan (daftar masalah, info versi). Dipanggil sebelum GUI dipakai."""
    base = base or app_dir()
    problems: list[str] = []
    info: dict[str, str] = {}

    try:
        import yt_dlp
        info["yt-dlp"] = yt_dlp.version.__version__
    except Exception as exc:
        problems.append(f"yt-dlp belum tersedia: {exc}")

    ffmpeg = prepare_path(base)
    if ffmpeg:
        info["ffmpeg"] = str(ffmpeg)
    else:
        problems.append("ffmpeg tidak ditemukan. Letakkan ffmpeg.exe di folder bin/ "

                        "atau tambahkan folder ffmpeg ke PATH.")

    try:
        import tkinter  # noqa: F401
        info["tkinter"] = "ok"
    except Exception as exc:
        problems.append(f"Tkinter belum tersedia: {exc}")

    return problems, info
