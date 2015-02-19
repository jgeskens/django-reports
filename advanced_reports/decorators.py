from functools import wraps
from advanced_reports import get_report_or_404

try:
    from django.utils.timezone import now
except:
    import datetime
    now = datetime.datetime.now


def conditional_delegation(condition_func):
    """
    Delegate a view depending on a certain condition.
    """
    def decorator(view_func):
        @wraps(view_func)
        def delegated_view(request, *args, **kwargs):
            # Only do the actual delegation if the django-delegation library is installed.
            try:
                from django_delegation.decorators import delegate
                from django_delegation.utils import SimpleHTTPRequest
            except ImportError:
                return view_func(request, *args, **kwargs)

            if not isinstance(request, SimpleHTTPRequest) and condition_func(request):
                return delegate(view_func)(request, *args, **kwargs)
            return view_func(request, *args, **kwargs)
        return delegated_view
    return decorator


def report_view(view_func):
    """
    Encapsulates a view which deals with a report and applies a custom decorator
    defined in the report, if it has ``decorate_views = True``.
    """
    @wraps(view_func)
    def decorated(request, slug, *args, **kwargs):
        report = get_report_or_404(slug)
        report.set_request(request)
        inner = view_func
        if report.decorate_views:
            inner = report.get_decorator()(inner)
        return inner(request, report, *args, **kwargs)
    return decorated
