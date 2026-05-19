from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_http_methods

from core.utils import get_page_range, paginate_or_404

from .forms import AnswerForm, QuestionForm
from .models import Question, Tag


_ANSWERS_PER_PAGE = 5


def index_view(request: HttpRequest) -> HttpResponse:
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


def hot_view(request: HttpRequest) -> HttpResponse:
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


@login_required
@require_http_methods(['GET', 'POST'])
def ask_view(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = QuestionForm(data=request.POST, author=request.user)
        if form.is_valid():
            question = form.save()
            messages.success(request, 'Вопрос опубликован.')
            return redirect(question.get_absolute_url())
    else:
        form = QuestionForm(author=request.user)

    return render(
        request,
        'questions/ask.html',
        {
            'form': form,
            'available_tags': Tag.name_suggestions_for_ask(),
        },
    )


def tag_view(request: HttpRequest, tag: str) -> HttpResponse:
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


@require_http_methods(['GET', 'POST'])
def question_detail_view(request: HttpRequest, question_id: int) -> HttpResponse:
    question = Question.objects.get_for_detail_or_404(question_id)
    answers_qs = question.get_answers_queryset()
    answer_form: AnswerForm | None = None

    if request.method == 'POST':
        if not request.user.is_authenticated:
            login_url = reverse('core:login')
            query = urlencode({'next': request.get_full_path()})
            return redirect(f'{login_url}?{query}')
        answer_form = AnswerForm(
            data=request.POST,
            author=request.user,
            question=question,
        )
        if answer_form.is_valid():
            answer = answer_form.save()
            page_number = _answer_page_number(answers_qs, answer, _ANSWERS_PER_PAGE)
            redirect_url = (
                f"{question.get_absolute_url()}?page={page_number}#answer-{answer.pk}"
            )
            messages.success(request, 'Ваш ответ опубликован.')
            return redirect(redirect_url)

    if answer_form is None and request.user.is_authenticated:
        answer_form = AnswerForm()

    answers = paginate_or_404(answers_qs, request, per_page=_ANSWERS_PER_PAGE)
    return render(
        request,
        'questions/question.html',
        {
            'question': question,
            'answers': answers,
            'page_range': get_page_range(answers),
            'answer_form': answer_form,
        },
    )


def _answer_page_number(answers_qs, answer, per_page: int) -> int:
    """Compute the 1-based page number where ``answer`` ends up."""
    ids = list(answers_qs.values_list('id', flat=True))
    try:
        position = ids.index(answer.pk) + 1
    except ValueError:
        position = len(ids)
    return max(1, (position + per_page - 1) // per_page)
