"""
data.py — Data loading and global constants for the CARTA telemetry dashboard.
"""

import configparser

import dash_bootstrap_components as dbc
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

configParser = configparser.ConfigParser()
configParser.read("config")

df_dir = configParser.get("PATH", "df_dir")

# ---------------------------------------------------------------------------
# Theme constants
# ---------------------------------------------------------------------------

LIGHT_THEME = dbc.themes.COSMO

# ---------------------------------------------------------------------------
# Chart constants
# ---------------------------------------------------------------------------

SHOWED_COUNTRY_NUM = 10  # top-N countries shown in country charts

SIZE_LABELS = [
    "<1MB",
    "1MB-10MB",
    "10MB-100MB",
    "100MB-1GB",
    "1GB-10GB",
    "10GB-100GB",
    "100GB-1TB",
    "1TB-10TB",
]

SIZE_LABEL_INDEX = {label: i for i, label in enumerate(SIZE_LABELS)}

# ---------------------------------------------------------------------------
# DataFrames  (loaded once at startup; gunicorn watches CSVs for hot-reload)
# ---------------------------------------------------------------------------

users_df = pd.read_csv(f"{df_dir}/processed_users.csv")
sessions_df = pd.read_csv(f"{df_dir}/processed_sessions.csv", dtype={"OS_version": str})
entries_df = pd.read_csv(f"{df_dir}/processed_entries.csv")
files_df = pd.read_csv(f"{df_dir}/processed_files.csv")
missing_data_dates = pd.read_csv(f"{df_dir}/missing_data_dates.csv")

# Parse datetime columns
users_df["datetime"] = pd.to_datetime(users_df.datetime, format="mixed")
sessions_df["datetime"] = pd.to_datetime(sessions_df.datetime, format="mixed")
entries_df["datetime"] = pd.to_datetime(entries_df.datetime, format="mixed")
files_df["datetime"] = pd.to_datetime(files_df.datetime, format="mixed")
missing_data_dates["datetime"] = pd.to_datetime(missing_data_dates.datetime)

# ---------------------------------------------------------------------------
# Computed statistics
# ---------------------------------------------------------------------------

_entry_counts = entries_df["action"].value_counts()
opt_in_frac: float = _entry_counts["optIn"] / (
    _entry_counts["optIn"] + _entry_counts["optOut"]
)
