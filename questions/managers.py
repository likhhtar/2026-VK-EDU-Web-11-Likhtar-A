from __future__ import annotations

from django.db import models
from django.db.models import Count, Exists, OuterRef


class QuestionQuerySet(models.QuerySet):
    def with_list_annotations(self):
        from .models import Answer

        return (
            self.select_related('author', 'author__profile')
            .prefetch_related('tags')
            .annotate(votes=Count('question_likes', distinct=True))
            .annotate(answers_count=Count('answers', distinct=True))
            .annotate(
                is_answered=Exists(
                    Answer.objects.filter(
                        question_id=OuterRef('pk'),
                        is_accepted=True,
                    )
                )
            )
        )


class QuestionManager(models.Manager):
    def get_queryset(self):
        return QuestionQuerySet(self.model, using=self._db)

    def new_questions(self):
        return self.get_queryset().with_list_annotations().order_by('-created_at')

    def best_questions(self):
        return (
            self.get_queryset()
            .with_list_annotations()
            .order_by('-votes', '-created_at', '-id')
        )

    def for_tag(self, tag):
        return self.get_queryset().with_list_annotations().filter(tags=tag).order_by('-created_at')

    def for_detail(self):
        from .models import Answer

        return (
            self.select_related('author', 'author__profile')
            .prefetch_related('tags')
            .annotate(
                votes=Count('question_likes', distinct=True),
            )
            .annotate(answers_count=Count('answers', distinct=True))
            .annotate(
                is_answered=Exists(
                    Answer.objects.filter(
                        question_id=OuterRef('pk'),
                        is_accepted=True,
                    )
                )
            )
        )

    def get_for_detail_or_404(self, question_id):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(self.for_detail(), pk=question_id)


class AnswerQuerySet(models.QuerySet):
    def with_list_annotations(self):
        return self.select_related('author', 'author__profile').annotate(
            votes=Count('answer_likes', distinct=True),
        )


class AnswerManager(models.Manager):
    def get_queryset(self):
        return AnswerQuerySet(self.model, using=self._db)
