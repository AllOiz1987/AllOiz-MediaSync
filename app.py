from pathlib import Path

print("================================")
print("       DokuSync v0.2")
print("================================")

video_eingabe = input("Pfad zur Videodatei: ").strip()
video = Path(video_eingabe)

if video.is_file():
    print()
    print("Video gefunden!")
    print(f"Dateiname: {video.name}")
    print(f"Ordner: {video.parent}")
    print(f"Dateigröße: {video.stat().st_size} Bytes")
else:
    print()
    print("Fehler: Die Videodatei wurde nicht gefunden.")
