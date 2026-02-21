"""
callbacks.py — All Dash callbacks for the CARTA telemetry dashboard.

Importing this module registers all callbacks with the `app` instance as a
side-effect (standard Dash pattern for multi-file apps).
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, ctx, dcc
from dash_bootstrap_templates import ThemeSwitchAIO
from plotly.subplots import make_subplots
from pycountry_convert import country_name_to_country_alpha3

from data import (
    SHOWED_COUNTRY_NUM,
    SIZE_LABELS,
    SIZE_LABEL_INDEX,
    entries_df,
    files_df,
    missing_data_dates,
    sessions_df,
    users_df,
)
from helpers import (
    add_incomplete_data_annotations,
    apply_date_xaxis,
    apply_standard_legend,
    compute_end_date,
    filter_by_country,
    get_missing_data_annotations,
    get_period_params,
    get_theme,
)
from layout import (
    OPT_IN_DISCLAIMER,
    OPT_IN_PCT,
    country_tab,
    file_tab,
    home_tab,
    users_tab,
    version_os_tab,
)

# Import app last to avoid circular import
from app import app

# ---------------------------------------------------------------------------
# Tab routers
# ---------------------------------------------------------------------------


@app.callback(
    Output("tabs-content", "children"),
    Input("tabs-selection", "value"),
)
def render_content(tab):
    if tab == "country_tab":
        return country_tab
    elif tab == "users_tab":
        return users_tab
    elif tab == "version_os_tab":
        return version_os_tab
    elif tab == "file_tab":
        return file_tab
    else:  # home_tab
        return home_tab


@app.callback(
    Output("tabs-counts-content", "children"),
    Input("tabs-counts-selection", "value"),
)
def render_counts_content(tab):
    if tab == "unique-IP_tab":
        return dcc.Graph(id="users-unique-IP"), dcc.Markdown(
            "Every IP recorded only once since the telemetry started"
        )
    elif tab == "uuid_tab":
        return dcc.Graph(id="users-uuid"), dcc.Markdown(
            "Unique ID for each computer"
        )
    elif tab == "active-IP_tab":
        return dcc.Graph(id="users-active-IP"), dcc.Markdown(
            "Unduplicated IPs recorded during the selected period (monthly, weekly, daily)"
        )
    else:  # session_tab
        return dcc.Graph(id="users-session"), dcc.Markdown(
            f"Session numbers are from {OPT_IN_PCT} users allowing to share the telemetry data"
        )


@app.callback(
    Output("tabs-versions-content", "children"),
    Input("tabs-versions-selection", "value"),
)
def render_versions(tab):
    if tab == "version_basic_tab":
        return (
            dcc.Graph(id="version-pie"),
            dcc.Graph(id="os-pie"),
            dcc.Markdown(
                f"Platform distribution is based on data from {OPT_IN_DISCLAIMER}"
            ),
        )
    else:  # version_detail_tab
        return dcc.Graph(id="os_detail-pie"), dcc.Markdown(
            f"Data from {OPT_IN_DISCLAIMER}"
        )


@app.callback(
    Output("tabs-files-content", "children"),
    Input("tabs-files-selection", "value"),
)
def render_files(tab):
    if tab == "file_size_tab":
        return (
            dcc.Graph(id="file-type-pie"),
            dcc.Graph(id="file-size-pie"),
            dcc.Graph(id="file-size-bar"),
            dcc.Markdown(
                f"All figures on this tab are based on data from {OPT_IN_DISCLAIMER}"
            ),
        )
    elif tab == "file_shape_tab":
        return dcc.Graph(id="file-shape"), dcc.Markdown(
            f"All figures on this tab are based on data from {OPT_IN_DISCLAIMER}"
        )
    else:  # action_tab
        return dcc.Graph(id="action-bar"), dcc.Markdown(
            f"Data from {OPT_IN_DISCLAIMER}"
        )


# ---------------------------------------------------------------------------
# Date range quick-select buttons
# ---------------------------------------------------------------------------


@app.callback(
    [Output("date-picker", "start_date"), Output("date-picker", "end_date")],
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input("btn-today", "n_clicks"),
        Input("btn-last-1m", "n_clicks"),
        Input("btn-last-3m", "n_clicks"),
        Input("btn-last-6m", "n_clicks"),
        Input("btn-last-1y", "n_clicks"),
        Input("btn-all", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def set_date_range(start_date, end_date, n_today, n_1m, n_3m, n_6m, n_1y, n_all):
    today_str = datetime.today().strftime("%Y-%m-%d")
    triggered_id = ctx.triggered_id

    if triggered_id == "btn-today":
        return start_date, today_str
    elif triggered_id == "btn-last-1m":
        return (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d"), today_str
    elif triggered_id == "btn-last-3m":
        return (datetime.today() - timedelta(days=90)).strftime("%Y-%m-%d"), today_str
    elif triggered_id == "btn-last-6m":
        return (datetime.today() - timedelta(days=180)).strftime("%Y-%m-%d"), today_str
    elif triggered_id == "btn-last-1y":
        return (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d"), today_str
    elif triggered_id == "btn-all":
        return users_df["datetime"].min(), users_df["datetime"].max()
    return start_date, end_date


# ---------------------------------------------------------------------------
# Theme wrapper class
# ---------------------------------------------------------------------------


@app.callback(
    Output("app-theme-wrapper", "className"),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
)
def toggle_theme_class(toggle):
    return "" if toggle else "dark-mode"


# ---------------------------------------------------------------------------
# Country tab figures
# ---------------------------------------------------------------------------


@app.callback(
    Output("country-map", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_country_map_chart(start_date, end_date, toggle):
    theme = get_theme(toggle)
    countries = users_df[
        (users_df["datetime"] >= start_date) & (users_df["datetime"] <= end_date)
    ]
    countries = (
        countries.country.value_counts()
        .to_frame()
        .reset_index()
        .rename(columns={"index": "Value", "A": "Count"})
    )
    countries["iso_alpha"] = countries.country.apply(
        lambda x: country_name_to_country_alpha3(x)
    )
    fig = px.scatter_geo(
        countries,
        locations="iso_alpha",
        hover_name="country",
        size="count",
        projection="natural earth",
        size_max=20,
        template=theme,
    )
    fig.update_geos(showcountries=True)
    fig.update_layout(transition_duration=500, margin={"r": 0, "t": 50, "l": 0, "b": 0})
    return fig


@app.callback(
    Output("country-pie", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_country_pie_chart(start_date, end_date, toggle):
    theme = get_theme(toggle)
    countries = users_df[
        (users_df["datetime"] >= start_date) & (users_df["datetime"] <= end_date)
    ]
    countries = countries.country.value_counts().reset_index().rename(
        columns={"index": "Value", "A": "Count"}
    )
    for other in countries.iloc[SHOWED_COUNTRY_NUM:].country:
        countries.loc[countries.country == other, "country"] = "Others"

    fig = px.pie(
        countries,
        values="count",
        names="country",
        hole=0.4,
        hover_data=["country"],
        template=theme,
    )
    fig.update_traces(textinfo="percent+value+label", insidetextorientation="horizontal")
    fig.update_layout(
        title_text="Top 10 countries",
        transition_duration=500,
        showlegend=False,
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
    )
    return fig


@app.callback(
    Output("country-other", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_other_country_chart(start_date, end_date, toggle):
    theme = get_theme(toggle)
    countries = users_df[
        (users_df["datetime"] >= start_date) & (users_df["datetime"] <= end_date)
    ]
    countries = countries.country.value_counts().reset_index().rename(
        columns={"index": "Value", "A": "Count"}
    )
    other_countries = countries.iloc[SHOWED_COUNTRY_NUM:]

    fig = px.bar(
        other_countries,
        x=other_countries["country"],
        y=other_countries["count"] / countries["count"].sum() * 100,
        text=other_countries["count"],
        labels={"y": "%", "x": "Country", "text": "Count"},
        hover_data=["country"],
        template=theme,
    )
    fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
    fig.update_layout(
        title_text="Details of others",
        transition_duration=500,
        xaxis_tickangle=45,
        xaxis_title=None,
    )
    return fig


# ---------------------------------------------------------------------------
# Users tab figures
# ---------------------------------------------------------------------------


@app.callback(
    Output("users-unique-IP", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input("period-radio-item", "value"),
        Input("country-item", "value"),
        Input("label-fontsize", "value"),
        Input("legend-fontsize", "value"),
        Input("x-tick-fontsize", "value"),
        Input("y-tick-fontsize", "value"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_users_unique_IP_chart(
    start_date, end_date, period_value, country_value,
    label_fontsize, legend_fontsize, x_tick_fontsize, y_tick_fontsize, toggle,
):
    theme = get_theme(toggle)
    period, fontsize, anno_y, day_shift = get_period_params(period_value)
    anno_dates = get_missing_data_annotations(missing_data_dates, period)
    new_end_date = compute_end_date(end_date)

    mask = filter_by_country(entries_df, country_value)
    entries_selected = entries_df[mask]
    unique_select = (
        entries_selected.reset_index()
        .groupby(["ipHash"])["index"]
        .min()
        .to_list()
    )
    monthly_unique_ip = entries_selected.loc[unique_select].resample(period, on="datetime").size()
    cum_unique_ip = np.cumsum(monthly_unique_ip)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=monthly_unique_ip.keys() + day_shift, y=monthly_unique_ip.values, name="unique IP"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=monthly_unique_ip.keys() + day_shift,
            y=cum_unique_ip,
            mode="lines",
            name="cumulative",
        ),
        secondary_y=True,
    )

    fig.update_layout(title_text="Unique IP counts", template=theme)
    apply_date_xaxis(fig, start_date, new_end_date)
    fig.update_yaxes(
        title_text="# Unique IP",
        secondary_y=False,
        gridcolor="lightblue",
        title_font=dict(size=label_fontsize),
        tickfont=dict(size=y_tick_fontsize),
    )
    fig.update_yaxes(
        title_text="# Cumulative Unique IP",
        color="red",
        secondary_y=True,
        gridcolor="#fccfd2",
        title_font=dict(size=label_fontsize),
        tickfont=dict(size=y_tick_fontsize),
    )
    fig.update_xaxes(
        rangeselector_y=1.0,
        rangeselector_x=0.5,
        title_font=dict(size=label_fontsize),
        tickfont=dict(size=x_tick_fontsize),
    )
    apply_standard_legend(fig, legend_fontsize)
    add_incomplete_data_annotations(fig, anno_dates, day_shift, anno_y, fontsize)
    return fig


@app.callback(
    Output("users-uuid", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input("period-radio-item", "value"),
        Input("country-item", "value"),
        Input("label-fontsize", "value"),
        Input("legend-fontsize", "value"),
        Input("x-tick-fontsize", "value"),
        Input("y-tick-fontsize", "value"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_users_uuid_chart(
    start_date, end_date, period_value, country_value,
    label_fontsize, legend_fontsize, x_tick_fontsize, y_tick_fontsize, toggle,
):
    theme = get_theme(toggle)
    period, fontsize, anno_y, day_shift = get_period_params(period_value)
    anno_dates = get_missing_data_annotations(missing_data_dates, period)
    new_end_date = compute_end_date(end_date)

    mask = filter_by_country(users_df, country_value)
    users_selected = users_df[mask]
    monthly_uuid = users_selected.resample(period, on="datetime").size()
    cum_uuid = np.cumsum(monthly_uuid)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=monthly_uuid.keys() + day_shift, y=monthly_uuid.values, name="uuid"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=monthly_uuid.keys() + day_shift,
            y=cum_uuid,
            mode="lines",
            name="cumulative",
        ),
        secondary_y=True,
    )

    fig.update_layout(title_text="UUID counts", template=theme)
    apply_date_xaxis(fig, start_date, new_end_date)
    fig.update_yaxes(
        title_text="# UUID",
        secondary_y=False,
        gridcolor="lightblue",
        title_font=dict(size=label_fontsize),
        tickfont=dict(size=y_tick_fontsize),
    )
    fig.update_yaxes(
        title_text="# Cumulative UUID",
        color="red",
        secondary_y=True,
        gridcolor="#fccfd2",
        title_font=dict(size=label_fontsize),
        tickfont=dict(size=y_tick_fontsize),
    )
    fig.update_xaxes(
        rangeselector_y=1.0,
        rangeselector_x=0.5,
        title_font=dict(size=label_fontsize),
        tickfont=dict(size=x_tick_fontsize),
    )
    apply_standard_legend(fig, legend_fontsize)
    add_incomplete_data_annotations(fig, anno_dates, day_shift, anno_y, fontsize)
    return fig


@app.callback(
    Output("users-active-IP", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input("period-radio-item", "value"),
        Input("country-item", "value"),
        Input("label-fontsize", "value"),
        Input("legend-fontsize", "value"),
        Input("x-tick-fontsize", "value"),
        Input("y-tick-fontsize", "value"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_users_active_IP_chart(
    start_date, end_date, period_value, country_value,
    label_fontsize, legend_fontsize, x_tick_fontsize, y_tick_fontsize, toggle,
):
    theme = get_theme(toggle)
    period, fontsize, anno_y, day_shift = get_period_params(period_value)
    anno_dates = get_missing_data_annotations(missing_data_dates, period)
    new_end_date = compute_end_date(end_date)

    mask = filter_by_country(entries_df, country_value)
    entries_selected = entries_df[mask]
    monthly_ip = entries_selected.resample(period, on="datetime").apply(
        lambda x: x.ipHash.unique().size
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly_ip.keys() + day_shift, y=monthly_ip.values, name="Active IP"))
    fig.update_layout(title_text="Active IP counts", template=theme)
    apply_date_xaxis(fig, start_date, new_end_date)
    fig.update_xaxes(
        rangeselector_y=1.0,
        rangeselector_x=0.5,
        title_font=dict(size=label_fontsize),
        tickfont=dict(size=x_tick_fontsize),
    )
    fig.update_yaxes(
        title_text="# Active IP",
        gridcolor="lightblue",
        title_font=dict(size=label_fontsize),
        tickfont=dict(size=y_tick_fontsize),
    )
    apply_standard_legend(fig, legend_fontsize)
    add_incomplete_data_annotations(fig, anno_dates, day_shift, anno_y, fontsize)
    return fig


@app.callback(
    Output("users-session", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input("period-radio-item", "value"),
        Input("country-item", "value"),
        Input("label-fontsize", "value"),
        Input("legend-fontsize", "value"),
        Input("x-tick-fontsize", "value"),
        Input("y-tick-fontsize", "value"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_users_session_chart(
    start_date, end_date, period_value, country_value,
    label_fontsize, legend_fontsize, x_tick_fontsize, y_tick_fontsize, toggle,
):
    theme = get_theme(toggle)
    period, fontsize, anno_y, day_shift = get_period_params(period_value)
    anno_dates = get_missing_data_annotations(missing_data_dates, period)
    new_end_date = compute_end_date(end_date)

    mask = filter_by_country(entries_df, country_value)
    entries_selected = entries_df[mask]
    monthly_session = entries_selected.resample(period, on="datetime").apply(
        lambda x: x.sessionId.unique().size
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=monthly_session.keys() + day_shift, y=monthly_session.values, name="session")
    )
    fig.update_layout(title_text="Session counts", template=theme)
    apply_date_xaxis(fig, start_date, new_end_date)
    fig.update_xaxes(
        rangeselector_y=1.0,
        rangeselector_x=0.5,
        title_font=dict(size=label_fontsize),
        tickfont=dict(size=x_tick_fontsize),
    )
    fig.update_yaxes(
        title_text="# Session",
        gridcolor="lightblue",
        title_font=dict(size=label_fontsize),
        tickfont=dict(size=y_tick_fontsize),
    )
    apply_standard_legend(fig, legend_fontsize)
    add_incomplete_data_annotations(fig, anno_dates, day_shift, anno_y, fontsize)
    return fig


# ---------------------------------------------------------------------------
# Versions and OS tab figures
# ---------------------------------------------------------------------------


@app.callback(
    Output("version-pie", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input("country-item", "value"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_version_pie_chart(start_date, end_date, country_value, toggle):
    theme = get_theme(toggle)
    mask = filter_by_country(sessions_df, country_value)
    versions = sessions_df[
        (sessions_df["datetime"] >= start_date)
        & (sessions_df["datetime"] <= end_date)
        & mask
    ]
    for other in versions.version.value_counts().keys()[5:]:
        versions.loc[versions.version == other, "version"] = "Others"

    fig = px.pie(versions, names="version", title="Version distribution", hole=0.4, template=theme)
    fig.update_traces(textinfo="value+percent+label", insidetextorientation="horizontal")
    fig.update_layout(
        transition_duration=500,
        showlegend=False,
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
    )
    return fig


@app.callback(
    Output("os-pie", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input("country-item", "value"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_os_pie_chart(start_date, end_date, country_value, toggle):
    theme = get_theme(toggle)
    mask = filter_by_country(sessions_df, country_value)
    platform = sessions_df[
        (sessions_df["datetime"] >= start_date)
        & (sessions_df["datetime"] <= end_date)
        & mask
    ]
    fig = px.pie(
        platform,
        names="backendPlatform",
        title="Platform distribution",
        hole=0.4,
        template=theme,
    )
    fig.update_traces(textinfo="value+percent+label", insidetextorientation="horizontal")
    fig.update_layout(
        transition_duration=500,
        showlegend=False,
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
    )
    return fig


@app.callback(
    Output("os_detail-pie", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input("country-item", "value"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_os_detail_pie_chart(start_date, end_date, country_value, toggle):
    theme = get_theme(toggle)
    mask = filter_by_country(sessions_df, country_value)

    linux = sessions_df[
        (sessions_df["datetime"] >= start_date)
        & (sessions_df["datetime"] <= end_date)
        & (sessions_df["backendPlatform"] == "Linux")
        & sessions_df["version"].notna()
        & mask
    ]
    linux_OS = linux["OS"].value_counts().reset_index().rename(
        columns={"index": "Value", "A": "Count"}
    )
    linux_sub = {}
    for selected_OS in linux_OS["OS"]:
        linux_selected = linux[linux["OS"] == selected_OS]
        linux_sub[selected_OS] = linux_selected["OS_version"].value_counts().reset_index().rename(
            columns={"index": "Value", "A": "Count"}
        )

    mac = sessions_df[
        (sessions_df["datetime"] >= start_date)
        & (sessions_df["datetime"] <= end_date)
        & (sessions_df["backendPlatform"] == "macOS")
        & sessions_df["version"].notna()
        & mask
    ]
    mac_sub = {}
    for selected_OS in mac["OS"].value_counts().reset_index()["OS"]:
        mac_selected = mac[mac["OS"] == selected_OS]
        mac_sub[selected_OS] = mac_selected["OS_version"].value_counts().reset_index().rename(
            columns={"index": "Value", "A": "Count"}
        )

    # Fix: always assign showed_linux_num (was a NameError bug when len < 3)
    showed_linux_num = min(len(linux_sub), 3)

    version_labels, version_values, os_array, platform_array = [], [], [], []

    for i in range(showed_linux_num):
        the_linux = linux_sub[list(linux_sub.keys())[i]]
        showed_num = min(len(the_linux["OS_version"]), 3)

        version_labels += the_linux["OS_version"][:showed_num].to_list()
        version_values += the_linux["count"][:showed_num].to_list()
        version_labels += ["others"]
        version_values += [the_linux["count"][showed_num:].sum()]

        os_key = list(linux_sub.keys())[i]
        os_array += [os_key] * (showed_num + 1)
        platform_array += ["Linux"] * (showed_num + 1)

    version_labels += [None]
    os_array += ["others"]
    version_values += [linux_OS["count"][showed_linux_num:].sum()]
    platform_array += ["Linux"]

    the_mac = mac_sub["macOS"]
    showed_num = min(len(the_mac["OS_version"]), 3)

    version_labels += the_mac["OS_version"][:showed_num].to_list()
    version_values += the_mac["count"][:showed_num].to_list()
    version_labels += ["others"]
    version_values += [the_mac["count"][showed_num:].sum()]
    os_array += [list(mac_sub.keys())[0]] * (showed_num + 1)
    platform_array += ["macOS"] * (showed_num + 1)

    df = pd.DataFrame(
        dict(os=os_array, version=version_labels, count=version_values, platform=platform_array)
    )
    fig = px.sunburst(df, path=["platform", "os", "version"], values="count", template=theme)
    fig.update_layout(
        transition_duration=1000,
        showlegend=False,
        width=800,
        height=800,
    )
    return fig


# ---------------------------------------------------------------------------
# Files and Actions tab figures
# ---------------------------------------------------------------------------


@app.callback(
    Output("file-type-pie", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input("country-item", "value"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_file_pie_chart(start_date, end_date, country_value, toggle):
    theme = get_theme(toggle)
    mask = filter_by_country(files_df, country_value)
    select_files = files_df[
        (files_df["datetime"] >= start_date) & (files_df["datetime"] <= end_date) & mask
    ]
    file_types = select_files.file_type.value_counts().reset_index().rename(
        columns={"index": "Value", "A": "Count"}
    )
    fig = go.Figure(
        go.Pie(
            name="",
            values=file_types["count"],
            labels=file_types["file_type"],
            text=file_types["file_type"],
            hole=0.4,
        )
    )
    fig.update_traces(insidetextorientation="horizontal")
    fig.update_layout(
        transition_duration=500,
        title_text="File types distribution",
        template=theme,
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        showlegend=False,
    )
    return fig


@app.callback(
    Output("file-size-pie", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input("country-item", "value"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_file_size_pie_chart(start_date, end_date, country_value, toggle):
    theme = get_theme(toggle)
    mask = filter_by_country(files_df, country_value)
    select_files = files_df[
        (files_df["datetime"] >= start_date) & (files_df["datetime"] <= end_date) & mask
    ]
    file_size_df = select_files["size_label"].value_counts().reset_index().rename(
        columns={"index": "size_label", "A": "Count"}
    )
    for label in SIZE_LABELS:
        file_size_df.loc[file_size_df.size_label == label, "index"] = SIZE_LABEL_INDEX[label]
    file_size_df.sort_values(by="index", inplace=True)

    fig = go.Figure(
        go.Pie(
            name="",
            values=file_size_df["count"],
            labels=file_size_df["size_label"],
            text=file_size_df["size_label"],
            hole=0.4,
        )
    )
    fig.update_traces(insidetextorientation="horizontal")
    fig.update_layout(
        title_text="File size distribution",
        transition_duration=500,
        template=theme,
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        showlegend=False,
    )
    return fig


@app.callback(
    Output("file-size-bar", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input("country-item", "value"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_file_size_bar_chart(start_date, end_date, country_value, toggle):
    theme = get_theme(toggle)
    mask = filter_by_country(files_df, country_value)
    select_files = files_df[
        (files_df["datetime"] >= start_date) & (files_df["datetime"] <= end_date) & mask
    ]
    size_by_type = {
        sl: select_files.loc[select_files.size_label == sl, "file_type"]
            .value_counts()
            .reset_index()
            .rename(columns={"index": "Value", "A": "Count"})
        for sl in SIZE_LABELS
    }
    fig = go.Figure()
    for sl in SIZE_LABELS:
        fig.add_trace(
            go.Bar(
                y=size_by_type[sl]["file_type"],
                x=size_by_type[sl]["count"],
                name=sl,
                orientation="h",
                text=sl,
            )
        )
    fig.update_layout(
        barmode="stack",
        barnorm="percent",
        template=theme,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(title_text="%")
    return fig


@app.callback(
    Output("file-shape", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input("country-item", "value"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_file_shape_chart(start_date, end_date, country_value, toggle):
    theme = get_theme(toggle)
    mask = filter_by_country(files_df, country_value)
    select_files = files_df[
        (files_df["datetime"] >= start_date) & (files_df["datetime"] <= end_date) & mask
    ]
    cube = select_files.loc[
        (select_files.file_type == "3D") | (select_files.file_type == "3D+Stokes")
    ]

    hist_kwargs = dict(
        colorscale="dense",
        autobinx=False,
        autobiny=False,
        xbins=dict(start=0, end=5, size=0.2),
        ybins=dict(start=0, end=5, size=0.2),
    )

    fig = make_subplots(rows=1, cols=2)
    fig.add_trace(
        go.Histogram2d(
            x=np.log10(cube["details.width"]),
            y=np.log10(cube["details.height"]),
            colorbar=dict(len=1, x=0.45),
            **hist_kwargs,
        ),
        row=1, col=1,
    )
    fig.add_trace(go.Scatter(x=[0, 5], y=[0, 5]), row=1, col=1)
    fig.update_xaxes(title_text="Spatial X pixels [log]", row=1, col=1)
    fig.update_yaxes(title_text="Spatial Y pixels [log]", row=1, col=1)

    fig.add_trace(
        go.Histogram2d(
            x=np.log10(cube["details.width"]),
            y=np.log10(cube["details.depth"]),
            colorbar=dict(len=1, x=1),
            **hist_kwargs,
        ),
        row=1, col=2,
    )
    fig.update_xaxes(title_text="Spatial X pixels [log]", row=1, col=2)
    fig.update_yaxes(title_text="Channels [log]", row=1, col=2)

    fig.update_layout(
        xaxis=dict(autorangeoptions=dict(clipmin=0, clipmax=5)),
        yaxis=dict(autorangeoptions=dict(clipmin=0, clipmax=5)),
        template=theme,
    )
    return fig


@app.callback(
    Output("action-bar", "figure"),
    [
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date"),
        Input("country-item", "value"),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    ],
)
def update_action_bar_chart(start_date, end_date, country_value, toggle):
    theme = get_theme(toggle)
    mask = filter_by_country(entries_df, country_value)
    select_entries = entries_df[
        (entries_df["datetime"] >= start_date) & (entries_df["datetime"] <= end_date) & mask
    ]
    actions = select_entries.action.value_counts()

    plot_action_names = [
        "spectralProfileGeneration",
        "momentGeneration",
        "catalogLoading",
        "pvGeneration",
    ]
    fig = go.Figure()
    for action_name in plot_action_names:
        ratio = actions[action_name] / actions["endSession"]
        fig.add_trace(
            go.Bar(
                y=["action"],
                x=[ratio],
                name=action_name,
                orientation="h",
                text=[action_name],
            )
        )
    fig.update_layout(
        barmode="stack",
        barnorm="percent",
        template=theme,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(title_text="%")
    return fig

# ---------------------------------------------------------------------------
# Clientside: auto-detect OS dark mode on page load
# ---------------------------------------------------------------------------
# The dcc.Store "os-theme-store" fires once on mount with data=None.
# We check window.matchMedia and set the ThemeSwitchAIO value accordingly.
# True  → light (COSMO), False → dark (CYBORG)
app.clientside_callback(
    """
    function(data) {
        var prefersDark = window.matchMedia &&
                          window.matchMedia('(prefers-color-scheme: dark)').matches;
        return !prefersDark;
    }
    """,
    Output(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input("os-theme-store", "data"),
    prevent_initial_call=False,
)
