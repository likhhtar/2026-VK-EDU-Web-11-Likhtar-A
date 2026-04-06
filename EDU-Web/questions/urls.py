from django.urls import path
from . import views

app_name = 'questions'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('hot/', views.hot_view, name='hot'),
    path('tag/<str:tag>/', views.tag_view, name='tag'),
    path('question/<int:question_id>/', views.question_detail_view, name='question_detail'),
]