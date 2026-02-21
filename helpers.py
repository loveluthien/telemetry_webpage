"""
helpers.py — Reusable utility functions for the CARTA telemetry dashboard.
"""

import calendar
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

def get_theme(toggle: bool) -> str:
    """Return the Plotly template name based on the theme toggle value."""
    return "cosmo" if toggle else "cyborg"


# ---------------------------------------------------------------------------
# Period / time-series helpers (used by Users-tab callbacks)
# ---------------------------------------------------------------------------

def get_period_params(period_value: str) -> tuple:
    """Convert a period radio-button value into resample params.

    Returns
    -------
    period : str
        Pandas resample frequency string.
    fontsize : int
        Annotation font size for this period granularity.
    anno_y : int | float
        Y-position for "incomplete data" annotations.
    day_shift : timedelta
        Bar offset so bars are centred on the period.
    """
    if period_value == "monthly":
        return "MS", 12, 50, timedelta(days=14)
    elif period_value == "weekly":
        return "W", 8, 10, timedelta(days=3)
    else:  # daily
        return "d", 5, 5, timedelta(days=0)


def get_missing_data_annotations(missing_data_dates, period: str):
    """Return the index dates that have at least one missing-data entry."""
    resampled = missing_data_dates.resample(period, on="datetime").size()
    return resampled[resampled.values > 0].keys()


def compute_end_date(end_date: str) -> str:
    """Extend end_date to the last day of its month for x-axis clipping."""
    dd_end = datetime.strptime(end_date.replace("T00:00:00", ""), "%Y-%m-%d")
    last_day = calendar.monthrange(dd_end.year, dd_end.month)[1]
    return f"{dd_end.year}-{dd_end.month}-{last_day}"


# ---------------------------------------------------------------------------
# DataFrame filtering
# ---------------------------------------------------------------------------

def filter_by_country(df, country_value: str):
    """Return a boolean mask that selects rows matching the country filter.

    When *country_value* is empty string (''), all rows are selected.
    """
    if country_value == "":
        return df["countryCode"].isnull() | df["countryCode"].notnull()
    return df["countryCode"] == country_value


# ---------------------------------------------------------------------------
# Figure layout helpers
# ---------------------------------------------------------------------------

def apply_date_xaxis(fig, start_date: str, new_end_date: str) -> None:
    """Apply the standard date x-axis with range clipping and no slider."""
    fig.update_layout(
        xaxis=dict(
            autorangeoptions=dict(
                clipmin=start_date,
                clipmax=new_end_date,
            ),
            rangeslider=dict(visible=False),
            type="date",
        )
    )


def apply_standard_legend(fig, legend_fontsize: int) -> None:
    """Pin the legend above the chart area (bottom-left anchor)."""
    fig.update_layout(
        legend=dict(
            yanchor="bottom",
            y=1.00,
            xanchor="left",
            x=0.9,
            font=dict(size=legend_fontsize),
        )
    )


def add_incomplete_data_annotations(fig, anno_dates, day_shift, anno_y, fontsize) -> None:
    """Add vertical 'incomplete data' text annotations for each flagged date."""
    for dd in anno_dates:
        fig.add_annotation(
            x=dd + day_shift,
            y=anno_y,
            text="incomplete data",
            showarrow=False,
            xanchor="center",
            yanchor="bottom",
            textangle=-90,
            font=dict(size=fontsize),
        )
