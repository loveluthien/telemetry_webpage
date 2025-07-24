import dash
from dash import dcc, html, Input, Output, ctx, dash_table
# import dash_daq as daq
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeSwitchAIO

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import calendar
from pycountry_convert import country_name_to_country_alpha3
import configparser

## some global variables ##
today = datetime.today().date()
init_date = date(2021, 12, 1)
configParser = configparser.ConfigParser()
configParser.read('config')
SHOWED_COUNTRY_NUM = 10
## some global variables ##

# Available themes
LIGHT_THEME = dbc.themes.BOOTSTRAP
DARK_THEME = dbc.themes.DARKLY


#### load data ####
# Load CSV data
df_dir = configParser.get('PATH', 'df_dir')

users_df = pd.read_csv(f"{df_dir}/processed_users.csv")
sessions_df = pd.read_csv(f"{df_dir}/processed_sessions.csv", dtype={'OS_version': str})
entries_df = pd.read_csv(f"{df_dir}/processed_entries.csv")
files_df = pd.read_csv(f"{df_dir}/processed_files.csv")
missing_data_dates = pd.read_csv(f"{df_dir}/missing_data_dates.csv")

# process date information 
users_df['datetime'] = pd.to_datetime(users_df.datetime, format='mixed')
sessions_df['datetime'] = pd.to_datetime(sessions_df.datetime, format='mixed')
entries_df['datetime'] = pd.to_datetime(entries_df.datetime, format='mixed')
files_df['datetime'] = pd.to_datetime(files_df.datetime, format='mixed')
missing_data_dates['datetime'] = pd.to_datetime(missing_data_dates.datetime)

# optIn fraction
entries_df_counts = entries_df['action'].value_counts()
opt_in_frac = entries_df_counts['optIn'] / (entries_df_counts['optIn'] + entries_df_counts['optOut'])

size_label = ["<1MB", "1MB-10MB", "10MB-100MB", "100MB-1GB", "1GB-10GB", "10GB-100GB", "100GB-1TB", "1TB-10TB"] # in MB
size_label_index = {}

for i in range(len(size_label)):
    size_label_index[size_label[i]] = i
#### load data ####


# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[LIGHT_THEME, DARK_THEME])
server = app.server

#### make dataframes to table item ####

home_tab = html.Div([
    html.H1(["CARTA"]),
    html.H2(f"has been opened on {users_df.__len__()} computers"),
    html.H3("since Dec. 2021"),
    html.P(["* The statistics is not included the data from the ALMA archive and other self deployed servers", 
            html.Br(), 
            f"* {opt_in_frac*100:.1f}% users who allowed to share the telemetry data"]),
    ], className="home")

country_tab = html.Div([
    dbc.Row([
            dcc.Graph(id='country-pie'),
            dcc.Graph(id='country-map'),
            dbc.Row([dcc.Graph(id='country-other')])
    ], class_name="country-row1")
    ])

users_tab = html.Div([
        dbc.Row([
        dbc.RadioItems(
            options=["monthly", "weekly", "daily"],
            value="monthly",
            id="period-radio-item",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-primary",
            labelCheckedClassName="active",
        ),
        # Font size controls for axis labels
        html.Div([
            html.Label("Label Font Size:"),
            dcc.Input(id='label-fontsize', type='number', value=16, min=8, max=40, step=1, style={'width': '60px'}),
            html.Label("X Size:", style={'marginLeft': '20px'}),
            dcc.Input(id='x-tick-fontsize', type='number', value=12, min=6, max=32, step=1, style={'width': '60px'}),
            html.Label("Y Size:", style={'marginLeft': '10px'}),
            dcc.Input(id='y-tick-fontsize', type='number', value=12, min=6, max=32, step=1, style={'width': '60px'}),
            html.Label("Legend Font Size:", style={'marginLeft': '20px'}),
            dcc.Input(id='legend-fontsize', type='number', value=14, min=8, max=40, step=1, style={'width': '60px'}),
        ], style={'display': 'inline-block', 'marginLeft': '20px'}),
        ]),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Tabs(
                            id="tabs-counts-selection", value='unique-IP_tab', vertical=True,
                            children=[
                            dcc.Tab(label='Unique-IP', value='unique-IP_tab'),
                            dcc.Tab(label='UUID', value='uuid_tab'),
                            dcc.Tab(label='Active-IP', value='active-IP_tab'),
                            dcc.Tab(label='Sessions', value='session_tab'),
                        ]),
                    ),
                dbc.Col(
                    html.Div(id='tabs-counts-content'),
                    ),
            ], class_name="users-row2")
    ])

version_os_tab = html.Div([
        dbc.Row(
            [
                dbc.Col(
                    dcc.Tabs(
                            id="tabs-versions-selection", value='version_basic_tab', vertical=True,
                            children=[
                            dcc.Tab(label='version basic', value='version_basic_tab'),
                            dcc.Tab(label='version detail', value='version_detail_tab'),
                        ]),
                    ),
                dbc.Col(
                    html.Div(id='tabs-versions-content'),
                    ),
            ], class_name="version-os-row1")
    ])

file_tab = html.Div([
        dbc.Row(
            [
                dbc.Col(
                    dcc.Tabs(
                            id="tabs-files-selection", value='file_size_tab', vertical=True,
                            children=[
                            dcc.Tab(label='File size', value='file_size_tab'),
                            dcc.Tab(label='File shape', value='file_shape_tab'),
                            dcc.Tab(label='Action', value='action_tab'),
                        ]),
                    ),
                dbc.Col(
                    html.Div(id='tabs-files-content'),
                    ),
            ], class_name="file-row1")
    ])

date_range_button_group = dbc.ButtonGroup([
    dbc.Button("1 month", id="btn-last-1m", n_clicks=0, outline=True, color="secondary"),
    dbc.Button("3 month", id="btn-last-3m", n_clicks=0, outline=True, color="secondary"),
    dbc.Button("6 month", id="btn-last-6m", n_clicks=0, outline=True, color="secondary"),
    dbc.Button("1 year", id="btn-last-1y", n_clicks=0, outline=True, color="secondary"),
    dbc.Button("All", id="btn-all", n_clicks=0, outline=True, color="secondary"),
])

country_selection = html.Div([
    dbc.RadioItems(
            options=[
                {"label": "South Africa", "value":"ZA"},
                {"label": "Taiwan", "value":"TW"}, 
                {"label": "United States", "value":"US"},
                {"label": "All", "value":""}
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
    style={'display': 'inline-block', 'justify-content': 'center'})


@app.callback(Output('tabs-content', 'children'),
              Input('tabs-selection', 'value'))
def render_content(tab):
    if tab == 'country_tab':
        return country_tab
    elif tab == 'users_tab':
        return users_tab
    elif tab == 'version_os_tab':
        return version_os_tab
    elif tab == 'file_tab':
        return file_tab
    elif tab == 'home_tab':
        return home_tab
    

@app.callback(Output('tabs-counts-content', 'children'),
              Input('tabs-counts-selection', 'value'))
def render_content(tab):
    if tab == 'unique-IP_tab':
        return dcc.Graph(id='users-unique-IP'), dcc.Markdown("Every IP recorded only once since the telemetry started")
    elif tab == 'uuid_tab':
        return dcc.Graph(id='users-uuid'), dcc.Markdown("Unique ID for each computer")
    elif tab == 'active-IP_tab':
        return dcc.Graph(id='users-active-IP'), dcc.Markdown("Unduplicated IPs recorded during the selected period (montly, weekly, daily)")
    elif tab == 'session_tab':
        return dcc.Graph(id='users-session'), dcc.Markdown(f"Session numbers are from {opt_in_frac*100:.1f}% users allowing to share the telemetry data")


@app.callback(Output('tabs-versions-content', 'children'),
              Input('tabs-versions-selection', 'value'))
def render_versions(tab):
    if tab == 'version_basic_tab':
        return dcc.Graph(id='version-pie'), \
                dcc.Graph(id='os-pie'), \
                dcc.Markdown(f"Platform distribution is based on data from {opt_in_frac*100:.1f}% users who allowed to share the telemetry data")
    elif tab == 'version_detail_tab':
        return dcc.Graph(id='os_detail-pie'), dcc.Markdown(f"Data from {opt_in_frac*100:.1f}% users who allowed to share the telemetry data")

@app.callback(Output('tabs-files-content', 'children'),
              Input('tabs-files-selection', 'value'))
def render_files(tab):
    if tab == 'file_size_tab':
        return dcc.Graph(id='file-type-pie'), \
                dcc.Graph(id='file-size-pie'), \
                dcc.Graph(id='file-size-bar'), dcc.Markdown(f"All figures on this tab are based on data from {opt_in_frac*100:.1f}% users who allowed to share the telemetry data")
    elif tab == 'file_shape_tab':
        return dcc.Graph(id='file-shape'), dcc.Markdown(f"All figures on this tab are based on data from {opt_in_frac*100:.1f}% users who allowed to share the telemetry data")
    elif tab == 'action_tab':
        return dcc.Graph(id='action-bar'), dcc.Markdown(f"Data from {opt_in_frac*100:.1f}% users who allowed to share the telemetry data")


@app.callback(
    [Output('date-picker', 'start_date'),
        Output('date-picker', 'end_date')],
    [Input('date-picker', 'start_date'),
        Input('date-picker', 'end_date'),
        Input('btn-today', 'n_clicks'),
        Input('btn-last-1m', 'n_clicks'),
        Input('btn-last-3m', 'n_clicks'),
        Input('btn-last-6m', 'n_clicks'),
        Input('btn-last-1y', 'n_clicks'),
        Input('btn-all', 'n_clicks')
        ],
        prevent_initial_call=True
        )
def set_date_range(start_date, end_date, n_today, n_1m, n_3m, n_6m, n_1y, n_all):
    
    triggered_id = ctx.triggered_id
    
    if triggered_id == 'btn-today':
        return start_date, datetime.today().strftime('%Y-%m-%d')
    elif triggered_id == 'btn-last-1m':
        st = datetime.today() - timedelta(days=30)
        return st.strftime('%Y-%m-%d'), datetime.today().strftime('%Y-%m-%d')
    elif triggered_id == 'btn-last-3m':
        st = datetime.today() - timedelta(days=90)
        return st.strftime('%Y-%m-%d'), datetime.today().strftime('%Y-%m-%d')
    elif triggered_id == 'btn-last-6m':
        st = datetime.today() - timedelta(days=180)
        return st.strftime('%Y-%m-%d'), datetime.today().strftime('%Y-%m-%d')
    elif triggered_id == 'btn-last-1y':
        st = datetime.today() - timedelta(days=365)
        return st.strftime('%Y-%m-%d'), datetime.today().strftime('%Y-%m-%d')
    elif triggered_id == 'btn-all':
        return users_df['datetime'].min(), users_df['datetime'].max()
    return start_date, end_date



#### figures ####

## country tab ##
@app.callback(
    Output('country-map', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input(ThemeSwitchAIO.ids.switch("theme"), "value")]
)
def update_country_map_chart(start_date, end_date, toogle):
    theme = "cosmo" if not toogle else "cyborg"

    # process country information
    countries = users_df[(users_df['datetime'] >= start_date) & (users_df['datetime'] <= end_date)]
    countries = countries.country.value_counts().to_frame().reset_index().rename(columns={'index': 'Value', 'A': 'Count'})
    countries['iso_alpha'] = countries.country.apply(lambda x: country_name_to_country_alpha3(x))

    fig = px.scatter_geo(countries, locations="iso_alpha",
                        hover_name="country", size="count",
                        projection="natural earth", size_max=20, template=theme)
    fig.update_geos(showcountries=True)
    fig.update_layout(transition_duration=500)
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

    return fig

@app.callback(
    Output('country-pie', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input(ThemeSwitchAIO.ids.switch("theme"), "value")]
)
def update_country_pie_chart(start_date, end_date, toogle):
    theme = "cosmo" if not toogle else "cyborg"
    
    countries = users_df[(users_df['datetime'] >= start_date) & (users_df['datetime'] <= end_date)]
    countries = countries.country.value_counts().reset_index().rename(columns={'index': 'Value', 'A': 'Count'})
    other_countries = countries.iloc[SHOWED_COUNTRY_NUM:]

    for other in other_countries.country:
        countries.loc[countries.country == other, 'country'] = 'Others'

    fig = px.pie(countries, values="count", names="country", 
                hole=.4, hover_data=['country'], template=theme)
    # fig.update_traces(textposition='outside', textinfo='percent+label')
    # fig.update_traces(textposition='outside', textinfo='percent+value+label')
    fig.update_traces(textinfo='percent+value+label', insidetextorientation='horizontal')
    fig.update_layout(title_text="Top 10 countries", transition_duration=500, showlegend=False)
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

    return fig


@app.callback(
    Output('country-other', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input(ThemeSwitchAIO.ids.switch("theme"), "value")]
)
def update_other_country_chart(start_date, end_date, toogle):
    theme = "cosmo" if not toogle else "cyborg"
    
    countries = users_df[(users_df['datetime'] >= start_date) & (users_df['datetime'] <= end_date)]
    countries = countries.country.value_counts().reset_index().rename(columns={'index': 'Value', 'A': 'Count'})
    other_countries = countries.iloc[SHOWED_COUNTRY_NUM:]

    fig = px.bar(other_countries, x=other_countries['country'], y=other_countries['count']/countries['count'].sum()*100,
                text=other_countries['count'], 
                labels={'y':'%', 'x':'Country', 'text':'Count'},
                hover_data=['country'], template=theme)
    fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
    fig.update_layout(title_text="Details of others", transition_duration=500, xaxis_tickangle=45, xaxis_title=None)
    # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return fig

## country tab ##

## users tab ##
@app.callback(
    Output('users-unique-IP', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('period-radio-item', 'value'),
     Input('country-item', 'value'),
     Input('label-fontsize', 'value'),
     Input('legend-fontsize', 'value'),
     Input('x-tick-fontsize', 'value'),
     Input('y-tick-fontsize', 'value'),
     Input(ThemeSwitchAIO.ids.switch("theme"), "value")
    ]
)
def update_users_unique_IP_chart(start_date, end_date, period_value, country_value, label_fontsize, legend_fontsize, x_tick_fontsize, y_tick_fontsize, toogle):
    theme = "cosmo" if not toogle else "cyborg"
    
    if period_value == 'monthly':
        period = 'MS'
        fontsize = 12
        anno_y = 50
        day_shift = timedelta(days=14)
    elif period_value == 'weekly':
        period = 'W'
        fontsize = 8
        anno_y = 10
        day_shift = timedelta(days=3)
    elif period_value == 'daily':
        period = 'd'
        fontsize = 5
        anno_y = 5
        day_shift = timedelta(days=0)

    missing_data_resample =  missing_data_dates.resample(period, on='datetime').size()
    anno_dates = missing_data_resample[missing_data_resample.values > 0].keys()

    if country_value == '':
        country_select = entries_df['countryCode'] != country_value
    else:
        country_select = entries_df['countryCode'] == country_value
        

    entries_df_selected = entries_df[country_select]
    unique_select = entries_df_selected.reset_index().groupby(['ipHash'])['index'].min().to_list() # select the first entry of each unique IP
    monthly_uniqueIP = entries_df_selected.loc[unique_select].resample(period, on='datetime').size()
    cum_monthly_uniqueIP = np.cumsum(monthly_uniqueIP)

    dd_end = datetime.strptime(end_date.replace("T00:00:00", ""), '%Y-%m-%d')
    the_last_date_fo_month = calendar.monthrange(dd_end.year, dd_end.month)[1]
    new_end_date = f"{dd_end.year}-{dd_end.month}-{the_last_date_fo_month}"

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(x=monthly_uniqueIP.keys()+day_shift, y=monthly_uniqueIP.values, name='unique IP'),
        secondary_y=False,
        )

    fig.add_trace(
        go.Scatter(x=monthly_uniqueIP.keys()+day_shift, y=cum_monthly_uniqueIP,
                mode='lines',
                name='cumulative',
                ),
        # go.Bar(x=monthly_uniqueIP.keys(), y=cum_monthly_uniqueIP, name='cumulative'),
        secondary_y=True,
        )

    fig.update_layout(
        title_text="Unique IP counts",
        template=theme
    )

    fig.update_yaxes(title_text="# Unique IP", secondary_y=False, gridcolor='lightblue', title_font=dict(size=label_fontsize), tickfont=dict(size=y_tick_fontsize))
    fig.update_yaxes(title_text="# Cumulative Unique IP", color='red', secondary_y=True, gridcolor='#fccfd2', title_font=dict(size=label_fontsize), tickfont=dict(size=y_tick_fontsize))
    fig.update_xaxes(rangeselector_y=1.0, rangeselector_x=0.5, title_font=dict(size=label_fontsize), tickfont=dict(size=x_tick_fontsize))

    fig.update_layout(
        xaxis=dict(
            autorangeoptions=dict(
                clipmin=start_date,
                clipmax=new_end_date,
            ),
            rangeslider=dict(
                visible=False
            ),
            type="date",
        )
    )

    fig.update_layout(legend=dict(
        yanchor="bottom",
        y=1.00,
        xanchor="left",
        x=0.9,
        font=dict(size=legend_fontsize)
    ))

    for dd in anno_dates:
        fig.add_annotation(
            x=dd + day_shift,
            y=anno_y,
            text="incomplete data",
            showarrow=False,
            xanchor="center",
            yanchor="bottom",
            textangle=-90,
            font=dict(
                size=fontsize
            )
        )

    return fig


@app.callback(
    Output('users-uuid', 'figure'),
    [
        Input('date-picker', 'start_date'),
        Input('date-picker', 'end_date'),
        Input('period-radio-item', 'value'),
        Input('country-item', 'value'),
        Input('label-fontsize', 'value'),
        Input('legend-fontsize', 'value'),
        Input('x-tick-fontsize', 'value'),
        Input('y-tick-fontsize', 'value'),
        Input(ThemeSwitchAIO.ids.switch("theme"), "value")
    ]
)
def update_users_uuid_chart(start_date, end_date, period_value, country_value, label_fontsize, legend_fontsize, x_tick_fontsize, y_tick_fontsize, toogle):
    theme = "cosmo" if not toogle else "cyborg"

    if period_value == 'monthly':
        period = 'MS'
        fontsize = 12
        anno_y = 50
        day_shift = timedelta(days=14)
    elif period_value == 'weekly':
        period = 'W'
        fontsize = 8
        anno_y = 10
        day_shift = timedelta(days=3)
    elif period_value == 'daily':
        period = 'd'
        fontsize = 5
        anno_y = 5
        day_shift = timedelta(days=0)

    missing_data_resample =  missing_data_dates.resample(period, on='datetime').size()
    anno_dates = missing_data_resample[missing_data_resample.values > 0].keys()

    if country_value == '':
        country_select = users_df['countryCode'] != country_value
    else:
        country_select = users_df['countryCode'] == country_value

    users_df_selected = users_df[country_select]
    monthly_uuid = users_df_selected.resample(period, on='datetime').size()
    cum_monthly_uuid = np.cumsum(monthly_uuid)

    dd_end = datetime.strptime(end_date.replace("T00:00:00", ""), '%Y-%m-%d')
    the_last_date_fo_month = calendar.monthrange(dd_end.year, dd_end.month)[1]
    new_end_date = f"{dd_end.year}-{dd_end.month}-{the_last_date_fo_month}"

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(x=monthly_uuid.keys() + day_shift, y=monthly_uuid.values, name='uuid'),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=monthly_uuid.keys() + day_shift, y=cum_monthly_uuid,
                mode='lines',
                name='cumulative',
                ),
        secondary_y=True,
    )

    fig.update_layout(
        title_text="UUID counts",
        template=theme
    )

    fig.update_layout(
        xaxis=dict(
            autorangeoptions=dict(
                clipmin=start_date,
                clipmax=new_end_date,
            ),
            rangeslider=dict(
                visible=False
            ),
            type="date"
        )
    )

    fig.update_yaxes(
        title_text="# UUID",
        secondary_y=False,
        gridcolor='lightblue',
        title_font=dict(size=label_fontsize),  # Use y label font size from UI
        tickfont=dict(size=y_tick_fontsize)
    )
    fig.update_yaxes(
        title_text="# Cumulative UUID",
        color='red',
        secondary_y=True,
        gridcolor='#fccfd2',
        title_font=dict(size=label_fontsize),  # Use y label font size from UI
        tickfont=dict(size=y_tick_fontsize)
    )
    fig.update_xaxes(
        rangeselector_y=1.0,
        rangeselector_x=0.5,
        title_font=dict(size=label_fontsize),  # Use x label font size from UI
        tickfont=dict(size=x_tick_fontsize)
    )

    fig.update_layout(legend=dict(
        yanchor="bottom",
        y=1.00,
        xanchor="left",
        x=0.9,
        font=dict(size=legend_fontsize)
    ))

    for dd in anno_dates:
        fig.add_annotation(
            x=dd + day_shift,
            y=anno_y,
            text="incomplete data",
            showarrow=False,
            xanchor="center",
            yanchor="bottom",
            textangle=-90,
            font=dict(
                size=fontsize
            )
        )

    return fig


@app.callback(
    Output('users-active-IP', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('period-radio-item', 'value'),
     Input('country-item', 'value'),
     Input('label-fontsize', 'value'),
     Input('legend-fontsize', 'value'),
     Input('x-tick-fontsize', 'value'),
     Input('y-tick-fontsize', 'value'),
     Input(ThemeSwitchAIO.ids.switch("theme"), "value")
    ]
)
def update_users_active_IP_chart(start_date, end_date, period_value, country_value, label_fontsize, legend_fontsize, x_tick_fontsize, y_tick_fontsize, toogle):
    theme = "cosmo" if not toogle else "cyborg"
    
    if period_value == 'monthly':
        period = 'MS'
        fontsize = 12
        anno_y = 50
        day_shift = timedelta(days=14)
    elif period_value == 'weekly':
        period = 'W'
        fontsize = 8
        anno_y = 10
        day_shift = timedelta(days=3)
    elif period_value == 'daily':
        period = 'd'
        fontsize = 5
        anno_y = 5
        day_shift = timedelta(days=0)

    missing_data_resample =  missing_data_dates.resample(period, on='datetime').size()
    anno_dates = missing_data_resample[missing_data_resample.values > 0].keys()
    
    if country_value == '':
        country_select = entries_df['countryCode'] != country_value
    else:
        country_select = entries_df['countryCode'] == country_value

    entries_df_selected = entries_df[country_select]
    monthly_IP = entries_df_selected.resample(period, on='datetime')
    monthly_IP = monthly_IP.apply(lambda x: x.ipHash.unique().size)

    dd_end = datetime.strptime(end_date.replace("T00:00:00", ""), '%Y-%m-%d')
    the_last_date_fo_month = calendar.monthrange(dd_end.year, dd_end.month)[1]
    new_end_date = f"{dd_end.year}-{dd_end.month}-{the_last_date_fo_month}"

    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(x=monthly_IP.keys()+day_shift, y=monthly_IP.values, name='Active IP'))


    fig.update_layout(
        title_text="Active IP counts",
        template=theme
        )

    fig.update_layout(
        xaxis=dict(
            autorangeoptions=dict(
                clipmin=start_date,
                clipmax=new_end_date,
            ),
            rangeslider=dict(
                visible=False
            ),
            type="date"
        )
    )

    fig.update_xaxes(rangeselector_y=1.0, rangeselector_x=0.5, title_font=dict(size=label_fontsize), tickfont=dict(size=x_tick_fontsize))
    fig.update_yaxes(title_text="# Active IP", gridcolor='lightblue', title_font=dict(size=label_fontsize), tickfont=dict(size=y_tick_fontsize))

    fig.update_layout(legend=dict(
        yanchor="bottom",
        y=1.00,
        xanchor="left",
        x=0.9,
        font=dict(size=legend_fontsize)
    ))

    for dd in anno_dates:
        fig.add_annotation(
            x=dd + day_shift,
            y=anno_y,
            text="incomplete data",
            showarrow=False,
            xanchor="center",
            yanchor="bottom",
            textangle=-90,
            font=dict(
                size=fontsize
            )
        )

    return fig


@app.callback(
    Output('users-session', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('period-radio-item', 'value'),
     Input('country-item', 'value'),
     Input('label-fontsize', 'value'),
     Input('legend-fontsize', 'value'),
     Input('x-tick-fontsize', 'value'),
     Input('y-tick-fontsize', 'value'),
     Input(ThemeSwitchAIO.ids.switch("theme"), "value")
    ]
)
def update_users_session_chart(start_date, end_date, period_value, country_value, label_fontsize, legend_fontsize, x_tick_fontsize, y_tick_fontsize, toogle):
    theme = "cosmo" if not toogle else "cyborg"
    
    if period_value == 'monthly':
        period = 'MS'
        fontsize = 12
        anno_y = 50
        day_shift = timedelta(days=14)
    elif period_value == 'weekly':
        period = 'W'
        fontsize = 8
        anno_y = 10
        day_shift = timedelta(days=3)
    elif period_value == 'daily':
        period = 'd'
        fontsize = 5
        anno_y = 5
        day_shift = timedelta(days=0)

    missing_data_resample =  missing_data_dates.resample(period, on='datetime').size()
    anno_dates = missing_data_resample[missing_data_resample.values > 0].keys()
    
    if country_value == '':
        country_select = entries_df['countryCode'] != country_value
    else:
        country_select = entries_df['countryCode'] == country_value

    entries_df_selected = entries_df[country_select]
    monthly_session = entries_df_selected.resample(period, on='datetime')
    monthly_session = monthly_session.apply(lambda x: x.sessionId.unique().size)

    dd_end = datetime.strptime(end_date.replace("T00:00:00", ""), '%Y-%m-%d')
    the_last_date_fo_month = calendar.monthrange(dd_end.year, dd_end.month)[1]
    new_end_date = f"{dd_end.year}-{dd_end.month}-{the_last_date_fo_month}"

    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(x=monthly_session.keys()+day_shift, y=monthly_session.values, name='session'))


    fig.update_layout(
        title_text="Session counts",
        template=theme
        )

    fig.update_layout(
        xaxis=dict(
            autorangeoptions=dict(
                clipmin=start_date,
                clipmax=new_end_date,
            ),
            rangeslider=dict(
                visible=False
            ),
            type="date"
        )
    )

    fig.update_xaxes(rangeselector_y=1.0, rangeselector_x=0.5, title_font=dict(size=label_fontsize), tickfont=dict(size=x_tick_fontsize))
    fig.update_yaxes(title_text="# Session", gridcolor='lightblue', title_font=dict(size=label_fontsize), tickfont=dict(size=y_tick_fontsize))

    fig.update_layout(legend=dict(
        yanchor="bottom",
        y=1.00,
        xanchor="left",
        x=0.9,
        font=dict(size=legend_fontsize)
    ))

    for dd in anno_dates:
        fig.add_annotation(
            x=dd + day_shift,
            y=anno_y,
            text="incomplete data",
            showarrow=False,
            xanchor="center",
            yanchor="bottom",
            textangle=-90,
            font=dict(
                size=fontsize
            )
        )

    return fig
## users tab ##

## version and os tab ##
@app.callback(
    Output('version-pie', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('country-item', 'value'),]
)
def update_version_pie_chart(start_date, end_date, country_value):
    # theme = "cosmo" if toogle else "cyborg"

    if country_value == '':
        country_select = sessions_df['countryCode'] != country_value
    else:
        country_select = sessions_df['countryCode'] == country_value

    versions = sessions_df[(sessions_df['datetime'] >= start_date) & (sessions_df['datetime'] <= end_date) & country_select]

    # others = versions.version.value_counts().keys()[versions.version.value_counts() < versions.__len__()/50]
    others = versions.version.value_counts().keys()[5:]
    for other in others:
        versions.loc[versions.version == other, 'version'] = 'Others'


    fig = px.pie(versions, names='version', title=f'Version distribution', hole=.4)
    # fig.update_traces(textinfo='percent+label')
    fig.update_traces(textinfo='value+percent+label', insidetextorientation='horizontal')

    fig.update_layout(
        transition_duration=500, 
        showlegend=False,
        margin={"r":0,"t":50,"l":0,"b":0}
    )
    return fig

@app.callback(
    Output('os-pie', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('country-item', 'value'),]
)
def update_os_pie_chart(start_date, end_date, country_value):
    # theme = "cosmo" if toogle else "cyborg"

    if country_value == '':
        country_select = sessions_df['countryCode'] != country_value
    else:
        country_select = sessions_df['countryCode'] == country_value

    platform = sessions_df[(sessions_df['datetime'] >= start_date) & (sessions_df['datetime'] <= end_date) & country_select]

    fig = px.pie(platform, names='backendPlatform', title=f'Platform distribution', hole=.4)
    fig.update_traces(textinfo='value+percent+label', insidetextorientation='horizontal')

    fig.update_layout(
        transition_duration=500, 
        showlegend=False,
        margin={"r":0,"t":50,"l":0,"b":0}
    )
    return fig


@app.callback(
    Output('os_detail-pie', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('country-item', 'value'),]
)
def update_os_detail_pie_chart(start_date, end_date, country_value):
    # theme = "cosmo" if toogle else "cyborg"

    if country_value == '':
        country_select = sessions_df['countryCode'] != country_value
    else:
        country_select = sessions_df['countryCode'] == country_value

    linux = sessions_df[(sessions_df['datetime'] >= start_date) & (sessions_df['datetime'] <= end_date) & (sessions_df['backendPlatform'] == 'Linux') & (sessions_df['version'].isnull() == False) & country_select]
    linux_OS = linux['OS'].value_counts().reset_index().rename(columns={'index': 'Value', 'A': 'Count'})
    
    linux_sub = {}
    for selected_OS in linux_OS['OS']:

        linux_selected = linux[linux['OS'] == selected_OS]
        linux_OS_version = linux_selected['OS_version'].value_counts().reset_index().rename(columns={'index': 'Value', 'A': 'Count'})
        linux_sub[selected_OS] = linux_OS_version

    mac = sessions_df[(sessions_df['datetime'] >= start_date) & (sessions_df['datetime'] <= end_date) & (sessions_df['backendPlatform'] == 'macOS') & (sessions_df['version'].isnull() == False) & country_select]
    mac_OS = mac['OS'].value_counts().reset_index().rename(columns={'index': 'Value', 'A': 'Count'})
    
    mac_sub = {}
    for selected_OS in mac_OS['OS']:

        mac_selected = mac[mac['OS'] == selected_OS]
        mac_OS_version = mac_selected['OS_version'].value_counts().reset_index().rename(columns={'index': 'Value', 'A': 'Count'})
        mac_sub[selected_OS] = mac_OS_version

    if linux_sub.keys().__len__() < 3:
        showed_num = linux_sub.keys().__len__()
    else:
        showed_linux_num = 3

    version_labels = []
    version_values = []
    os_array = []
    platform_array = []
    # linux
    for i in range(showed_linux_num):

        the_linux = linux_sub[list(linux_sub.keys())[i]]

        if the_linux['OS_version'].__len__() < 3:
            showed_num = the_linux['OS_version'].__len__()
        else:
            showed_num = 3

        version_labels += the_linux['OS_version'][:showed_num].to_list()
        version_values += the_linux['count'][:showed_num].to_list()

        version_labels += ['others']
        version_values += [the_linux['count'][showed_num:].sum()]

        os_array += [list(linux_sub.keys())[i] for redundent in range(showed_num+1)]
        platform_array += ['Linux' for redundent in range(showed_num+1)]

    version_labels += [None]
    os_array += ['others']
    version_values += [linux_OS['count'][showed_num:].sum()]
    platform_array += ['Linux']

    # mac 
    the_mac = mac_sub['macOS']

    if the_mac['OS_version'].__len__() < 3:
        showed_num = the_mac['OS_version'].__len__()
    else:
        showed_num = 3

    version_labels += the_mac['OS_version'][:showed_num].to_list()
    version_values += the_mac['count'][:showed_num].to_list()
    version_labels += ['others']
    version_values += [the_mac['count'][showed_num:].sum()]
    os_array += [list(mac_sub.keys())[0] for redundent in range(showed_num+1)]
    platform_array += ['macOS' for redundent in range(showed_num+1)]


    df = pd.DataFrame(
        dict(os=os_array, version=version_labels, count=version_values, platform=platform_array)
    )

    fig = px.sunburst(df, path=['platform', 'os', 'version'], values='count')

    fig.update_layout(
        transition_duration=1000, 
        showlegend=False,
        # margin={"r":0,"t":0,"l":0,"b":0}
        width=800,
        height=800
    )
    return fig

## version and os tab ##


## file tab ##

@app.callback(
    Output('file-type-pie', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('country-item', 'value'),]
)
def update_file_pie_chart(start_date, end_date, country_value):

    if country_value == '':
        country_select = files_df['countryCode'] != country_value
    else:
        country_select = files_df['countryCode'] == country_value

    select_files = files_df[(files_df['datetime'] >= start_date) & (files_df['datetime'] <= end_date) & country_select]
    file_types = select_files.file_type.value_counts().reset_index().rename(columns={'index': 'Value', 'A': 'Count'})

    fig = go.Figure(go.Pie(
        name = "",
        values = file_types['count'],
        labels = file_types['file_type'],
        text = file_types['file_type'],
        hole=.4
    ))

    fig.update_traces(insidetextorientation='horizontal')
    fig.update_layout(
        transition_duration=500, 
        title_text=f'File types distribution',
        margin={"r":0,"t":50,"l":0,"b":0},
        showlegend=False
    )

    return fig

@app.callback(
    Output('file-size-pie', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('country-item', 'value'),]
)
def update_file_size_pie_chart(start_date, end_date, country_value):

    if country_value == '':
        country_select = files_df['countryCode'] != country_value
    else:
        country_select = files_df['countryCode'] == country_value

    select_files = files_df[(files_df['datetime'] >= start_date) & (files_df['datetime'] <= end_date) & country_select]
    file_size_df = select_files["size_label"].value_counts().reset_index().rename(columns={'index': 'size_label', 'A': 'Count'})

    for label in size_label:
        file_size_df.loc[file_size_df.size_label == label, 'index'] = size_label_index[label]

    file_size_df.sort_values(by='index', inplace=True)

    fig = go.Figure(go.Pie(
        name = "",
        values = file_size_df['count'],
        labels = file_size_df['size_label'],
        text = file_size_df['size_label'],
        hole=.4
    ))

    fig.update_traces(insidetextorientation='horizontal')
    fig.update_layout(
        title_text=f'File size distribution',
        transition_duration=500, 
        margin={"r":0,"t":50,"l":0,"b":0},
        showlegend=False,
    )

    return fig

@app.callback(
    Output('file-size-bar', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('country-item', 'value'),]
)
def update_file_size_bar_chart(start_date, end_date, country_value):

    if country_value == '':
        country_select = files_df['countryCode'] != country_value
    else:
        country_select = files_df['countryCode'] == country_value

    select_files = files_df[(files_df['datetime'] >= start_date) & (files_df['datetime'] <= end_date) & country_select]
    ss = {}
    for sl in size_label:
        ss[sl] = select_files.loc[select_files.size_label == sl, 'file_type'].value_counts().reset_index().rename(columns={'index': 'Value', 'A': 'Count'})

    fig = go.Figure()

    for sl in size_label:
        fig.add_trace(go.Bar(y=ss[sl]['file_type'], x=ss[sl]['count'], name=sl, orientation='h', text=sl))

    fig.update_layout(
        barmode='stack', 
        barnorm='percent',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
    ))
    fig.update_xaxes(title_text="%")

    return fig


@app.callback(
    Output('file-shape', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('country-item', 'value'),]
)
def update_file_shape_chart(start_date, end_date, country_value):

    if country_value == '':
        country_select = files_df['countryCode'] != country_value
    else:
        country_select = files_df['countryCode'] == country_value

    select_files = files_df[(files_df['datetime'] >= start_date) & (files_df['datetime'] <= end_date) & country_select]
    cube = select_files.loc[(select_files.file_type == '3D') | (select_files.file_type == '3D+Stokes')]
    
    fig = make_subplots(rows=1, cols=2)


    fig.add_trace(go.Histogram2d(x=np.log10(cube['details.width']), 
                            y=np.log10(cube['details.height']), 
                            #  colorscale='Viridis',
                            colorscale='dense',
                            autobinx=False,
                            autobiny=False,
                            xbins=dict(start=0, end=5, size=0.2),
                            ybins=dict(start=0, end=5, size=0.2),
                            colorbar=dict(len=1, x=0.45),
                            ),
                            row=1, col=1,
    )

    fig.add_trace(
        go.Scatter(
        x=[0,5], y=[0,5]),
        row=1, col=1,
        )
    
    fig.update_xaxes(title_text=r"Spatial X pixels [log]", row=1, col=1)
    fig.update_yaxes(title_text=r"Spatial Y pixels [log]", row=1, col=1)

    fig.add_trace(go.Histogram2d(x=np.log10(cube['details.width']), 
                            y=np.log10(cube['details.depth']), 
                            #  colorscale='Viridis',
                            colorscale='dense',
                            autobinx=False,
                            autobiny=False,
                            xbins=dict(start=0, end=5, size=0.2),
                            ybins=dict(start=0, end=5, size=0.2),
                            colorbar=dict(len=1, x=1),
                            ),
                            row=1, col=2,
    )

    fig.update_layout(
        xaxis=dict(
            autorangeoptions=dict(
                clipmin=0,
                clipmax=5,
            ),
            ),
        yaxis=dict(
            autorangeoptions=dict(
                clipmin=0,
                clipmax=5,
            )
            ,),
        # margin=dict(l=0, r=0, t=0, b=0),
        )
    
    # fig.add_trace(
    #     go.Scatter(
    #     x=[0,5], y=[0,5]),
    #     row=1, col=2,
    #     )

    fig.update_xaxes(title_text=r"Spatial X pixels [log]", row=1, col=2)
    fig.update_yaxes(title_text=r"Channels [log]", row=1, col=2)

    return fig


@app.callback(
    Output('action-bar', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('country-item', 'value'),]
)
def update_file_shape_XY_chart(start_date, end_date, country_value):

    if country_value == '':
        country_select = entries_df['countryCode'] != country_value
    else:
        country_select = entries_df['countryCode'] == country_value

    select_entries = entries_df[(entries_df['datetime'] >= start_date) & (entries_df['datetime'] <= end_date) & country_select]
    
    actions = select_entries.action.value_counts()

    plot_action_names = ['spectralProfileGeneration', 'momentGeneration', 'catalogLoading', 'pvGeneration']

    fig = go.Figure()
    for action_name in plot_action_names:
        ratio = actions[action_name] / actions['endSession']
        fig.add_trace(go.Bar(y=['action'], x=[ratio], name=f'{action_name}', orientation='h', text=[f'{action_name}']))

    fig.update_layout(
        barmode='stack', 
        barnorm='percent',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
    ))
    fig.update_xaxes(title_text="%")

    return fig

## file tab ##


def serve_layout():
    layout = dbc.Container([
        html.Div([
            dcc.DatePickerRange(
                id='date-picker',
                start_date='2021-12-01',
                end_date=today.strftime('%Y-%m-%d'),
                display_format='YYYY-MM-DD',
            ),
            dbc.Button("Today", id="btn-today", n_clicks=0, outline=True, color="primary"),
            date_range_button_group,
            country_selection,
            ThemeSwitchAIO(
                aio_id="theme", themes=[dbc.themes.COSMO, dbc.themes.CYBORG],
                # switch_props={"label": "Dark Mode", "labelPosition": "start"}
            )
        ], style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'width': '100%'}),
        dcc.Tabs(
            id="tabs-selection", value='home_tab',
            children=[
            dcc.Tab(label='Home', value='home_tab'),
            dcc.Tab(label='Countries', value='country_tab'),
            dcc.Tab(label='Users', value='users_tab'),
            dcc.Tab(label='Versions and OS', value='version_os_tab'),
            dcc.Tab(label='Files and actions', value='file_tab'),
        ]),
        html.Div(id='tabs-content'),
        ], fluid=True)
    
    return layout


app.layout = serve_layout

if __name__ == '__main__':
    debug_mode = configParser.get('SERVER', 'debug') == 'True'
    host_ip = configParser.get('SERVER', 'host')
    if host_ip == '':
        host_ip = 'localhost'
    port = configParser.get('SERVER', 'port')
    if port == '':
        port = 8050
    app.run(debug=debug_mode, host=host_ip, port=port)
