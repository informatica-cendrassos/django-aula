# This Python file uses the following encoding: utf-8

#Genera un PDF amb lavaluació qualitativa visible per a una família.
import io
import textwrap
from datetime import datetime

import matplotlib
from django.http import FileResponse
from django.utils.text import slugify

from aula.utils.tools import unicode

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402


PAGE_SIZE = (8.27, 11.69)  # A4 vertical
LEFT_MARGIN = 0.06
TITLE_TOP = 0.95
BODY_TOP = 0.86
BODY_FONT_SIZE = 10
TITLE_FONT_SIZE = 18
SUBTITLE_FONT_SIZE = 10
LINES_PER_PAGE = 42
WRAP_WIDTH = 92


def _wrap_lines(lines):
    wrapped = []
    for line in lines:
        if not line:
            wrapped.append("")
            continue
        parts = textwrap.wrap(
            line,
            width=WRAP_WIDTH,
            break_long_words=False,
            break_on_hyphens=False,
        )
        wrapped.extend(parts or [""])
    return wrapped


def _paginate_lines(lines):
    if not lines:
        return [[]]
    return [lines[i : i + LINES_PER_PAGE] for i in range(0, len(lines), LINES_PER_PAGE)]


def _render_page(pdf, title, subtitles, body_lines):
    fig = plt.figure(figsize=PAGE_SIZE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    fig.text(
        LEFT_MARGIN,
        TITLE_TOP,
        title,
        fontsize=TITLE_FONT_SIZE,
        fontweight="bold",
        ha="left",
        va="top",
    )

    subtitle_y = TITLE_TOP - 0.055
    for subtitle in subtitles:
        if subtitle.startswith("Alumne: "):
            prefix, value = subtitle.split(": ", 1)
            fig.text(
                LEFT_MARGIN,
                subtitle_y,
                prefix + ": ",
                fontsize=SUBTITLE_FONT_SIZE,
                ha="left",
                va="top",
            )
            fig.text(
                LEFT_MARGIN + 0.12,
                subtitle_y,
                value,
                fontsize=SUBTITLE_FONT_SIZE,
                fontweight="bold",
                ha="left",
                va="top",
            )
        else:
            fig.text(
                LEFT_MARGIN,
                subtitle_y,
                subtitle,
                fontsize=SUBTITLE_FONT_SIZE,
                ha="left",
                va="top",
            )
        subtitle_y -= 0.028

    if body_lines:
        y = BODY_TOP
        for line in body_lines:
            if not line:
                y -= 0.016
                continue
            if line.startswith("Matèria: "):
                prefix, value = line.split(": ", 1)
                fig.text(LEFT_MARGIN, y, prefix + ": " + value, fontsize=BODY_FONT_SIZE, fontweight="bold", ha="left", va="top")
            else:
                fig.text(LEFT_MARGIN, y, line, fontsize=BODY_FONT_SIZE, ha="left", va="top")
            y -= 0.022

    pdf.savefig(fig)
    plt.close(fig)


def _get_qualitatives_amb_resposta(alumne):
    qualitatives = {}
    for resposta in (
        alumne.respostaavaluacioqualitativa_set.select_related("qualitativa")
        .all()
        .order_by("qualitativa__data_obrir_avaluacio", "assignatura__nom_assignatura")
    ):
        qualitativa = resposta.qualitativa
        if not qualitativa.data_obrir_portal_families:
            continue
        if not qualitativa.data_tancar_tancar_portal_families:
            continue
        qualitatives[qualitativa.pk] = qualitativa
    return sorted(
        qualitatives.values(),
        key=lambda q: (q.data_obrir_avaluacio, q.nom_avaluacio),
    )


def _build_body_lines(alumne):
    lines = []
    qualitatives = _get_qualitatives_amb_resposta(alumne)

    if not qualitatives:
        lines.append(
            "No hi ha cap avaluació qualitativa disponible per a aquest alumne."
        )
        return lines

    respostes = list(
        alumne.respostaavaluacioqualitativa_set.select_related(
            "qualitativa",
            "assignatura",
            "item",
            "professor",
        )
        .filter(qualitativa__in=qualitatives)
        .order_by(
            "qualitativa__data_obrir_avaluacio",
            "qualitativa__nom_avaluacio",
            "assignatura__nom_assignatura",
            "professor__last_name",
            "professor__first_name",
            "item__text",
        )
    )

    from itertools import groupby

    for qualitativa in qualitatives:
        respostes_qualitativa = [
            resposta for resposta in respostes if resposta.qualitativa_id == qualitativa.pk
        ]
        if not respostes_qualitativa:
            continue

        lines.append("")
        lines.append(f"Avaluació: {unicode(qualitativa.nom_avaluacio)}")

        for _, respostes_assignatura in groupby(
            respostes_qualitativa, key=lambda r: r.assignatura_id
        ):
            respostes_assignatura = list(respostes_assignatura)
            assignatura = respostes_assignatura[0].assignatura
            lines.append(f"Matèria: {unicode(assignatura)}")
            for resposta in respostes_assignatura:
                lines.append(f"  - {unicode(resposta.get_resposta_display())}")

    return lines


def genera_pdf_qualitativa(alumne, request=None):
    """Genera un PDF amb la informació qualitativa visible per a una família."""

    title = "Avaluació qualitativa"
    subtitles = [
        "Alumne: {0}".format(unicode(alumne)),
        "Grup: {0}".format(unicode(alumne.grup)),
    ]

    body_lines = _wrap_lines(_build_body_lines(alumne))
    pages = _paginate_lines(body_lines)

    buf = io.BytesIO()
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages(buf) as pdf:
        for page in pages:
            _render_page(pdf, title, subtitles, page)

    buf.seek(0)
    filename = "qualitativa-{0}.pdf".format(slugify(unicode(alumne)) or alumne.pk)
    return FileResponse(buf, as_attachment=True, filename=filename)