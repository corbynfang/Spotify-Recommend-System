<<<<<<< HEAD
=======
# Callback for server to get imformation:  http://127.0.0.1:8000/callback
# Client ID: c9774ae12bd948ecb0cbd29e175b182c
>>>>>>> ac357341b8ee56ba911ae980fcbd01d6b059a0f9
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import logging

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')

# Correct client credentials and set environment variables
os.environ["SPOTIPY_CLIENT_ID"] = "c9774ae12bd948ecb0cbd29e175b182c"
os.environ["SPOTIPY_CLIENT_SECRET"] = "4ac6fac31b3441a3b7eeae3a9cc6d453"  # Using the correct secret from comments
os.environ["SPOTIPY_REDIRECT_URI"] = "http://127.0.0.1:8000/callback"

scope = "playlist-read-private playlist-modify-private user-library-read user-read-private user-read-email user-top-read user-library-modify"

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
app.logger.setLevel(logging.DEBUG)

# Create auth manager for reuse
auth_manager = SpotifyOAuth(
    client_id=os.environ["SPOTIPY_CLIENT_ID"],
    client_secret=os.environ["SPOTIPY_CLIENT_SECRET"],
    redirect_uri=os.environ["SPOTIPY_REDIRECT_URI"],
    scope=scope,
    cache_path=".spotify_cache",
    show_dialog=True
)

def get_spotify_client():
    """Gets an authenticated Spotify client"""
    token_info = auth_manager.get_cached_token()
    if not token_info:
        return None

    # Check if token is expired and refresh if needed
    if auth_manager.is_token_expired(token_info):
        token_info = auth_manager.refresh_access_token(token_info['refresh_token'])

    return spotipy.Spotify(auth=token_info['access_token'])

def search_song(song_name, limit=20):
    """Search for songs on Spotify"""
    try:
        sp = get_spotify_client()
        if not sp:
            return []

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
        app.logger.error(f"Error during search: {str(e)}")
        return []

def get_recommendations(seed_track=None, seed_artists=None, seed_genres=None, num_recommendations=10):
    """Get track recommendations from Spotify API"""
    try:
        sp = get_spotify_client()
        if not sp:
            app.logger.error("Not authenticated")
            return []

        # Build parameters
        params = {'limit': min(num_recommendations, 100)}

        # Handle track seeds - IMPORTANT FIX HERE
        if seed_track and isinstance(seed_track, str) and seed_track.strip():
            # Don't use commas, use a list directly
            params['seed_tracks'] = [seed_track.strip()]
            app.logger.debug(f"Using seed track: {params['seed_tracks']}")

        # Handle artist seeds
        if seed_artists:
            if isinstance(seed_artists, list):
                params['seed_artists'] = seed_artists
            elif isinstance(seed_artists, str) and seed_artists.strip():
                # Use a list for artists too
                params['seed_artists'] = [seed_artists.strip()]

        # Handle genre seeds
        if seed_genres:
            if isinstance(seed_genres, list):
                params['seed_genres'] = seed_genres
            elif isinstance(seed_genres, str) and seed_genres.strip():
                # Use a list for genres
                params['seed_genres'] = [seed_genres.strip()]

        app.logger.info(f"Getting recommendations with params: {params}")

        # Get recommendations
        recommendations = sp.recommendations(**params)

        # Process results
        recommended_tracks = []
        for track in recommendations.get('tracks', []):
            artist_name = track['artists'][0]['name'] if track.get('artists') else "Unknown Artist"
            recommended_tracks.append({
                'id': track.get('id', ''),
                'name': track.get('name', 'Unknown Track'),
                'artist': artist_name,
                'url': track.get('external_urls', {}).get('spotify', '#')
            })

        app.logger.info(f"Found {len(recommended_tracks)} recommended tracks")
        return recommended_tracks

    except Exception as e:
        app.logger.error(f"Error getting recommendations: {str(e)}")
        return []

def _ensure_authentication():
    """Ensure the user is authenticated with Spotify. Returns True if authenticated."""
    try:
        token_info = auth_manager.get_cached_token()
        if not token_info:
            app.logger.info("No token found, authentication required")
            return False

        # Check if token is expired
        if auth_manager.is_token_expired(token_info):
            app.logger.info("Token expired, refreshing")
            token_info = auth_manager.refresh_access_token(token_info['refresh_token'])

        # Test the token
        sp = spotipy.Spotify(auth=token_info['access_token'])
        sp.current_user()
        return True

    except Exception as e:
        app.logger.error(f"Authentication error: {str(e)}")
        return False

def _handle_song_search(form_data, search_results):
    """Handle song search form submission. Updates search_results list.
    Returns error message if any."""
    song_name = form_data.get('song_name', '').strip()
    if not song_name:
        return "Please enter a song name to search"

    try:
        results = search_song(song_name)
        if results:
            search_results.clear()  # Clear previous results
            search_results.extend(results)
            return None
        else:
            return "No songs found. Please try again."
    except Exception as e:
        app.logger.error(f"Search error: {str(e)}")
        return f"Error searching for songs: {str(e)}"

def _handle_recommendations(form_data, recommendations):
    """Handle recommendations form submission. Updates recommendations list.
    Returns error message if any."""
    try:
        # Get the track ID directly - no splitting
        seed_track = form_data.get("track_id", "").strip()
        app.logger.debug(f"Raw track ID from form: {seed_track}")

        # Get artists and genres
        seed_artists = form_data.get("seed_artists", "").strip()
        seed_genres = form_data.get("seed_genres", "").strip()

        # Validate inputs
        if not (seed_track or seed_artists or seed_genres):
            return "Please provide at least one seed value (track, artist, or genre)."

        # Convert comma-separated values to lists (if needed)
        artists_list = None
        if seed_artists:
            artists_list = [a.strip() for a in seed_artists.split(',') if a.strip()]

        genres_list = None
        if seed_genres:
            genres_list = [g.strip() for g in seed_genres.split(',') if g.strip()]

        # IMPORTANT: Log the exact track ID being used
        app.logger.debug(f"Using track ID: {seed_track}")

        # Get recommendations
        results = get_recommendations(
            seed_track=seed_track,  # Pass the raw track ID
            seed_artists=artists_list,
            seed_genres=genres_list
        )

        if results:
            recommendations.clear()
            recommendations.extend(results)
            return None
        else:
            return "No recommendations found. Please try different seeds."

    except Exception as e:
        app.logger.error(f"Recommendation error: {str(e)}")
        return f"Error getting recommendations: {str(e)}"

    except Exception as e:
        app.logger.error(f"Recommendation error: {str(e)}")
        return f"Error getting recommendations: {str(e)}"


@app.route('/test_recommendation')
def test_recommendation():
    """Test endpoint with a hardcoded track ID"""
    try:
        # Use a valid Spotify track ID (Adele - Hello)
        track_id = "4NHQUGzhtTLFvgF5SZesLK"

        sp = get_spotify_client()
        if not sp:
            return "Not authenticated", 401

        # Make the API call directly with this known-good ID
        recommendations = sp.recommendations(seed_tracks=[track_id], limit=5)

        tracks = []
        for track in recommendations.get('tracks', []):
            tracks.append({
                'id': track['id'],
                'name': track['name'],
                'artist': track['artists'][0]['name'] if track.get('artists') else "Unknown"
            })

        return jsonify({
            'test_track_id': track_id,
            'recommendations': tracks
        })
    except Exception as e:
        return f"Error: {str(e)}", 400


# Routes
@app.route('/login')
def login():
    # Generate auth URL
    auth_url = auth_manager.get_authorize_url()
    app.logger.info(f"Redirecting to Spotify auth URL: {auth_url}")
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Process the callback from Spotify after authorization"""
    code = request.args.get('code')

    if not code:
        app.logger.error("No authorization code received")
        return "Authentication failed: No code received", 400

    # Get the token using the code
    try:
        token_info = auth_manager.get_access_token(code)
        app.logger.info(f"Successfully obtained token, expires at: {token_info['expires_at']}")
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Failed to get access token: {str(e)}")
        return f"Authentication error: {str(e)}", 400

@app.route("/", methods=['GET', 'POST'])
def index():
    """Main route for the web app."""
    # First, ensure authentication
    if not _ensure_authentication():
        return redirect(url_for('login'))

    # Initialize results
    recommendations = []
    search_results = []
    error = None

    # Handle form submissions
    if request.method == "POST":
        if 'search-song' in request.form:
            error = _handle_song_search(request.form, search_results)
        elif 'get_recommendations' in request.form:
            error = _handle_recommendations(request.form, recommendations)

    # Render the template
    return render_template("index.html",
                          recommendations=recommendations,
                          search_results=search_results,
                          error=error)

@app.route('/user_info')
def user_info():
    """Get detailed user information to check token permissions"""
    try:
        sp = get_spotify_client()
        if not sp:
            return "Not authenticated", 401

        # Get user information
        user = sp.current_user()

        # Get user's playlists
        playlists = sp.current_user_playlists(limit=5)

        token_info = auth_manager.get_cached_token()

        return jsonify({
            'user': user,
            'token_info': {
                'expires_in': token_info.get('expires_in'),
                'scope': token_info.get('scope'),
            },
            'playlists': playlists
        })
    except Exception as e:
        return f"Error: {str(e)}", 400

@app.route('/related_artists/<artist_id>')
def related_artists(artist_id):
    try:
        sp = get_spotify_client()
        if not sp:
            return "Not authenticated", 401

        # Get related artists
        related = sp.artist_related_artists(artist_id)

        # Then get top tracks for each related artist
        results = []
        for artist in related.get('artists', [])[:5]:  # Limit to 5 artists
            artist_info = {
                'id': artist['id'],
                'name': artist['name'],
                'top_tracks': []
            }

            # Get top tracks for this artist
            try:
                top_tracks = sp.artist_top_tracks(artist['id'], country='US')
                for track in top_tracks.get('tracks', [])[:3]:  # Limit to 3 tracks per artist
                    artist_info['top_tracks'].append({
                        'id': track['id'],
                        'name': track['name'],
                        'preview_url': track['preview_url']
                    })
            except Exception as inner_e:
                app.logger.error(f"Error getting top tracks: {str(inner_e)}")

            results.append(artist_info)

        return jsonify(results)
    except Exception as e:
        return f"Error: {str(e)}", 400

@app.route('/test_track/<track_id>')
def test_track(track_id):
    try:
        sp = get_spotify_client()
        if not sp:
            return "Not authenticated", 401

        track = sp.track(track_id)
        return jsonify(track)
    except Exception as e:
        return f"Error: {str(e)}", 400

@app.route('/test_recommendations_direct')
def test_recommendations_direct():
    """Test recommendations with hardcoded track ID"""
    try:
        sp = get_spotify_client()
        if not sp:
            return "Not authenticated", 401

        # Use a known working track ID directly
        test_track_id = "4NHQUGzhtTLFvgF5SZesLK"  # Adele - Hello

        # Make the API call
        recommendations = sp.recommendations(seed_tracks=[test_track_id], limit=5)

        # Process results
        tracks = []
        for item in recommendations.get('tracks', []):
            tracks.append({
                'id': item['id'],
                'name': item['name'],
                'artist': item['artists'][0]['name'] if item.get('artists') else "Unknown"
            })

        return jsonify({
            'seed_track': test_track_id,
            'recommendations': tracks
        })
    except Exception as e:
        return f"Error: {str(e)}", 400

if __name__ == "__main__":
    app.run(debug=True, port=8000)
