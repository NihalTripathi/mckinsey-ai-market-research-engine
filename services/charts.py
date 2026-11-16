"""Charts for the report.

make_chart(...) returns {"title", "plotly_json", "png_path"} (the ReportChart shape):
  plotly_json  an interactive chart the website draws with Plotly (a JSON string)
  png_path     a picture for the PDF (matplotlib, no browser needed)

One or several series can be drawn. Several series are drawn side by side, which is
how disagreeing estimates for the same year are shown instead of hiding all but one.
A picture that fails to draw never crashes the report: png_path is then None.
"""
import math
import os
import re
from typing import Optional

import matplotlib

matplotlib.use("Agg")                 # draw to files, never open a window
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from matplotlib.ticker import FuncFormatter

PALETTE = ["#2F5597", "#ED7D31", "#70AD47", "#7F7F7F", "#FFC000", "#5B9BD5", "#A5A5A5", "#C00000"]
MAX_SERIES = 6


def _safe(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(text)) or "chart"


def _mpl(text) -> str:
    """matplotlib treats $...$ as maths, so a dollar sign must be escaped."""
    return str(text).replace("$", r"\$")


def _short(text: str, limit: int = 24) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _clean(series: dict) -> dict:
    """Keep at most MAX_SERIES series and turn missing values into NaN."""
    out = {}
    for name, values in list(series.items())[:MAX_SERIES]:
        out[str(name)] = [float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else math.nan
                          for v in values]
    return out


def _plotly(labels, series, title, xlabel, ylabel):
    fig = go.Figure()
    for i, (name, values) in enumerate(series.items()):
        shown = [None if math.isnan(v) else v for v in values]
        fig.add_trace(go.Bar(x=labels, y=shown, name=_short(name, 40),
                             text=shown, textposition="outside",
                             marker_color=PALETTE[i % len(PALETTE)]))
    overlap = any(sum(not math.isnan(v[k]) for v in series.values()) > 1 for k in range(len(labels)))
    fig.update_layout(title=title, xaxis_title=xlabel, yaxis_title=ylabel, barmode="group" if overlap else "overlay",
                      template="plotly_white", showlegend=len(series) > 1)
    return fig


def _png(labels, series, title, xlabel, ylabel, path, png_title=False):
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    n = len(series)
    # When no label has more than one value, centre every bar on its label instead of spreading them.
    overlap = any(sum(not math.isnan(v[k]) for v in series.values()) > 1 for k in range(len(labels)))
    width = 0.8 / n if overlap else 0.55
    for i, (name, values) in enumerate(series.items()):
        xs = [k + ((i - (n - 1) / 2) * width if overlap else 0) for k in range(len(labels))]
        shown = [0 if math.isnan(v) else v for v in values]
        bars = ax.bar(xs, shown, width=width * 0.92, color=PALETTE[i % len(PALETTE)],
                      label=_mpl(_short(name, 40)))
        ax.bar_label(bars, labels=["" if math.isnan(v) else f"{v:,g}" for v in values], fontsize=8, padding=2)
    ax.set_xticks(range(len(labels)))
    long_labels = any(len(str(l)) > 8 for l in labels)
    ax.set_xticklabels([_mpl(_short(l)) for l in labels], rotation=30 if long_labels else 0,
                       ha="right" if long_labels else "center", fontsize=9)
    if png_title:                          # the report prints its own figure title above the picture
        ax.set_title(_mpl(title), fontsize=12, fontweight="bold")
    top = max((v for vals in series.values() for v in vals if not math.isnan(v)), default=1)
    decimals = 2 if top < 10 else 0
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.{decimals}f}"))
    ax.set_xlabel(_mpl(xlabel))
    ax.set_ylabel(_mpl(ylabel))
    ax.spines[["top", "right"]].set_visible(False)
    ax.margins(y=0.12)                     # headroom so the top value label is not cut
    if n > 1:
        ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def make_chart(labels: list, series: dict, title: str, xlabel: str, ylabel: str,
               name: str, job_id: str = "job_demo", out_dir: str = "storage/charts",
               png_title: bool = False) -> Optional[dict]:
    """labels: the x positions (years, company names...). series: {series name: [values]},
    one value per label (None for a missing value). Returns None if there is nothing to draw."""
    series = _clean(series or {})
    if not labels or not series or all(math.isnan(v) for vals in series.values() for v in vals):
        return None
    series = {k: (v + [math.nan] * len(labels))[: len(labels)] for k, v in series.items()}   # match lengths

    png_path = None
    try:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{_safe(job_id)}_{_safe(name)}.png")
        _png(labels, series, title, xlabel, ylabel, path, png_title)
        png_path = path
    except Exception as e:
        print(f"[charts] picture failed for {name!r}: {type(e).__name__}: {e}")

    try:
        plotly_json = _plotly(labels, series, title, xlabel, ylabel).to_json()
    except Exception as e:
        print(f"[charts] interactive chart failed for {name!r}: {type(e).__name__}: {e}")
        return None
    return {"title": title, "plotly_json": plotly_json, "png_path": png_path, "name": name}