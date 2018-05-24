from __future__ import unicode_literals

from django.core.paginator import Paginator


def paginate(request, object_list, per_page):
    paginator = Paginator(object_list, per_page)
    return paginator.page(request.GET.get('page', 1))
