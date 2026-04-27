from django.core.paginator import Paginator, EmptyPage


def paginate(objects_list, request, per_page=10):
    paginator = Paginator(objects_list, per_page)
    raw = request.GET.get('page', '1')

    try:
        page_number = int(raw)
    except (TypeError, ValueError):
        page_number = 1

    if page_number < 1:
        page_number = 1

    last = paginator.num_pages
    if last >= 1 and page_number > last:
        page_number = last

    try:
        return paginator.page(page_number)
    except EmptyPage:
        return paginator.page(last) if last >= 1 else paginator.page(1)


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
