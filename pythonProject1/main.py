from dash import Dash, html, dcc, Input, Output, callback
import pandas as pd
import numpy as np
from urllib.request import urlopen
import json
import plotly.express as px
from plotly.subplots import make_subplots

df = pd.read_csv('crimedata.csv')

df = df.dropna(subset=['countyCode']).reset_index()

external_stylesheets = [
    'https://gist.githubusercontent.com/zluvsand/4debf98c2d12bea077275c56f90bc767/raw/ccbfe65ac9dab4b232ee016e6344c3b2ffba72b8/style.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

df_sample = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/laucnty16.csv')
df_sample['State FIPS Code'] = df_sample['State FIPS Code'].apply(lambda x: str(x).zfill(2))
df_sample['County FIPS Code'] = df_sample['County FIPS Code'].apply(lambda x: str(x).zfill(3))
df_sample['FIPS'] = df_sample['State FIPS Code'] + df_sample['County FIPS Code']
df['countyCode'] = df['countyCode'].apply(lambda x: str(int(x)).zfill(3))


def replacing_words(x):
    x = x.split(",")[0]
    samples = [" County", "/town", " Parish", "/city"]
    for s in samples:
        x = x.replace(s, "")
    return x


def changing_state(x):
    x = x.split(", ")[-1]
    if x == 'District of Columbia':
        x = "DC"
    return x


df_sample["county"] = df_sample["County Name/State Abbreviation"].apply(lambda x: replacing_words(x))
df_sample["state"] = df_sample["County Name/State Abbreviation"].apply(lambda x: changing_state(x))
df_fips = pd.merge(df, df_sample[["County FIPS Code", 'county', "state", "FIPS"]], left_on=['countyCode', "state"],
                   right_on=['County FIPS Code', "state"], how='left')

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

fig = px.choropleth(df_fips, geojson=counties, locations='FIPS', color='ViolentCrimesPerPop',
                    color_continuous_scale="orrd",
                    range_color=(0, 1000),
                    scope="usa",
                    fitbounds='locations',
                    hover_data=["state", 'communityName', "ViolentCrimesPerPop"]
                    )
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

perc_data = pd.melt(df_fips[["communityName", "state", "racePctWhite", "racepctblack", "racePctHisp", "racePctAsian"]],
                    id_vars=["state", 'communityName'], var_name="Race", value_name="Perc")

inc_data = pd.melt(
    df_fips[['communityName', "state", 'whitePerCap', 'blackPerCap', 'AsianPerCap', 'HispPerCap']],
    id_vars=["state", 'communityName'], var_name="Race", value_name="Income")

inc_data = inc_data[inc_data.Income < 45000]
cop_data = pd.melt(
    df_fips[["communityName", "state", "PctPolicWhite", "PctPolicBlack", "PctPolicHisp", "PctPolicAsian"]],
    id_vars=["state", 'communityName'], var_name="Race", value_name="Perc")

learn_data = df_fips[['PctBSorMore', 'medFamInc']].sort_values(by=['PctBSorMore'])

fig_1 = px.pie(data_frame=perc_data, values="Perc", names="Race")
fig_2 = px.box(data_frame=inc_data, x='Race', y='Income')
fig_3 = px.pie(data_frame=cop_data, values='Perc', names='Race')
fig_1.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig_2.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig_3.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

fig_4 = px.line(data_frame=learn_data, x='PctBSorMore', y='medFamInc')

app.layout = html.Div(children=[
    html.Div([
        dcc.Markdown('Select State and community'),
        html.Div([
            html.Div([
                dcc.Dropdown(np.append(df.state.unique(), ['All']), 'All', id='state_dropdown'),
            ], style=dict(width='40%', align='center'), className='drop'),
            html.Div([
                dcc.Dropdown(np.append(df.communityName.unique(), ['All']), 'All', id='comm_dropdown'),
            ], style=dict(width='40%', align='center'), className='drop')
        ], style=dict(display='flex')),
        dcc.Markdown('Number of crimes per population'),
        dcc.RadioItems(['Violent Crimes', 'Nonviolent Crimes'], 'Violent Crimes', inline=True, id='crime-type', className='checkbox')
    ]),

    dcc.Graph(
        id='US_map',
        figure=fig,
        style=dict(horizontalAlign = 'middle'),
        className='graph'
    ),

    html.Div([
        html.Div([
            dcc.Checklist(["White", "Black", "Hispanic", "Asian"], ["White", "Black", "Hispanic", "Asian"], inline=True,
                          id='race_dist'),
            dcc.Checklist(["Race Distribution", 'Income Distribution', 'Police Race Distribution'],
                          ["Race Distribution", 'Income Distribution', 'Police Race Distribution'], inline=True,
                          id='graph_types')
        ], style={'columnCount': 2, 'align': 'center'}, className='checkbox'),
        html.Div([
            dcc.Markdown('Distribution of race in population', id='m1'),
            dcc.Markdown('Per capita income of races', id ='m2'),
            dcc.Markdown('Distribution of race in police', id='m3'),
        ], style={'columnCount': 3}),
        html.Div([
            html.Div([
                dcc.Graph(
                    id='Race_pie',
                    figure=fig_1,
                    style=dict(align='center', color='E0E6FF')
                )], style=dict(align='center')),
            html.Div([
                dcc.Graph(
                    id='Inc_bar',
                    figure=fig_2,
                    style=dict(align='center')
                )], style=dict(align='center')),
            html.Div([
                dcc.Graph(
                    id='Cop_pie',
                    figure=fig_3,
                    style=dict(align='center')
                )
            ], style=dict(align='center'))
        ], style={'columnCount': 3, 'align': 'center'}, className='drop')
    ]),

    dcc.Markdown('Dependence of earnings on education'),
    html.Div([
        dcc.Graph(
            id='learn_plot',
            figure=fig_4
        )
    ])
])


@callback(
    Output('comm_dropdown', 'options'),
    Input('state_dropdown', 'value')
)
def update_comm(state):
    res = np.append(df[df.state == state].communityName.unique(), ['All'])
    return res


@callback(
    Output('US_map', 'figure'),
    Input('state_dropdown', 'value'),
    Input('comm_dropdown', 'value'),
    Input('crime-type', 'value')
)
def update_map(state, comm, type):
    if type == 'Violent Crimes':
        cr_type = 'ViolentCrimesPerPop'
        m = 1000
    else:
        cr_type = 'nonViolPerPop'
        m = 8000
    if state == 'All' and comm == 'All':
        fig = px.choropleth(df_fips, geojson=counties, locations='FIPS', color=cr_type,
                            color_continuous_scale="orrd",
                            range_color=(0, m),
                            scope="usa",
                            fitbounds='locations',
                            hover_data=["state", 'communityName', cr_type]
                            )
    elif comm == 'All':
        fig = px.choropleth(df_fips[df_fips.state == state], geojson=counties, locations='FIPS',
                            color=cr_type,
                            color_continuous_scale="orrd",
                            range_color=(0, m),
                            scope="usa",
                            fitbounds='locations',
                            hover_data=["state", 'communityName', cr_type]
                            )
    else:
        fig = px.choropleth(df_fips[df_fips.communityName == comm], geojson=counties, locations='FIPS',
                            color=cr_type,
                            color_continuous_scale="orrd",
                            range_color=(0, m),
                            scope="usa",
                            fitbounds='locations',
                            hover_data=["state", 'communityName', cr_type]
                            )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


@callback(
    Output('Race_pie', 'figure'),
    Output('Race_pie', 'style'),
    Output('Inc_bar', 'figure'),
    Output('Inc_bar', 'style'),
    Output('Cop_pie', 'figure'),
    Output('Cop_pie', 'style'),
    Output('m1', 'style'),
    Output('m2', 'style'),
    Output('m3', 'style'),
    Input('state_dropdown', 'value'),
    Input('comm_dropdown', 'value'),
    Input('race_dist', 'value'),
    Input('graph_types', 'value')
)
def display_graphs(state, comm, race, g_types):
    lst = []
    if 'White' in race:
        lst.append('racePctWhite')
        lst.append('whitePerCap')
        lst.append('PctPolicWhite')
    if 'Asian' in race:
        lst.append('racePctAsian')
        lst.append('PctPolicAsian')
        lst.append('AsianPerCap')
    if 'Black' in race:
        lst.append('racepctblack')
        lst.append('blackPerCap')
        lst.append('PctPolicBlack')
    if 'Hispanic' in race:
        lst.append('racePctHisp')
        lst.append('HispPerCap')
        lst.append('PctPolicHisp')
    if 'Race Distribution' in g_types:
        a_1 = {'display': 'block', 'align': 'center'}
    else:
        a_1 = {'display': 'none'}
    if 'Income Distribution' in g_types:
        a_2 = {'display': 'block', 'align': 'center'}
    else:
        a_2 = {'display': 'none'}
    if 'Police Race Distribution' in g_types:
        a_3 = {'display': 'block', 'align': 'center'}
    else:
        a_3 = {'display': 'none'}
    if state == 'All' and comm == 'All':
        fig_1 = px.pie(data_frame=perc_data[perc_data.Race.isin(lst)], values="Perc", names="Race")
        fig_2 = px.box(data_frame=inc_data[(inc_data.Race.isin(lst))], x='Race', y='Income')
        fig_3 = px.pie(data_frame=cop_data[cop_data.Race.isin(lst)], values='Perc', names='Race')
    elif comm == 'All':
        fig_1 = px.pie(data_frame=perc_data[(perc_data.state == state) & (perc_data.Race.isin(lst))], values="Perc",
                       names="Race")
        fig_2 = px.box(data_frame=inc_data[(inc_data.Race.isin(lst)) & (inc_data.state == state)],
                       x='Race', y='Income')
        fig_3 = px.pie(data_frame=cop_data[(cop_data.Race.isin(lst)) & (cop_data.state == state)], values='Perc',
                       names='Race')
    else:
        fig_1 = px.pie(data_frame=perc_data[(perc_data.communityName == comm) & (perc_data.Race.isin(lst))],
                       values="Perc",
                       names="Race")
        fig_2 = px.box(data_frame=inc_data[(inc_data.Race.isin(
            lst)) & (inc_data.communityName == comm)],
                       x='Race', y='Income')
        fig_3 = px.pie(
            data_frame=cop_data[(cop_data.Race.isin(lst)) & (cop_data.communityName == comm)],
            values='Perc',
            names='Race')
    fig_1.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig_1, a_1, fig_2, a_2, fig_3, a_3, a_1, a_2, a_3


if __name__ == '__main__':
    app.run_server(debug=True)
