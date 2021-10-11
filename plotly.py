import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import os
import psycopg2
import datetime
from dash.dependencies import Input, Output, State
from spotify import SpotifyAPI

#################################################  DB & SETUP #########################################
client_id = ['ID']
client_secret = ['SECRET']
spotify = SpotifyAPI(client_id=client_id, client_secret=client_secret)

DATABASE_URL = ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

# retrive len table
cur.execute("select artist_id,Popularity, spotify.day, followers, artist.artist_name from spotify LEFT JOIN artist on spotify.artist_id = artist.id_artist")
num = cur.fetchall()
num = pd.DataFrame(num)
num.columns = ['id','popularity','date','followers','name']
last_day = num.loc[num['date']==num['date'].max(),]

app = dash.Dash(__name__,external_stylesheets=[dbc.themes.LUX])
server = app.server

url_bar_and_content_div = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

colors = {
    'background': '#191414',
    'text': '#1DB954'
}

##############################  RETRIEVING & MANIPULATING #################################################
# Analytics Data  
id = num.sort_values(by=['followers'], ascending=False).drop_duplicates(['id'])
growth_df = pd.DataFrame(columns=['name','perc_change','current', 'follow_change','id'])
for i in list(id['id']):
    xx = num.loc[num['id']==i,].sort_values(['date'])['followers'].pct_change()[-7:].sum()
    yy = num.loc[num['id']==i,].sort_values(['date'], ascending=False)['followers'].iloc[0]
    try:
        ff = int(list(num.loc[num['id']==i,].sort_values(['date'])['followers'])[-1]) -  int(list(num.loc[num['id']==i,].sort_values(['date'])['followers'])[-7])
    except:
        None
    name = num.loc[num['id']==i,].sort_values(['date'], ascending=False)['name'].iloc[0]
    growth_df.loc[len(growth_df)] = [name, float(xx*100), int(yy), int(ff), i]

artist_album_growth = growth_df.sort_values(by=["perc_change"], ascending=False).head(8)['id']
album_list = []
for i in artist_album_growth:
    alb = spotify.get_artist_album(i)
    alb = alb['items'][0]['id']
    album_list.append(alb)

magnets = growth_df.sort_values(by=["follow_change"], ascending=False).head(8)['id']
album_magnets = []
for i in magnets:
    alb = spotify.get_artist_album(i)
    alb = alb['items'][0]['id']
    album_magnets.append(alb)

num = num.fillna('NaN')

genres = {}
genres['post'] = 'Post Punk'
genres['new'] = 'New Wave'
dicts = {}
id_art = num[['id','name']].drop_duplicates().reset_index(drop=True)
for i in range(len(id_art)):
    dicts[id_art['id'][i]] = id_art['name'][i]

####################################################################################################
####################################### ANALYTICS PAGE #############################################
fig = px.scatter(last_day, x='followers', y='popularity',
                 hover_name='name', log_x=True, title="Popularity & Followers on Spotify", template="plotly_dark"
                 )

fig.update_layout(title=dict(font=dict(color='#1DB954')),paper_bgcolor='#191414',plot_bgcolor='#191414')
fig.update_traces(marker_color='#1DB954', marker_line_color='#1DB954',
                opacity=0.9)

fig1 = px.bar(growth_df.sort_values(by=["perc_change"], ascending=False).head(10), 
                x="name", y="perc_change", title='Asceding Artists: higher 7-Days growth (in percentage)', template="plotly_dark",text='perc_change')

fig2 = px.bar(growth_df.sort_values(by=["follow_change"], ascending=False).head(10), 
                x="name", y="follow_change", title='Attractive Artists: higher 7-Days followers gains', template="plotly_dark", text='follow_change')

fig1.update_layout(title=dict(font=dict(color='#1DB954')),paper_bgcolor='#191414',plot_bgcolor='#191414')
fig1.update_traces(marker_color='#1DB954', marker_line_color='#1DB954',
                opacity=0.9, texttemplate='%{text:.2s}', textposition='inside')

fig2.update_layout(title=dict(font=dict(color='#1DB954')),paper_bgcolor='#191414',plot_bgcolor='#191414')
fig2.update_traces(marker_color='#1DB954', marker_line_color='#1DB954',
                opacity=0.9, texttemplate='%{text:.2s}', textposition='outside')

############################################# Analytics Page HTML ######################################################
#######################################################################################################################
analytics_page = html.Div(style={'backgroundColor': colors['background']},children=[
    html.Div(children=[
    html.H1(children='Trendify', style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-top': '20px',
            'font-family': 'Gotham',
        }),
    html.Br(),
    html.Br(),
    dbc.Nav(
    [
        dbc.NavItem(dbc.NavLink("Home", active=True, href="/home", style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-bottom': '20px', 
            'font-family': 'Gotham',
            'font-size': '18px',
        })),
        dbc.NavItem(dbc.NavLink("Explore", active=True, href="/explore", style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-bottom': '20px',  
            'font-family': 'Gotham',
            'font-size': '18px',
        })),
        dbc.NavItem(dbc.NavLink("Analytics", href="/analytics",style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-bottom': '20px',
            'font-family': 'Gotham',
            'font-size': '18px',
        })),
        dbc.NavItem(dbc.NavLink("About", href="http://punkifyabout.s3-website.eu-central-1.amazonaws.com/",style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-bottom': '20px',
            'font-family': 'Gotham',
            'font-size': '18px',
        }))
    ],horizontal='center'),
    ]),
    html.Br(),
    html.Hr(style={'width':'90%','border-top': '1px solid #1DB954'}),
    html.Br(),
    html.P('OVERVIEW',style={'font-size': '40px','textAlign': 'center'}),
    html.Br(),
    html.Br(),
    dcc.Graph(
        id='popularity',
        figure=fig,
    ),
    html.Div(
    dcc.Graph(
        id='weekly-change-perc',
        figure=fig1,
    ),style={'width': '49%', 'display': 'inline-block'}),
    html.Div(
    dcc.Graph(
        id='weekly-change-abs',
        figure=fig2,
    ),style={'width': '49%', 'float': 'right', 'display': 'inline-block'}),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Hr(style={'width':'90%','border-top': '1px solid #1DB954'}),
    html.Br(),
    html.Br(),
    html.P('Pick an Artist:',style={'font-size': '30px','textAlign': 'center'}),
    html.Br(),
    html.Div([
            dcc.Dropdown(
                style={'width':'50%','margin-top':'5px','margin-bottom':'5px','margin-left': '25%'},
                id='artist-analytics',
                options=[{'label': dicts[i], 'value': i} for i in dicts],
                value=num['id'][0])
    ]),
    html.Br(),
    html.Div(style={"display": "flex", "justify-content": "center","align-items": "center", "height": "50px"},children=[
    html.Button('Get Data', id='button-data-artist',style={"background": "#f3f0f1","border-radius": "32px","text-align": "center"}),]),
    html.Br(),
    html.Div(
    dcc.Graph(
        id='artist-graph-1'
    ),style={'backgroundColor': colors['background']},),
    html.Div(
    dcc.Graph(
        id='artist-graph-2'
    ),style={'backgroundColor': colors['background']},),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Div(
    dcc.Graph(
        id='artist-graph-4'
    ),style={'backgroundColor': colors['background']},),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Hr(style={'width':'90%','border-top': '1px solid #1DB954'}),
    html.Br(),
    html.Br(),
    html.Footer(children=[
        dbc.Nav(style={'margin':'30px','padding':'0 25%'},children=
        [
            dbc.NavItem(dbc.NavLink("Home",active=True, href="/home",style={'color': '#1DB954'})),
            dbc.NavItem(dbc.NavLink("Explore", href="/explore",style={'color': '#1DB954'})),
            dbc.NavItem(dbc.NavLink("Analytics", href="/analytics",style={'color': '#1DB954'})),
            dbc.NavItem(dbc.NavLink("About", active=True, href="/about",style={'color': '#1DB954'})),
        ],
        vertical="md",
        )]),
    html.Br(), 
])

@app.callback(
    (Output(component_id='artist-graph-1', component_property='figure'),
    Output(component_id='artist-graph-2', component_property='figure'),
    Output(component_id='artist-graph-4', component_property='figure')),
    [Input(component_id='artist-analytics', component_property='value'),
    Input(component_id='button-data-artist', component_property='n_clicks')])
def artist_analytics(artist_identity, n_clicks):
    if n_clicks == None:
        fig4 = go.Figure()
        fig5 = go.Figure()
        fig7 = go.Figure()
    else:
         ###### Big Numbers Graph ##############
        fig4 = go.Figure()

        fig4.add_trace(go.Indicator(
            mode = "number",
            value = int(last_day.loc[last_day['id']==str(artist_identity),'followers']),
            domain = {'row': 0, 'column': 0},
            title="<b>Followers</b>"))

        fig4.add_trace(go.Indicator(
            mode = "number",
            value = int(last_day.loc[last_day['id']==str(artist_identity),'popularity']),
            domain = {'row': 1, 'column': 0},
            title=f"<b>Popularity</b>"))

        fig4.add_trace(go.Indicator(
            mode = "number",
            value = float(growth_df.loc[growth_df['id']==str(artist_identity),'perc_change']),
            domain = {'row': 0, 'column': 1},
            title="<b>Percentage Growth</b>"))

        fig4.add_trace(go.Indicator(
            mode = "number",
            value = int(growth_df.loc[growth_df['id']==str(artist_identity),'follow_change']),
            domain = {'row': 1, 'column': 1},
            title="<b>Followers Acquisition</b>"))

        fig4.update_layout(
            title=dict(font=dict(color='#1DB954')),
            paper_bgcolor='#191414',
            plot_bgcolor='#1DB954',
            grid = {'rows': 2, 'columns': 2, 'pattern': "independent"},
            template = {'data' : {'indicator': [{
                'mode' : "number+gauge",
                'delta' : {'reference': 90}}]
                                }})
        
        fig4.update_traces(
            number=dict(font=dict(color='#1DB954')),
            title=dict(font=dict(color='#1DB954')),
        )

        ################ Timeline Followers #########################
        time_follow = num.loc[num['id']==str(artist_identity),]

        fig5 = px.line(time_follow, x='date', y='followers',
                 hover_name='name', title="Followers growth on Spotify", template="plotly_dark")
        fig5.update_layout(title=dict(font=dict(color='#1DB954')),paper_bgcolor='#191414',plot_bgcolor='#191414')
        fig5.update_traces(marker_color='#1DB954', marker_line_color='#1DB954',
                opacity=0.9)

        ############# Music Data #################
        if int(last_day.loc[last_day['id']==str(artist_identity),'followers']) < 10000:
            idid = str(artist_identity)
            albumm = spotify.get_artist_album(idid)
            albumm = albumm['items']
            lists_album = []
            for i in range(len(albumm)):
                lists_album.append(albumm[i]['id'])
            music_data = pd.DataFrame(columns=['id','danceability',"energy","tempo","speechiness","acousticness","instrumentalness"])
            lists_tracks = []
            for i in lists_album:
                tracks = spotify.get_track_album(i)
                for i in range(len(tracks['items'])):
                    lists_tracks.append(tracks['items'][i]['id'])
            for i in lists_tracks:
                track_analytics = spotify.get_info_tracks(i)
                music_data.loc[len(music_data)] = [track_analytics['audio_features'][0]['id'], track_analytics['audio_features'][0]['danceability'], float(track_analytics['audio_features'][0]['energy']), track_analytics['audio_features'][0]['tempo'],track_analytics['audio_features'][0]['speechiness'],track_analytics['audio_features'][0]['acousticness'],track_analytics['audio_features'][0]['instrumentalness']]

            fig7 = go.Figure(go.Violin(y=music_data['energy'], box_visible=True, line_color='black',
                                meanline_visible=True, fillcolor='#1DB954', opacity=0.6,name='Energy'))
            fig7.add_trace(go.Violin(y=music_data['acousticness'], box_visible=True, line_color='black',
                                meanline_visible=True, fillcolor='#1DB954', opacity=0.6, name='Acousticness'))
            fig7.add_trace(go.Violin(y=music_data['instrumentalness'], box_visible=True, line_color='black',
                                meanline_visible=True, fillcolor='#1DB954', opacity=0.6,name='Instrumentalness'))
            fig7.add_trace(go.Violin(y=music_data['speechiness'], box_visible=True, line_color='black',
                                meanline_visible=True, fillcolor='#1DB954', opacity=0.6,name='Speechiness'))
            fig7.add_trace(go.Violin(y=music_data['danceability'], box_visible=True, line_color='black',
                                meanline_visible=True, fillcolor='#1DB954', opacity=0.6,name='Danceability'))

            fig7.update_layout(font={'color':'#1DB954'},showlegend=False,title_text="Tracks Features Distribution",title=dict(font=dict(color='#1DB954')),paper_bgcolor='#191414',plot_bgcolor='#191414')
            fig7.update_traces(marker_color='#1DB954', marker_line_color='#1DB954')
        else:
            idid = str(artist_identity)
            albumm = spotify.get_artist_album(idid)
            albumm = albumm['items']
            lists_album = []
            for i in range(8):
                lists_album.append(albumm[i]['id'])
            music_data = pd.DataFrame(columns=['id','danceability',"energy","tempo","speechiness","acousticness","instrumentalness"])
            lists_tracks = []
            for i in lists_album:
                tracks = spotify.get_track_album(i)
                for i in range(len(tracks['items'])):
                    lists_tracks.append(tracks['items'][i]['id'])
            for i in lists_tracks:
                track_analytics = spotify.get_info_tracks(i)
                music_data.loc[len(music_data)] = [track_analytics['audio_features'][0]['id'], track_analytics['audio_features'][0]['danceability'], float(track_analytics['audio_features'][0]['energy']), track_analytics['audio_features'][0]['tempo'],track_analytics['audio_features'][0]['speechiness'],track_analytics['audio_features'][0]['acousticness'],track_analytics['audio_features'][0]['instrumentalness']]

            fig7 = go.Figure(go.Violin(y=music_data['energy'], box_visible=True, line_color='black',
                                meanline_visible=True, fillcolor='#1DB954', opacity=0.6,name='Energy'))
            fig7.add_trace(go.Violin(y=music_data['acousticness'], box_visible=True, line_color='black',
                                meanline_visible=True, fillcolor='#1DB954', opacity=0.6, name='Acousticness'))
            fig7.add_trace(go.Violin(y=music_data['instrumentalness'], box_visible=True, line_color='black',
                                meanline_visible=True, fillcolor='#1DB954', opacity=0.6,name='Instrumentalness'))
            fig7.add_trace(go.Violin(y=music_data['speechiness'], box_visible=True, line_color='black',
                                meanline_visible=True, fillcolor='#1DB954', opacity=0.6,name='Speechiness'))
            fig7.add_trace(go.Violin(y=music_data['danceability'], box_visible=True, line_color='black',
                                meanline_visible=True, fillcolor='#1DB954', opacity=0.6,name='Danceability'))

            fig7.update_layout(font={'color':'#1DB954'},showlegend=False,title_text="Tracks Features Distribution",title=dict(font=dict(color='#1DB954')),paper_bgcolor='#191414',plot_bgcolor='#191414')
            fig7.update_traces(marker_color='#1DB954', marker_line_color='#1DB954')

    return (fig4, fig5,fig7)


#######################################################################################################
########################################### EXPLORE PAGE ##############################################

## Explore Page HTML ###
explore_page = html.Div(style={'backgroundColor': colors['background']},children=[
    html.H1(children='Trendify', style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-top': '20px',
            'font-family': 'Gotham',
        }),
    html.Br(),
    html.Br(),
    dbc.Nav(
    [
        dbc.NavItem(dbc.NavLink("Home", active=True, href="/home", style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-bottom': '20px', 
            'font-family': 'Gotham',
            'font-size': '18px',
        })),
        dbc.NavItem(dbc.NavLink("Explore", active=True, href="/explore", style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-bottom': '20px',  
            'font-family': 'Gotham',
            'font-size': '18px',
        })),
        dbc.NavItem(dbc.NavLink("Analytics", href="/analytics",style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-bottom': '20px',
            'font-family': 'Gotham',
            'font-size': '18px',
        })),
        dbc.NavItem(dbc.NavLink("About", href="http://punkifyabout.s3-website.eu-central-1.amazonaws.com/",style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-bottom': '20px',
            'font-family': 'Gotham',
            'font-size': '18px',
        }))
    ],horizontal='center'),
    html.Br(),
    html.Br(),
    html.P('DISCOVER. ALWAYS.', style={'font-size': '40px', 'textAlign': 'center'}),
    html.Br(),
    html.Br(),
    html.Div(style={'border-style':'solid','border-width':'0.5px','margin':'20px', 'padding':'10px'},children=[
    html.P('GROWTH ARTISTS', style={'font-size': '32px', 'textAlign': 'center'}),
    html.P('Artists having fastest-growing fanbase', style={'font-size': '20px', 'textAlign': 'center'}),
    html.Br(),
    html.Div(style = {'textAlign': 'center'},children=[
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_list[0]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_list[1]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_list[2]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_list[3]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),]),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Div(style = {'textAlign': 'center'},children=[
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_list[4]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_list[5]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_list[6]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_list[7]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),]),
    html.Br(),
    html.Br(),]),
    html.Br(),
    html.Div(style={'border-style':'solid','border-width':'0.5px','margin':'20px', 'padding':'10px'},children=[
    html.P('MAGNET ARTISTS', style={'font-size': '32px', 'textAlign': 'center'}),
    html.P('Artists who are gaining more followers', style={'font-size': '20px', 'textAlign': 'center'}),
    html.Br(),
    html.Div(style = {'textAlign': 'center'},children=[
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_magnets[0]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_magnets[1]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_magnets[2]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_magnets[3]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),]),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Div(style = {'textAlign': 'center'},children=[
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_magnets[4]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_magnets[5]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_magnets[6]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),
    html.Iframe(src=f"https://open.spotify.com/embed/album/{album_magnets[7]}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),]),
    ]),
    html.Br(),
    html.Br(),
    html.P('GET A RECO', style={'font-size': '32px', 'textAlign': 'center'}),
    html.Br(),
    html.Div(children=[
            html.Div(children=[
            dcc.Dropdown(
                style={'width':'50%','margin-top':'5px','margin-bottom':'5px','margin-left': '25%'},
                id='my-input1',
                options=[{'label': dicts[i], 'value': i} for i in dicts],
                value=None,
                placeholder='Select Artist')]),
            html.Div(children=[
            dcc.Input(  
                style={'width':'30%','margin-top':'5px','margin-bottom':'5px','left': '100%','margin-left':'35%','padding-right':'10%'},
                id='my-input2',
                placeholder='Insert Spotify track URL')]),
            html.Div(children=[
            dcc.Dropdown(
                style={'width':'50%','margin-top':'5px','margin-bottom':'5px','margin-left': '25%'},
                id='my-input3',
                options=[{'label': i, 'value': i} for i in ['post-punk','new wave', 'dark post-punk','russian post-punk','sovietwave','synthpop','nu gaze']],
                value=None,
                placeholder='Select genre')])]),
    html.Br(),
    html.Div(style={"display": "flex", "justify-content": "center","align-items": "center", "height": "50px"},children=[
    html.Button('Get Reco', id='button-reco', style={"background": "#f3f0f1","border-radius": "32px","text-align": "center"}),]),
    html.Div(id='rec-artist-1'),
    html.Br(),
    html.Br(),
    html.Hr(style={'width':'90%','border-top': '1px solid #1DB954'}),
    html.Footer(children=[
        dbc.Nav(style={'margin':'30px','padding':'0 25%'},children=
        [
            dbc.NavItem(dbc.NavLink("Home",active=True, href="/home",style={'color': '#1DB954'})),
            dbc.NavItem(dbc.NavLink("Explore", href="/explore",style={'color': '#1DB954'})),
            dbc.NavItem(dbc.NavLink("Analytics", href="/analytics",style={'color': '#1DB954'})),
            dbc.NavItem(dbc.NavLink("About", active=True, href="/about",style={'color': '#1DB954'})),
        ],
        vertical="md",
        )]),
    html.Br(), 
    ])


## CALLBACKS

@app.callback(
    Output(component_id='rec-artist-1', component_property='children'),
    Input(component_id='my-input1', component_property='value'),
    Input(component_id='my-input2', component_property='value'),
    Input(component_id='my-input3', component_property='value'),
    Input(component_id='button-reco', component_property='n_clicks'))
def update_output_div(input_value1,input_value2,input_value3, n_clicks):
    if n_clicks is None:
        None
    else:
        input_track = input_value2.replace('https://open.spotify.com/track/','')
        input_track, sep, tail = input_track.partition('?')
        spot_rec = spotify.raccomand_basic(seed_artist=input_value1, genre=input_value3, seed_track=input_track)
        return html.Div([html.Iframe(src=f"https://open.spotify.com/embed/track/{str(spot_rec[0]['id'])}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),html.Iframe(src=f"https://open.spotify.com/embed/track/{str(spot_rec[1]['id'])}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),html.Iframe(src=f"https://open.spotify.com/embed/track/{str(spot_rec[2]['id'])}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'}),html.Iframe(src=f"https://open.spotify.com/embed/track/{str(spot_rec[4]['id'])}",width='300px', height='80px', style={'margin':'10px','border-radius': '20px'})])



###################################################################################################
###########################################  HOME PAGE ############################################

#### Home Page HTML ###########################
home_page = html.Div(style={'backgroundColor': colors['background']},children=[
    html.Div(children=[
    html.H1(children='Trendify', style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-top': '20px',
            'font-family': 'Gotham',
        }),
    html.Br(),
    html.Br(),
    dbc.Nav(style={'textAlign': 'center','right': '50%',},children=[
        dbc.NavItem(dbc.NavLink("Home", active=True, href="/home", style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-bottom': '20px',  
            'font-family': 'Gotham',
            'font-size': '18px',
        })),
        dbc.NavItem(dbc.NavLink("Explore", active=True, href="/explore", style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-bottom': '20px', 
            'font-family': 'Gotham',
            'font-size': '18px',
        })),
        dbc.NavItem(dbc.NavLink("Analytics", href="/analytics",style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-bottom': '20px',
            'font-family': 'Gotham',
            'font-size': '18px',
        })),
        dbc.NavItem(dbc.NavLink("About", href="http://punkifyabout.s3-website.eu-central-1.amazonaws.com/",style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-bottom': '20px',
            'font-family': 'Gotham',
            'font-size': '18px',
        })),
    ],horizontal='center'),

    ]),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Div(style={'textAlign': 'center','padding-bottom': '20px','font-family': 'Gotham','max-width': '100%'},children=[
        html.Br(),
        html.Img(style={'max-width': '85%','height': 'auto','opacity': 0.9,'filter': 'blur(6px)','border-radius': '30px'},src="https://dunnmorgan.files.wordpress.com/2019/01/screen-shot-2019-01-26-at-9.51.40-pm-e1548561198297.png?w=1000&h=454&crop=1"),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.P('Tredify helps to track artists growth, showing their trends and audio data. It provide also a useful recommendation tool which allows to retrieve some suggestions based on an artist,song and genre selected.', style={'font-size': '22px', 'textAlign': 'center', 'padding-top': '20px','padding-bottom': '20px','padding-left': '10%','padding-right': '10%'}),
        html.P('...and remember...', style={'font-size': '22px', 'textAlign': 'center'}),
        html.H3(children='The best gift the Punk scene left us is the Post-Punk',style={'textAlign': 'center','padding-top': '20px','color': colors['text'],'padding-bottom': '20px','font-family': 'Copperplate',}),
        html.Br(),
        html.Hr(style={'width':'30%','border-top': '1px solid #55595c'}),
        html.Br(),
        html.P('The project started for tracking the post-punk/new wave bubble but will be expanded to others genre, trying to reaching most of them.Also the Analytics Dashboard will be integrated with other interesting insights.', style={'font-size': '22px', 'textAlign': 'center', 'padding-top': '20px','padding-left': '10%','padding-right': '10%'}),
        html.P('If you have any suggestion or idea to improve something make sure to reach me, you can find my contacts on the About page.', style={'font-size': '22px', 'textAlign': 'center','padding-bottom': '20px','padding-left': '10%','padding-right': '10%'}),
        html.Br(),
        html.Br(),
        html.P('FOLLOW OUR PLAYLIST',style={'font-size': '24px'}),
        html.Iframe(src='https://open.spotify.com/embed/playlist/5RxJPJjv6h3qPXsZeZYHzP', width='300px', height='80px', style={'border-radius': '20px'}),
        html.Br(),
        html.Br(),  
        html.Hr(style={'width':'90%','border-top': '1px solid #1DB954'}),   
        html.Footer(children=[
        dbc.Nav(style={'margin':'30px','padding':'0 25%'},children=
        [
            dbc.NavItem(dbc.NavLink("Home",active=True, href="/home",style={'color': '#1DB954'})),
            dbc.NavItem(dbc.NavLink("Explore", href="/explore",style={'color': '#1DB954'})),
            dbc.NavItem(dbc.NavLink("Analytics", href="/analytics",style={'color': '#1DB954'})),
            dbc.NavItem(dbc.NavLink("About", active=True, href="/about",style={'color': '#1DB954'})),
        ],
        vertical="md",
        )]),]),   
])


#############################################################################################
########################### PAGES MANAGER ###################################################
app.layout = url_bar_and_content_div

app.validation_layout = html.Div([
    url_bar_and_content_div,
    analytics_page,
    explore_page,
    home_page])

@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == "/analytics":
        return analytics_page
    elif pathname == "/explore":
        return explore_page
    elif pathname == "/home":
        return home_page
    else:
        return home_page



#######################################################
############### TITLE AND RUN #########################
app.title = 'Trendify'

if __name__ == '__main__':
    app.run_server(debug=True)