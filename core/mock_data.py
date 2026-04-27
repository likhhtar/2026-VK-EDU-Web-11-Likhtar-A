MOCK_USERS = [
    {
        'id': 1,
        'username': 'john_doe',
        'email': 'john@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'avatar': 'img/avatar.svg',
        'rating': 1234,
        'questions_count': 5,
        'answers_count': 12,
    },
    {
        'id': 2,
        'username': 'jane_smith',
        'email': 'jane@example.com',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'avatar': 'img/avatar.svg',
        'rating': 987,
        'questions_count': 3,
        'answers_count': 8,
    },
    {
        'id': 3,
        'username': 'alex_dev',
        'email': 'alex@example.com',
        'first_name': 'Alex',
        'last_name': 'Developer',
        'avatar': 'img/avatar.svg',
        'rating': 856,
        'questions_count': 8,
        'answers_count': 15,
    },
    {
        'id': 4,
        'username': 'sarah_code',
        'email': 'sarah@example.com',
        'first_name': 'Sarah',
        'last_name': 'Coder',
        'avatar': 'img/avatar.svg',
        'rating': 743,
        'questions_count': 4,
        'answers_count': 9,
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

MOCK_QUESTIONS[0]['code_snippet'] = (
    "def paginate(items, page, per_page=10):\n"
    "    start = (page - 1) * per_page\n"
    "    return items[start:start + per_page]\n"
)

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

def get_popular_tags():
    tag_counts = {}
    for question in MOCK_QUESTIONS:
        for tag in question['tags']:
            tag_counts[tag['name']] = tag_counts.get(tag['name'], 0) + 1
    
    popular = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    return [tag_name for tag_name, count in popular]

def get_best_members():
    """Get top members by rating"""
    return sorted(MOCK_USERS, key=lambda u: u['rating'], reverse=True)[:4]