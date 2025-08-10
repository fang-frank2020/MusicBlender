from flask import Flask, request, session, redirect, jsonify, send_from_directory
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv
from flask import g
import sqlite3
import json
from openai import OpenAI

DATABASE = 'database.db'

load_dotenv()

app = Flask(__name__, static_folder='build', static_url_path='')
CORS(app, supports_credentials=True)

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'

SCOPES = 'playlist-read-private playlist-read-collaborative user-read-private user-read-email playlist-modify-public playlist-modify-private'

app.secret_key = 'my-secret-key12345'

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def isAuthenticated():
    return session.get('access_token') is not None and session.get('user_info') is not None

@app.route('/')
def serve_react():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/login')
def login():
    auth_url = (
        f"{SPOTIFY_AUTH_URL}"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
    )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "No code found in callback", 400

    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(SPOTIFY_TOKEN_URL, data=payload, headers=headers)
    token_info = response.json()
    access_token = token_info['access_token']
    session['access_token'] = access_token


    userData = requests.get('https://api.spotify.com/v1/me',
            headers={
                'Authorization': f'Bearer {session["access_token"]}'
            })
    userData.raise_for_status()
    user_info = userData.json()


    session['user_info'] = user_info

    return redirect('/')



@app.route('/api/message')
def home():
    if  not isAuthenticated():
        print("User not authenticated, redirecting to login")
        return redirect('/api/login/')

    userId = session['user_info']['id']
    response = requests.get(
        f'https://api.spotify.com/v1/users/{userId}/playlists',
        headers={
            'Authorization': f'Bearer {session["access_token"]}'
        }
    )
    response.raise_for_status()
    res = response.json()['items']

    return res


@app.route('/api/room')
def createRoom():
    if  not isAuthenticated():
        print("User not authenticated, redirecting to login")
        return redirect('/api/login/')

    connection = get_db()
    cursor = connection.cursor()

    # check = cursor.execute(
    #     "SELECT * FROM rooms",
    # ).fetchall()

    # print(check)


    cursor.execute(
       "INSERT INTO rooms (names, songs) VALUES (?, ?)",
       (json.dumps([session["user_info"]["id"]]), json.dumps([]))
    )
    connection.commit()

    all = cursor.execute(
        "SELECT * FROM rooms",
    ).fetchall()

    userId = session['user_info']['id']
    roomsWithUser = []
    for room in all:
        if userId in json.loads(room[1]):
            roomsWithUser.append(room)
    

    return roomsWithUser


@app.route('/api/readRooms')
def readRoom():
    if  not isAuthenticated():
        print("User not authenticated, redirecting to login")
        return redirect('/api/login/')

    connection = get_db()
    cursor = connection.cursor()

    all = cursor.execute(
        "SELECT * FROM rooms",
    ).fetchall()

    userId = session['user_info']['id']
    roomsWithUser = []
    for room in all:
        if userId in json.loads(room[1]):
            roomsWithUser.append(room)

    return roomsWithUser

@app.route('/api/getMe')
def getMe():
    if  not isAuthenticated():
        print("User not authenticated, redirecting to login")
        return redirect('/api/login/')

    userId = session['user_info']['id']
    res = {
        'id': userId,
    }
    return res


@app.route('/api/addSongs')
def addSongs():
    if  not isAuthenticated():
        print("User not authenticated, redirecting to login")
        return redirect('/api/login/')

    tracklink = request.args.get('trackLink')
    roomId = request.args.get('roomId')


    response = requests.get(
        f'{tracklink}',
        headers={
            'Authorization': f'Bearer {session["access_token"]}'
        }
    )
    response.raise_for_status()
    res = response.json()

    allSongsInPlayList = []
    print(len(res["items"]))
    for song in res['items']:
        track = song['track']

        song = []
        song.append(track['name'])

        artists = []
        for artist in track['artists']:
            artists.append(artist['name'])

        song.append(artists)

        allSongsInPlayList.append(song)

    connection = get_db()
    cursor = connection.cursor()

    existingSongs = cursor.execute(
        "SELECT * FROM rooms WHERE id = ?",
        (roomId,)
    ).fetchone()

    existing = json.loads(existingSongs[2]) if existingSongs else []
    
    #[0][2] if existingSongs else []

    for song in allSongsInPlayList:
        if song not in existing:
            existing.append(song)


    cursor.execute(
       "UPDATE rooms SET songs = ? WHERE id = ?",
       (json.dumps(existing), roomId, )
    )
    connection.commit()


    # songsNow = cursor.execute(
    #     "SELECT songs FROM rooms WHERE id = ?",
    #     (roomId,)
    # ).fetchone()

    # response = {
    #     'songs': json.loads(songsNow[0]) if songsNow else []
    # }


    return ("", 204)

@app.route('/api/getSongs')
def getSongs():
    if  not isAuthenticated():
        print("User not authenticated, redirecting to login")
        return redirect('/api/login/')

    roomId = request.args.get('roomId')
    connection = get_db()
    cursor = connection.cursor()

    songsNow = cursor.execute(
        "SELECT songs FROM rooms WHERE id = ?",
        (roomId,)
    ).fetchone()

    response = {
        'songs': json.loads(songsNow[0]) if songsNow else []
    }


    return response

@app.route('/api/addUserToRoom')
def addUserToRoom():
    if  not isAuthenticated():
        print("User not authenticated, redirecting to login")
        return redirect('/api/login/')

    user = request.args.get('user')
    roomId = request.args.get('roomId')
    connection = get_db()
    cursor = connection.cursor()

    names = cursor.execute(
        "SELECT names FROM rooms WHERE id = ?",
        (roomId,)
    ).fetchone()

    print("names: ", names)

    if (user not in json.loads(names[0])):
        names = json.loads(names[0])
        names.append(user)

        cursor.execute(
            "UPDATE rooms SET names = ? WHERE id = ?",
            (json.dumps(names), roomId)
        )
        connection.commit()


    all = cursor.execute(
        "SELECT * FROM rooms",
    ).fetchall()

    userId = session['user_info']['id']
    roomsWithUser = []
    for room in all:
        if userId in json.loads(room[1]):
            roomsWithUser.append(room)
    return roomsWithUser


@app.route('/api/generate')
def generateSongs():
    if  not isAuthenticated():
        print("User not authenticated, redirecting to login")
        return redirect('/api/login/')

    roomId = request.args.get('roomId')
    numSongs = request.args.get('numSongs', default=10, type=int)
    connection = get_db()
    cursor = connection.cursor()

    songs = cursor.execute(
        "SELECT songs FROM rooms WHERE id = ?",
        (roomId,)
    ).fetchone()
    print(songs)

    test = json.dumps(json.loads(songs[0]) if songs else [])
    print("test: ",test)

    response = client.responses.create(
        model="openai/gpt-oss-120b",
        instructions= f"You are a music recommendation assistant. "
                        f"Given the following list of songs in the format [[title, [artist1, artist2, ...]], ...], generate a list of exactly {numSongs} new songs that are similar in style, mood, or vibe. "
                        f"Exclude any songs that are already in the list. "
                        f"The new songs must be in the same format: each item should be a list containing the song title as a string, followed by a list of artist(s). "
                        f"Return only the list — no extra explanation or formatting.\n\n"
                        f"The songs are:\n",
        input= json.dumps(json.loads(songs[0]) if songs else []),
    )
    print("response: ", response.output_text)

    res = {
        "data": json.loads(response.output_text)
    }

    return res

    

if __name__ == '__main__':
    app.run()