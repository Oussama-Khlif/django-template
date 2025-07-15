import requests
from django.core.files.base import ContentFile
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            picture_url = extra_data.get('picture')

            if picture_url and not user.profile_picture:

                response = requests.get(picture_url)
                if response.status_code == 200:
                    user.profile_picture.save(
                        f"{user.username}_google.jpg",
                        ContentFile(response.content),
                        save=True
                    )
        return user