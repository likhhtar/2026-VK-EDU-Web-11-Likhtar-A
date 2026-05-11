from django.db.models import Count

from questions.models import Tag
from .models import Profile


def global_data(_request):
    popular_tags = list(
        Tag.objects.annotate(c=Count('questions'))
        .order_by('-c', 'name')
        .values_list('name', flat=True)[:6]
    )
    best_members = list(
        Profile.objects.select_related('user').order_by('-rating', 'user_id')[:4]
    )
    return {
        'popular_tags': popular_tags,
        'best_members': best_members,
    }
