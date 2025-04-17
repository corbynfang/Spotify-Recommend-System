# Callback for server to get imformation:  http://127.0.0.1:8000/callback
# Client ID: fc3735a0571c4df6af0defd64b875c4b
# Client Secret: 4ac6fac31b3441a3b7eeae3a9cc6d453
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from typing import Any, Dict

os.environ["SPOTIFY_CLIENT_ID"] = "fc3735a0571c4df6af0defd64b875c4b"
os.environ["SPOTIFY_CLIENT_SECRET"] = "4ac6fac31b3441a3b7eeae3a9cc6d453"
os.environ["SPOTIFY_REDIRECT_URI"] = "http://127.0.0.1:8000/callback"

scope = "playlist-read-private playlist-modify-private user-library-read"

client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirct_uri = os.getenv('SPOTIPY_REDIRECT_URI')

# Debugging the client_id's needed for the SpotifyClientCredentials to work
print("SPOTIFY_CLIENT_ID:", os.getenv('SPOTIFY_CLIENT_ID'))
print("SPOTIFY_CLIENT_SECRET:", os.getenv('SPOTIFY_CLIENT_SECRET'))
print("SPOTIFY_REDIRECT_URI:", os.getenv('SPOTIFY_REDIRECT_URI'))

if not client_id or not client_secret:
    raise ValueError("Enviormental variables are not set")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

def fetch_user_playlist(sp: spotipy.Spotify):
    try:
        playlists: Dict[str, Any] = sp.cuurent_user_playlists()
        while playlists:
            items = playlists.get('items')
            if items:
                for playlist in items:
                    print(f"Playlist: {playlist['name']} (ID: {playlist['id']})")
            else:
                print('No playlists found')
            if playlists.get('next'):
                playlists = sp.next(playlists)
            else:
                playlists = None
    except spotipy.exceptions.SpotifyException as e:
        print(f"Error fetching playlists: {e}")

'''
try:
    playlists = sp.current_user_playlists()
    if playlists is not None and 'items' in playlists:
        for playlist in playlists['items']:
            print(f"Playlist: {playlist['name']} (ID: {playlist['id']})")
    else:
        print("No playlists found or invalid response.")
except spotipy.exceptions.SpotifyException as e:
    print(f"Error fetching playlists: {e}")
'''

def create_playlist(name, description=""):
    user_id = sp.current_user()
    playlist = sp.user_playlist_create(user=user_id, name=name, public=False, description=description)
    print(f"Created Playlist: {playlist['name']} (ID: {playlist['id']})")
    return playlist

if __name__ == '__main__':
    print("Fetching your playlist....")
    get_user_playlist()

    print("\nCreating a new playlist... With recommendations")
    create_playlist("Your new Playlist", "This is a test playlist created with spotify")

top_tracks = sp.current_user_top_tracks(limit=5)
seed_tracks = [track['id'] for track in top_tracks['items']]

top_artists = sp.current_user_top_artists(limit=5)
seed_artists = [artist['id']for artist in top_artists['items']]

try:
    recommendations = sp.recommendations(
        seed_artists=seed_artists,
        seed_tracks=seed_tracks,
        seed_genres=seed_genres,
        target_danceability=0.8,
        target_energy=0.7,
        target_tempo=120,
        limit=10
    )
    for track in recommendations['tracks']:
        print(f"{track + 1}. {track['name']} by {', '.join(artist['name'] for artist in track['artist'])}")
except spotipy.exceptions.SpotifyException as e:
    print(f"Error: {e}")
