from django.core.paginator import EmptyPage, Paginator
from django.http import Http404


def paginate_or_404(objects_list, request, per_page=10):
    raw = request.GET.get('page', '1')
    try:
        page_number = int(raw)
    except (TypeError, ValueError):
        raise Http404
    if page_number < 1:
        raise Http404
    paginator = Paginator(objects_list, per_page)
    try:
        return paginator.page(page_number)
    except EmptyPage:
        raise Http404


def get_page_range(page):
    current = page.number
    total = page.paginator.num_pages

    if total < 1:
        return [1]

    if total <= 7:
        return list(range(1, total + 1))

    if current <= 3:
        return [1, 2, 3, '...', total]

    if current >= total - 2:
        return [1, '...', total - 2, total - 1, total]

    return [1, '...', current - 1, current, current + 1, '...', total]
