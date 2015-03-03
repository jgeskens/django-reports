from __future__ import unicode_literals
from django.conf.urls import url
from django.template.response import TemplateResponse
from django.views.generic.base import TemplateView
import advanced_reports
from advanced_reports.backoffice.base import BackOfficeBase
from advanced_reports.backoffice.contrib.views import AdvancedReportView, AdvancedReportActionView
from advanced_reports.backoffice.examples.backoffice import UserModel, UserView
from advanced_reports.backoffice.examples.reports import NoModelReport, UserReport, NewStyleReport, TodoListReport
from advanced_reports.backoffice.examples.views import SimpleView
from advreport_examples.views import ExampleIncludePythonView, ExampleIncludeTemplateView
from oemfoe_todos_app.backoffice.definitions import TodoListModel, TodoItemModel, TodoListsView


class TodosBackoffice(BackOfficeBase):
    title = 'Oemfoe Todo List Administration'
    model_template = 'advreport_examples/page-base.html'

    def define_urls(self):
        return (
            url(r'^users/$',
                self.decorate(TemplateView.as_view(template_name='advreport_examples/users.html')),
                name='users'),
            url(r'^examples/$',
                self.decorate(TemplateView.as_view(template_name='advreport_examples/examples.html')),
                name='examples'),
        )

    def page(self, request):
        return TemplateResponse(request, 'advanced_reports/backoffice/tests/page.html', {'backoffice': self})


todos_backoffice = TodosBackoffice(name='todos')


todos_backoffice.register_model(UserModel)
todos_backoffice.register_view(UserView)
todos_backoffice.register_view(SimpleView)

todos_backoffice.register_model(TodoListModel)
todos_backoffice.register_model(TodoItemModel)
todos_backoffice.register_view(TodoListsView)

todos_backoffice.register_view(AdvancedReportView)
todos_backoffice.register_view(AdvancedReportActionView)

todos_backoffice.register_view(ExampleIncludeTemplateView)
todos_backoffice.register_view(ExampleIncludePythonView)

advanced_reports.register(NoModelReport)
advanced_reports.register(UserReport)
advanced_reports.register(NewStyleReport)
advanced_reports.register(TodoListReport)
