# AllOiz MediaSync

**Alle Medien. Eine Sprache.**

AllOiz MediaSync ist eine lokale Windows-Anwendung zur Analyse, Vorbereitung und KI-gestützten Transkription von Mediendateien.

Die Verarbeitung erfolgt direkt auf dem eigenen Rechner. Für die Transkription müssen keine Videos oder Audiodateien an einen kostenpflichtigen Onlinedienst übertragen werden.

## Aktueller Entwicklungsstand

**Version 1.4**

Version 1.4 befindet sich derzeit im Entwicklungszweig `version-1.4`.

## Funktionen

- moderne grafische Windows-Oberfläche
- AllOiz-Design in Charcoal, Gold und Türkis
- eigener Startbildschirm
- MP4-, MKV-, WebM- und MOV-Dateien auswählen
- Medieninformationen mit FFprobe auslesen
- Videoauflösung, Codec, FPS und Tonspur anzeigen
- Audiospur mit FFmpeg als WAV extrahieren
- vollständige Projektstruktur automatisch erstellen
- lokale KI-Transkription mit Faster-Whisper
- automatische Spracherkennung
- manuelle Auswahl für Deutsch, Englisch und Polnisch
- auswählbare Whisper-Modelle
- Transkript als TXT-Datei erstellen
- zeitcodierte Untertitel als SRT-Datei erstellen
- Transkript und Untertitel direkt aus AllOiz öffnen
- überlange Dateinamen automatisch kürzen
- Metadaten und Projektinformationen speichern
- fertiges Projekt als ZIP-Datei verpacken

## Whisper-Modelle

AllOiz bietet aktuell drei Modelle an:

- `tiny` – besonders schnell, aber weniger genau
- `small` – ausgewogen und als Standard empfohlen
- `medium` – genauer, benötigt aber mehr Speicher und Rechenzeit

Beim ersten Einsatz eines Modells muss es einmalig heruntergeladen werden. Danach kann es lokal weiterverwendet werden.

## Projektstruktur

Für jede Mediendatei erstellt AllOiz automatisch einen eigenen Projektordner:

```text
AllOiz_Projekte/
└── Projektname/
    ├── Video/
    ├── Audio/
    ├── Untertitel/
    ├── Frames/
    ├── Metadaten/
    ├── KI/
    ├── Logs/
    └── README.txt

```

Das fertige Projekt wird zusätzlich als ZIP-Datei gespeichert.

## Voraussetzungen für die aktuelle Entwicklerversion

Zum Starten direkt aus dem Python-Quellcode werden aktuell benötigt:

- Windows 10 oder Windows 11
- Python 3
- FFmpeg und FFprobe
- Internetverbindung beim erstmaligen Herunterladen eines Whisper-Modells

Git wird nur benötigt, wenn das Repository geklont, aktualisiert oder weiterentwickelt werden soll.

Für eine spätere eigenständige Windows-EXE sollen Python, Git und FFmpeg nicht mehr separat durch den Nutzer eingerichtet werden müssen.

## Installation für die Entwicklung

Repository herunterladen:

```bash
git clone https://github.com/AllOiz1987/AllOiz-MediaSync.git
cd AllOiz-MediaSync
```

Virtuelle Python-Umgebung erstellen:

```bash
python -m venv .venv
```

Virtuelle Umgebung unter Windows aktivieren:

```bash
.venv\Scripts\activate
```

Python-Abhängigkeiten installieren:

```bash
python -m pip install -r requirements.txt
```

## Programm starten

```bash
python app.py
```

## Bedienung

1. Mediendatei auswählen
2. Datei analysieren
3. Whisper-Modell und Sprache festlegen
4. Projektpaket erstellen
5. KI-Transkription starten
6. Transkript oder Untertitel direkt öffnen
7. Ergebnisordner bei Bedarf anzeigen

## Datenschutz

Die Medienverarbeitung und KI-Transkription erfolgen lokal auf dem Rechner.

AllOiz MediaSync lädt ausgewählte Mediendateien nicht automatisch zu einem externen Transkriptionsdienst hoch.

## Roadmap

Geplante spätere Funktionen:

- Übersetzung erkannter Texte
- KI-Sprachausgabe
- automatische Synchronisation
- verbesserte Fortschrittsanzeige
- weitere Sprachen
- Export als eigenständige Windows-EXE

## Projektstatus

AllOiz MediaSync befindet sich in aktiver Entwicklung.

Die Grundfunktionen für Medienanalyse, Projektaufbau, lokale Transkription und SRT-Untertitel sind bereits funktionsfähig.