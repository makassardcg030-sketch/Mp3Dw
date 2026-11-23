"""Logika download YouTube ke MP3."""
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
from typing import Callable

SUPPORTED_QUALITIES = {"128", "192", "256", "320"}


def normalize_quality(value: str) -> str:
    quality = re.search(r"\d+", str(value))
    quality = quality.group(0) if quality else ""
    if quality not in SUPPORTED_QUALITIES:
        raise ValueError("Kualitas tidak didukung. Pilih 128, 192, 256, atau 320 kbps.")
    return quality


def make_safe_filename(name: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", str(name))
    return re.sub(r"\s+", " ", value).strip(" .") or "audio"


@dataclass
class DownloadConfig:
    output_dir: Path
    quality: str = "192"
    embed_metadata: bool = True
    playlist: bool = False


def build_download_options(config: DownloadConfig, progress_hook: Callable | None = None) -> dict:
    quality = normalize_quality(config.quality)
    options = {
        "format": "bestaudio/best",
        "outtmpl": str(Path(config.output_dir) / "%(title)s.%(ext)s"),
        "noplaylist": not config.playlist,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": quality,
        }],
        "final_ext": "mp3",
        "overwrites": False,
        "quiet": True,
        "no_warnings": True,
        "windowsfilenames": True,
        "restrictfilenames": False,
        "download_archive": str(Path(config.output_dir) / "download_archive.txt"),
    }
    if config.embed_metadata:
        options["postprocessors"].append({"key": "FFmpegMetadata"})
        options["writethumbnail"] = True
        options["postprocessors"].append({"key": "EmbedThumbnail"})
    node = shutil.which("node")
    if node:
        options["js_runtimes"] = {"node": {"path": node}}
    if progress_hook:
        options["progress_hooks"] = [progress_hook]
    return options


def clean_url(url: str) -> str:
    value = url.strip()
    if value.startswith("@url:`") and value.endswith("`"):
        value = value[6:-1]
    return value


def download(url: str, config: DownloadConfig, progress_hook=None, logger=None) -> None:
    url = clean_url(url)
    if not url:
        raise ValueError("Link YouTube wajib diisi.")

    if not re.match(r"^https?://(www\.)?(youtube\.com|youtu\.be)/", url):
        raise ValueError("Link harus berupa URL YouTube yang valid.")
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError("Paket yt-dlp belum terpasang.") from exc
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    options = build_download_options(config, progress_hook)
    options["logger"] = logger
    with yt_dlp.YoutubeDL(options) as client:
        client.download([url.strip()])
