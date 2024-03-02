from django.urls import path
from .views import AuthURL, spotify_callback, IsAuthenticated, ListAllTokens

app_name = 'spotify'

urlpatterns = [
    path('get-auth-url', AuthURL.as_view(), name='get-auth-url'),
    path('redirect', spotify_callback, name='callback'),
    path('is-authenticated', IsAuthenticated.as_view(), name='is-authenticated'),
    path('all-tokens', ListAllTokens.as_view(), name='all-tokens'),
]
