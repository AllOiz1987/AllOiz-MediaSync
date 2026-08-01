from pathlib import Path
import json
import subprocess

APP_NAME = "AllOiz MediaSync"
VERSION = "0.5"

ERLAUBTE_FORMATE = {".mp4", ".mkv", ".webm", ".mov"}


def medieninfos_auslesen(datei: Path) -> dict:
    befehl = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(datei),
    ]

    ergebnis = subprocess.run(
        befehl,
        capture_output=True,
        text=True,
        check=True,
    )

    return json.loads(ergebnis.stdout)


def sekunden_formatieren(sekunden: float) -> str:
    gesamtsekunden = int(float(sekunden))
    stunden, rest = divmod(gesamtsekunden, 3600)
    minuten, sekunden = divmod(rest, 60)

    return f"{stunden:02d}:{minuten:02d}:{sekunden:02d}"


def fps_formatieren(fps_wert: str) -> str:
    try:
        zaehler, nenner = fps_wert.split("/")
        fps = float(zaehler) / float(nenner)
        return f"{fps:g}"
    except (ValueError, ZeroDivisionError):
        return fps_wert


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


print("=" * 44)
print(f"       {APP_NAME} v{VERSION}")
print("=" * 44)

datei_eingabe = input("Pfad zur Mediendatei: ").strip()
datei = Path(datei_eingabe)

if not datei.is_file():
    print()
    print("Fehler: Die Datei wurde nicht gefunden.")

elif datei.suffix.lower() not in ERLAUBTE_FORMATE:
    print()
    print("Fehler: Dieses Dateiformat wird noch nicht unterstützt.")
    print("Erlaubt sind: MP4, MKV, WEBM und MOV.")

else:
    try:
        infos = medieninfos_auslesen(datei)

        video_stream = next(
            (
                stream
                for stream in infos["streams"]
                if stream["codec_type"] == "video"
            ),
            None,
        )

        audio_stream = next(
            (
                stream
                for stream in infos["streams"]
                if stream["codec_type"] == "audio"
            ),
            None,
        )

        dauer = sekunden_formatieren(
            infos["format"].get("duration", 0)
        )

        print()
        print("Datei gefunden!")
        print(f"Dateiname: {datei.name}")
        print(f"Format: {datei.suffix.lower()}")
        print(f"Ordner: {datei.parent}")
        print(f"Dateigröße: {datei.stat().st_size} Bytes")
        print(f"Dauer: {dauer}")

        if video_stream:
            print(
                f"Auflösung: "
                f"{video_stream['width']} x {video_stream['height']}"
            )
            print(f"Videocodec: {video_stream['codec_name']}")

            fps = fps_formatieren(
                video_stream.get("r_frame_rate", "unbekannt")
            )
            print(f"FPS: {fps}")
        else:
            print("Videospur: Nicht vorhanden")

        if audio_stream:
            print(f"Audiocodec: {audio_stream['codec_name']}")
            print("Tonspur: Ja")

            print()
            antwort = input(
                "Audio als WAV extrahieren? (j/n): "
            ).strip().lower()

            if antwort == "j":
                audio_datei = audio_extrahieren(datei)

                print()
                print("Audio erfolgreich extrahiert!")
                print(f"Ausgabedatei: {audio_datei.name}")
            else:
                print()
                print("Audioextraktion übersprungen.")

        else:
            print("Tonspur: Nein")
            print("Eine Audioextraktion ist nicht möglich.")

    except subprocess.CalledProcessError:
        print()
        print("Fehler: FFmpeg konnte die Datei nicht verarbeiten.")

    except (KeyError, ValueError, json.JSONDecodeError):
        print()
        print("Fehler: Die Medieninformationen konnten nicht gelesen werden.")
