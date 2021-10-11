import os
import psycopg2
import datetime
from spotify import SpotifyAPI
from apscheduler.schedulers.blocking import BlockingScheduler
import random

#sched = BlockingScheduler()

#@sched.scheduled_job('cron', day_of_week='mon-sun', hour=10)
def upload_follows():
    # Access Spotify
    client_id = ['ID']
    client_secret = ['SECRET']
    spotify = SpotifyAPI(client_id=client_id, client_secret=client_secret)

    # Access DB
    DATABASE_URL = ['URL_DATABASE']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()

    # retrive len table
    cur.execute("SELECT MAX(id) FROM spotify")
    num = cur.fetchone()
    num = num[0]

    today = datetime.datetime.today().date()

    # load artist id
    cur.execute("SELECT id_artist FROM artist")
    db = cur.fetchall() 
    for i in range(len(db)):
        artist = spotify.get_artist(db[i][0])
        data =  (int(num+i+1), str(db[i][0]), int(artist['popularity']), int(artist['followers']['total']), today)
        SQL = """INSERT INTO spotify (id, artist_id, popularity, followers, day) VALUES (%s, %s, %s, %s, %s);"""
        cur.execute(SQL, data)
        conn.commit()

#@sched.scheduled_job('cron', day_of_week='mon-sun', hour=15)
def new_artist():
    # Access Spotify
    client_id = ['ID']
    client_secret =['SECRET']
    spotify = SpotifyAPI(client_id=client_id, client_secret=client_secret)

    # Access DB
    DATABASE_URL = ['DB_URL']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()

    # retrive IDs
    cur.execute("SELECT id_artist FROM artist")
    db = cur.fetchall()
    ids = [i[0] for i in db]

    # select random ID and the related artist
    id_pick = random.choice(ids)
    related = spotify.get_related(id_pick)

    # find related artist not already in the db
    for i in range(len(related['artists'])):
        if related['artists'][i]['id'] not in ids:
            if  'new wave' or 'post-punk' or 'russian post-punk' in related['artists'][i]['genres']:
                data =  (related['artists'][i]['id'], related['artists'][i]['name'])
                SQL = """INSERT INTO artist (id_artist, artist_name) VALUES (%s, %s);"""
                cur.execute(SQL, data)
                conn.commit()

#sched.start()