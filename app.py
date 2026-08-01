from pathlib import Path
import json
import os
import subprocess
import sys


APP_NAME = "AllOiz MediaSync"
VERSION = "0.9"

ERLAUBTE_FORMATE = {
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
}


def zeit_formatieren(sekunden: float) -> str:
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
        check=True,
    )

    return json.loads(ergebnis.stdout)


def projektordner_erstellen(datei: Path) -> Path:
    hauptordner = Path("AllOiz_Projekte")
    hauptordner.mkdir(exist_ok=True)

    projektordner = hauptordner / datei.stem
    projektordner.mkdir(exist_ok=True)

    return projektordner


def audio_extrahieren(
    datei: Path,
    projektordner: Path,
) -> Path:
    ausgabe = projektordner / f"{datei.stem}.wav"

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

    subprocess.run(
        befehl,
        capture_output=True,
        text=True,
        check=True,
    )

    return ausgabe


def ki_modul_pruefen() -> tuple[bool, str]:
    test_code = (
        "from faster_whisper import WhisperModel; "
        "print('KI_OK')"
    )

    umgebung = os.environ.copy()
    umgebung["CT2_FORCE_CPU_ISA"] = "GENERIC"

    ergebnis = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        text=True,
        env=umgebung,
    )

    if ergebnis.returncode == 0 and "KI_OK" in ergebnis.stdout:
        return True, "Faster-Whisper ist verfügbar."

    if ergebnis.returncode < 0:
        return (
            False,
            "Der Prozessor unterstützt das KI-Modul nicht.",
        )

    fehlermeldung = ergebnis.stderr.strip()

    if not fehlermeldung:
        fehlermeldung = "Das KI-Modul konnte nicht geladen werden."

    return False, fehlermeldung


def projektdatei_speichern(
    projektordner: Path,
    datei: Path,
    audio_datei: Path,
    dauer: str,
    video_stream: dict | None,
    audio_stream: dict | None,
    ki_verfuegbar: bool,
) -> Path:
    projekt_daten = {
        "programm": APP_NAME,
        "version": VERSION,
        "projektname": datei.stem,
        "originaldatei": str(datei.resolve()),
        "dateiname": datei.name,
        "format": datei.suffix.lower(),
        "dateigroesse_bytes": datei.stat().st_size,
        "dauer": dauer,
        "wav_datei": audio_datei.name,
        "ki_lokal_verfuegbar": ki_verfuegbar,
        "status": (
            "Bereit für lokale Transkription"
            if ki_verfuegbar
            else "Bereit für Transkription auf dem Haupt-PC"
        ),
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

    projektdatei = projektordner / "projekt.json"

    projektdatei.write_text(
        json.dumps(
            projekt_daten,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return projektdatei


print("=" * 50)
print(f"          {APP_NAME} v{VERSION}")
print("=" * 50)
print()

datei_eingabe = input(
    "Pfad zur Mediendatei: "
).strip()

datei = Path(datei_eingabe)

if not datei.is_file():
    print()
    print("Fehler: Die Datei wurde nicht gefunden.")
    raise SystemExit(1)

if datei.suffix.lower() not in ERLAUBTE_FORMATE:
    print()
    print("Fehler: Dieses Dateiformat wird nicht unterstützt.")
    print("Erlaubt sind: MP4, MKV, WEBM und MOV.")
    raise SystemExit(1)

try:
    infos = medieninfos_auslesen(datei)

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

    dauer = zeit_formatieren(
        infos.get("format", {}).get("duration", 0)
    )

    print()
    print("Datei gefunden!")
    print(f"Dateiname: {datei.name}")
    print(f"Format: {datei.suffix.lower()}")
    print(f"Ordner: {datei.parent}")
    print(f"Dateigröße: {datei.stat().st_size} Bytes")
    print(f"Dauer: {dauer}")

    if video_stream:
        breite = video_stream.get("width", "unbekannt")
        hoehe = video_stream.get("height", "unbekannt")

        print(f"Auflösung: {breite} x {hoehe}")
        print(
            "Videocodec: "
            f"{video_stream.get('codec_name', 'unbekannt')}"
        )

        fps = fps_formatieren(
            video_stream.get(
                "r_frame_rate",
                "unbekannt",
            )
        )

        print(f"FPS: {fps}")
    else:
        print("Videospur: Nein")

    if not audio_stream:
        print("Tonspur: Nein")
        print("Ohne Tonspur kann kein Projekt erstellt werden.")
        raise SystemExit(0)

    print(
        "Audiocodec: "
        f"{audio_stream.get('codec_name', 'unbekannt')}"
    )
    print("Tonspur: Ja")

    print()
    antwort = input(
        "AllOiz-Projekt erstellen? (j/n): "
    ).strip().lower()

    if antwort != "j":
        print()
        print("Projekterstellung abgebrochen.")
        raise SystemExit(0)

    projektordner = projektordner_erstellen(datei)

    print()
    print("Projektordner wurde erstellt:")
    print(projektordner)

    print()
    print("Audio wird vorbereitet...")

    audio_datei = audio_extrahieren(
        datei,
        projektordner,
    )

    print("Audio erfolgreich extrahiert!")
    print(f"WAV-Datei: {audio_datei.name}")

    print()
    print("=" * 50)
    print("                 KI-Prüfung")
    print("=" * 50)

    ki_ok, ki_meldung = ki_modul_pruefen()

    print()
    print(ki_meldung)

    projektdatei = projektdatei_speichern(
        projektordner=projektordner,
        datei=datei,
        audio_datei=audio_datei,
        dauer=dauer,
        video_stream=video_stream,
        audio_stream=audio_stream,
        ki_verfuegbar=ki_ok,
    )

    print()
    print("=" * 50)
    print("              Projekt abgeschlossen")
    print("=" * 50)
    print()
    print(f"Projektordner: {projektordner}")
    print(f"WAV-Datei: {audio_datei.name}")
    print(f"Projektdatei: {projektdatei.name}")

    if ki_ok:
        print()
        print("Dieses Gerät kann die Transkription übernehmen.")
    else:
        print()
        print("Der Projektordner kann jetzt auf den")
        print("Haupt-PC kopiert und dort transkribiert werden.")

    print()
    print("Onkel Alois sagt:")
    print('"Alles eingepackt. Ab zum großen Rechner!"')

except subprocess.CalledProcessError as fehler:
    print()
    print("Fehler: FFmpeg oder ffprobe konnte die Datei")
    print("nicht richtig verarbeiten.")

    if fehler.stderr:
        print(fehler.stderr)

except json.JSONDecodeError:
    print()
    print("Fehler: Die Medieninformationen waren ungültig.")

except OSError as fehler:
    print()
    print("Fehler beim Erstellen oder Speichern des Projekts:")
    print(fehler)

except Exception as fehler:
    print()
    print("Unerwarteter Fehler:")
    print(fehler)
