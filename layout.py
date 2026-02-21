"""
layout.py — Dash layout components for the CARTA telemetry dashboard.
"""

from datetime import datetime

import dash_bootstrap_components as dbc
from dash import dcc, html
from dash_bootstrap_templates import ThemeSwitchAIO

from data import opt_in_frac, users_df

# ---------------------------------------------------------------------------
# Opt-in disclaimer (used in several tab descriptions)
# ---------------------------------------------------------------------------

OPT_IN_PCT = f"{opt_in_frac * 100:.1f}%"
OPT_IN_DISCLAIMER = f"{OPT_IN_PCT} users who allowed to share the telemetry data"

# ---------------------------------------------------------------------------
# Tab content components
# ---------------------------------------------------------------------------

home_tab = html.Div(
    [
        html.H1("CARTA"),
        html.H2(f"has been opened on {len(users_df)} computers"),
        html.H3("since Dec. 2021"),
        html.P(
            [
                "* The statistics is not included the data from the ALMA archive"
                " and other self deployed servers",
                html.Br(),
                f"* {OPT_IN_DISCLAIMER}",
            ]
        ),
    ],
    className="home",
)

country_tab = html.Div(
    [
        dbc.Row(
            [
                dcc.Graph(id="country-pie"),
                dcc.Graph(id="country-map"),
                dbc.Row([dcc.Graph(id="country-other")]),
            ],
            class_name="country-row1",
        )
    ]
)

users_tab = html.Div(
    [
        dbc.Row(
            [
                dbc.RadioItems(
                    options=["monthly", "weekly", "daily"],
                    value="monthly",
                    id="period-radio-item",
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-primary",
                    labelCheckedClassName="active",
                ),
                html.Div(
                    [
                        html.Label("Label Font Size:"),
                        dcc.Input(
                            id="label-fontsize",
                            type="number",
                            value=16,
                            min=8,
                            max=40,
                            step=1,
                            style={"width": "60px"},
                        ),
                        html.Label("X Size:", style={"marginLeft": "20px"}),
                        dcc.Input(
                            id="x-tick-fontsize",
                            type="number",
                            value=12,
                            min=6,
                            max=32,
                            step=1,
                            style={"width": "60px"},
                        ),
                        html.Label("Y Size:", style={"marginLeft": "10px"}),
                        dcc.Input(
                            id="y-tick-fontsize",
                            type="number",
                            value=12,
                            min=6,
                            max=32,
                            step=1,
                            style={"width": "60px"},
                        ),
                        html.Label("Legend Font Size:", style={"marginLeft": "20px"}),
                        dcc.Input(
                            id="legend-fontsize",
                            type="number",
                            value=14,
                            min=8,
                            max=40,
                            step=1,
                            style={"width": "60px"},
                        ),
                    ],
                    style={"display": "inline-block", "marginLeft": "20px"},
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Tabs(
                        id="tabs-counts-selection",
                        value="unique-IP_tab",
                        vertical=True,
                        children=[
                            dcc.Tab(label="Unique-IP", value="unique-IP_tab"),
                            dcc.Tab(label="UUID", value="uuid_tab"),
                            dcc.Tab(label="Active-IP", value="active-IP_tab"),
                            dcc.Tab(label="Sessions", value="session_tab"),
                        ],
                    ),
                ),
                dbc.Col(html.Div(id="tabs-counts-content")),
            ],
            class_name="users-row2",
        ),
    ]
)

version_os_tab = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    dcc.Tabs(
                        id="tabs-versions-selection",
                        value="version_basic_tab",
                        vertical=True,
                        children=[
                            dcc.Tab(label="version basic", value="version_basic_tab"),
                            dcc.Tab(label="version detail", value="version_detail_tab"),
                        ],
                    ),
                ),
                dbc.Col(html.Div(id="tabs-versions-content")),
            ],
            class_name="version-os-row1",
        )
    ]
)

file_tab = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    dcc.Tabs(
                        id="tabs-files-selection",
                        value="file_size_tab",
                        vertical=True,
                        children=[
                            dcc.Tab(label="File size", value="file_size_tab"),
                            dcc.Tab(label="File shape", value="file_shape_tab"),
                            dcc.Tab(label="Action", value="action_tab"),
                        ],
                    ),
                ),
                dbc.Col(html.Div(id="tabs-files-content")),
            ],
            class_name="file-row1",
        )
    ]
)

# ---------------------------------------------------------------------------
# Header controls
# ---------------------------------------------------------------------------

date_range_button_group = dbc.ButtonGroup(
    [
        dbc.Button("1 month", id="btn-last-1m", n_clicks=0, outline=True, color="secondary"),
        dbc.Button("3 month", id="btn-last-3m", n_clicks=0, outline=True, color="secondary"),
        dbc.Button("6 month", id="btn-last-6m", n_clicks=0, outline=True, color="secondary"),
        dbc.Button("1 year", id="btn-last-1y", n_clicks=0, outline=True, color="secondary"),
        dbc.Button("All", id="btn-all", n_clicks=0, outline=True, color="secondary"),
    ]
)

country_selection = html.Div(
    [
        dbc.RadioItems(
            options=[
                {"label": "South Africa", "value": "ZA"},
                {"label": "Taiwan", "value": "TW"},
                {"label": "United States", "value": "US"},
                {"label": "All", "value": ""},
            ],
            value="",
            id="country-item",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-primary",
            labelCheckedClassName="active",
        ),
    ],
    className="radio-group",
    style={"display": "inline-block", "justify-content": "center"},
)

# ---------------------------------------------------------------------------
# serve_layout — called on every page load so end_date is always fresh
# ---------------------------------------------------------------------------


def serve_layout():
    end_date = datetime.today().strftime("%Y-%m-%d")

    layout = html.Div(
        [
            # Fires once on page load (data=None); triggers OS dark-mode detection
            dcc.Store(id="os-theme-store", storage_type="memory"),
            dbc.Container(
                [
                    html.Div(
                        [
                            dcc.DatePickerRange(
                                id="date-picker",
                                start_date="2021-12-01",
                                end_date=end_date,
                                display_format="YYYY-MM-DD",
                            ),
                            dbc.Button(
                                "Today",
                                id="btn-today",
                                n_clicks=0,
                                outline=True,
                                color="primary",
                            ),
                            date_range_button_group,
                            country_selection,
                            ThemeSwitchAIO(
                                aio_id="theme",
                                themes=[dbc.themes.COSMO, dbc.themes.CYBORG],
                            ),
                        ],
                        style={
                            "display": "flex",
                            "justify-content": "space-between",
                            "align-items": "center",
                            "width": "100%",
                        },
                    ),
                    dcc.Tabs(
                        id="tabs-selection",
                        value="home_tab",
                        children=[
                            dcc.Tab(label="Home", value="home_tab"),
                            dcc.Tab(label="Countries", value="country_tab"),
                            dcc.Tab(label="Users", value="users_tab"),
                            dcc.Tab(label="Versions and OS", value="version_os_tab"),
                            dcc.Tab(label="Files and actions", value="file_tab"),
                        ],
                    ),
                    html.Div(id="tabs-content"),
                ],
                fluid=True,
            )
        ],
        id="app-theme-wrapper",
    )
    return layout
