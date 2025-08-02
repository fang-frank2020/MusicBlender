from flask import Flask, request, session, redirect, jsonify, send_from_directory
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='build', static_url_path='')
CORS(app, supports_credentials=True)

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'

SCOPES = 'playlist-read-private playlist-read-collaborative user-read-private user-read-email'

app.secret_key = 'my-secret-key12345'


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

    # Exchange code for access token
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(SPOTIFY_TOKEN_URL, data=payload, headers=headers)
    response.raise_for_status()
    token_info = response.json()
    access_token = token_info['access_token']
    session['access_token'] = access_token

    print(response.json())

    userData = requests.get('https://api.spotify.com/v1/me',
            headers={
                'Authorization': f'Bearer {session["access_token"]}'
            })
    userData.raise_for_status()
    user_info = userData.json()
    print("User info:", user_info)


    session['user_info'] = user_info

    # res = jsonify({
    #     'access_token': access_token,
    # })
    #print(res)
    print('here')
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
    print("Playlists:", res)

    return res

if __name__ == '__main__':
    app.run()