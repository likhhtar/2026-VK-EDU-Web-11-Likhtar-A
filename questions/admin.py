from django.contrib import admin
from django.db.models import Count

from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    show_change_link = True
    fields = ('author', 'text', 'is_accepted', 'created_at', 'updated_at')
    autocomplete_fields = ('author',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'questions_count')
    search_fields = ('name',)

    @admin.display(description='вопросов', ordering='questions_count')
    def questions_count(self, obj: Tag) -> int:
        return obj.questions_count

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(questions_count=Count('questions'))


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'created_at', 'tags_count', 'answers_count', 'views')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'text', 'author__username')
    autocomplete_fields = ('author', 'tags')
    inlines = (AnswerInline,)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='теги', ordering='tags_count')
    def tags_count(self, obj: Question) -> int:
        return obj.tags_count

    @admin.display(description='ответов', ordering='answers_count')
    def answers_count(self, obj: Question) -> int:
        return obj.answers_count

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('author', 'author__profile')
            .annotate(tags_count=Count('tags', distinct=True), answers_count=Count('answers', distinct=True))
        )


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'author', 'is_accepted', 'created_at', 'question_id')
    list_filter = ('is_accepted', 'created_at', 'updated_at')
    search_fields = ('text', 'author__username', 'question__title')
    autocomplete_fields = ('question', 'author')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('question', 'author', 'author__profile')


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'question__title')
    autocomplete_fields = ('user', 'question')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'question', 'user__profile')


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'answer', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'answer__text', 'answer__question__title')
    autocomplete_fields = ('user', 'answer')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'answer', 'answer__question', 'user__profile')
