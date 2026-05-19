from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render, resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, ProfileForm, SignupForm


_NEXT_PARAM = 'next'


def _safe_next(request: HttpRequest, fallback: str | None = None) -> str:
    raw = request.POST.get(_NEXT_PARAM) or request.GET.get(_NEXT_PARAM) or ''
    if raw and url_has_allowed_host_and_scheme(
        url=raw,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return raw
    if fallback is None:
        fallback = resolve_url(settings.LOGIN_REDIRECT_URL)
    return fallback


def _next_value(request: HttpRequest) -> str:
    """Raw next value from POST or GET, used to round-trip the hidden input."""
    return request.POST.get(_NEXT_PARAM) or request.GET.get(_NEXT_PARAM, '')


@never_cache
@require_http_methods(['GET', 'POST'])
def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect(_safe_next(request))

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(_safe_next(request))
    else:
        form = LoginForm(request)

    return render(
        request,
        'core/login.html',
        {
            'form': form,
            'next': _next_value(request),
        },
    )


@never_cache
@require_http_methods(['GET', 'POST'])
def signup_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect(_safe_next(request))

    if request.method == 'POST':
        form = SignupForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно. Добро пожаловать!')
            return redirect(_safe_next(request))
    else:
        form = SignupForm()

    return render(
        request,
        'core/signup.html',
        {
            'form': form,
            'next': _next_value(request),
        },
    )


@require_http_methods(['POST'])
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    fallback = resolve_url(settings.LOGOUT_REDIRECT_URL)
    return redirect(_safe_next(request, fallback=fallback))


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def profile_view(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(
            data=request.POST,
            files=request.FILES,
            instance=profile,
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('core:profile')
    else:
        form = ProfileForm(instance=profile)

    return render(
        request,
        'core/profile.html',
        {
            'form': form,
            'profile': profile,
        },
    )
