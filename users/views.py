import os
import shutil
from datetime import timedelta
from uuid import uuid4
from venv import logger

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    update_session_auth_hash,
    get_user_model,
)
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from django.utils.translation import gettext as _

from .forms import (
    DeleteAccountForm,
    ForgotPasswordForm,
    LoginForm,
    PersonalInfoForm,
    RegisterForm,
    ResetPasswordForm,
    UserProfileForm,
    VerifyEmailForm,
    CustomPasswordChangeForm,
)
from .models import CustomUser
from .utils import send_email, check_and_update_login_attempts

User = get_user_model()

@staff_member_required
@login_required
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')

        if user_id and action:
            user = get_object_or_404(User, id=user_id)

            if user == request.user:
                messages.error(request, _("You cannot modify your own account!"))
                return redirect('admin_users')

            if action == 'delete':
                user.delete()
                messages.success(request, _("User {username} has been deleted.").format(username=user.username))
            elif action == 'toggle_ban':
                user.is_banned = not user.is_banned
                user.save()
                status = _("banned") if user.is_banned else _("unbanned")
                messages.success(request, _("User {username} has been {status}.").format(username=user.username, status=status))

            return redirect('admin_users')

    return render(request, 'admin_users.html', {'users': users})

def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                username = user.username
                code = get_random_string(length=6, allowed_chars='0123456789')
                cache.set(f'password_reset_{username}', code, timeout=300)

                subject = _("Your password reset code")
                message = f"""
                <html>
                <body>
                <h2>{_("Password Reset")}</h2>
                <p>{_("Your password reset code is:")} <strong>{code}</strong></p>
                <p>{_("This code will expire in 5 minutes.")}</p>
                </body>
                </html>
                """
                email_sent = send_email(email, subject, message)

                if email_sent:
                    request.session['reset_username'] = username
                    messages.success(request, _("Password reset code has been sent to your email address."))
                    return redirect('reset_password')
                else:
                    messages.error(request, _("Failed to send email. Please try again later."))
                    return redirect('forgot_password')

            except CustomUser.DoesNotExist:
                messages.success(request, _("If this email exists in our system, a password reset code has been sent."))
                return redirect('forgot_password')
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(_("Password reset error: {error}").format(error=str(e)))
                messages.error(request, _("An error occurred. Please try again later."))
                return redirect('forgot_password')
    else:
        form = ForgotPasswordForm()

    return render(request, 'forgot_password.html', {'form': form})

def get_temporary_upload_path(filename):
    ext = filename.split('.')[-1]
    new_filename = f"{uuid4().hex}.{ext}"
    return os.path.join('tmp', new_filename)

def check_and_update_login_attempts(request, username, login_successful=False):
    cache_key = f'login_attempts_{username.lower()}'
    attempts_data = cache.get(cache_key)

    if login_successful:
        cache.delete(cache_key)
        return {'allowed': True}

    current_time = timezone.now()

    if not attempts_data:
        attempts_data = {
            'count': 0,
            'suspended_until': None
        }
    else:
        if attempts_data.get('suspended_until') and isinstance(attempts_data['suspended_until'], str):
            attempts_data['suspended_until'] = parse_datetime(attempts_data['suspended_until'])

    if attempts_data.get('suspended_until') and current_time < attempts_data['suspended_until']:
        remaining_time = attempts_data['suspended_until'] - current_time
        minutes_remaining = int(remaining_time.total_seconds() / 60)

        messages.error(request, _("Account temporarily suspended. Try again in {minutes} minutes.").format(minutes=minutes_remaining))
        return {'allowed': False, 'message': _("Account suspended for {minutes} minutes").format(minutes=minutes_remaining)}

    if attempts_data.get('suspended_until') and current_time >= attempts_data['suspended_until']:
        attempts_data = {
            'count': 0,
            'suspended_until': None
        }

    attempts_data['count'] += 1

    if attempts_data['count'] >= 5:
        suspension_duration = timedelta(minutes=30)
        attempts_data['suspended_until'] = (current_time + suspension_duration).isoformat()
        attempts_data['count'] = 0

        cache_data = attempts_data.copy()
        cache.set(cache_key, cache_data, timeout=3600 * 2)

        messages.error(request, _("Too many failed login attempts. Account suspended for 30 minutes."))
        return {'allowed': False, 'message': _("Account suspended for 30 minutes")}

    cache_data = attempts_data.copy()
    if cache_data.get('suspended_until') and hasattr(cache_data['suspended_until'], 'isoformat'):
        cache_data['suspended_until'] = cache_data['suspended_until'].isoformat()

    cache.set(cache_key, cache_data, timeout=3600)

    return {'allowed': True}

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            input_identifier = form.cleaned_data['username']
            password = form.cleaned_data['password']

            User = get_user_model()
            user_obj = None

            try:
                user_obj = User.objects.get(username__iexact=input_identifier)
            except User.DoesNotExist:
                try:
                    user_obj = User.objects.get(email__iexact=input_identifier)
                except User.DoesNotExist:
                    pass

            if user_obj and getattr(user_obj, 'is_banned', False):
                login(request, user_obj)
                return redirect('index')

            actual_username = user_obj.username if user_obj else input_identifier
            cache_key = f'login_attempts_{actual_username.lower()}'
            attempts_data = cache.get(cache_key)

            if attempts_data and attempts_data.get('suspended_until'):
                suspended_until = attempts_data['suspended_until']
                if isinstance(suspended_until, str):
                    suspended_until = parse_datetime(suspended_until)
                if suspended_until and now() < suspended_until:
                    minutes_remaining = int((suspended_until - now()).total_seconds() / 60)
                    messages.error(request, _("Account temporarily suspended. Please try again in {} minutes.").format(minutes_remaining))
                    return render(request, 'login.html', {'form': form})

            user = None
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                check_and_update_login_attempts(request, user.username, login_successful=True)

                if user.is_two_factor_enabled:
                    code = get_random_string(length=6, allowed_chars='0123456789')
                    cache.set(f'login_verification_{user.username}', code, timeout=300)

                    request.session['login_user_id'] = user.id
                    request.session['login_verification_username'] = user.username

                    subject = _("Login verification code")
                    message = _("Your verification code for login is: {}").format(code)
                    print(code)
                    send_email(user.email, subject, message)

                    messages.success(request, _("A verification code has been sent to your email address."))
                    return redirect('verify_login')
                else:
                    login(request, user)

                    if not getattr(user, 'is_banned', False):
                        messages.success(request, _("Welcome back, %(name)s!") % {
                            'name': f"{user.first_name} {user.last_name}"
                        })
                    return redirect('index')
            else:
                rate_limit_result = check_and_update_login_attempts(request, actual_username)
                if not rate_limit_result['allowed']:
                    return render(request, 'login.html', {'form': form})

                messages.error(request, _("Invalid username or password."))
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

@login_required
def profile(request):
    profile_form = UserProfileForm(instance=request.user)
    personal_info_form = PersonalInfoForm(instance=request.user)
    password_form = CustomPasswordChangeForm(request.user)
    delete_form = DeleteAccountForm()

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, _('Your profile has been updated successfully!'))
                return redirect('profile')

        elif 'update_personal_info' in request.POST:
            old_email = request.user.email or ''
            personal_info_form = PersonalInfoForm(request.POST, instance=request.user)

            if personal_info_form.is_valid():
                new_email = personal_info_form.cleaned_data['email']

                if new_email and new_email != old_email:
                    verification_code = get_random_string(length=6, allowed_chars='0123456789')
                    print(verification_code)
                    cache.set(f'verify_email_profile_{request.user.username}', {
                        'email': new_email,
                        'code': verification_code
                    }, timeout=300)

                    subject = _("Verify your new email address")
                    message = _("Your verification code is: {}").format(verification_code)
                    send_email(new_email, subject, message)

                    messages.success(request, _("A verification code has been sent to your new email address."))
                    return redirect('verify_email_profile')

                personal_info_form.save()
                messages.success(request, _('Your personal information has been updated successfully!'))
                return redirect('profile')

        elif 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(request.user, request.POST)

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, _('Your password has been changed successfully!'))
                return redirect('profile')

        elif 'toggle_2fa_submit' in request.POST:
            user = request.user
            if user.email:
                print("2FA toggle detected")
                print("POST data:", request.POST)
                print("Current 2FA status:", request.user.is_two_factor_enabled)
            else:
                messages.error(request, _("No email available"))
                return redirect('profile')
            user = request.user
            is_checked = 'toggle_2fa' in request.POST

            user.is_two_factor_enabled = is_checked
            user.save()

            print("New 2FA status:", user.is_two_factor_enabled)

            if user.is_two_factor_enabled:
                messages.success(request, _('Two-factor authentication has been enabled!'))
            else:
                messages.success(request, _('Two-factor authentication has been disabled!'))

            return redirect('profile')

        elif 'delete_account' in request.POST:
            delete_form = DeleteAccountForm(request.POST)
            user = request.user
            if user.has_usable_password():
                if delete_form.is_valid():
                    password = delete_form.cleaned_data['password']
                    if user.check_password(password):
                        user.delete()
                        messages.success(request, _('Your account has been deleted successfully.'))
                        return redirect('login')
                    else:
                        messages.error(request, _('Incorrect password.'))
                        return redirect('profile')
            else:

                user.delete()
                messages.success(request, _('Your account has been deleted successfully.'))
                return redirect('login')

    return render(request, 'profile.html', {
        'profile_form': profile_form,
        'personal_info_form': personal_info_form,
        'password_form': password_form,
        'delete_form': delete_form
    })

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.generate_username(first_name, last_name)
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            profile_picture = form.cleaned_data.get('profile_picture')

            temp_profile_picture_path = None
            if profile_picture:
                tmp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp')
                os.makedirs(tmp_dir, exist_ok=True)

                temp_path = get_temporary_upload_path(profile_picture.name)
                full_temp_path = os.path.join(settings.MEDIA_ROOT, temp_path)

                with open(full_temp_path, 'wb+') as destination:
                    for chunk in profile_picture.chunks():
                        destination.write(chunk)

                temp_profile_picture_path = temp_path

            request.session['user_registration_data'] = {
                'username': username,
                'email': email,
                'password': password,
                'first_name': first_name,
                'last_name': last_name,
                'temp_profile_picture': temp_profile_picture_path
            }

            code = get_random_string(length=6, allowed_chars='0123456789')
            cache.set(f'email_verification_{username}', code, timeout=300)

            subject = _("Verify your email address")
            message = _("Your verification code is: {}").format(code)
            print(code)
            send_email(email, subject, message)

            request.session['verification_username'] = username
            messages.success(request, _("A verification code has been sent to your email address."))
            return redirect('verify_email')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

def reset_password(request):
    username = request.session.get('reset_username')

    if not username:
        messages.error(request, _("Session expired or invalid request."))
        return redirect('forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            new_password = form.cleaned_data['new_password']

            cached_code = cache.get(f'password_reset_{username}')

            if cached_code == code:
                user = CustomUser.objects.get(username=username)
                user.set_password(new_password)
                user.save()

                cache.delete(f'password_reset_{username}')
                del request.session['reset_username']

                messages.success(request, _("Password reset successfully."))
                return redirect('login')
            else:
                messages.error(request, _("Invalid or expired code."))

    else:
        form = ResetPasswordForm()

    return render(request, 'reset_password.html', {'form': form})

def verify_email(request):
    username = request.session.get('verification_username')
    user_data = request.session.get('user_registration_data')

    if not username or not user_data:
        messages.error(request, _("Session expired or invalid request."))
        return redirect('register')

    if request.method == 'POST':
        form = VerifyEmailForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            cached_code = cache.get(f'email_verification_{username}')

            if cached_code == code:
                CustomUser = get_user_model()

                user = CustomUser.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', '')
                )
                user.is_active = True

                temp_profile_picture = user_data.get('temp_profile_picture')
                if temp_profile_picture:
                    temp_full_path = os.path.join(settings.MEDIA_ROOT, temp_profile_picture)
                    if os.path.exists(temp_full_path):
                        try:
                            final_filename = f"profile_pictures/{user.id}_{os.path.basename(temp_profile_picture)}"
                            final_full_path = os.path.join(settings.MEDIA_ROOT, final_filename)

                            os.makedirs(os.path.dirname(final_full_path), exist_ok=True)
                            shutil.move(temp_full_path, final_full_path)

                            user.profile_picture = final_filename
                        except (IOError, OSError) as e:
                            logger.error(f"Error handling profile picture for user {username}: {str(e)}")
                            try:
                                if os.path.exists(temp_full_path):
                                    os.remove(temp_full_path)
                            except OSError:
                                pass

                user.save()

                cache.delete(f'email_verification_{username}')
                request.session.pop('verification_username', None)
                request.session.pop('user_registration_data', None)

                login(request, user)

                messages.success(request, _("Welcome, {}! Your account has been created successfully.").format(user.username))
                return redirect('index')
            else:
                temp_profile_picture = user_data.get('temp_profile_picture')
                if temp_profile_picture:
                    temp_full_path = os.path.join(settings.MEDIA_ROOT, temp_profile_picture)
                    try:
                        if os.path.exists(temp_full_path):
                            os.remove(temp_full_path)
                    except OSError:
                        pass

                messages.error(request, _("Invalid or expired verification code."))
    else:
        form = VerifyEmailForm()

    return render(request, 'verify_email.html', {'form': form})

def verify_login(request):
    username = request.session.get('login_verification_username')
    user_id = request.session.get('login_user_id')

    if not username or not user_id:
        messages.error(request, _("Session expired or invalid request."))
        return redirect('login')

    if request.method == 'POST':
        form = VerifyEmailForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            cached_code = cache.get(f'login_verification_{username}')

            if cached_code == code:
                CustomUser = get_user_model()
                try:
                    user = CustomUser.objects.get(id=user_id)
                    login(request, user)

                    cache.delete(f'login_verification_{username}')
                    del request.session['login_verification_username']
                    del request.session['login_user_id']

                    messages.success(request, _("Welcome back, {}!").format(user.username))
                    return redirect('index')
                except CustomUser.DoesNotExist:
                    messages.error(request, _("User not found."))
                    return redirect('login')
            else:
                messages.error(request, _("Invalid or expired verification code."))
    else:
        form = VerifyEmailForm()

    return render(request, 'verify_email.html', {'form': form})

def verify_email_profile(request):
    user = request.user
    cache_key = f'verify_email_profile_{user.username}'
    cached_data = cache.get(cache_key)

    if not cached_data:
        messages.error(request, _("No pending verification."))
        return redirect('profile')

    form = VerifyEmailForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            code_entered = form.cleaned_data['code']
            if code_entered == cached_data['code']:
                user.email = cached_data['email']
                user.save()
                cache.delete(cache_key)
                messages.success(request, _("Your email address has been updated successfully!"))
                return redirect('profile')
            else:
                messages.error(request, _("Incorrect verification code."))

    return render(request, 'verify_email.html', {'form': form})