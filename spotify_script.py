# Callback for server to get imformation:  http://127.0.0.1:8000/callback
# Client ID: c9774ae12bd948ecb0cbd29e175b182c
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

os.environ["SPOTIPY_CLIENT_ID"] = "c9774ae12bd948ecb0cbd29e175b182c"
os.environ["SPOTIPY_CLIENT_SECRET"] = "157c3b964c9b44a0a5ed417fdf6ed9ea"
os.environ["SPOTIPY_REDIRECT_URI"] = "http://127.0.0.1:8000/callback"

scope = "playlist-read-private playlist-modify-private user-library-read user-read-private user-read-email user-top-read user-library-modify"

try:
    auth_manager = SpotifyOAuth(scope=scope, cache_path=".spotify_cache")
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Debugging: Print token info
    token_info = auth_manager.get_cached_token()
    if token_info:
        print("Access Token:", token_info['access_token'])
        print("Expires At:", token_info['expires_at'])
    else:
        print("No token found. Please authenticate.")

except Exception as e:
    print(f"Error during authentication: {e}")

def search_song(song_name, limit=20):
    try:
        results = sp.search(q=song_name, type="track", limit=limit)

        tracks = []
        for item in results['tracks']['items']:
            tracks.append({
                'id': item['id'],
                'name': item['name'],
                'artist': item['artists'][0]['name'],
                'url': item['external_urls']['spotify']
            })

        return tracks
    except Exception as e:
        print(f"Error during search: {e}")
        return []


def get_recommendations(seed_track=None, seed_artists=None, seed_genres=None, num_recommendations=10):
    try:
        # Refresh token if needed
        token_info = auth_manager.get_cached_token()
        if not token_info or not auth_manager.validate_token(token_info):
            token_info = auth_manager.refresh_access_token(token_info['refresh_token'])

        access_token = token_info['access_token']

        # Build request parameters
        params = {'limit': num_recommendations}
        if seed_track:
            params['seed_tracks'] = seed_track
        if seed_artists:
            params['seed_artists'] = ','.join(seed_artists) if isinstance(seed_artists, list) else seed_artists
        if seed_genres:
            params['seed_genres'] = ','.join(seed_genres) if isinstance(seed_genres, list) else seed_genres

        # Make request directly
        headers = {'Authorization': f'Bearer {access_token}'}
        url = 'https://api.spotify.com/v1/recommendations'

        print(f"Making request to: {url}")
        print(f"With params: {params}")

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 404:
            print("Error: Seed track, artist, or genre not found.")
            print(f"Response content: {response.text}")
            return []

        if response.status_code != 200:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response content: {response.text}")
            return []

        data = response.json()

        # Process recommended tracks
        recommended_tracks = []
        for track in data['tracks']:
            artist_name = track['artists'][0]['name'] if track['artists'] else "Unknown Artist"
            recommended_tracks.append({
                'id': track['id'],
                'name': track['name'],
                'artist': artist_name,
                'url': track['external_urls']['spotify']
            })

        return recommended_tracks
    except Exception as e:
        print(f"Error during recommendations: {e}")
        return []

def create_playlist(user_id, playlist_name, track_ids):
    try:
        playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=False)
        playlist_id = playlist['id']

        sp.playlist_add_items(playlist_id, track_ids)
        return playlist['external_urls']['spotify']
    except Exception as e:
        print(f"Error during the playlist creation: {e}")


@app.route("/", methods=['GET', 'POST'])
def index():
    """Main route for the web app."""
    recommendations = []
    search_results = []
    playlist_url = None
    error = None

    if request.method == "POST":

        if 'search-song' in request.form:
            # Handle song search
            song_name = request.form.get('song_name')
            search_results = search_song(song_name)
            if not search_results:
                error = "No songs found. Please try again."

        elif "get_recommendations" in request.form:
            # Handle recommendations
            seed_track = request.form.get("track_id")
            seed_artists = request.form.get("seed_artists")
            seed_genres = request.form.get("seed_genres")

            print(f"Raw Seed Track from Form: {seed_track}")
            print(f"Seed Track Type from Form: {type(seed_track)}")

            if seed_track and not isinstance(seed_track, str):
                raise ValueError("Invalid seed_track. Expected a string.")

            # Convert seed_artists and seed_genres to lists if provided
            seed_artists = seed_artists.split(',') if seed_artists else None
            seed_genres = seed_genres.split(',') if seed_genres else None

            print(f" Processed Seed Track: {seed_track}")
            print(f" Processed Seed Artists: {seed_artists}")
            print(f" Processed Seed Genres: {seed_genres}")

            if seed_track or seed_artists or seed_genres:
                recommendations = get_recommendations(
                    seed_track=seed_track,
                    seed_artists=seed_artists,
                    seed_genres=seed_genres
                )
            else:
                error = "Please provide at least one seed value (track, artist, or genre)."

        elif "create_playlist" in request.form:
            try:
                track_ids = request.form.getlist("track_ids")
                print(f"Raw Track IDs: {track_ids}")

                if not track_ids:
                    raise ValueError("No tracks selected. Please select at least one track.")
                playlist_name = request.form.get("playlist_name")
                user_id = sp.current_user()['id']

                print(f"Track IDs Type: {type(track_ids)}")
                print(f"Track IDs Content: {track_ids}")
                playlist = create_playlist(user_id, playlist_name, track_ids)
                if playlist:
                    playlist_url = playlist['external_urls']['spotify']
                else:
                    error = "Failed to create playlist. Please try again."
            except Exception as e:
                error = f"An error occurred while creating the playlist: {e}"

    return render_template("index.html", recommendations=recommendations, playlist_url=playlist_url, search_results=search_results, error=error)

if __name__ == "__main__":
    app.run(debug=True, port=8080)
