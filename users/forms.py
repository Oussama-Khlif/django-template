from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from django import forms
import re

class RegisterForm(forms.Form):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('First name')
        })
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Last name')
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('email@example.com')
        })
    )

    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Password')
        })
    )

    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm password')
        })
    )

    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control-file',
            'accept': 'image/*'
        })
    )

    def generate_username(self, first_name, last_name):
        """Generate a unique username from first_name and last_name"""
        User = get_user_model()
        base_username = f"{first_name.lower()}_{last_name.lower()}"

        base_username = re.sub(r'[^a-zA-Z0-9_]', '', base_username)

        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        User = get_user_model()

        if User.objects.filter(email=email).exists():
            raise ValidationError(_("This email is already in use."))

        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise ValidationError(_("Passwords do not match."))

        return cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Username or email address')
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Password')
        })
    )

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'profile_picture']  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_picture'].widget.attrs.update({'class': 'form-control'})
        self.fields['username'].widget.attrs.update({'class': 'form-control'})

class PersonalInfoForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('Enter your first name'),
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('Enter your last name'),
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': _('Enter your email'),
                'required': True
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})

class DeleteAccountForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'deletePasswordInput',
            'placeholder': _('Enter your password')
        })
    )

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Enter your email address')}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise forms.ValidationError(_("No user found with this email address."))
        return email

class ResetPasswordForm(forms.Form):
    code = forms.CharField(max_length=6, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter the 6-digit code')}))
    new_password = forms.CharField(max_length=128, required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Enter your new password')}), validators=[validate_password])
    confirm_password = forms.CharField(max_length=128, required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Confirm your new password')}))

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password != confirm_password:
            raise forms.ValidationError(_("The passwords do not match."))

        return cleaned_data

class VerifyEmailForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        label=_("Verification Code"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-center",
                "placeholder": _("Enter the 6-digit code"),
                "autocomplete": "off",
                "pattern": "[0-9]{6}",
                "title": _("The code must contain exactly 6 digits"),
            }
        ),
        help_text=_("Please enter the verification code we sent to your email."),
    )