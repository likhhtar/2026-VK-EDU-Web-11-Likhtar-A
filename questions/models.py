from django.conf import settings
from django.db import models
from django.db.models import Count
from django.urls import reverse

from .managers import AnswerManager, QuestionManager


class Tag(models.Model):
    name = models.SlugField(max_length=64, unique=True, verbose_name='имя', db_index=True)
    color = models.CharField(max_length=7, default='#6c757d', verbose_name='цвет')

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'
        db_table = 'questions_tag'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self) -> str:
        return reverse('questions:tag', kwargs={'tag': self.name})

    @classmethod
    def name_suggestions_for_ask(cls, limit: int = 30) -> list:
        return list(cls.objects.order_by('name').values_list('name', flat=True)[:limit])


class Question(models.Model):
    title = models.CharField(max_length=255, verbose_name='заголовок')
    text = models.TextField(verbose_name='текст')
    code_snippet = models.TextField(blank=True, default='', verbose_name='фрагмент кода')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='автор',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='обновлён')
    views = models.PositiveIntegerField(default=0, verbose_name='просмотры')
    tags = models.ManyToManyField(Tag, related_name='questions', blank=True, verbose_name='теги')

    objects = QuestionManager()

    class Meta:
        verbose_name = 'вопрос'
        verbose_name_plural = 'вопросы'
        db_table = 'questions_question'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self) -> str:
        return reverse('questions:question_detail', kwargs={'question_id': self.pk})

    def get_answers_queryset(self):
        return (
            Answer.objects.filter(question_id=self.pk)
            .select_related('author', 'author__profile')
            .annotate(votes=Count('answer_likes', distinct=True))
            .order_by('-is_accepted', '-votes', 'created_at', 'id')
        )


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='вопрос',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='автор',
    )
    text = models.TextField(verbose_name='текст')
    is_accepted = models.BooleanField(default=False, verbose_name='принят')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='обновлён')

    objects = AnswerManager()

    class Meta:
        verbose_name = 'ответ'
        verbose_name_plural = 'ответы'
        db_table = 'questions_answer'
        ordering = ['-is_accepted', '-created_at']
        indexes = [
            models.Index(fields=['question', '-is_accepted', '-created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['question'],
                condition=models.Q(is_accepted=True),
                name='questions_answer_one_accepted',
            ),
        ]

    def save(self, *args, **kwargs):
        if self.is_accepted and self.question_id:
            qs = type(self).objects.filter(question_id=self.question_id, is_accepted=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(is_accepted=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Answer #{self.pk} to Q{self.question_id}'


class QuestionLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='question_likes',
        verbose_name='пользователь',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='question_likes',
        verbose_name='вопрос',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='создан')

    class Meta:
        verbose_name = 'лайк вопроса'
        verbose_name_plural = 'лайки вопросов'
        db_table = 'questions_questionlike'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'question'],
                name='questions_qlike_user_question',
            ),
        ]

    def __str__(self):
        return f'QLike u{self.user_id} q{self.question_id}'


class AnswerLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answer_likes',
        verbose_name='пользователь',
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='answer_likes',
        verbose_name='ответ',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='создан')

    class Meta:
        verbose_name = 'лайк ответа'
        verbose_name_plural = 'лайки ответов'
        db_table = 'questions_answerlike'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'answer'],
                name='questions_alike_user_answer',
            ),
        ]

    def __str__(self):
        return f'ALike u{self.user_id} a{self.answer_id}'
