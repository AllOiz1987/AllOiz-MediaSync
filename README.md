# AllOiz MediaSync

**Alle Medien. Eine Sprache.**

AllOiz MediaSync ist eine lokale Windows-Anwendung zur Analyse, Vorbereitung und KI-gestützten Transkription von Mediendateien.

Die Verarbeitung erfolgt direkt auf dem eigenen Rechner. Ausgewählte Videos und Audiodateien werden nicht automatisch an einen externen Transkriptionsdienst übertragen.

## Aktuelle Version

**Version 1.6 – Portable Windows-Version**

Version 1.6 enthält FFmpeg und FFprobe direkt im Programmpaket. Für die Nutzung der fertigen Windows-Version müssen Python, Git, FFmpeg und FFprobe daher nicht separat installiert werden.

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
- portable Windows-Anwendung ohne separate Python-Installation
- FFmpeg und FFprobe im Windows-Paket integriert

## Whisper-Modelle

AllOiz bietet aktuell drei Modelle an:

- `tiny` – besonders schnell, aber weniger genau
- `small` – ausgewogen und als Standard empfohlen
- `medium` – genauer, benötigt aber mehr Speicher und Rechenzeit

Beim ersten Einsatz eines Modells muss es einmalig aus dem Internet heruntergeladen werden. Danach kann es lokal weiterverwendet werden.

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

## Installation der portablen Windows-Version

1. Auf der GitHub-Seite unter **Releases** die ZIP-Datei für Version 1.6 herunterladen.
2. Die ZIP-Datei vollständig entpacken.
3. Den enthaltenen Programmordner zusammenlassen und keine internen Dateien einzeln verschieben.
4. `AllOiz-MediaSync.exe` starten.

Beim ersten Start kann Windows eine Sicherheitswarnung anzeigen, da die Anwendung noch nicht digital signiert ist.

Für die fertige Windows-Version werden nicht separat benötigt:

- Python
- Git
- FFmpeg
- FFprobe

Eine Internetverbindung wird beim ersten Einsatz eines Whisper-Modells benötigt, damit das gewählte Modell heruntergeladen werden kann. Die anschließende Transkription erfolgt lokal.

## Bedienung

1. Mediendatei auswählen
2. Datei analysieren
3. Whisper-Modell und Sprache festlegen
4. Projektpaket erstellen
5. KI-Transkription starten
6. Transkript oder Untertitel direkt öffnen
7. Ergebnisordner bei Bedarf anzeigen

## Installation für die Entwicklung

Zum Starten direkt aus dem Python-Quellcode werden benötigt:

- Windows 10 oder Windows 11
- Python 3
- die Python-Abhängigkeiten aus `requirements.txt`
- FFmpeg und FFprobe im Systempfad oder unter `vendor/ffmpeg/`
- Internetverbindung beim erstmaligen Herunterladen eines Whisper-Modells

Git wird nur benötigt, wenn das Repository geklont, aktualisiert oder weiterentwickelt werden soll.

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

Programm starten:

```bash
python app.py
```

## Datenschutz

Die Medienverarbeitung und KI-Transkription erfolgen lokal auf dem Rechner.

AllOiz MediaSync lädt ausgewählte Mediendateien nicht automatisch zu einem externen Transkriptionsdienst hoch. Nur beim erstmaligen Laden eines Whisper-Modells wird eine Internetverbindung benötigt.

## Drittanbieter und Lizenzen

Die portable Windows-Version enthält separate ausführbare Dateien von FFmpeg und FFprobe. Diese Bestandteile werden unter der GNU General Public License Version 3 (GPLv3) bereitgestellt.

Die zugehörigen Hinweise und der Lizenztext befinden sich im Programmordner unter:

- `licenses/GPL-3.0.txt`
- `licenses/THIRD_PARTY_NOTICES.txt`

Weitere Informationen zum FFmpeg-Projekt: [ffmpeg.org](https://ffmpeg.org/)

## Roadmap

Geplante spätere Funktionen:

- Übersetzung erkannter Texte
- KI-Sprachausgabe
- automatische Synchronisation
- verbesserte Fortschrittsanzeige
- weitere Sprachen
- vereinfachte Installation und automatische Updates

## Projektstatus

AllOiz MediaSync befindet sich in aktiver Entwicklung.

Version 1.6 ist als portable Windows-Anwendung funktionsfähig. Medienanalyse, Projektaufbau, lokale Transkription, TXT-Transkripte und SRT-Untertitel wurden erfolgreich getestet.
