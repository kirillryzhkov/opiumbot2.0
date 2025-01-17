import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import bot_tokens

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=bot_tokens.CLIENT_ID, client_secret=bot_tokens.CLIENT_SECRET))

def get_playlist_top_tracks(playlist_id):
    try:
        results = sp.playlist_items(playlist_id, limit=10)
        tracks = []
        for item in results['items']:
            track = item['track']
            tracks.append({
                "name": track['name'],
                "artist": track['artists'][0]['name'],
                "url": track['external_urls']['spotify']
            })
        return tracks
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def search_tracks(query):
    try:
        results = sp.search(q=query, type="track", limit=10)
        tracks = []
        for item in results['tracks']['items']:
            tracks.append({
                "name": item['name'],
                "artist": item['artists'][0]['name'],
                "url": item['external_urls']['spotify']
            })
        return tracks
    except Exception as e:
        print(f"Ошибка поиска треков: {e}")
        return None

def get_artist_profile(artist_name):
    try:
        result = sp.search(q=artist_name, type="artist", limit=1)
        if result['artists']['items']:
            artist_url = result['artists']['items'][0]['external_urls']['spotify']
            return artist_url
        else:
            return None
    except Exception as e:
        print(f"Ошибка поиска исполнителя: {e}")
        return None

def get_album_tracks(album_name):
    try:
        results = sp.search(q=album_name, type="album", limit=1)
        albums = results['albums']['items']
        if albums:
            album = albums[0]
            album_id = album['id']
            album_name = album['name']
            artist_name = album['artists'][0]['name']

            tracks = sp.album_tracks(album_id)
            tracks_list = []

            for track in tracks['items']:
                track_name = track['name']
                track_url = track['external_urls']['spotify']
                tracks_list.append(f"{track_name} [Слушать]({track_url})")

            return f"Треки из альбома {album_name} ({artist_name}):\n" + "\n".join(tracks_list)
        else:
            return f"Альбом {album_name} не найден."
    except Exception as e:
        print(f"Ошибка получения треков из альбома: {e}")
        return f"Ошибка получения треков из альбома {album_name}."

def get_top_tracks_for_artist(artist_name):
    try:
        result = sp.search(q=artist_name, type="artist", limit=3)
        if result['artists']['items']:
            artist_id = result['artists']['items'][0]['id']

            top_tracks = sp.artist_top_tracks(artist_id)['tracks']
            tracks = []

            for track in top_tracks:
                tracks.append({
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "url": track['external_urls']['spotify']
                })

            return tracks
        else:
            print(f"Исполнитель с именем {artist_name} не найден.")
            return None
    except Exception as e:
        print(f"Ошибка получения топ треков: {e}")
        return None
