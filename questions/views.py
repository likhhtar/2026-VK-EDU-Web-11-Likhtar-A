from django.shortcuts import get_object_or_404, render

from core.utils import get_page_range, paginate_or_404
from .models import Question, Tag


def index_view(request):
    page = paginate_or_404(Question.objects.new_questions(), request, per_page=10)
    return render(
        request,
        'questions/index.html',
        {
            'questions': page,
            'page_range': get_page_range(page),
            'page_title': 'Новые вопросы',
            'active_tab': 'new',
        },
    )


def hot_view(request):
    page = paginate_or_404(Question.objects.best_questions(), request, per_page=10)
    return render(
        request,
        'questions/hot.html',
        {
            'questions': page,
            'page_range': get_page_range(page),
            'page_title': 'Лучшие вопросы',
            'active_tab': 'hot',
        },
    )


def ask_view(request):
    return render(request, 'questions/ask.html', {'available_tags': Tag.name_suggestions_for_ask()})


def tag_view(request, tag):
    tag_obj = get_object_or_404(Tag, name__iexact=tag)
    page = paginate_or_404(
        Question.objects.for_tag(tag_obj),
        request,
        per_page=10,
    )
    return render(
        request,
        'questions/tag.html',
        {
            'questions': page,
            'page_range': get_page_range(page),
            'tag': tag_obj,
            'page_title': f'Вопросы с тегом «{tag_obj.name}»',
            'active_tab': 'tag',
        },
    )


def question_detail_view(request, question_id):
    question = Question.objects.get_for_detail_or_404(question_id)
    answers = paginate_or_404(question.get_answers_queryset(), request, per_page=5)
    return render(
        request,
        'questions/question.html',
        {
            'question': question,
            'answers': answers,
            'page_range': get_page_range(answers),
        },
    )
