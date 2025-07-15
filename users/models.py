from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    settings = models.JSONField(default=dict, blank=True)
    is_two_factor_enabled = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return self.username
