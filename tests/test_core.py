from pathlib import Path

import pytest

import ytmp3.core as core


def test_options_uses_available_node_runtime(monkeypatch):
    monkeypatch.setattr(core.shutil, "which", lambda name: "C:/node.exe" if name == "node" else None)
    options = core.build_download_options(DownloadConfig(output_dir=Path(".")))
    assert options["js_runtimes"] == {"node": {"path": "C:/node.exe"}}


from ytmp3.core import DownloadConfig, build_download_options, clean_url, make_safe_filename, normalize_quality


def test_clean_url_removes_context_wrapper():
    assert clean_url("@url:`https://www.youtube.com/watch?v=abc`") == "https://www.youtube.com/watch?v=abc"


def test_normalize_quality_accepts_supported_bitrate():
    assert normalize_quality("192 kbps") == "192"


def test_normalize_quality_rejects_unsupported_bitrate():
    with pytest.raises(ValueError, match="Kualitas tidak didukung"):
        normalize_quality("999 kbps")


def test_safe_filename_removes_windows_forbidden_characters():
    assert make_safe_filename('Halo: Dunia? <lagu>') == "Halo Dunia lagu"


def test_options_configures_mp3_audio_and_destination(tmp_path: Path):
    config = DownloadConfig(output_dir=tmp_path, quality="320", embed_metadata=True)

    options = build_download_options(config, progress_hook=lambda _: None)

    assert options["format"] == "bestaudio/best"
    assert options["postprocessors"][0]["preferredcodec"] == "mp3"
    assert options["postprocessors"][0]["preferredquality"] == "320"
    assert options["outtmpl"].startswith(str(tmp_path))
    assert options["noplaylist"] is True
    assert options["progress_hooks"]
    assert options["final_ext"] == "mp3"
    assert options["overwrites"] is False
