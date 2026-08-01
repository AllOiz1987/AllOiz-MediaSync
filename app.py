from pathlib import Path

APP_NAME = "AllOiz MediaSync"
VERSION = "0.3"

ERLAUBTE_FORMATE = {".mp4", ".mkv", ".webm", ".mov"}

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
    print()
    print("Datei gefunden!")
    print(f"Dateiname: {datei.name}")
    print(f"Format: {datei.suffix.lower()}")
    print(f"Ordner: {datei.parent}")
    print(f"Dateigröße: {datei.stat().st_size} Bytes")
