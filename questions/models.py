from django.conf import settings
from django.db import models
from django.urls import reverse

from core.models import DefaultModel
from .managers import AnswerManager, QuestionManager


class Tag(models.Model):
    name = models.SlugField(max_length=64, unique=True, verbose_name='имя', db_index=True)
    color = models.CharField(max_length=7, default='#6c757d', verbose_name='цвет')

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self) -> str:
        return reverse('questions:tag', kwargs={'tag': self.name})

    @classmethod
    def name_suggestions_for_ask(cls, limit: int = 30) -> list:
        return list(cls.objects.order_by('name').values_list('name', flat=True)[:limit])


class Question(DefaultModel):
    title = models.CharField(max_length=255, verbose_name='заголовок')
    text = models.TextField(verbose_name='текст')
    code_snippet = models.TextField(blank=True, default='', verbose_name='фрагмент кода')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='автор',
    )
    views = models.PositiveIntegerField(default=0, verbose_name='просмотры')
    tags = models.ManyToManyField(Tag, related_name='questions', blank=True, verbose_name='теги')
    
    votes = models.IntegerField(default=0, verbose_name='рейтинг')
    is_answered = models.BooleanField(default=False, verbose_name='имеет принятый ответ')
    answers_cnt = models.PositiveIntegerField(default=0, verbose_name='количество ответов')

    objects = QuestionManager()

    class Meta:
        verbose_name = 'вопрос'
        verbose_name_plural = 'вопросы'
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
            Answer.objects.filter(question_id=self.pk, is_active=True)
            .select_related('author', 'author__profile')
            .order_by('-is_accepted', 'created_at', 'id')
        )

    def sync_answer_cnt(self):
        answer_cnt = Answer.objects.filter(question_id=self.pk, is_active=True).count()
        self.answers_cnt = answer_cnt
        self.save(update_fields=["answers_cnt"])

    def sync_has_accepted_answer(self):
        has_accepted_answer = Answer.objects.filter(
            question_id=self.pk, is_active=True, is_accepted=True
        ).exists()
        self.is_answered = has_accepted_answer
        self.save(update_fields=["is_answered"])

    def sync_votes(self):
        votes_count = QuestionLike.objects.filter(question_id=self.pk).count()
        self.votes = votes_count
        self.save(update_fields=["votes"])


class Answer(DefaultModel):
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
    
    votes = models.IntegerField(default=0, verbose_name='рейтинг')

    objects = AnswerManager()

    class Meta:
        verbose_name = 'ответ'
        verbose_name_plural = 'ответы'
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

    def __str__(self):
        return f'Answer #{self.pk} to Q{self.question_id}'

    def accept_answer(self):
        if self.question_id:
            Answer.objects.filter(
                question_id=self.question_id,
                is_accepted=True,
                is_active=True
            ).exclude(pk=self.pk).update(is_accepted=False)
            
            self.is_accepted = True
            self.save(update_fields=['is_accepted'])
            
            self.question.sync_has_accepted_answer()

    def sync_votes(self):
        votes_count = AnswerLike.objects.filter(answer_id=self.pk).count()
        self.votes = votes_count
        self.save(update_fields=["votes"])


class QuestionLike(DefaultModel):
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

    class Meta:
        verbose_name = 'лайк вопроса'
        verbose_name_plural = 'лайки вопросов'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'question'],
                name='questions_qlike_user_question',
            ),
        ]

    def __str__(self):
        return f'Лайк вопроса #{self.question_id} от пользователя #{self.user_id}'


class AnswerLike(DefaultModel):
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

    class Meta:
        verbose_name = 'лайк ответа'
        verbose_name_plural = 'лайки ответов'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'answer'],
                name='questions_alike_user_answer',
            ),
        ]

    def __str__(self):
        return f'Лайк ответа #{self.answer_id} от пользователя #{self.user_id}'
