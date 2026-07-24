"""
chart_generator.py
==================
Generates a visually clean performance chart that compares a candidate's
section-level scores against a benchmark average.

Public API
----------
generate_score_chart_base64(section_scores, avg_scores) -> str
    Returns a "data:image/png;base64,..." string ready to embed in an
    HTML <img> tag.

Design notes
------------
- Blue (#3B82F6) bars for the candidate, light-gray (#D1D5DB) for benchmark.
- Clean white background, no chart junk.
- A summary table is rendered below the bars showing:
      Section | Score | Benchmark | Delta
- plt.close() is called after encoding to prevent memory leaks.
"""

from __future__ import annotations

import base64
import io
import textwrap
from typing import Optional

import matplotlib
matplotlib.use("Agg")          # Non-interactive backend — safe on servers
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np


# ─── Colour palette ──────────────────────────────────────────────────────────

_BLUE      = "#3B82F6"   # candidate bars
_GRAY      = "#D1D5DB"   # benchmark bars
_BG        = "#FFFFFF"   # figure background
_GRID_CLR  = "#F1F5F9"   # very light grid lines
_TEXT_DARK = "#1E293B"   # axis labels / titles
_TEXT_MED  = "#64748B"   # secondary text
_ACCENT    = "#EFF6FF"   # table header background

# Maximum weighted score per section (2x1 + 2x2 + 1x4 = 10 pts)
_MAX_PER_SECTION = 10


def _wrap_label(label: str, width: int = 10) -> str:
    """Wrap long section names for X-axis readability."""
    return "\n".join(textwrap.wrap(label, width=width))


def generate_score_chart_base64(
    section_scores: dict,
    avg_scores: Optional[dict] = None,
) -> str:
    """
    Generate a performance comparison chart and return it as a Base64-encoded
    PNG data URL suitable for embedding directly in HTML.

    Parameters
    ----------
    section_scores : dict[str, int | float]
        Candidate's weighted score per section, e.g. {"SQL": 8, "Python": 6, ...}.
    avg_scores : dict[str, int | float] | None
        Benchmark (cohort average) score per section.  If None or empty, only
        the candidate's bars are rendered (no benchmark overlay).

    Returns
    -------
    str
        "data:image/png;base64,<encoded bytes>"
    """
    if not section_scores:
        # Return a 1x1 transparent PNG as a safe fallback
        return (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
            "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )

    avg_scores = avg_scores or {}

    sections  = list(section_scores.keys())
    n         = len(sections)
    cand_vals = [float(section_scores.get(s, 0)) for s in sections]
    avg_vals  = [float(avg_scores.get(s, 0))     for s in sections]
    has_avg   = any(v > 0 for v in avg_vals)

    # ── Figure layout ────────────────────────────────────────────────────────
    fig_h = 6.8 if has_avg else 5.4
    fig   = plt.figure(figsize=(11, fig_h), facecolor=_BG, dpi=130)

    if has_avg:
        gs  = GridSpec(2, 1, figure=fig, height_ratios=[3, 1.2],
                       hspace=0.42, left=0.08, right=0.97, top=0.88, bottom=0.04)
        ax  = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
    else:
        gs  = GridSpec(1, 1, figure=fig, left=0.08, right=0.97, top=0.88, bottom=0.10)
        ax  = fig.add_subplot(gs[0])
        ax2 = None

    # ── Bar chart ────────────────────────────────────────────────────────────
    x     = np.arange(n)
    width = 0.38 if has_avg else 0.52

    if has_avg:
        bars_avg  = ax.bar(x - width / 2, avg_vals,  width, color=_GRAY, zorder=3,
                           label="Benchmark Avg", linewidth=0)
        bars_cand = ax.bar(x + width / 2, cand_vals, width, color=_BLUE, zorder=3,
                           label="Your Score",    linewidth=0)
    else:
        bars_cand = ax.bar(x, cand_vals, width, color=_BLUE, zorder=3,
                           label="Your Score", linewidth=0)

    # Value labels on top of each bar
    for bar in bars_cand:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + 0.15,
            f"{h:.0f}",
            ha="center", va="bottom",
            fontsize=8, fontweight="bold", color=_BLUE,
        )
    if has_avg:
        for bar in bars_avg:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + 0.15,
                f"{h:.0f}",
                ha="center", va="bottom",
                fontsize=7.5, color=_TEXT_MED,
            )

    # ── Axes styling ─────────────────────────────────────────────────────────
    ax.set_facecolor(_BG)
    ax.set_xlim(-0.6, n - 0.4)
    ax.set_ylim(0, _MAX_PER_SECTION + 1.5)
    ax.set_xticks(x)
    ax.set_xticklabels(
        [_wrap_label(s) for s in sections],
        fontsize=8, color=_TEXT_DARK,
    )
    ax.set_ylabel("Score (out of 10)", fontsize=9, color=_TEXT_MED, labelpad=6)
    ax.set_yticks(range(0, _MAX_PER_SECTION + 2, 2))
    ax.tick_params(axis="y", labelsize=8, colors=_TEXT_MED)
    ax.tick_params(axis="x", length=0)
    ax.yaxis.grid(True, color=_GRID_CLR, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # ── Chart title & legend ─────────────────────────────────────────────────
    total_cand = sum(cand_vals)
    total_poss = n * _MAX_PER_SECTION
    fig.suptitle(
        f"Section Performance Overview  |  Total: {total_cand:.0f} / {total_poss}",
        x=0.52, y=0.97,
        fontsize=12, fontweight="bold", color=_TEXT_DARK,
    )

    legend_handles = [mpatches.Patch(color=_BLUE, label="Your Score")]
    if has_avg:
        legend_handles.append(mpatches.Patch(color=_GRAY, label="Benchmark Avg"))

    ax.legend(
        handles=legend_handles,
        loc="upper right", fontsize=8,
        frameon=True, framealpha=0.85,
        edgecolor=_GRID_CLR,
    )

    # ── Summary table (only when benchmark data is present) ──────────────────
    if has_avg and ax2 is not None:
        ax2.set_facecolor(_BG)
        ax2.axis("off")

        col_labels = ["Section", "Your Score", "Benchmark", "Delta"]
        table_data = []
        for s in sections:
            cval  = float(section_scores.get(s, 0))
            aval  = float(avg_scores.get(s, 0))
            delta = cval - aval
            delta_str = f"+{delta:.1f}" if delta >= 0 else f"{delta:.1f}"
            table_data.append([s, f"{cval:.0f} / {_MAX_PER_SECTION}", f"{aval:.1f}", delta_str])

        tbl = ax2.table(
            cellText=table_data,
            colLabels=col_labels,
            cellLoc="center",
            loc="center",
            bbox=[0, 0, 1, 1],
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(7.5)

        # Style header row
        for col_idx in range(len(col_labels)):
            cell = tbl[0, col_idx]
            cell.set_facecolor(_ACCENT)
            cell.set_text_props(fontweight="bold", color=_TEXT_DARK)
            cell.set_edgecolor(_GRID_CLR)

        # Style data rows
        for row_idx in range(1, len(table_data) + 1):
            for col_idx in range(len(col_labels)):
                cell = tbl[row_idx, col_idx]
                cell.set_facecolor(_BG)
                cell.set_edgecolor(_GRID_CLR)
                cell.set_text_props(color=_TEXT_DARK)
                # Colour the delta column green/red
                if col_idx == 3:
                    raw_delta = (
                        float(section_scores.get(sections[row_idx - 1], 0))
                        - float(avg_scores.get(sections[row_idx - 1], 0))
                    )
                    cell.set_text_props(
                        color="#16A34A" if raw_delta >= 0 else "#DC2626",
                        fontweight="bold",
                    )

    # ── Encode to Base64 ─────────────────────────────────────────────────────
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", facecolor=_BG)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)   # Prevent memory leaks — critical for long-running servers
    buf.close()

    return f"data:image/png;base64,{encoded}"
