from pathlib import Path
import json
import subprocess

APP_NAME = "AllOiz MediaSync"
VERSION = "0.4"

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


print("=" * 40)
print(f"       {APP_NAME} v{VERSION}")
print("=" * 40)

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

        dauer = sekunden_formatieren(infos["format"]["duration"])

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
            print(f"FPS: {video_stream.get('r_frame_rate', 'unbekannt')}")
        else:
            print("Videospur: Nicht vorhanden")

        if audio_stream:
            print(f"Audiocodec: {audio_stream['codec_name']}")
            print("Tonspur: Ja")
        else:
            print("Tonspur: Nein")

    except subprocess.CalledProcessError:
        print()
        print("Fehler: ffprobe konnte die Datei nicht analysieren.")

    except (KeyError, ValueError, json.JSONDecodeError):
        print()
        print("Fehler: Die Medieninformationen konnten nicht gelesen werden.")
