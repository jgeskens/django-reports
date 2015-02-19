from __future__ import unicode_literals


# Compatibility layer for pagination
try:
    import django_ajax
except ImportError:
    from django.core.paginator import Paginator
    def paginate(request, object_list, per_page):
        paginator = Paginator(object_list, per_page)
        return paginator.page(request.GET.get('page', 1))
else:
    from django_ajax.pagination import paginate as old_paginate
    def paginate(request, object_list, per_page):
        return old_paginate(request, object_list, per_page, use_get_parameters=True)
