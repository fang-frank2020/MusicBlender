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
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

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


    user_info = userData.json()

    if "error" in user_info and userData["error"]["status"] == 401:
        # Token expired or invalid
        session.clear()
        return redirect('/api/login')


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
    response = response.json()

    if "error" in response and response["error"]["status"] == 401:
        # Token expired or invalid
        session.clear()
        return redirect('/api/login')

    res = response['items']

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
    res = response.json()

    if "error" in res and res["error"]["status"] == 401:
        # Token expired or invalid
        session.clear()
        return redirect('/api/login')

    allSongsInPlayList = []
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

    response = client.responses.create(
        model="openai/gpt-oss-120b",
        instructions= f"You are a music recommendation assistant. "
    f"Given the following list of songs in the format [[title, [artist1, artist2, ...]], ...], "
    f"generate a list of exactly {numSongs} new songs that blend the styles, moods, and vibes of the input songs. "
    f"Your recommendations should reflect a thoughtful fusion, creating a cohesive mix that naturally integrates the diverse influences found across the input songs. "
    f"Some items may be only video titles rather than actual songs — in such cases, infer the most likely real song title and correct artist(s) based on the title and common music knowledge. "
    f"Only recommend real, existing songs that can be found on major streaming platforms. "
    f"Do not include songs already present in the input list, but you may include other songs by the same artists if they match the style, mood, or vibe. "
    f"Ensure no single style or artist dominates; the list should feel balanced, varied, and well integrated, capturing the full spectrum of the original playlist's influences. "
    f"Aim to recommend songs from different genres and artists roughly proportional to their presence and prominence in the input list, blending them into a seamless playlist."
    f"Return ONLY a JSON array in the exact format [[title, [artist1, artist2, ...]], ...], without any explanations, markdown, or extra formatting. "
    f"Strings should be double quoted as required by JSON. "
    f"Place the output directly in the main text response so it appears as plain text.\n\n"
    f"The songs are:\n",
        input= json.dumps(json.loads(songs[0]) if songs else []),
    )

    res = {
        "data": json.loads(response.output_text)
    }

    return res

@app.route('/api/youtubeURLAdd')
def youtubeURLAdd():
    if  not isAuthenticated():
        print("User not authenticated, redirecting to login")
        return redirect('/api/login/')

    user = session['user_info']['id']
    id = request.args.get('playlistId')

    connection = get_db()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO youtubeLinks (user, playlistId) VALUES (?, ?)",
        (user, id)
    )

    connection.commit()

    all = cursor.execute(
        "SELECT playlistId FROM youtubeLinks WHERE user = ?",
        (user, )
    ).fetchall()
    print(all)


    res = {
        'data': all
    }
    return res

@app.route('/api/getYoutube')
def getYoutube():
    if  not isAuthenticated():
        print("User not authenticated, redirecting to login")
        return redirect('/api/login/')

    user = session['user_info']['id']

    connection = get_db()
    cursor = connection.cursor()

    connection.commit()

    all = cursor.execute(
        "SELECT playlistId FROM youtubeLinks WHERE user = ?",
        (user, )
    ).fetchall()


    res = {
        'data': all
    }
    return res


@app.route('/api/youtubeAdd')
def youtubeAdd():
    if  not isAuthenticated():
        print("User not authenticated, redirecting to login")
        return redirect('/api/login/')

    roomId = request.args.get('roomId')
    playlistId = request.args.get('playlistId')
    response = requests.get(f'https://youtube.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={playlistId}&key={YOUTUBE_API_KEY}&maxResults=50')
    response = response.json()

    songs = []

    for item in response['items']:
        song = []
        title = item['snippet']['title']
        song.append(title)
        song.append([])
        songs.append(song)

    connection = get_db()
    cursor = connection.cursor()

    existingSongs = cursor.execute(
        "SELECT * FROM rooms WHERE id = ?",
        (roomId,)
    ).fetchone()

    existing = json.loads(existingSongs[2]) if existingSongs else []

    for song in songs:
        if song not in existing:
            existing.append(song)
    
    cursor.execute(
       "UPDATE rooms SET songs = ? WHERE id = ?",
       (json.dumps(existing), roomId, )
    )
    connection.commit()
   


    return ("", 204)


@app.route('/api/exportGeneratedPlaylist', methods=['POST'])
def exportGeneratedPlaylist():
    if  not isAuthenticated():
        print("User not authenticated, redirecting to login")
        return redirect('/api/login/')

    data = request.get_json()
    user = session['user_info']['id']
    name = request.args.get('name', default="Cool Generated Playlist")

    if not data or 'songs' not in data:
        return jsonify({"error": "No songs provided"}), 400
    songs = data['songs']
    uris = []

    for song in songs:
        track_name = song[0]
        artist_names = song[1]
        print(f"Searching for track: {track_name} by artists: {artist_names}")

        artist_query = " ".join(artist_names)

        query = f"track:{track_name} artist:{artist_query}"
        response = requests.get(
            f'https://api.spotify.com/v1/search',
            headers={
                'Authorization': f'Bearer {session["access_token"]}'
            },
            params={
                'q': query,
                'type': 'track',
                'limit': 1
            }
        )
        response = response.json()
        if response['tracks']['items']:
            track = response['tracks']['items'][0]
            uris.append(track['uri'])
    
    print("Exporting generated playlist with URIs:", uris)
    response = requests.post(
        f'https://api.spotify.com/v1/users/{user}/playlists',
        headers={
            'Authorization': f'Bearer {session["access_token"]}'
        },
        json={
            'name': name,
            'description': 'playlist generated by Frank Music Blender Project',
            'public': False
        }
    )

    response = response.json()
    print("Created playlist:", response)
    id = response['id']

    res = requests.post(
        f'https://api.spotify.com/v1/playlists/{id}/tracks',
        headers= {
            'Authorization': f'Bearer {session["access_token"]}',
            'Content-Type': 'application/json'
        },
        json={
            'uris': uris
        }
    )


    return ("", 204)

    

if __name__ == '__main__':
    app.run()