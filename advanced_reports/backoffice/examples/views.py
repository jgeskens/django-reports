from advanced_reports.backoffice.base import BackOfficeView

class SimpleView(BackOfficeView):
    def get_ip(self, request):
        return request.META['REMOTE_ADDR']

    def get_items(self, request):
        return {'a': 5, 'b': 3, 'c': 4}
