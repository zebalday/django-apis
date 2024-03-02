from django.urls import path
from .views import *

app_name = 'spotify'

urlpatterns = [
    path('get-auth-url', AuthURL.as_view(), name='get-auth-url'),
    path('redirect', spotify_callback, name='callback'),
    path('is-authenticated', IsAuthenticated.as_view(), name='is-authenticated'),
    path('get-all-tokens', ListAllTokens.as_view(), name='all-tokens'),
    path('get-current-song', CurrentSong.as_view(), name='current-song'),
    path('get-songs-history', SongsHistory.as_view(), name='songs-history'),
    path('top-artists', TopArtists.as_view(), name='top-artists'),
    path('top-tracks', TopTracks.as_view(), name='top-tracks'),
    path('user-info', UserInfo.as_view(), name='user-info'),
]
