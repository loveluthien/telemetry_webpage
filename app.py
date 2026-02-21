"""
app.py — Dash application instance.

Kept in its own module so that both `callbacks.py` and `main.py` can import
`app` without creating a circular dependency.
"""

import dash
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

from data import LIGHT_THEME

load_figure_template(["cosmo", "cyborg"])

app = dash.Dash(__name__, external_stylesheets=[LIGHT_THEME])
server = app.server  # expose Flask server for gunicorn
