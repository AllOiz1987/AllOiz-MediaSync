from __future__ import annotations

from pathlib import Path

from faster_whisper import WhisperModel


STANDARD_MODELL = "small"


def srt_zeit(sekunden: float) -> str:
    """Wandelt Sekunden in das SRT-Zeitformat um."""
    millisekunden_gesamt = max(
        0,
        int(round(sekunden * 1000)),
    )

    stunden, rest = divmod(
        millisekunden_gesamt,
        3_600_000,
    )
    minuten, rest = divmod(rest, 60_000)
    sekunden, millisekunden = divmod(rest, 1000)

    return (
        f"{stunden:02d}:"
        f"{minuten:02d}:"
        f"{sekunden:02d},"
        f"{millisekunden:03d}"
    )


def transkribieren(
    audio_datei: Path,
    ki_ordner: Path,
    untertitel_ordner: Path,
    modell_name: str = STANDARD_MODELL,
    sprache: str | None = None,
) -> dict[str, object]:
    """
    Transkribiert eine Audiodatei und erzeugt
    TXT- und SRT-Dateien.
    """

    if not audio_datei.exists():
        raise FileNotFoundError(
            f"Audiodatei wurde nicht gefunden: "
            f"{audio_datei}"
        )

    ki_ordner.mkdir(
        parents=True,
        exist_ok=True,
    )
    untertitel_ordner.mkdir(
        parents=True,
        exist_ok=True,
    )

    modell = WhisperModel(
        modell_name,
        device="cpu",
        compute_type="int8",
    )

    optionen: dict[str, object] = {
        "beam_size": 5,
        "vad_filter": False,
    }

    if sprache:
        optionen["language"] = sprache

    segmente, info = modell.transcribe(
        str(audio_datei),
        **optionen,
    )

    segment_liste = list(segmente)

    text_zeilen: list[str] = []
    srt_bloecke: list[str] = []

    for nummer, segment in enumerate(
        segment_liste,
        start=1,
    ):
        text = segment.text.strip()

        if not text:
            continue

        text_zeilen.append(text)

        srt_bloecke.append(
            "\n".join(
                [
                    str(nummer),
                    (
                        f"{srt_zeit(segment.start)} --> "
                        f"{srt_zeit(segment.end)}"
                    ),
                    text,
                ]
            )
        )

    txt_datei = (
        ki_ordner
        / f"{audio_datei.stem}_transkript.txt"
    )
    srt_datei = (
        untertitel_ordner
        / f"{audio_datei.stem}_untertitel.srt"
    )

    txt_datei.write_text(
        "\n".join(text_zeilen),
        encoding="utf-8",
    )

    srt_datei.write_text(
        "\n\n".join(srt_bloecke),
        encoding="utf-8",
    )

    return {
        "sprache": info.language,
        "sprachwahrscheinlichkeit": (
            info.language_probability
        ),
        "modell": modell_name,
        "segmente": len(segment_liste),
        "txt_datei": txt_datei,
        "srt_datei": srt_datei,
    }