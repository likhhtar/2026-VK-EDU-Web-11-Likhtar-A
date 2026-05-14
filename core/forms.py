from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Profile

User = get_user_model()


_BS_INPUT = {'class': 'form-control'}
_BS_FILE = {'class': 'form-control'}


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={**_BS_INPUT, 'autofocus': True, 'autocomplete': 'username'}),
    )
    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={**_BS_INPUT, 'autocomplete': 'current-password'}),
    )

    error_messages = {
        'invalid_login': 'Неверный логин или пароль. Проверьте данные и попробуйте ещё раз.',
        'inactive': 'Этот аккаунт деактивирован.',
    }


class SignupForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={**_BS_INPUT, 'autocomplete': 'new-password'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label='Повторите пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={**_BS_INPUT, 'autocomplete': 'new-password'}),
        help_text='Введите тот же пароль ещё раз для проверки.',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        labels = {
            'username': 'Логин',
            'email': 'Email',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
        }
        widgets = {
            'username': forms.TextInput(attrs={**_BS_INPUT, 'autocomplete': 'username'}),
            'email': forms.EmailInput(attrs={**_BS_INPUT, 'autocomplete': 'email'}),
            'first_name': forms.TextInput(attrs={**_BS_INPUT, 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={**_BS_INPUT, 'autocomplete': 'family-name'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Пользователь с таким логином уже существует.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Пароли не совпадают.')
        return password2

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get('password1')
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error('password1', error)

    @transaction.atomic
    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            Profile.objects.get_or_create(user=user)
        return user


class ProfileForm(forms.ModelForm):
    username = forms.CharField(
        label='Логин',
        max_length=150,
        widget=forms.TextInput(attrs={**_BS_INPUT, 'autocomplete': 'username'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={**_BS_INPUT, 'autocomplete': 'email'}),
    )
    first_name = forms.CharField(
        label='Имя',
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={**_BS_INPUT, 'autocomplete': 'given-name'}),
    )
    last_name = forms.CharField(
        label='Фамилия',
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={**_BS_INPUT, 'autocomplete': 'family-name'}),
    )

    class Meta:
        model = Profile
        fields = ('avatar',)
        labels = {'avatar': 'Аватар'}
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={**_BS_FILE, 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.instance.user if self.instance.pk else None
        if user is not None:
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError('Поле обязательно.')
        qs = User.objects.filter(username__iexact=username).exclude(pk=self.instance.user_id)
        if qs.exists():
            raise ValidationError('Этот логин уже занят.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('Поле обязательно.')
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.user_id)
        if qs.exists():
            raise ValidationError('Этот email уже используется.')
        return email

    @transaction.atomic
    def save(self, commit: bool = True):
        profile = super().save(commit=False)
        user = profile.user
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
            profile.save()
        return profile
