from importlib import import_module

from advanced_reports.backoffice.base import BackOfficeView
from django.template.loaders.app_directories import Loader
from pygments import highlight
from pygments.lexers.python import PythonLexer
from pygments.lexers.templates import HtmlDjangoLexer
from pygments.formatters.html import HtmlFormatter
import inspect


class ExampleIncludeTemplateView(BackOfficeView):
    template = 'advanced_reports/backoffice/views/exampleinclude.html'

    def get_extra_context(self, request):
        include = request.view_params.get('include')
        html, _ = Loader().load_template_source(include)
        html_snippet = highlight(html, HtmlDjangoLexer(), HtmlFormatter(full=False, noclasses=True))
        return {'html': html_snippet, 'path': include}


class ExampleIncludePythonView(BackOfficeView):
    template = 'advanced_reports/backoffice/views/exampleinclude.html'

    def get_extra_context(self, request):
        include = request.view_params.get('include')
        module, member = include.rsplit('.', 1)
        module = import_module(module)
        source = inspect.getsource(getattr(module, member))
        html_snippet = highlight(source, PythonLexer(), HtmlFormatter(full=False, noclasses=True))
        return {'html': html_snippet, 'path': include}
