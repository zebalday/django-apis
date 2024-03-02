from django.db import models

class SpotifyToken(models.Model):
    user = models.CharField(max_length=50, unique=True)
    token_type = models.CharField(max_length=50)
    access_token = models.CharField(max_length=150)
    refresh_token = models.CharField(max_length=150)
    expires_in = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return (f"{self.user} | {self.created_at}")

    