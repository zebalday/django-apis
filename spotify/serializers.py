from rest_framework import serializers
from .models import SpotifyToken

class SpotifyTokensSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpotifyToken
        fields = '__all__'