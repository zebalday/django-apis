from django.shortcuts import render, redirect
from dotenv import load_dotenv
from requests import Request, post
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import SpotifyToken
from .util import get_user_tokens, update_or_create_user_tokens, is_spotify_authenticated
import os

# Global variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")


# Prepares the url for the first petition
class AuthURL(APIView):
    def get(self, request, format=None):
        scope = "user-read-currently-playing user-read-recently-played user-read-playback-state"

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

    return redirect("frontend:")


class IsAuthenticated(APIView):
    def get(self, request, format=None):
        is_authenticated = is_spotify_authenticated(request.session.session_key)
        return Response({'status':is_authenticated}, status.HTTP_200_OK)