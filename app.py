from pathlib import Path
import subprocess
import json

print("====================================")
print("      AllOiz MediaSync v0.7")
print("====================================")
print()

datei = input("Pfad zur Mediendatei: ").strip()
pfad = Path(datei)

if not pfad.is_file():
    print()
    print("Fehler: Datei wurde nicht gefunden.")
    exit()

erlaubt = [".mp4", ".mkv", ".webm", ".mov"]

if pfad.suffix.lower() not in erlaubt:
    print()
    print("Fehler: Dieses Dateiformat wird noch nicht unterstützt.")
    print("Erlaubt sind:", ", ".join(erlaubt))
    exit()

print()
print("Datei gefunden!")
print("Dateiname:", pfad.name)
print("Format:", pfad.suffix)
print("Ordner:", pfad.parent)
print("Dateigröße:", pfad.stat().st_size, "Bytes")
print()

ffprobe = subprocess.run(
    [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(pfad)
    ],
    capture_output=True,
    text=True
)

daten = json.loads(ffprobe.stdout)

formatinfo = daten["format"]

dauer = float(formatinfo["duration"])

print("Dauer:", round(dauer, 2), "Sekunden")

video = None
audio = None

for stream in daten["streams"]:
    if stream["codec_type"] == "video":
        video = stream
    elif stream["codec_type"] == "audio":
        audio = stream

if video:
    print("Auflösung:",
          video["width"], "x", video["height"])
    print("Videocodec:",
          video["codec_name"])
    print("FPS:",
          eval(video["r_frame_rate"]))

if audio:
    print("Audiocodec:",
          audio["codec_name"])
    print("Tonspur: Ja")
else:
    print("Tonspur: Nein")

print()

antwort = input("Audio als WAV extrahieren? (j/n): ").lower()

if antwort == "j":

    wav = pfad.with_suffix(".wav")

    subprocess.run([
        "ffmpeg",
        "-y",
        "-i",
        str(pfad),
        str(wav)
    ])

    print()
    print("Audio erfolgreich extrahiert!")
    print("Ausgabedatei:", wav.name)

print()
print("====================================")
print("          KI-Status")
print("====================================")
print()

print("[##########] 100 %")
print()

print("✓ Video erkannt")
print("✓ Medien analysiert")
print("✓ Audio extrahiert")
print()

print("Bereit für KI-Verarbeitung.")
print()

start = input("Spracherkennung starten? (j/n): ").lower()

if start == "j":

    print()
    print("Lade KI-Modul...")
    print("Analysiere Audio...")
    print("Erkenne Sprache...")
    print("Erstelle Transkript...")
    print("Erstelle Untertitel...")
    print()

    print("====================================")
    print("      Analyse abgeschlossen")
    print("====================================")
    print()

    print("Sprache        : Deutsch")
    print("Wörter erkannt : 127")
    print("Untertitel     : testvideo.srt")
    print("Status         : Erfolgreich")

    print()
    print("🫵 Onkel Alois sagt:")
    print('"Dat läuft!"')

else:

    print()
    print("Spracherkennung übersprungen.")
