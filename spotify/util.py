from .models import SpotifyToken
from django.utils import timezone
from datetime import timedelta
from requests import post, put, get
from dotenv import load_dotenv
import os

# Global variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
BASE_URL = os.getenv("BASE_URL")


# Verify is there're saved tokens associated to an user session
def get_user_tokens(session_id):
    
    user_tokens = SpotifyToken.objects.filter(user=session_id)
    if user_tokens.exists():
        return user_tokens[0]
    return None


# Create new tokens or update existing ones
def update_or_create_user_tokens(session_id, access_token, token_type, expires_in, refresh_token):
    
    tokens = get_user_tokens(session_id)
    expires_in = timezone.now() + timedelta(seconds=expires_in)
    
    if tokens:
        tokens.access_token = access_token
        tokens.refresh_token = refresh_token
        tokens.expires_in = expires_in
        tokens.token_type = token_type
        tokens.save(update_fields=['access_token', 'refresh_token', 'expires_in','token_type'])
    else:
        tokens = SpotifyToken(user=session_id, access_token=access_token, refresh_token=refresh_token, token_type=token_type, expires_in=expires_in)
        tokens.save()


# Check if user is authenticated (false if else) & its token hasn't expired (refresh if else)
def is_spotify_authenticated(session_id):
    
    tokens = get_user_tokens(session_id)
    print(tokens) # --> DEBUG

    if tokens:
        expiry = tokens.expires_in
        if expiry <= timezone.now():
            refresh_spotify_token(session_id)
        return (True, tokens)
    return False


# Refresh spotify token
def refresh_spotify_token(session_id):
    refresh_token = get_user_tokens(session_id).refresh_token

    response = post('https://accounts.spotify.com/api/token',
                    data = {
                        'grant_type':'refresh_token',
                        'refresh_token':refresh_token,
                        'client_id': CLIENT_ID,
                        'client_secret': CLIENT_SECRET
                })
    
    access_token = response.get('access_token')
    token_type = response.get('token_type')
    expires_in = response.get('expires_in')
    refresh_token = response.get('refresh_token')

    update_or_create_user_tokens(session_id, access_token, token_type, expires_in, refresh_token)


# Perform request to Spotify API endpoint
def execute_spotify_api_request(session_id, endpoint, post_=False, put_=False):
    
    tokens = get_user_tokens(session_id)
    
    headers = {
        'Content-Type':'application/json',
        'Authorization': f'Bearer {tokens.access_token}'
    }
    
    if post_:
        post(BASE_URL + endpoint, headers = headers)
    
    if put_:
        put(BASE_URL + endpoint, headers = headers)
    
    response = get(BASE_URL + endpoint,{},headers=headers)
    print(response)

    try:
        return response.json()
    except:
        return ({'error':'Request error.'})