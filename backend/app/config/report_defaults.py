"""
report_defaults.py
==================
Configuration for report benchmarks, rating rules, and scoring thresholds.
Decouples all tunable constants from report rendering logic.
"""

# ─── Reference Cohort Benchmarks (out of 10 weighted points per section) ─────

DEFAULT_BENCHMARKS: dict[str, float] = {
    "SQL":                  6.8,
    "Python":               6.2,
    "Pandas":               5.8,
    "Data Visualization":   6.0,
    "Applied Statistics":   5.5,
    "Machine Learning":     5.2,
    "A/B Testing":          6.4,
}

# ─── Score-based Bar Chart Colors (Candidate-Only View) ──────────────────────

COLOR_TIERS: dict[str, str] = {
    "EXCELLENT": "#16A34A",   # 8.0 - 10.0  (Green)
    "GOOD":      "#3B82F6",   # 6.0 -  7.9  (Blue)
    "AVERAGE":   "#F59E0B",   # 4.0 -  5.9  (Orange)
    "POOR":      "#DC2626",   # 0.0 -  3.9  (Red)
}


def get_score_color(score: float) -> str:
    """Return the hex color for a given section score."""
    if score >= 8.0:
        return COLOR_TIERS["EXCELLENT"]
    if score >= 6.0:
        return COLOR_TIERS["GOOD"]
    if score >= 4.0:
        return COLOR_TIERS["AVERAGE"]
    return COLOR_TIERS["POOR"]


def get_performance_status(
    candidate_score: float,
    benchmark_score: float,
) -> tuple[str, str]:
    """
    Return (Status Label, Color Hex) based on the delta between a candidate's
    section score and the reference benchmark.

    Bands (delta = candidate - benchmark):
      > +2.0  → Excellent    (green)
      >= 0.0  → Above Avg    (blue)
      >= -2.0 → On Track     (slate)
      >= -4.0 → Needs Work   (amber)
      < -4.0  → Critical Gap (red)
    """
    delta = candidate_score - benchmark_score
    if delta > 2.0:
        return "Excellent",    "#16A34A"
    if delta >= 0.0:
        return "Above Avg",    "#2563EB"
    if delta >= -2.0:
        return "On Track",     "#64748B"
    if delta >= -4.0:
        return "Needs Work",   "#D97706"
    return "Critical Gap", "#DC2626"
