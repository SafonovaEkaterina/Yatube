from django.conf import settings
from django.core.paginator import Paginator


def show_post_count_in_page(request, posts):
    """Данная функция возвращает количество постов на странице."""
    paginator = Paginator(posts, settings.POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
