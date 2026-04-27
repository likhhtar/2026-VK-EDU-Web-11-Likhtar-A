from .mock_data import get_popular_tags, get_best_members


def global_data(request):
    return {
        'popular_tags': get_popular_tags(),
        'best_members': get_best_members()
    }