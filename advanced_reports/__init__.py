__version__ = '0.9.24'


REGISTRY = {}


def register(advreport):
    REGISTRY[advreport.slug] = advreport


def get_report_for_slug(slug):
    return REGISTRY.get(slug, lambda: None)()


def get_report_or_404(slug):
    advreport = get_report_for_slug(slug)
    if advreport is None:
        from django.http import Http404
        raise Http404('No AdvancedReport matches the given query.')

    advreport.internal_mode = False
    advreport.report_header_visible = True
    return advreport
