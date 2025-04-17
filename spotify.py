# Callback for server to get imformation:  http://127.0.0.1:8000/callback
# Client ID: fc3735a0571c4df6af0defd64b875c4b
# Client Secret: 4ac6fac31b3441a3b7eeae3a9cc6d453
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from collections import defaultdict
import os

client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')

# Debugging the client_id's needed for the SpotifyClientCredentials to work
print("SPOTIFY_CLIENT_ID:", os.getenv('SPOTIFY_CLIENT_ID'))
print("SPOTIFY_CLIENT_SECRET:", os.getenv('SPOTIFY_CLIENT_SECRET'))
print("SPOTIFY_REDIRECT_URI:", os.getenv('SPOTIFY_REDIRECT_URI'))

if not client_id or not client_secret:
    raise ValueError("Enviormental variables are not set")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
))

results = sp.search(q='Imagine Dragons', limit=5)

print('API Response: ', results)
for idx, track in enumerate(results['tracks']['items']): #
    print(f"{idx + 1}. {track['name']} by {track['artists'][0]['name']}")
