from __future__ import annotations

import re

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Answer, Question, Tag


_BS_INPUT = {'class': 'form-control'}

_MAX_TAGS = 5
_MIN_TITLE_LEN = 10
_MIN_TEXT_LEN = 20
_TAG_SPLIT_RE = re.compile(r'[\s,]+')
_TAG_VALID_RE = re.compile(r'^[\w-]+\Z', flags=re.UNICODE)


class QuestionForm(forms.ModelForm):
    tags = forms.CharField(
        label='Теги',
        required=False,
        max_length=255,
        widget=forms.TextInput(
            attrs={
                **_BS_INPUT,
                'placeholder': 'например: python django pagination',
                'autocomplete': 'off',
            }
        ),
        help_text='До 5 тегов через пробел или запятую. Допустимы буквы, цифры, дефис и подчёркивание.',
    )

    class Meta:
        model = Question
        fields = ('title', 'text')
        labels = {
            'title': 'Заголовок',
            'text': 'Текст вопроса',
        }
        widgets = {
            'title': forms.TextInput(
                attrs={
                    **_BS_INPUT,
                    'placeholder': 'Например: Как реализовать пагинацию в Django?',
                    'maxlength': '255',
                }
            ),
            'text': forms.Textarea(
                attrs={**_BS_INPUT, 'rows': 8, 'placeholder': 'Опишите задачу как можно подробнее.'}
            ),
        }

    def __init__(self, *args, author=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._author = author

    def clean_title(self):
        title = (self.cleaned_data.get('title') or '').strip()
        if len(title) < _MIN_TITLE_LEN:
            raise ValidationError(
                f'Заголовок слишком короткий — минимум {_MIN_TITLE_LEN} символов.'
            )
        return title

    def clean_text(self):
        text = (self.cleaned_data.get('text') or '').strip()
        if len(text) < _MIN_TEXT_LEN:
            raise ValidationError(
                f'Текст вопроса слишком короткий — минимум {_MIN_TEXT_LEN} символов.'
            )
        return text

    def clean_tags(self) -> list[str]:
        raw = (self.cleaned_data.get('tags') or '').strip()
        if not raw:
            return []
        parts = [item.strip().lower() for item in _TAG_SPLIT_RE.split(raw) if item.strip()]
        seen: list[str] = []
        for tag in parts:
            if tag in seen:
                continue
            if len(tag) > 64:
                raise ValidationError(f'Слишком длинный тег: «{tag}» (макс. 64 символа).')
            if not _TAG_VALID_RE.match(tag):
                raise ValidationError(
                    f'Тег «{tag}» содержит недопустимые символы. Разрешены буквы, цифры, "-" и "_".'
                )
            seen.append(tag)
        if len(seen) > _MAX_TAGS:
            raise ValidationError(f'Не более {_MAX_TAGS} тегов.')
        return seen

    @transaction.atomic
    def save(self, commit: bool = True):
        question: Question = super().save(commit=False)
        if self._author is not None:
            question.author = self._author
        if not commit:
            return question
        question.save()
        tag_names: list[str] = self.cleaned_data.get('tags') or []
        if tag_names:
            tag_objs: list[Tag] = []
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                tag_objs.append(tag)
            question.tags.set(tag_objs)
        else:
            question.tags.clear()
        return question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ('text',)
        labels = {'text': 'Текст ответа'}
        widgets = {
            'text': forms.Textarea(
                attrs={
                    **_BS_INPUT,
                    'rows': 6,
                    'placeholder': 'Напишите ответ здесь...',
                }
            ),
        }

    def __init__(self, *args, author=None, question: Question | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._author = author
        self._question = question

    def clean_text(self):
        text = (self.cleaned_data.get('text') or '').strip()
        if len(text) < 10:
            raise ValidationError('Ответ слишком короткий — минимум 10 символов.')
        return text

    @transaction.atomic
    def save(self, commit: bool = True):
        answer: Answer = super().save(commit=False)
        if self._author is not None:
            answer.author = self._author
        if self._question is not None:
            answer.question = self._question
        if not commit:
            return answer
        answer.save()
        if answer.question_id:
            answer.question.sync_answer_cnt()
        return answer
