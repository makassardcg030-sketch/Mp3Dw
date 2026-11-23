"""GUI Kivy untuk bulk download MP3."""
from pathlib import Path
import queue
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner

from ytmp3.core import DownloadConfig, download
from ytmp3.requirements import check_requirements


class QueueLogger:
    def __init__(self, events):
        self.events = events

    def debug(self, message):
        pass

    def warning(self, message):
        self.events.put(("log", "PERINGATAN: " + message))

    def error(self, message):
        self.events.put(("log", "ERROR: " + message))


class YTMP3App(App):
    def build(self):
        Window.size = (720, 430)
        Window.minimum_width, Window.minimum_height = 620, 380

        self.events = queue.Queue()
        self.config = None

        root = BoxLayout(orientation="vertical", padding=12, spacing=12)

        # URL input
        root.add_widget(Label(text="Link YouTube / Playlist", size_hint_y=None, height=30))
        self.url_input = TextInput(multiline=True, hint_text="Masukkan URL YouTube...", size_hint_y=2)
        root.add_widget(self.url_input)

        # Output folder
        folder_row = BoxLayout(orientation="horizontal", spacing=6, size_hint_y=None, height=36)
        folder_row.add_widget(Label(text="Folder output", size_hint_x=0.3))
        self.folder_input = TextInput(hint_text=str(Path.home() / "Downloads"), size_hint_x=0.6)
        folder_row.add_widget(self.folder_input)
        self.btn_browse = Button(text="Pilih", size_hint_x=0.1)
        self.btn_browse.bind(on_press=self._show_folder_chooser)
        folder_row.add_widget(self.btn_browse)
        root.add_widget(folder_row)

        # Quality
        quality_row = BoxLayout(orientation="horizontal", spacing=6, size_hint_y=None, height=36)
        quality_row.add_widget(Label(text="Kualitas MP3", size_hint_x=0.3))
        self.quality_spinner = Spinner(
            values=["128 kbps", "192 kbps", "256 kbps", "320 kbps"],
            text="192 kbps",
            size_hint_x=0.7,
        )
        quality_row.add_widget(self.quality_spinner)
        root.add_widget(quality_row)

        # Options
        options_row = BoxLayout(orientation="horizontal", spacing=12, size_hint_y=None, height=36)
        self.playlist_check = CheckBox(active=False, size_hint_x=None, width=24)
        options_row.add_widget(self.playlist_check)
        options_row.add_widget(Label(text="Download seluruh playlist", size_hint_x=0.4))

        self.metadata_check = CheckBox(active=True, size_hint_x=None, width=24)
        options_row.add_widget(self.metadata_check)
        options_row.add_widget(Label(text="Simpan metadata & thumbnail", size_hint_x=0.4))
        root.add_widget(options_row)

        # Start button
        self.btn_start = Button(text="Download MP3", size_hint_y=None, height=48, font_size=16)
        self.btn_start.bind(on_press=self._start)
        root.add_widget(self.btn_start)

        # Progress bar
        self.progress = ProgressBar(size_hint_y=None, height=24, max=100)
        root.add_widget(self.progress)

        # Log
        log_container = BoxLayout(orientation="vertical", size_hint_y=1)
        log_container.add_widget(Label(text="Log", size_hint_y=None, height=30))
        self.log_text = TextInput(multiline=True, readonly=True, size_hint_y=1)
        log_container.add_widget(self.log_text)
        root.add_widget(log_container)

        # Check requirements
        problems, info = check_requirements()
        if problems:
            self._show_error("Kebutuhan belum terpenuhi", " | ".join(problems))
            self.btn_start.disabled = True
        else:
            self._log(f"Cek kebutuhan OK: {' | '.join(f'{k} {v}' for k, v in sorted(info.items()))}")
        Clock.schedule_interval(self._poll_events, 0.1)

        return root

    def _log(self, text):
        self.log_text.insert(text + "\n")
        self.log_text.cursor = (0, len(self.log_text.text.splitlines()))

    def _show_error(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.6, 0.4),
        )
        popup.open()

    def _show_folder_chooser(self, instance):
        content = BoxLayout(orientation="vertical")
        self.filechooser = FileChooserListView(path=str(Path.home() / "Downloads"), size_hint_y=0.8)
        content.add_widget(self.filechooser)

        btn_row = BoxLayout(orientation="horizontal", size_hint_y=0.2)
        btn_ok = Button(text="Pilih", size_hint_x=0.5)
        btn_ok.bind(on_press=lambda _: self._select_folder())
        btn_cancel = Button(text="Batal", size_hint_x=0.5)
        btn_cancel.bind(on_press=lambda _: self._close_folder_chooser())
        btn_row.add_widget(btn_ok)
        btn_row.add_widget(btn_cancel)
        content.add_widget(btn_row)

        self.folder_popup = Popup(
            title="Pilih Folder Output",
            content=content,
            size_hint=(0.8, 0.8),
        )
        self.folder_popup.open()

    def _select_folder(self):
        if self.filechooser.selection:
            self.folder_input.text = self.filechooser.selection[0]
        self._close_folder_chooser()

    def _close_folder_chooser(self):
        if hasattr(self, "folder_popup"):
            self.folder_popup.dismiss()

    def _normalize_quality(self, value):
        import re

        quality = re.search(r"\d+", str(value))
        quality = quality.group(0) if quality else ""
        if quality not in {"128", "192", "256", "320"}:
            raise ValueError("Kualitas tidak didukung. Pilih 128, 192, 256, atau 320 kbps.")
        return quality

    def _start(self, instance):
        urls = [line.strip() for line in self.url_input.text.splitlines() if line.strip()]
        if not urls:
            self._show_error("Input kosong", "Masukkan minimal satu link YouTube.")
            return

        self.btn_start.disabled = True
        self.progress.value = 0
        self.progress.mode = "indeterminate"

        threading.Thread(target=self._worker, args=(urls,), daemon=True).start()

    def _worker(self, urls):
        try:
            quality = self._normalize_quality(self.quality_spinner.text)
            config = DownloadConfig(
                Path(self.folder_input.text),
                quality,
                self.metadata_check.active,
                self.playlist_check.active,
            )
            for index, url in enumerate(urls, 1):
                self.events.put(("log", f"Mulai {index}/{len(urls)}: {url}"))
                download(
                    url,
                    config,
                    progress_hook=lambda data: self.events.put(("progress", data)),
                    logger=QueueLogger(self.events),
                )
                self.events.put(("log", f"Selesai {index}/{len(urls)}"))
            self.events.put(("done", None))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _poll_events(self, dt):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "log":
                    self._log(value)
                elif kind == "progress":
                    status = value.get("_status", value.get("status"))
                    if status == "downloading":
                        percent = float(value.get("_percent_str", "0%").rstrip("%"))
                        speed = value.get("_speed", "")
                        eta = value.get("_eta", "-")
                        self.progress.value = percent
                        self._log(f"Download {percent:.1f}% | {speed} | sisa {eta}")
                    elif status == "finished":
                        self._log("Download selesai, konversi ke MP3...")
                elif kind == "error":
                    self._log("ERROR: " + value)
                    self.btn_start.disabled = False
                    self.progress.value = 0
                else:
                    self.btn_start.disabled = False
                    self.progress.value = 100
        except queue.Empty:
            pass


if __name__ == "__main__":
    YTMP3App().run()
