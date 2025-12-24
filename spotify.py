import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
    )
)

def spotify_to_search(url):
    if "track" in url:
        track = sp.track(url)
        return f"{track['name']} {track['artists'][0]['name']}"

    if "playlist" in url:
        playlist = sp.playlist_items(url)
        tracks = playlist["items"]
        return f"{tracks[0]['track']['name']} {tracks[0]['track']['artists'][0]['name']}"

    if "album" in url:
        album = sp.album(url)
        track = album["tracks"]["items"][0]
        return f"{track['name']} {track['artists'][0]['name']}"

    return url
