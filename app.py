from pathlib import Path
import json
import os
import subprocess
import sys


APP_NAME = "AllOiz MediaSync"
VERSION = "0.8"

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


def audio_extrahieren(datei: Path) -> Path:
    ausgabe = datei.with_suffix(".wav")

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
        fehlermeldung = "Unbekannter Fehler beim Laden des KI-Moduls."

    return False, fehlermeldung


def srt_zeit(sekunden: float) -> str:
    millisekunden = int((sekunden % 1) * 1000)
    gesamt = int(sekunden)

    stunden, rest = divmod(gesamt, 3600)
    minuten, sekunden = divmod(rest, 60)

    return (
        f"{stunden:02d}:{minuten:02d}:{sekunden:02d},"
        f"{millisekunden:03d}"
    )


def transkribieren(audio_datei: Path) -> tuple[Path, str]:
    from faster_whisper import WhisperModel

    print()
    print("Lade Whisper-Modell...")
    print("Beim ersten Start wird das Modell heruntergeladen.")

    modell = WhisperModel(
        "tiny",
        device="cpu",
        compute_type="int8",
    )

    print("Transkription läuft...")

    segmente, info = modell.transcribe(
        str(audio_datei),
        beam_size=5,
        vad_filter=True,
    )

    srt_datei = audio_datei.with_suffix(".srt")
    text_datei = audio_datei.with_suffix(".txt")

    alle_texte = []

    with srt_datei.open(
        "w",
        encoding="utf-8",
    ) as srt:
        for nummer, segment in enumerate(segmente, start=1):
            text = segment.text.strip()

            if not text:
                continue

            alle_texte.append(text)

            srt.write(f"{nummer}\n")
            srt.write(
                f"{srt_zeit(segment.start)} --> "
                f"{srt_zeit(segment.end)}\n"
            )
            srt.write(f"{text}\n\n")

    text_datei.write_text(
        "\n".join(alle_texte),
        encoding="utf-8",
    )

    return srt_datei, info.language


print("=" * 46)
print(f"       {APP_NAME} v{VERSION}")
print("=" * 46)
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

    video_stream = next(
        (
            stream
            for stream in infos.get("streams", [])
            if stream.get("codec_type") == "video"
        ),
        None,
    )

    audio_stream = next(
        (
            stream
            for stream in infos.get("streams", [])
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
            f"Videocodec: "
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
        print("Ohne Tonspur ist keine Transkription möglich.")
        raise SystemExit(0)

    print(
        f"Audiocodec: "
        f"{audio_stream.get('codec_name', 'unbekannt')}"
    )
    print("Tonspur: Ja")

    print()
    antwort = input(
        "Audio als WAV extrahieren? (j/n): "
    ).strip().lower()

    if antwort != "j":
        print()
        print("Audioextraktion übersprungen.")
        raise SystemExit(0)

    audio_datei = audio_extrahieren(datei)

    print()
    print("Audio erfolgreich extrahiert!")
    print(f"Ausgabedatei: {audio_datei.name}")

    print()
    print("=" * 46)
    print("              KI-Prüfung")
    print("=" * 46)

    ki_ok, meldung = ki_modul_pruefen()

    if not ki_ok:
        print()
        print("KI-Modul nicht verfügbar.")
        print(meldung)
        print()
        print("Die WAV-Datei wurde trotzdem vorbereitet.")
        print("Sie kann auf dem Haupt-PC transkribiert werden.")
        print()
        print("Onkel Alois sagt:")
        print('"Dann macht dat eben der große Rechner!"')
        raise SystemExit(0)

    print()
    print("KI-Modul verfügbar.")
    print("Faster-Whisper kann gestartet werden.")

    print()
    start = input(
        "Echte Spracherkennung starten? (j/n): "
    ).strip().lower()

    if start != "j":
        print()
        print("Spracherkennung übersprungen.")
        raise SystemExit(0)

    srt_datei, sprache = transkribieren(audio_datei)

    print()
    print("=" * 46)
    print("         Transkription abgeschlossen")
    print("=" * 46)
    print()
    print(f"Erkannte Sprache: {sprache}")
    print(f"Untertiteldatei: {srt_datei.name}")
    print(f"Textdatei: {audio_datei.with_suffix('.txt').name}")
    print()
    print("Onkel Alois sagt:")
    print('"Dat wurde wirklich verstanden!"')

except subprocess.CalledProcessError as fehler:
    print()
    print("Fehler: FFmpeg oder ffprobe konnte die Datei")
    print("nicht richtig verarbeiten.")

    if fehler.stderr:
        print(fehler.stderr)

except json.JSONDecodeError:
    print()
    print("Fehler: Die Medieninformationen waren ungültig.")

except Exception as fehler:
    print()
    print("Unerwarteter Fehler:")
    print(fehler)
