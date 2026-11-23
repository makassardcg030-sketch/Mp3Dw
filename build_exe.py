import os, shutil, zipfile, sys, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist" / "YTMP3"
DIST.mkdir(parents=True, exist_ok=True)

pydir = Path(sys.base_prefix)
exe_dir = DIST
shutil.copy(pydir / "pythonw.exe", exe_dir / "YTMP3.exe")
for f in ["python3.dll", "python314.dll", "vcruntime140.dll", "vcruntime140_1.dll"]:
    shutil.copy(pydir / f, exe_dir)

def ignore_pdb(d, names):
    return [n for n in names if n.endswith(".pdb")]

shutil.copytree(pydir / "DLLs", exe_dir / "DLLs", dirs_exist_ok=True, ignore=ignore_pdb)
shutil.copytree(pydir / "tcl", exe_dir / "tcl", dirs_exist_ok=True)

lib_dir = pydir / "Lib"
z_path = exe_dir / "python314.zip"
with zipfile.ZipFile(z_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in lib_dir.rglob("*.py"):
        if any(x in p.parts for x in ("__pycache__", "site-packages", "test", "idlelib", "turtledemo")):
            continue
        z.write(p, p.relative_to(lib_dir).as_posix())

shutil.copy("app.py", exe_dir / "app.py")
shutil.copytree("ytmp3", exe_dir / "ytmp3", dirs_exist_ok=True)

shutil.copy("requirements.txt", exe_dir / "requirements.txt")
shutil.copy("README.txt", exe_dir / "README.txt")

yt_src = ROOT / ".venv-build" / "Lib" / "site-packages"
if (yt_src / "yt_dlp").is_dir():
    shutil.copytree(yt_src / "yt_dlp", exe_dir / "yt_dlp", dirs_exist_ok=True)

ffmpeg_src = Path(r"C:/ffmpeg/bin/ffmpeg.exe")
if ffmpeg_src.is_file():
    ffmpeg_dst = exe_dir / "bin" / "ffmpeg.exe"
    ffmpeg_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(ffmpeg_src, ffmpeg_dst)

pth_lines = [
    "python314.zip",
    "DLLs",
    ".",
    "import site",
]
(exe_dir / "python314._pth").write_text("\n".join(pth_lines) + "\n", encoding="utf-8")

sitecustomize_content = (
    "import os, sys, traceback\n"
    "from pathlib import Path\n"
    "def _main():\n"
    "    here = Path(sys.executable).resolve().parent\n"
    "    os.chdir(here)\n"
    "    sys.path.insert(0, str(here))\n"
    "    if os.environ.get(\"YTMP3_SELFTEST\") == \"1\":\n"
    "        lines = []\n"
    "        try:\n"
    "            import tkinter as tk\n"
    "            import yt_dlp\n"
    "            import ytmp3.core, ytmp3.requirements\n"
    "            problems, info = ytmp3.requirements.check_requirements(here)\n"
    "            lines.append(\"tk=\" + str(tk.TkVersion))\n"
    "            lines.append(\"yt_dlp=\" + yt_dlp.version.__version__)\n"
    "            lines.append(\"problems=\" + repr(problems))\n"
    "            lines.append(\"info=\" + repr(info))\n"
    "        except Exception:\n"
    "            lines.append(traceback.format_exc())\n"
    "        (here / \"selftest.txt\").write_text(chr(10).join(lines), encoding=\"utf-8\")\n"
    "        return\n"
    "    try:\n"
    "        import runpy\n"
    "        runpy.run_path(str(here / \"app.py\"), run_name=\"__main__\")\n"
    "    except SystemExit:\n"
    "        raise\n"
    "    except BaseException:\n"
    "        (here / \"crash.log\").write_text(traceback.format_exc(), encoding=\"utf-8\")\n"
    "        try:\n"
    "            import tkinter.messagebox as mb\n"
    "            mb.showerror(\"YTMP3 gagal dijalankan\", traceback.format_exc()[-1200:])\n"
    "        except Exception:\n"
    "            pass\n"
    "try:\n"
    "    _main()\n"
    "finally:\n"
    "    os._exit(0)\n"
)
(exe_dir / "sitecustomize.py").write_text(sitecustomize_content, encoding="utf-8")

out_zip = ROOT / "YTMP3-win64.zip"
with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(DIST):
        for file in files:
            full = Path(root) / file
            z.write(full, full.relative_to(DIST))
print(f"Dist created at {DIST}")
print(f"Zip package: {out_zip}")
