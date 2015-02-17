from django.conf.urls import url
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from advanced_reports.backoffice.base import BackOfficeBase, BackOfficeModel, BackOfficeTab, BackOfficeView
from advanced_reports.backoffice.contrib.views import AdvancedReportView
import advanced_reports


from advanced_reports.backoffice.examples.reports import UserReport, UserForm
from advanced_reports.backoffice.examples.views import SimpleView


User = get_user_model()


class TestBackOffice(BackOfficeBase):
    title = 'Test Backoffice'

    def __init__(self):
        super(TestBackOffice, self).__init__(name='test_backoffice')

    def define_urls(self):
        return (url(r'^page/$', self.page, name='page'),)

    def page(self, request):
        return TemplateResponse(request, 'advanced_reports/backoffice/tests/page.html', {'backoffice': self})


class UserModel(BackOfficeModel):
    model = User
    verbose_name = u'user'
    verbose_name_plural = u'users'

    tabs = (BackOfficeTab('details', u'Details', 'advanced_reports/backoffice/tests/user-details.html'),)

    def get_title(self, instance):
        return u'%s (%s)' % (instance.username, instance.get_full_name())

    def search_index(self, instance):
        return u' '.join((instance.username, instance.get_full_name(), instance.email))


class UserView(BackOfficeView):
    def render(self, request, user, form):
        return TemplateResponse(request, 'advanced_reports/backoffice/tests/user-form.html', {'user': user, 'form': form})

    def get(self, request):
        user = get_object_or_404(User, pk=request.view_params.get('pk'))
        form = UserForm(instance=user)
        return self.render(request, user, form)

    def post(self, request):
        user = get_object_or_404(User, pk=request.view_params.get('pk'))
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, u'Successfully saved user details! Try a search now...')
        return self.render(request, user, form)

    def update(self, request):
        data = request.view_params.get('data')
        user = get_object_or_404(User, pk=request.view_params.get('pk'))
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.save()
        return data


test_backoffice = TestBackOffice()
test_backoffice.register_model(UserModel)
test_backoffice.register_view(AdvancedReportView)
test_backoffice.register_view(UserView)
test_backoffice.register_view(SimpleView)

advanced_reports.register(UserReport)
