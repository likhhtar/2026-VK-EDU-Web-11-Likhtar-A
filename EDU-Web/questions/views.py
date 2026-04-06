from django.shortcuts import render
from django.http import Http404
from core.utils import paginate
from core.mock_data import (
    MOCK_QUESTIONS, 
    MOCK_ANSWERS, 
    get_questions_by_tag, 
    get_question_by_id, 
    get_answers_for_question,
    get_hot_questions
)


def index_view(request):
    questions = sorted(MOCK_QUESTIONS, key=lambda q: q['id'], reverse=True)
    
    page = paginate(questions, request, per_page=10)
    
    context = {
        'questions': page,
        'page_title': 'New Questions',
        'active_tab': 'new'
    }
    
    return render(request, 'questions/index.html', context)


def hot_view(request):
    questions = get_hot_questions()
    
    page = paginate(questions, request, per_page=10)
    
    context = {
        'questions': page,
        'page_title': 'Hot Questions',
        'active_tab': 'hot'
    }
    
    return render(request, 'questions/hot.html', context)


def tag_view(request, tag):
    questions = get_questions_by_tag(tag)
    
    if not questions:
        questions = []
    
    page = paginate(questions, request, per_page=10)
    
    context = {
        'questions': page,
        'tag': tag,
        'page_title': f'Questions tagged "{tag}"',
        'active_tab': 'tag'
    }
    
    return render(request, 'questions/tag.html', context)


def question_detail_view(request, question_id):
    question = get_question_by_id(question_id)
    
    if not question:
        raise Http404("Question not found")
    
    answers = get_answers_for_question(question_id)
    
    answers = sorted(answers, key=lambda a: (a['is_accepted'], a['votes']), reverse=True)
    
    answers_page = paginate(answers, request, per_page=5)
    
    context = {
        'question': question,
        'answers': answers_page,
        'answers_count': len(answers),
        'page_title': question['title']
    }
    
    return render(request, 'questions/question.html', context)