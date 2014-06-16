from functools import wraps

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
            if condition_func(request):
                # Only import django_delegation when asked.
                from django_delegation.decorators import delegate
                from django_delegation.utils import SimpleHTTPRequest
                if not isinstance(request, SimpleHTTPRequest):
                    return delegate(view_func)(request, *args, **kwargs)
            return view_func(request, *args, **kwargs)
        return delegated_view
    return decorator
