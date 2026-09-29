"""Пагінація у форматі компонента components/pagination.html."""

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

# Скільки сусідніх номерів сторінок показувати навколо поточної
WINDOW = 2


def _page_url(request, number):
    params = request.GET.copy()
    if number == 1:
        params.pop("page", None)
    else:
        params["page"] = number
    query = params.urlencode()
    return f"?{query}" if query else request.path


def paginate(request, queryset, per_page):
    """Повертає (сторінка Paginator, дані для компонента або None, якщо сторінка одна)."""
    paginator = Paginator(queryset, per_page)
    try:
        page_obj = paginator.page(request.GET.get("page", 1))
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    if paginator.num_pages <= 1:
        return page_obj, None

    current = page_obj.number
    last = paginator.num_pages
    window = range(max(1, current - WINDOW), min(last, current + WINDOW) + 1)
    numbers = sorted({1, last, *window})
    pages, previous = [], 0
    for number in numbers:
        if number - previous > 1:
            pages.append({"gap": True})
        pages.append(
            {"number": number, "url": _page_url(request, number), "current": number == current}
        )
        previous = number

    return page_obj, {
        "pages": pages,
        "prev_url": _page_url(request, current - 1) if page_obj.has_previous() else "",
        "next_url": _page_url(request, current + 1) if page_obj.has_next() else "",
    }
