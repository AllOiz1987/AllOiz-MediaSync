from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path
from queue import Empty, Queue
from tkinter import (
    BOTH,
    DISABLED,
    END,
    LEFT,
    NORMAL,
    RIGHT,
    StringVar,
    Text,
    Tk,
    Toplevel,
    Label,
    Frame,
    filedialog,
    messagebox,
)
from tkinter import ttk

from transkription import transkribieren


APP_NAME = "AllOiz MediaSync"
VERSION = "1.4"

ERLAUBTE_FORMATE = {
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
}

EREIGNISSE: Queue[tuple[str, object]] = Queue()

CHARCOAL = "#202328"
DUNKEL = "#15171B"
PANEL = "#292D33"
PANEL_HELL = "#333840"
GOLD = "#C9A227"
GOLD_HELL = "#E0C45A"
TUERKIS = "#1DB9B8"
TUERKIS_HELL = "#55D6D4"
TEXT = "#F2F2F2"
TEXT_GRAU = "#B8BDC7"


def projektname_erzeugen(name: str) -> str:
    bereinigt = re.sub(
        r"[^A-Za-z0-9ÄÖÜäöüß _-]",
        "_",
        name,
    )
    bereinigt = re.sub(r"\s+", " ", bereinigt)
    bereinigt = re.sub(r"_+", "_", bereinigt)
    bereinigt = bereinigt.strip(" ._-")

    if not bereinigt:
        bereinigt = "AllOiz_Projekt"

    if len(bereinigt) <= 60:
        return bereinigt

    kennung = hashlib.sha1(
        name.encode("utf-8")
    ).hexdigest()[:8]

    kurzer_name = bereinigt[:50].rstrip(" ._-")

    return f"{kurzer_name}_{kennung}"


def zeit_formatieren(sekunden: float | str) -> str:
    gesamt = int(float(sekunden))
    stunden, rest = divmod(gesamt, 3600)
    minuten, sekunden = divmod(rest, 60)

    return f"{stunden:02d}:{minuten:02d}:{sekunden:02d}"


def fps_formatieren(fps_wert: str) -> str:
    try:
        zaehler, nenner = fps_wert.split("/")
        fps = float(zaehler) / float(nenner)

        return f"{fps:g}"

    except (ValueError, ZeroDivisionError):
        return fps_wert


def dateigroesse_formatieren(bytes_anzahl: int) -> str:
    groesse = float(bytes_anzahl)

    for einheit in ("Bytes", "KB", "MB", "GB", "TB"):
        if groesse < 1024 or einheit == "TB":
            if einheit == "Bytes":
                return f"{int(groesse)} {einheit}"

            return f"{groesse:.2f} {einheit}"

        groesse /= 1024

    return f"{bytes_anzahl} Bytes"


def programm_verfuegbar(name: str) -> bool:
    return shutil.which(name) is not None


def voraussetzungen_pruefen() -> None:
    fehlend = []

    if not programm_verfuegbar("ffmpeg"):
        fehlend.append("FFmpeg")

    if not programm_verfuegbar("ffprobe"):
        fehlend.append("FFprobe")

    if fehlend:
        programme = ", ".join(fehlend)

        raise RuntimeError(
            f"Folgende Programme wurden nicht gefunden: {programme}.\n\n"
            "Bitte installiere FFmpeg und starte AllOiz neu."
        )


def medieninfos_auslesen(datei: Path) -> dict:
    befehl = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(datei),
    ]

    ergebnis = subprocess.run(
        befehl,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )

    return json.loads(ergebnis.stdout)


def streams_finden(
    infos: dict,
) -> tuple[dict | None, dict | None]:
    streams = infos.get("streams", [])

    video_stream = next(
        (
            stream
            for stream in streams
            if stream.get("codec_type") == "video"
        ),
        None,
    )

    audio_stream = next(
        (
            stream
            for stream in streams
            if stream.get("codec_type") == "audio"
        ),
        None,
    )

    return video_stream, audio_stream


def projektstruktur_erstellen(
    datei: Path,
) -> dict[str, Path]:
    hauptordner = (
        Path(__file__).resolve().parent
        / "AllOiz_Projekte"
    )
    hauptordner.mkdir(exist_ok=True)

    projektname = projektname_erzeugen(datei.stem)
    projektordner = hauptordner / projektname
    projektordner.mkdir(exist_ok=True)

    ordner = {
        "projekt": projektordner,
        "video": projektordner / "Video",
        "audio": projektordner / "Audio",
        "untertitel": projektordner / "Untertitel",
        "frames": projektordner / "Frames",
        "metadaten": projektordner / "Metadaten",
        "ki": projektordner / "KI",
        "logs": projektordner / "Logs",
    }

    for pfad in ordner.values():
        pfad.mkdir(exist_ok=True)

    return ordner


def originaldatei_kopieren(
    datei: Path,
    video_ordner: Path,
) -> Path:
    projektname = video_ordner.parent.name
    ziel = video_ordner / (
        f"{projektname}{datei.suffix.lower()}"
    )

    if datei.resolve() != ziel.resolve():
        shutil.copy2(datei, ziel)

    return ziel


def audio_extrahieren(
    datei: Path,
    audio_ordner: Path,
) -> Path:
    projektname = audio_ordner.parent.name
    ausgabe = audio_ordner / f"{projektname}.wav"

    befehl = [
        "ffmpeg",
        "-y",
        "-i",
        str(datei),
        "-map",
        "0:a:0",
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(ausgabe),
    ]

    ergebnis = subprocess.run(
        befehl,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if ergebnis.returncode != 0:
        meldung = ergebnis.stderr.strip()

        if not meldung:
            meldung = (
                "FFmpeg konnte die Audiospur "
                "nicht extrahieren."
            )

        raise RuntimeError(meldung)

    return ausgabe


def ki_modul_pruefen() -> tuple[bool, str]:
    vorhanden = (
        importlib.util.find_spec("faster_whisper")
        is not None
    )

    if vorhanden:
        return True, "Faster-Whisper ist installiert."

    return (
        False,
        "Faster-Whisper ist noch nicht installiert.",
    )


def projektdatei_speichern(
    ordner: dict[str, Path],
    datei: Path,
    kopierte_videodatei: Path,
    audio_datei: Path,
    infos: dict,
    ki_verfuegbar: bool,
) -> Path:
    video_stream, audio_stream = streams_finden(infos)

    dauer = zeit_formatieren(
        infos.get("format", {}).get("duration", 0)
    )

    projekt_daten: dict[str, object] = {
        "programm": APP_NAME,
        "version": VERSION,
        "projektname": datei.stem,
        "originaldatei": str(datei.resolve()),
        "projekt_video": str(
            kopierte_videodatei.relative_to(
                ordner["projekt"]
            )
        ),
        "projekt_audio": str(
            audio_datei.relative_to(
                ordner["projekt"]
            )
        ),
        "dateiname": datei.name,
        "format": datei.suffix.lower(),
        "dateigroesse_bytes": datei.stat().st_size,
        "dauer": dauer,
        "ki_lokal_verfuegbar": ki_verfuegbar,
        "status": (
            "Bereit für lokale Transkription"
            if ki_verfuegbar
            else "Bereit für spätere KI-Verarbeitung"
        ),
        "projektstruktur": {
            "video": "Video",
            "audio": "Audio",
            "untertitel": "Untertitel",
            "frames": "Frames",
            "metadaten": "Metadaten",
            "ki": "KI",
            "logs": "Logs",
        },
    }

    if video_stream:
        projekt_daten["video"] = {
            "codec": video_stream.get(
                "codec_name",
                "unbekannt",
            ),
            "breite": video_stream.get(
                "width",
                "unbekannt",
            ),
            "hoehe": video_stream.get(
                "height",
                "unbekannt",
            ),
            "fps": fps_formatieren(
                video_stream.get(
                    "r_frame_rate",
                    "unbekannt",
                )
            ),
        }

    if audio_stream:
        projekt_daten["audio"] = {
            "codec": audio_stream.get(
                "codec_name",
                "unbekannt",
            ),
            "kanaele": audio_stream.get(
                "channels",
                "unbekannt",
            ),
            "abtastrate": audio_stream.get(
                "sample_rate",
                "unbekannt",
            ),
        }

    projektdatei = (
        ordner["metadaten"] / "projekt.json"
    )

    projektdatei.write_text(
        json.dumps(
            projekt_daten,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return projektdatei


def medieninfos_speichern(
    ordner: dict[str, Path],
    infos: dict,
) -> Path:
    datei = (
        ordner["metadaten"]
        / "ffprobe_medieninfos.json"
    )

    datei.write_text(
        json.dumps(
            infos,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return datei


def readme_erstellen(
    ordner: dict[str, Path],
    datei: Path,
    audio_datei: Path,
    ki_verfuegbar: bool,
) -> Path:
    readme = ordner["projekt"] / "README.txt"

    if ki_verfuegbar:
        ki_status = (
            "Faster-Whisper wurde gefunden.\n"
            "Das Projekt ist für die Transkription "
            "vorbereitet."
        )
    else:
        ki_status = (
            "Faster-Whisper ist noch nicht installiert.\n"
            "Die Audiodatei wurde trotzdem vollständig "
            "vorbereitet."
        )

    inhalt = f"""
====================================================
              AllOiz MediaSync v{VERSION}
====================================================

Projektname:
{datei.stem}

Originaldatei:
{datei.name}

Vorbereitete Audiodatei:
{audio_datei.name}

Projektstruktur:

Video
- enthält die kopierte Originaldatei

Audio
- enthält die vorbereitete WAV-Datei

Untertitel
- späterer Speicherort für SRT- und VTT-Dateien

Frames
- späterer Speicherort für Vorschaubilder

Metadaten
- projekt.json
- ffprobe_medieninfos.json

KI
- späterer Speicherort für Transkripte
  und KI-Auswertungen

Logs
- späterer Speicherort für Protokolldateien

KI-Status:
{ki_status}

====================================================

Onkel Alois sagt:
"Alles sortiert. Jetzt kann dat weitergehen!"

====================================================
""".strip()

    readme.write_text(
        inhalt,
        encoding="utf-8",
    )

    return readme


def logdatei_erstellen(
    ordner: dict[str, Path],
    datei: Path,
) -> Path:
    logdatei = (
        ordner["logs"] / "projekt_erstellung.log"
    )

    inhalt = (
        f"{APP_NAME} v{VERSION}\n"
        f"Projekt: {datei.stem}\n"
        f"Originaldatei: {datei}\n"
        "Projektstruktur erfolgreich erstellt.\n"
        "Videodatei kopiert.\n"
        "Audiodatei extrahiert.\n"
        "Metadaten gespeichert.\n"
        "ZIP-Paket erstellt.\n"
    )

    logdatei.write_text(
        inhalt,
        encoding="utf-8",
    )

    return logdatei


def projekt_als_zip_verpacken(
    projektordner: Path,
) -> Path:
    zip_datei = projektordner.with_suffix(".zip")

    if zip_datei.exists():
        zip_datei.unlink()

    erzeugter_pfad = shutil.make_archive(
        base_name=str(projektordner),
        format="zip",
        root_dir=str(projektordner),
    )

    return Path(erzeugter_pfad)


class AllOizApp:
    def __init__(self, fenster: Tk) -> None:
        self.fenster = fenster
        self.datei: Path | None = None
        self.infos: dict | None = None
        self.letzter_projektordner: Path | None = None
        self.letztes_projekt: dict | None = None
        self.letzte_transkript_datei: Path | None = None
        self.letzte_untertitel_datei: Path | None = None

        self.dateipfad = StringVar(
            value="Noch keine Mediendatei ausgewählt."
        )
        self.status = StringVar(value="Bereit.")
        self.ki_status = StringVar(
            value="KI-Modul noch nicht geprüft."
        )
        self.modell_auswahl = StringVar(
            value="Ausgewogen – small"
        )
        self.sprache_auswahl = StringVar(
            value="Automatisch erkennen"
        )
        self.aktives_modell = "small"
        self.aktive_sprache: str | None = None

        self.fenster.title(
            f"{APP_NAME} v{VERSION}"
        )
        self.fenster.geometry("920x720")
        self.fenster.minsize(820, 650)
        self.fenster.configure(bg=CHARCOAL)

        self.design_einrichten()
        self.oberflaeche_erstellen()
        self.ereignisse_pruefen()

        try:
            voraussetzungen_pruefen()

            self.log_schreiben(
                "FFmpeg und FFprobe wurden gefunden."
            )

        except RuntimeError as fehler:
            messagebox.showerror(
                "Fehlende Voraussetzung",
                str(fehler),
            )

            self.status.set(
                "FFmpeg oder FFprobe fehlt."
            )

        self.startbildschirm_anzeigen()

    def startbildschirm_anzeigen(self) -> None:
        self.fenster.withdraw()

        splash = Toplevel(self.fenster)
        self.splash = splash
        splash.overrideredirect(True)
        splash.configure(bg=CHARCOAL)
        splash.attributes("-topmost", True)

        breite = 620
        hoehe = 360
        bildschirm_breite = splash.winfo_screenwidth()
        bildschirm_hoehe = splash.winfo_screenheight()
        x = (bildschirm_breite - breite) // 2
        y = (bildschirm_hoehe - hoehe) // 2

        splash.geometry(
            f"{breite}x{hoehe}+{x}+{y}"
        )

        rahmen = Frame(
            splash,
            bg=CHARCOAL,
            highlightbackground=GOLD,
            highlightthickness=2,
        )
        rahmen.pack(
            fill=BOTH,
            expand=True,
            padx=4,
            pady=4,
        )

        Label(
            rahmen,
            text="👍",
            bg=CHARCOAL,
            fg=GOLD,
            font=("Segoe UI Emoji", 52),
        ).pack(pady=(42, 0))

        Label(
            rahmen,
            text=APP_NAME,
            bg=CHARCOAL,
            fg=GOLD,
            font=("Segoe UI", 29, "bold"),
        ).pack(pady=(0, 6))

        Label(
            rahmen,
            text="Alle Medien. Eine Sprache.",
            bg=CHARCOAL,
            fg=TUERKIS,
            font=("Segoe UI", 14, "bold"),
        ).pack()

        Label(
            rahmen,
            text=f"VERSION {VERSION}  •  LOKALE KI",
            bg=CHARCOAL,
            fg=TEXT_GRAU,
            font=("Segoe UI", 9, "bold"),
        ).pack(pady=(28, 18))

        ladeleiste = Frame(
            rahmen,
            bg=DUNKEL,
            height=5,
            width=440,
        )
        ladeleiste.pack()
        ladeleiste.pack_propagate(False)

        fortschritt = Frame(
            ladeleiste,
            bg=TUERKIS,
            height=5,
            width=440,
        )
        fortschritt.pack(side=LEFT)

        splash.after(
            1900,
            self.startbildschirm_schliessen,
        )

    def startbildschirm_schliessen(self) -> None:
        if hasattr(self, "splash"):
            self.splash.destroy()

        self.fenster.deiconify()
        self.fenster.lift()
        self.fenster.focus_force()

    def design_einrichten(self) -> None:
        stil = ttk.Style(self.fenster)
        stil.theme_use("clam")

        stil.configure(
            ".",
            background=CHARCOAL,
            foreground=TEXT,
            fieldbackground=PANEL,
            bordercolor=PANEL_HELL,
            lightcolor=PANEL_HELL,
            darkcolor=DUNKEL,
            font=("Segoe UI", 10),
        )
        stil.configure("TFrame", background=CHARCOAL)
        stil.configure(
            "TLabel",
            background=CHARCOAL,
            foreground=TEXT_GRAU,
        )
        stil.configure(
            "Titel.TLabel",
            background=CHARCOAL,
            foreground=GOLD,
            font=("Segoe UI", 24, "bold"),
        )
        stil.configure(
            "Untertitel.TLabel",
            background=CHARCOAL,
            foreground=TUERKIS,
            font=("Segoe UI", 11, "bold"),
        )
        stil.configure(
            "Status.TLabel",
            background=CHARCOAL,
            foreground=GOLD_HELL,
            font=("Segoe UI", 10, "bold"),
        )
        stil.configure(
            "TLabelframe",
            background=PANEL,
            bordercolor=PANEL_HELL,
            relief="solid",
            borderwidth=1,
        )
        stil.configure(
            "TLabelframe.Label",
            background=CHARCOAL,
            foreground=GOLD,
            font=("Segoe UI", 10, "bold"),
        )
        stil.configure(
            "TButton",
            background=PANEL_HELL,
            foreground=TEXT,
            borderwidth=0,
            focuscolor=TUERKIS,
            padding=(12, 8),
            font=("Segoe UI", 9, "bold"),
        )
        stil.map(
            "TButton",
            background=[
                ("active", "#424852"),
                ("disabled", PANEL),
            ],
            foreground=[
                ("disabled", "#707680"),
            ],
        )
        stil.configure(
            "Gold.TButton",
            background=GOLD,
            foreground=DUNKEL,
        )
        stil.map(
            "Gold.TButton",
            background=[
                ("active", GOLD_HELL),
                ("disabled", PANEL),
            ],
            foreground=[
                ("disabled", "#707680"),
            ],
        )
        stil.configure(
            "Tuerkis.TButton",
            background=TUERKIS,
            foreground=DUNKEL,
        )
        stil.map(
            "Tuerkis.TButton",
            background=[
                ("active", TUERKIS_HELL),
                ("disabled", PANEL),
            ],
            foreground=[
                ("disabled", "#707680"),
            ],
        )
        stil.configure(
            "TProgressbar",
            background=TUERKIS,
            troughcolor=DUNKEL,
            bordercolor=DUNKEL,
            lightcolor=TUERKIS,
            darkcolor=TUERKIS,
        )
        stil.configure(
            "TCombobox",
            background=PANEL_HELL,
            fieldbackground=PANEL_HELL,
            foreground=TEXT,
            arrowcolor=TUERKIS,
            bordercolor=PANEL_HELL,
            padding=6,
        )
        stil.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", PANEL_HELL),
                ("disabled", PANEL),
            ],
            foreground=[
                ("readonly", TEXT),
                ("disabled", "#707680"),
            ],
        )
        self.fenster.option_add(
            "*TCombobox*Listbox.background",
            PANEL_HELL,
        )
        self.fenster.option_add(
            "*TCombobox*Listbox.foreground",
            TEXT,
        )
        self.fenster.option_add(
            "*TCombobox*Listbox.selectBackground",
            TUERKIS,
        )
        self.fenster.option_add(
            "*TCombobox*Listbox.selectForeground",
            DUNKEL,
        )

    def oberflaeche_erstellen(self) -> None:
        hauptbereich = ttk.Frame(
            self.fenster,
            padding=20,
        )
        hauptbereich.pack(
            fill=BOTH,
            expand=True,
        )

        titel = ttk.Label(
            hauptbereich,
            text=f"👍  {APP_NAME}",
            style="Titel.TLabel",
        )
        titel.pack(pady=(0, 4))

        untertitel = ttk.Label(
            hauptbereich,
            text="Alle Medien. Eine Sprache.",
            style="Untertitel.TLabel",
        )
        untertitel.pack(pady=(0, 20))

        dateibereich = ttk.LabelFrame(
            hauptbereich,
            text="Mediendatei",
            padding=12,
        )
        dateibereich.pack(
            fill="x",
            pady=(0, 12),
        )

        datei_label = ttk.Label(
            dateibereich,
            textvariable=self.dateipfad,
            wraplength=590,
        )
        datei_label.pack(
            side=LEFT,
            fill="x",
            expand=True,
        )

        self.auswahl_button = ttk.Button(
            dateibereich,
            text="Datei auswählen",
            command=self.datei_auswaehlen,
        )
        self.auswahl_button.pack(
            side=RIGHT,
            padx=(12, 0),
        )

        info_bereich = ttk.LabelFrame(
            hauptbereich,
            text="Medieninformationen",
            padding=12,
        )
        info_bereich.pack(
            fill="x",
            pady=(0, 12),
        )

        self.info_text = ttk.Label(
            info_bereich,
            text="Noch keine Datei analysiert.",
            justify=LEFT,
        )
        self.info_text.pack(anchor="w")

        ki_einstellungen = ttk.LabelFrame(
            hauptbereich,
            text="KI-Einstellungen",
            padding=12,
        )
        ki_einstellungen.pack(
            fill="x",
            pady=(0, 12),
        )

        modell_label = ttk.Label(
            ki_einstellungen,
            text="Whisper-Modell:",
        )
        modell_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
        )

        self.modell_box = ttk.Combobox(
            ki_einstellungen,
            textvariable=self.modell_auswahl,
            values=(
                "Schnell – tiny",
                "Ausgewogen – small",
                "Genauer – medium",
            ),
            state="readonly",
            width=24,
        )
        self.modell_box.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(0, 24),
        )

        sprache_label = ttk.Label(
            ki_einstellungen,
            text="Sprache:",
        )
        sprache_label.grid(
            row=0,
            column=2,
            sticky="w",
            padx=(0, 8),
        )

        self.sprache_box = ttk.Combobox(
            ki_einstellungen,
            textvariable=self.sprache_auswahl,
            values=(
                "Automatisch erkennen",
                "Deutsch",
                "Englisch",
                "Polnisch",
            ),
            state="readonly",
            width=22,
        )
        self.sprache_box.grid(
            row=0,
            column=3,
            sticky="ew",
        )

        ki_einstellungen.columnconfigure(1, weight=1)
        ki_einstellungen.columnconfigure(3, weight=1)

        aktionen = ttk.Frame(hauptbereich)
        aktionen.pack(
            fill="x",
            pady=(0, 12),
        )

        self.analyse_button = ttk.Button(
            aktionen,
            text="Analysieren",
            command=self.analyse_starten,
            state=DISABLED,
        )
        self.analyse_button.pack(side=LEFT)

        self.start_button = ttk.Button(
            aktionen,
            text="👍  Projektpaket erstellen",
            command=self.projekt_starten,
            state=DISABLED,
            style="Gold.TButton",
        )
        self.start_button.pack(
            side=LEFT,
            padx=10,
        )

        self.ki_button = ttk.Button(
            aktionen,
            text="KI-Transkription starten",
            command=self.transkription_starten,
            state=DISABLED,
            style="Tuerkis.TButton",
        )
        self.ki_button.pack(side=LEFT)

        self.ordner_button = ttk.Button(
            aktionen,
            text="Ergebnisordner öffnen",
            command=self.ergebnisordner_oeffnen,
            state=DISABLED,
        )
        self.ordner_button.pack(side=RIGHT)

        datei_aktionen = ttk.Frame(hauptbereich)
        datei_aktionen.pack(
            fill="x",
            pady=(0, 12),
        )

        self.transkript_button = ttk.Button(
            datei_aktionen,
            text="Transkript öffnen",
            command=self.transkript_oeffnen,
            state=DISABLED,
        )
        self.transkript_button.pack(side=LEFT)

        self.untertitel_button = ttk.Button(
            datei_aktionen,
            text="Untertitel öffnen",
            command=self.untertitel_oeffnen,
            state=DISABLED,
        )
        self.untertitel_button.pack(
            side=LEFT,
            padx=(10, 0),
        )

        self.fortschritt = ttk.Progressbar(
            hauptbereich,
            mode="indeterminate",
        )
        self.fortschritt.pack(
            fill="x",
            pady=(0, 8),
        )

        status_label = ttk.Label(
            hauptbereich,
            textvariable=self.status,
            style="Status.TLabel",
        )
        status_label.pack(
            anchor="w",
            pady=(0, 4),
        )

        ki_label = ttk.Label(
            hauptbereich,
            textvariable=self.ki_status,
        )
        ki_label.pack(
            anchor="w",
            pady=(0, 12),
        )

        protokoll_bereich = ttk.LabelFrame(
            hauptbereich,
            text="Protokoll",
            padding=8,
        )
        protokoll_bereich.pack(
            fill=BOTH,
            expand=True,
        )

        self.protokoll = Text(
            protokoll_bereich,
            height=12,
            wrap="word",
            state=DISABLED,
            font=("Consolas", 9),
            background=DUNKEL,
            foreground=TEXT,
            insertbackground=TUERKIS,
            selectbackground=TUERKIS,
            selectforeground=DUNKEL,
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=10,
        )
        self.protokoll.pack(
            fill=BOTH,
            expand=True,
        )

    def log_schreiben(self, text: str) -> None:
        self.protokoll.config(state=NORMAL)
        self.protokoll.insert(END, text + "\n")
        self.protokoll.see(END)
        self.protokoll.config(state=DISABLED)

    def datei_auswaehlen(self) -> None:
        dateiname = filedialog.askopenfilename(
            title="Mediendatei auswählen",
            filetypes=[
                (
                    "Unterstützte Medien",
                    "*.mp4 *.mkv *.webm *.mov",
                ),
                ("MP4-Video", "*.mp4"),
                ("MKV-Video", "*.mkv"),
                ("WebM-Video", "*.webm"),
                ("MOV-Video", "*.mov"),
                ("Alle Dateien", "*.*"),
            ],
        )

        if not dateiname:
            return

        datei = Path(dateiname)

        if (
            datei.suffix.lower()
            not in ERLAUBTE_FORMATE
        ):
            messagebox.showerror(
                "Nicht unterstütztes Format",
                "Bitte wähle eine MP4-, MKV-, "
                "WEBM- oder MOV-Datei aus.",
            )
            return

        self.datei = datei
        self.infos = None
        self.letzte_transkript_datei = None
        self.letzte_untertitel_datei = None
        self.dateipfad.set(str(datei))
        self.status.set("Datei ausgewählt.")

        self.info_text.config(
            text=(
                "Datei ausgewählt. "
                "Jetzt analysieren."
            )
        )

        self.analyse_button.config(state=NORMAL)
        self.start_button.config(state=DISABLED)
        self.ki_button.config(state=DISABLED)
        self.transkript_button.config(state=DISABLED)
        self.untertitel_button.config(state=DISABLED)

        self.log_schreiben(
            f"Datei ausgewählt: {datei.name}"
        )

    def bedienung_sperren(self) -> None:
        self.auswahl_button.config(state=DISABLED)
        self.analyse_button.config(state=DISABLED)
        self.start_button.config(state=DISABLED)
        self.ki_button.config(state=DISABLED)
        self.transkript_button.config(state=DISABLED)
        self.untertitel_button.config(state=DISABLED)
        self.modell_box.config(state=DISABLED)
        self.sprache_box.config(state=DISABLED)
        self.fortschritt.start(12)

    def bedienung_freigeben(self) -> None:
        self.auswahl_button.config(state=NORMAL)
        self.modell_box.config(state="readonly")
        self.sprache_box.config(state="readonly")

        if self.datei:
            self.analyse_button.config(state=NORMAL)

        if self.infos:
            self.start_button.config(state=NORMAL)

        if (
            self.letztes_projekt
            and self.letztes_projekt.get("ki_ok")
        ):
            self.ki_button.config(state=NORMAL)

        if (
            self.letzte_transkript_datei
            and self.letzte_transkript_datei.exists()
        ):
            self.transkript_button.config(state=NORMAL)

        if (
            self.letzte_untertitel_datei
            and self.letzte_untertitel_datei.exists()
        ):
            self.untertitel_button.config(state=NORMAL)

        self.fortschritt.stop()

    def analyse_starten(self) -> None:
        if not self.datei:
            return

        self.bedienung_sperren()

        self.status.set(
            "Mediendatei wird analysiert …"
        )

        self.log_schreiben(
            "Medienanalyse wird gestartet."
        )

        threading.Thread(
            target=self.analyse_worker,
            daemon=True,
        ).start()

    def analyse_worker(self) -> None:
        try:
            if not self.datei:
                raise RuntimeError(
                    "Keine Datei ausgewählt."
                )

            infos = medieninfos_auslesen(self.datei)

            EREIGNISSE.put(
                ("analyse_erfolgreich", infos)
            )

        except Exception as fehler:
            EREIGNISSE.put(
                ("fehler", str(fehler))
            )

    def analyse_anzeigen(
        self,
        infos: dict,
    ) -> None:
        if not self.datei:
            return

        self.infos = infos

        video_stream, audio_stream = (
            streams_finden(infos)
        )

        dauer = zeit_formatieren(
            infos.get(
                "format",
                {},
            ).get(
                "duration",
                0,
            )
        )

        zeilen = [
            f"Dateiname: {self.datei.name}",
            f"Format: {self.datei.suffix.lower()}",
            (
                "Dateigröße: "
                f"{dateigroesse_formatieren(
                    self.datei.stat().st_size
                )}"
            ),
            f"Dauer: {dauer}",
        ]

        if video_stream:
            zeilen.extend(
                [
                    (
                        "Auflösung: "
                        f"{video_stream.get(
                            'width',
                            'unbekannt',
                        )} × "
                        f"{video_stream.get(
                            'height',
                            'unbekannt',
                        )}"
                    ),
                    (
                        "Videocodec: "
                        f"{video_stream.get(
                            'codec_name',
                            'unbekannt',
                        )}"
                    ),
                    (
                        "FPS: "
                        f"{fps_formatieren(
                            video_stream.get(
                                'r_frame_rate',
                                'unbekannt',
                            )
                        )}"
                    ),
                ]
            )
        else:
            zeilen.append(
                "Videospur: nicht vorhanden"
            )

        if audio_stream:
            zeilen.extend(
                [
                    (
                        "Audiocodec: "
                        f"{audio_stream.get(
                            'codec_name',
                            'unbekannt',
                        )}"
                    ),
                    (
                        "Audiokanäle: "
                        f"{audio_stream.get(
                            'channels',
                            'unbekannt',
                        )}"
                    ),
                ]
            )
        else:
            zeilen.append(
                "Tonspur: nicht vorhanden"
            )

        self.info_text.config(
            text="\n".join(zeilen)
        )

        self.status.set(
            "Analyse abgeschlossen."
        )

        self.log_schreiben(
            "Medienanalyse abgeschlossen."
        )

        if audio_stream:
            self.start_button.config(
                state=NORMAL
            )
        else:
            self.start_button.config(
                state=DISABLED
            )

            messagebox.showwarning(
                "Keine Tonspur",
                "Die ausgewählte Datei besitzt "
                "keine Audiospur.",
            )

    def projekt_starten(self) -> None:
        if not self.datei or not self.infos:
            messagebox.showwarning(
                "Analyse erforderlich",
                "Bitte analysiere die Datei zuerst.",
            )
            return

        self.bedienung_sperren()

        self.status.set(
            "Projektstruktur wird erstellt …"
        )

        self.log_schreiben(
            "Projektpaket v1.3 wird erstellt."
        )

        threading.Thread(
            target=self.projekt_worker,
            daemon=True,
        ).start()

    def projekt_worker(self) -> None:
        try:
            if not self.datei or not self.infos:
                raise RuntimeError(
                    "Datei oder Medieninformationen fehlen."
                )

            EREIGNISSE.put(
                (
                    "log",
                    "Projektordner und Unterordner "
                    "werden erstellt …",
                )
            )

            ordner = projektstruktur_erstellen(
                self.datei
            )

            EREIGNISSE.put(
                (
                    "log",
                    "Originalvideo wird in den "
                    "Video-Ordner kopiert …",
                )
            )

            kopierte_videodatei = (
                originaldatei_kopieren(
                    self.datei,
                    ordner["video"],
                )
            )

            EREIGNISSE.put(
                (
                    "log",
                    "Audiospur wird in den "
                    "Audio-Ordner extrahiert …",
                )
            )

            audio_datei = audio_extrahieren(
                self.datei,
                ordner["audio"],
            )

            EREIGNISSE.put(
                (
                    "log",
                    "KI-Installation wird geprüft …",
                )
            )

            ki_ok, ki_meldung = (
                ki_modul_pruefen()
            )

            projektdatei = (
                projektdatei_speichern(
                    ordner=ordner,
                    datei=self.datei,
                    kopierte_videodatei=(
                        kopierte_videodatei
                    ),
                    audio_datei=audio_datei,
                    infos=self.infos,
                    ki_verfuegbar=ki_ok,
                )
            )

            medieninfos_datei = (
                medieninfos_speichern(
                    ordner,
                    self.infos,
                )
            )

            readme = readme_erstellen(
                ordner=ordner,
                datei=self.datei,
                audio_datei=audio_datei,
                ki_verfuegbar=ki_ok,
            )

            logdatei = logdatei_erstellen(
                ordner,
                self.datei,
            )

            EREIGNISSE.put(
                (
                    "log",
                    "Komplette Projektstruktur "
                    "wird als ZIP verpackt …",
                )
            )

            zip_datei = (
                projekt_als_zip_verpacken(
                    ordner["projekt"]
                )
            )

            ergebnis = {
                "projektordner": (
                    ordner["projekt"]
                ),
                "zip_datei": zip_datei,
                "projektdatei": projektdatei,
                "medieninfos": medieninfos_datei,
                "readme": readme,
                "logdatei": logdatei,
                "ki_ok": ki_ok,
                "ki_meldung": ki_meldung,
                "audio_datei": audio_datei,
                "ki_ordner": ordner["ki"],
                "untertitel_ordner": ordner["untertitel"],
            }

            EREIGNISSE.put(
                ("projekt_erfolgreich", ergebnis)
            )

        except Exception as fehler:
            EREIGNISSE.put(
                ("fehler", str(fehler))
            )

    def projekt_fertig(
        self,
        ergebnis: dict,
    ) -> None:
        projektordner = ergebnis[
            "projektordner"
        ]
        zip_datei = ergebnis["zip_datei"]
        ki_ok = ergebnis["ki_ok"]
        ki_meldung = ergebnis["ki_meldung"]

        self.letzter_projektordner = (
            projektordner
        )
        self.letztes_projekt = ergebnis

        self.ki_status.set(ki_meldung)

        self.status.set(
            "Projektstruktur erfolgreich erstellt."
        )

        self.ordner_button.config(
            state=NORMAL
        )

        self.log_schreiben(
            "Ordner Video wurde erstellt."
        )
        self.log_schreiben(
            "Ordner Audio wurde erstellt."
        )
        self.log_schreiben(
            "Ordner Untertitel wurde erstellt."
        )
        self.log_schreiben(
            "Ordner Frames wurde erstellt."
        )
        self.log_schreiben(
            "Ordner Metadaten wurde erstellt."
        )
        self.log_schreiben(
            "Ordner KI wurde erstellt."
        )
        self.log_schreiben(
            "Ordner Logs wurde erstellt."
        )
        self.log_schreiben(
            f"ZIP-Paket: {zip_datei}"
        )

        if ki_ok:
            self.ki_button.config(state=NORMAL)
            zusatz = (
                "\n\nFaster-Whisper ist installiert."
                "\nDu kannst jetzt die KI-Transkription starten."
            )
        else:
            zusatz = (
                "\n\nDie KI-Transkription wird "
                "in einer der nächsten Versionen "
                "eingerichtet."
            )

        messagebox.showinfo(
            "Projekt abgeschlossen",
            (
                "Das AllOiz-Projektpaket v1.3 "
                "wurde erfolgreich erstellt."
                f"\n\nProjektordner:\n"
                f"{projektordner}"
                f"\n\nZIP-Datei:\n"
                f"{zip_datei}"
                f"{zusatz}"
            ),
        )

    def transkription_starten(self) -> None:
        if not self.letztes_projekt:
            messagebox.showwarning(
                "Projekt erforderlich",
                "Bitte erstelle zuerst ein Projektpaket.",
            )
            return

        if not self.letztes_projekt.get("ki_ok"):
            messagebox.showerror(
                "KI-Modul fehlt",
                "Faster-Whisper wurde nicht gefunden.",
            )
            return

        modell_map = {
            "Schnell – tiny": "tiny",
            "Ausgewogen – small": "small",
            "Genauer – medium": "medium",
        }
        sprache_map = {
            "Automatisch erkennen": None,
            "Deutsch": "de",
            "Englisch": "en",
            "Polnisch": "pl",
        }

        self.aktives_modell = modell_map.get(
            self.modell_auswahl.get(),
            "small",
        )
        self.aktive_sprache = sprache_map.get(
            self.sprache_auswahl.get()
        )

        self.bedienung_sperren()
        self.status.set("KI-Transkription läuft …")
        self.log_schreiben(
            "Lokale KI-Transkription wird gestartet. "
            f"Modell: {self.aktives_modell}, "
            f"Sprache: {self.aktive_sprache or 'automatisch'}."
        )

        threading.Thread(
            target=self.transkription_worker,
            daemon=True,
        ).start()

    def transkription_worker(self) -> None:
        try:
            if not self.letztes_projekt:
                raise RuntimeError("Projektdaten fehlen.")

            def fortschritt(text: str) -> None:
                EREIGNISSE.put(("log", text))

            ergebnis = transkribieren(
                audio_datei=self.letztes_projekt[
                    "audio_datei"
                ],
                ki_ordner=self.letztes_projekt[
                    "ki_ordner"
                ],
                untertitel_ordner=self.letztes_projekt[
                    "untertitel_ordner"
                ],
                modell_name=self.aktives_modell,
                sprache=self.aktive_sprache,
            )

            fortschritt(
                "Transkript und SRT-Untertitel wurden erstellt."
            )

            zip_datei = projekt_als_zip_verpacken(
                self.letztes_projekt["projektordner"]
            )
            ergebnis["zip_datei"] = zip_datei

            EREIGNISSE.put(
                ("transkription_erfolgreich", ergebnis)
            )

        except Exception as fehler:
            EREIGNISSE.put(("fehler", str(fehler)))

    def transkription_fertig(self, ergebnis: dict) -> None:
        sprache = ergebnis.get("sprache", "unbekannt")
        modell = ergebnis.get("modell", "unbekannt")
        txt_datei = ergebnis["txt_datei"]
        srt_datei = ergebnis["srt_datei"]

        self.letzte_transkript_datei = Path(txt_datei)
        self.letzte_untertitel_datei = Path(srt_datei)
        self.transkript_button.config(state=NORMAL)
        self.untertitel_button.config(state=NORMAL)

        self.status.set(
            "KI-Transkription erfolgreich abgeschlossen."
        )
        self.ki_status.set(
            f"Erkannte Sprache: {sprache} | Modell: {modell}"
        )
        self.log_schreiben(f"Transkript: {txt_datei}")
        self.log_schreiben(f"Untertitel: {srt_datei}")
        self.log_schreiben(
            "ZIP-Paket wurde mit den KI-Dateien aktualisiert."
        )

        messagebox.showinfo(
            "Transkription abgeschlossen",
            (
                "Die lokale KI-Transkription ist fertig."
                f"\n\nErkannte Sprache: {sprache}"
                f"\nVerwendetes Modell: {modell}"
                f"\n\nTranskript:\n{txt_datei}"
                f"\n\nUntertitel:\n{srt_datei}"
            ),
        )

    def datei_oeffnen(
        self,
        datei: Path | None,
        bezeichnung: str,
    ) -> None:
        if not datei or not datei.exists():
            messagebox.showerror(
                "Datei nicht gefunden",
                f"Die {bezeichnung} wurde nicht gefunden.",
            )
            return

        try:
            os.startfile(str(datei))

        except OSError as fehler:
            messagebox.showerror(
                "Datei konnte nicht geöffnet werden",
                str(fehler),
            )

    def transkript_oeffnen(self) -> None:
        self.datei_oeffnen(
            self.letzte_transkript_datei,
            "Transkriptdatei",
        )

    def untertitel_oeffnen(self) -> None:
        self.datei_oeffnen(
            self.letzte_untertitel_datei,
            "Untertiteldatei",
        )

    def ergebnisordner_oeffnen(self) -> None:
        if not self.letzter_projektordner:
            return

        try:
            subprocess.Popen(
                [
                    "explorer",
                    str(
                        self.letzter_projektordner
                    ),
                ]
            )

        except OSError as fehler:
            messagebox.showerror(
                "Ordner konnte nicht geöffnet werden",
                str(fehler),
            )

    def ereignisse_pruefen(self) -> None:
        try:
            while True:
                typ, daten = (
                    EREIGNISSE.get_nowait()
                )

                if typ == "analyse_erfolgreich":
                    self.analyse_anzeigen(daten)

                elif typ == "projekt_erfolgreich":
                    self.projekt_fertig(daten)

                elif typ == "transkription_erfolgreich":
                    self.transkription_fertig(daten)

                elif typ == "log":
                    self.log_schreiben(
                        str(daten)
                    )

                elif typ == "fehler":
                    self.status.set(
                        "Fehler aufgetreten."
                    )

                    self.log_schreiben(
                        f"FEHLER: {daten}"
                    )

                    messagebox.showerror(
                        "AllOiz-Fehler",
                        str(daten),
                    )

                self.bedienung_freigeben()

        except Empty:
            pass

        self.fenster.after(
            150,
            self.ereignisse_pruefen,
        )


def main() -> None:
    fenster = Tk()

    try:
        stil = ttk.Style(fenster)

        if "vista" in stil.theme_names():
            stil.theme_use("vista")

        AllOizApp(fenster)
        fenster.mainloop()

    except Exception as fehler:
        messagebox.showerror(
            "AllOiz MediaSync",
            (
                "Das Programm konnte nicht "
                "gestartet werden:\n\n"
                f"{fehler}"
            ),
        )


if __name__ == "__main__":
    main()
