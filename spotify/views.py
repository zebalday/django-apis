from django.shortcuts import render, redirect
from dotenv import load_dotenv
from datetime import datetime
from requests import Request, post
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import SpotifyTokensSerializer
from .models import SpotifyToken
from .util import *
import os

# Global variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
BASE_URL = os.getenv("BASE_URL")


# Prepares the url for the first petition
class AuthURL(APIView):
    def get(self, request, format=None):
        scope = """
                    playlist-read-collaborative
                    playlist-read-private
                    user-follow-read
                    user-library-read
                    user-read-currently-playing
                    user-read-playback-state
                    user-read-recently-played
                    user-top-read
                """
        
        scope = scope.strip()

        url = Request(
            'GET', 'https://accounts.spotify.com/authorize',
            params={
                'scope': scope,
                'response_type': 'code',
                'redirect_uri': REDIRECT_URI,
                'client_id': CLIENT_ID,
            }
        ).prepare().url

        return Response({
                'url': url,
                'status':status.HTTP_200_OK
                })


# Sends the petition to spotify auth service
def spotify_callback(request, format=None):
    
    code = request.GET.get('code')
    error = request.GET.get('error')

    # Performing post petition
    response = post(
                'https://accounts.spotify.com/api/token',
                data = {
                    'grant_type' : 'authorization_code',
                    'code' : code,
                    'redirect_uri' : REDIRECT_URI,
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                }
            ).json()

    # Fetching data from response
    access_token = response.get('access_token')
    token_type = response.get('token_type')
    refresh_token = response.get('refresh_token')
    expires_in = response.get('expires_in')
    error = response.get('error')

    # Verify if there's an active user session
    if not request.session.exists(request.session.session_key):
        request.session.create()

    # Saving tokens on the database
    update_or_create_user_tokens(request.session.session_key, access_token=access_token, token_type=token_type, expires_in=expires_in, refresh_token=refresh_token)

    return redirect("frontend:index")


# Show if current user current session is authenticated on spotify
class IsAuthenticated(APIView):
    def get(self, request, format=None):
        is_authenticated, tokens = is_spotify_authenticated(request.session.session_key)
        
        tokens = SpotifyTokensSerializer(tokens).data
        
        return Response({'status':is_authenticated,
                        'tokens':tokens},
                        status.HTTP_200_OK)


# List all session tokens stored on Database
class ListAllTokens(APIView):

    def get(self, request, format=None):
        all_tokens = SpotifyToken.objects.all()
        serializer = SpotifyTokensSerializer(all_tokens, many=True)
        return Response(serializer.data, status.HTTP_200_OK)


# Retrieve User Info
class UserInfo(APIView):
    def get(self, request, fotmat=None):
        user_session = self.request.session.session_key
        endpoint = ""
        response = execute_spotify_api_request(user_session, endpoint)

        # Fetch important info
        user_info = {
            'username': response.get('display_name'),
            'profile_url': response.get('external_urls').get('spotify'),
            'thumbail': response.get('images')[-1].get('url'),
            'followers':response.get('followers').get('total')
        }


        return Response({'user_info':user_info}, status=status.HTTP_200_OK)
            

# Retrieving current playing song from Spotify API
class CurrentSong(APIView):
    def get(self, request, format=None):
        user_session = self.request.session.session_key
        endpoint = "/player/currently-playing"
        response = execute_spotify_api_request(user_session, endpoint)

        current_song = {
            'name': response.get('item').get('name'),
            'artists':get_all_artists(response.get('item').get('artists')),
            'album':response.get('item').get('album').get('name'),
            'thumbnail':response.get('item').get('album').get('images')[0].get('url'),
            'song_url':response.get('item').get('external_urls').get('spotify'),
            'is_playing':response.get('is_playing')
        }
        
        return Response({'current_song':current_song}, status=status.HTTP_200_OK)


# Get user last played songs
class SongsHistory(APIView):
    def get(self, request, format=None):
        user_session = self.request.session.session_key
        endpoint = "/player/recently-played"
        response = execute_spotify_api_request(user_session, endpoint)
        
        track_list = []

        for track in response.get('items'):
            track_info = {
                'name': track.get('track').get('name'),
                'artists':get_all_artists(track.get('track').get('artists')),
                'album':track.get('track').get('album').get('name'),
                'thumbnail':track.get('track').get('album').get('images')[0].get('url'),
                'song_url':track.get('track').get('external_urls').get('spotify'),
            }
            track_list.append(track_info)

        return Response({'last_played_songs':track_list}, status=status.HTTP_200_OK)


# Get user top Artists & Top Genres
class TopArtists(APIView):
    def get(self, request, format=None):
        user_session = self.request.session.session_key
        endpoint = "/top/artists"
        response = execute_spotify_api_request(user_session, endpoint)

        artists_list = []
        all_genres = {}

        # Gettin artist info
        for artist in response.get('items'):
            artist = {
                'name':artist.get('name'),
                'artist_url':artist.get('external_urls').get('spotify'),
                'genres':artist.get('genres'),
                'thumbnail':artist.get('images')[0].get('url'),
                'followers':artist.get('followers').get('total'),
                'popularity':artist.get('popularity')
            }

            artists_list.append(artist)
            
            # Adding votes to each genre
            for genre in artist.get('genres'):
                if genre in all_genres:
                    all_genres[genre] += 1
                else:
                    all_genres[genre] = 1

            # Getting the top 10 genres in list format
            all_genres_sorted = sorted(all_genres.items(), key=lambda kv: kv[1], reverse=True)[:10]
            genres_list = [x[0] for x in all_genres_sorted]

        return Response({'top_artists':artists_list, 'top_genres':genres_list}, status=status.HTTP_200_OK)


# Get user top tracks
class TopTracks(APIView):
    
    def get(self, request, format=None):
        user_session = self.request.session.session_key
        endpoint = "/top/tracks"
        response = execute_spotify_api_request(user_session, endpoint)
        
        track_list = []

        for track in response.get('items'):
            track_info = {
                'name': track.get('name'),
                'artists':get_all_artists(track.get('artists')),
                'album':track.get('album').get('name'),
                'thumbnail':track.get('album').get('images')[0].get('url'),
                'song_url':track.get('external_urls').get('spotify'),
            }
            track_list.append(track_info)

        return Response({'top_tracks':track_list}, status=status.HTTP_200_OK)
    

# Get user last saved songs
class LastSavedSongs(APIView):
    def get(self, request, format=None):
        user_session = self.request.session.session_key
        endpoint = "/tracks"
        params = {'limit':10}
        response = execute_spotify_api_request(user_session, endpoint, params_=params)

        track_list = []
        for track in response.get('items'):

            track_info = {
                'name':track.get('track').get('name'),
                'added_at':get_formatted_date(track.get('added_at')),
                'artists':get_all_artists(track.get('track').get('artists')),
                'song_url':track.get('track').get('external_urls').get('spotify'),
            }

            track_list.append(track_info)

        return Response({'saved_songs':track_list}, status=status.HTTP_200_OK)


def get_all_artists(artists) -> list:
    artists_list = []

    for artist in artists:
        artist_info = {
            'name':artist.get('name'),
            'profile_url':artist.get('external_urls').get('spotify')
        }
        artists_list.append(artist_info)
    
    return artists_list

def get_formatted_date(date) -> str:
    date = datetime.strptime(date,"%Y-%m-%dT%H:%M:%SZ")
    return (date.strftime("%d-%m-%Y"))

def get_playlist_list(response) -> list:
    playlists = []

    for playlist in response.get('items'):
        playlist_info = {
            'name': playlist.get('name'),
            'total_songs':playlist.get('tracks').get('total'),
            'playlist_url':playlist.get('external_urls').get('spotify'),
            'owner':playlist.get('owner').get('display_name'),
            'owner_url':playlist.get('owner').get('external_urls').get('spotify'),
            'is_public':playlist.get('public'),
            'thumbnail':playlist.get('images')[0].get('url')
        }
        playlists.append(playlist_info)
    
    return playlists

def get_followed_artists(response) -> list:
    artists = []

    for artist in response:
        artist_info = {
            'name':artist.get('name'),
            'artist_url':artist.get('external_urls').get('spotify'),
            'followers':artist.get('followers').get('total'),
            'rank':artist.get('popularity'),
        }
        if len(artist.get('images')) > 0:
            artist_info['thumbnail'] = artist.get('images')[0].get('url')
        artists.append(artist_info)
    
    return artists


# Get user seved playlists
class GetUserPlaylists(APIView):
    def get(self, request, format=None):
        user_session = self.request.session.session_key
        endpoint = "/playlists"
        params = {'limit':50, 'offset':0}

        response = execute_spotify_api_request(user_session, endpoint, params_=params)

        playlists = get_playlist_list(response)
    
        while params['offset'] <= response.get('total'):
            params['offset'] += 50
            response = execute_spotify_api_request(user_session, endpoint, params_=params)
            playlists += get_playlist_list(response)

        playlists = [p for p in playlists if p['name'] != ""]
        playlists_sorted = sorted(playlists, key=lambda kv: kv['total_songs'], reverse=True)

        return Response({'user_playlists':playlists_sorted}, status=status.HTTP_200_OK)

# Get user followed artists
class GetFollowedArtists(APIView):
    def get(self, request, format=None):
        user_session = self.request.session.session_key
        endpoint = "/following"
        params = {'type':'artist','limit':50}
        
        response = execute_spotify_api_request(user_session, endpoint, params_=params)
        
        followed_artists = get_followed_artists(response.get('artists').get('items'))

        params['after'] = response.get('artists').get('items')[-1].get('id')

        while len(followed_artists) < response.get('artists').get('total'):
            response = execute_spotify_api_request(user_session, endpoint, params_=params)
            followed_artists += get_followed_artists(response.get('artists').get('items'))
            params['after'] = response.get('artists').get('items')[-1].get('id')

        sorted_artists = sorted(followed_artists, key=lambda kv: kv["rank"], reverse=True)

        return Response({'followed_artists':sorted_artists}, status=status.HTTP_200_OK)