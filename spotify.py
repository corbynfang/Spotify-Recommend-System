# Callback for server to get imformation:  http://127.0.0.1:8000/callback
# Client ID: fc3735a0571c4df6af0defd64b875c4b
# Client Secret: 4ac6fac31b3441a3b7eeae3a9cc6d453
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv()

env_file_path = 'ev.env'

if os.path.exists(env_file_path):
    with open(env_file_path) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value
            else:
                raise FileNotFoundError(f"{env_file_path} file not found")

client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirct_uri = os.getenv('SPOTIPY_REDIRECT_URI')

# Debugging the client_id's needed for the SpotifyClientCredentials to work
print("SPOTIFY_CLIENT_ID:", os.getenv('SPOTIFY_CLIENT_ID'))
print("SPOTIFY_CLIENT_SECRET:", os.getenv('SPOTIFY_CLIENT_SECRET'))
print("SPOTIFY_REDIRECT_URI:", os.getenv('SPOTIFY_REDIRECT_URI'))

if not client_id or not client_secret:
    raise ValueError("Enviormental variables are not set")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
    scope='user-top-read'
))

top_tracks = sp.current_user_top_tracks(limit=5)
seed_tracks = [track['id'] for track in top_tracks['items']]

top_artists = sp.current_user_top_artists(limit=5)
seed_artists = [artist['id']for artist in top_artists['items']]

recommendations = sp.recommendations(
    seed_tracks=seed_tracks[:2], # Use up to 2 seed tracks
    seed_artists=seed_artists[:2], # Use up to 2 seed artist
    seed_genres=['pop'],
    limit=10,
    target_energy=0.7,
    target_tempo=120,
    target_danceability=0.8,
)

print("Recommended Tracks: ")
for i, track in enumerate(recommendations['tracks']):
    print(f"{i + 1}. {track['name']} by {', '.join(artist['name'] for artist in track['artist'])}")
