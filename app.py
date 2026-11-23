"""GUI Windows sederhana untuk bulk download MP3."""
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ytmp3.core import DownloadConfig, download
from ytmp3.requirements import check_requirements


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YTMP3 Downloader")
        self.geometry("720x430")
        self.minsize(620, 380)
        self.events = queue.Queue()
        self._build_ui()
        problems, info = check_requirements()
        if problems:
            messagebox.showerror("Kebutuhan belum terpenuhi", " | ".join(problems))
            self.destroy()
            return
        self._write_log("Cek kebutuhan OK: " + " | ".join(f"{k} {v}" for k, v in sorted(info.items())))
        self.after(100, self._poll_events)

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(4, weight=1)
        ttk.Label(self, text="Link YouTube / Playlist").grid(row=0, column=0, padx=12, pady=12, sticky="nw")
        self.url = tk.Text(self, height=4, width=60)
        self.url.grid(row=0, column=1, columnspan=2, padx=12, pady=12, sticky="ew")
        ttk.Label(self, text="Folder output").grid(row=1, column=0, padx=12, pady=8, sticky="w")
        self.folder = tk.StringVar(value=str(Path.home() / "Downloads"))
        ttk.Entry(self, textvariable=self.folder).grid(row=1, column=1, padx=12, sticky="ew")
        ttk.Button(self, text="Pilih", command=self._choose_folder).grid(row=1, column=2, padx=12)
        ttk.Label(self, text="Kualitas MP3").grid(row=2, column=0, padx=12, pady=8, sticky="w")
        self.quality = tk.StringVar(value="192 kbps")
        ttk.Combobox(self, textvariable=self.quality, values=["128 kbps", "192 kbps", "256 kbps", "320 kbps"], state="readonly").grid(row=2, column=1, padx=12, sticky="w")
        self.playlist = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Download seluruh playlist", variable=self.playlist).grid(row=3, column=1, padx=12, sticky="w")
        self.metadata = tk.BooleanVar(value=True)
        ttk.Checkbutton(self, text="Simpan metadata dan thumbnail", variable=self.metadata).grid(row=3, column=1, padx=12, sticky="e")
        self.start = ttk.Button(self, text="Download MP3", command=self._start)
        self.start.grid(row=3, column=2, padx=12, pady=8)
        self.progress = ttk.Progressbar(self, mode="determinate", maximum=100)
        self.progress.grid(row=4, column=0, columnspan=3, padx=12, pady=8, sticky="ew")
        self.log = tk.Text(self, height=10, state="disabled")
        self.log.grid(row=5, column=0, columnspan=3, padx=12, pady=8, sticky="nsew")
        self.rowconfigure(5, weight=1)

    def _choose_folder(self):
        selected = filedialog.askdirectory(initialdir=self.folder.get())
        if selected:
            self.folder.set(selected)

    def _write_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _start(self):
        urls = [line.strip() for line in self.url.get("1.0", "end").splitlines() if line.strip()]
        if not urls:
            messagebox.showwarning("Input kosong", "Masukkan minimal satu link YouTube.")
            return
        self.start.configure(state="disabled")
        self.progress.configure(mode="indeterminate")
        self.progress.start(10)
        threading.Thread(target=self._worker, args=(urls,), daemon=True).start()

    def _worker(self, urls):
        try:
            config = DownloadConfig(Path(self.folder.get()), self.quality.get(), self.metadata.get(), self.playlist.get())
            for index, url in enumerate(urls, 1):
                self.events.put(("log", f"Mulai {index}/{len(urls)}: {url}"))
                download(url, config, progress_hook=lambda data: self.events.put(("progress", data)), logger=QueueLogger(self.events))
                self.events.put(("log", f"Selesai {index}/{len(urls)}"))
            self.events.put(("done", None))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _poll_events(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "log": self._write_log(value)
                elif kind == "progress":
                    status = value.get("status")
                    if status == "downloading":
                        percent = value.get("_percent_str", "")
                        speed = value.get("_speed_str", "")
                        eta = value.get("_eta", "-")
                        self.progress.configure(mode="determinate", value=float(value.get("_percent", 0)))
                        self._write_log(f"Download {percent} | {speed} | sisa {eta} detik")
                    elif status == "finished":
                        self._write_log("Download selesai, konversi ke MP3...")
                elif kind == "error":
                    self._write_log("ERROR: " + value)
                    self.start.configure(state="normal"); self.progress.stop(); self.progress.configure(mode="determinate")
                else:
                    self.start.configure(state="normal"); self.progress.stop(); self.progress.configure(mode="determinate", value=100)
        except queue.Empty:
            pass
        self.after(100, self._poll_events)


class QueueLogger:
    def __init__(self, events): self.events = events
    def debug(self, message): pass
    def warning(self, message): self.events.put(("log", "PERINGATAN: " + message))
    def error(self, message): self.events.put(("log", "ERROR: " + message))


if __name__ == "__main__":
    app = App()
    if app.winfo_exists():
        app.mainloop()
