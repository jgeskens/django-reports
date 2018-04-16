from functools import wraps
from advanced_reports import get_report_or_404


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
