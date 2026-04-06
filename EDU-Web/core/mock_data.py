MOCK_USERS = [
    {
        'id': 1,
        'username': 'john_doe',
        'email': 'john@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'avatar': '/static/img/avatar.svg',
        'rating': 150,
        'questions_count': 5,
        'answers_count': 12,
    },
    {
        'id': 2,
        'username': 'jane_smith',
        'email': 'jane@example.com',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'avatar': '/static/img/avatar.svg',
        'rating': 89,
        'questions_count': 3,
        'answers_count': 8,
    },
    {
        'id': 3,
        'username': 'mike_wilson',
        'email': 'mike@example.com',
        'first_name': 'Mike',
        'last_name': 'Wilson',
        'avatar': '/static/img/avatar.svg',
        'rating': 234,
        'questions_count': 8,
        'answers_count': 15,
    },
]

MOCK_TAGS = [
    {'id': 1, 'name': 'python', 'color': '#3776ab'},
    {'id': 2, 'name': 'django', 'color': '#092e20'},
    {'id': 3, 'name': 'javascript', 'color': '#f7df1e'},
    {'id': 4, 'name': 'react', 'color': '#61dafb'},
    {'id': 5, 'name': 'css', 'color': '#1572b6'},
    {'id': 6, 'name': 'html', 'color': '#e34f26'},
    {'id': 7, 'name': 'sql', 'color': '#336791'},
    {'id': 8, 'name': 'git', 'color': '#f05032'},
]

MOCK_QUESTIONS = [
    {
        'id': i,
        'title': f'How to solve problem {i}?',
        'text': f'This is the detailed description of problem {i}. It contains multiple lines of text to simulate a real question with proper formatting and detailed explanation of the issue.',
        'author': MOCK_USERS[i % len(MOCK_USERS)],
        'created_at': f'2024-01-{(i % 28) + 1:02d}',
        'votes': (i * 3) % 50,
        'answers_count': (i * 2) % 10,
        'views': (i * 15) % 500,
        'tags': [MOCK_TAGS[j % len(MOCK_TAGS)] for j in range(i % 3 + 1)],
        'is_answered': i % 3 == 0,
    }
    for i in range(1, 51)
]

MOCK_ANSWERS = [
    {
        'id': i,
        'question_id': ((i - 1) // 3) + 1,
        'text': f'This is answer {i} with detailed explanation and code examples. It provides a comprehensive solution to the problem.',
        'author': MOCK_USERS[i % len(MOCK_USERS)],
        'created_at': f'2024-01-{(i % 28) + 1:02d}',
        'votes': (i * 2) % 30,
        'is_accepted': i % 5 == 0,
    }
    for i in range(1, 31)
]

def get_questions_by_tag(tag_name):
    return [q for q in MOCK_QUESTIONS if any(tag['name'] == tag_name for tag in q['tags'])]

def get_question_by_id(question_id):
    for question in MOCK_QUESTIONS:
        if question['id'] == question_id:
            return question
    return None

def get_answers_for_question(question_id):
    return [a for a in MOCK_ANSWERS if a['question_id'] == question_id]

def get_user_by_id(user_id):
    for user in MOCK_USERS:
        if user['id'] == user_id:
            return user
    return None

def get_hot_questions():
    return sorted(MOCK_QUESTIONS, key=lambda q: q['votes'] + q['answers_count'], reverse=True)