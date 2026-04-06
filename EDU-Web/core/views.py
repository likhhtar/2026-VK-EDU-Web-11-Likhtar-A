from django.shortcuts import render, redirect
from django.contrib import messages
from .mock_data import MOCK_USERS, get_user_by_id


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            messages.success(request, f'Welcome back, {username}!')
            return redirect('questions:index')
        else:
            messages.error(request, 'Please enter both username and password.')
    
    return render(request, 'core/login.html')


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if not all([username, email, password, password_confirm]):
            messages.error(request, 'All fields are required.')
        elif password != password_confirm:
            messages.error(request, 'Passwords do not match.')
        else:
            messages.success(request, f'Account created successfully for {username}!')
            return redirect('core:login')
    
    return render(request, 'core/signup.html')


def profile_view(request):
    user = MOCK_USERS[0]
    
    context = {
        'user': user,
        'user_questions': [
            {'id': 1, 'title': 'How to use Django pagination?', 'votes': 15, 'answers': 3},
            {'id': 2, 'title': 'Best practices for Django views?', 'votes': 8, 'answers': 1},
            {'id': 3, 'title': 'Django template inheritance tips?', 'votes': 12, 'answers': 5},
        ],
        'user_answers': [
            {'question_title': 'Python list comprehension', 'votes': 5, 'accepted': True},
            {'question_title': 'Django URL patterns', 'votes': 3, 'accepted': False},
            {'question_title': 'CSS flexbox layout', 'votes': 7, 'accepted': True},
        ]
    }
    
    return render(request, 'core/profile.html', context)


def ask_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        text = request.POST.get('text')
        tags = request.POST.get('tags')
        
        if title and text:
            messages.success(request, 'Your question has been posted successfully!')
            return redirect('questions:index')
        else:
            messages.error(request, 'Title and description are required.')
    
    context = {
        'available_tags': [
            'python', 'django', 'javascript', 'react', 'css', 'html', 'sql', 'git'
        ]
    }
    
    return render(request, 'core/ask.html', context)