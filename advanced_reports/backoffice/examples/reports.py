from __future__ import unicode_literals
from django.contrib.auth import get_user_model
from django import forms
from django.http.response import HttpResponse
from django.template.defaultfilters import yesno
from django.utils.html import escape
from advanced_reports.backoffice.contrib.mixins import BackOfficeReportMixin

from advanced_reports.backoffice.shortcuts import action
from advanced_reports.defaults import ActionException, BootstrapReport, ActionType
from oemfoe_todos_app.models import TodoList


User = get_user_model()


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')


class UserReport(BootstrapReport):
    models = (User,)
    fields = ('email', 'first_name', 'last_name',)
    help_text = 'This is a help text!'
    links = ((u'Refresh', '.'),)

    item_actions = (
        action(method='edit', verbose_name='Edit', form=UserForm, form_via_ajax=True, group='no_superuser'),
        action(method='send_reminder_email', verbose_name='Send reminder email', individual_display=True),
    )
    multiple_actions = True
    template = 'advanced_reports/bootstrap/report.html'
    item_template = 'advanced_reports/bootstrap/item.html'
    date_range = 'last_login'
    action_list_type = ActionType.INLINE_BUTTONS
    compact = True

    def queryset_request(self, request):
        return User.objects.all()

    def get_username_html(self, item):
        return u'<a href="#/user/%d/">%s</a>' % (item.pk, escape(item.username))

    def get_html_for_value(self, value):
        if isinstance(value, bool):
            return yesno(value, '<i class="glyphicon glyphicon-ok-circle">,<i class="glyphicon glyphicon-remove-circle">')
        return super(UserReport, self).get_html_for_value(value)

    def edit(self, item, form):
        form.save()

    def send_reminder_email(self, item):
        if item.pk % 2 == 0:
            raise ActionException('Could not deliver email')

    def verify_action_group(self, item, group):
        if not group: return True
        elif group == 'no_superuser' and not item.is_superuser: return True
        return False


class NoModel(object):
    def __init__(self, value):
        self.value = value

    @property
    def square(self):
        return self.value * self.value


class CSVForm(forms.Form):
    filename = forms.CharField(initial='numbers.csv', required=True)


class SumForm(forms.Form):
    factor = forms.IntegerField(initial=1, required=True)


class NoModelReport(BootstrapReport):
    verbose_name = 'number'
    verbose_name_plural = 'numbers'
    fields = ('value', 'square',)
    items_per_page = 10
    multiple_actions = True
    search_fields = ('value', 'square',)

    item_actions = (
        action(method='calculate_sum', verbose_name='Calculate sum', individual_display=False,
               form=SumForm, form_via_ajax=True),
        action(method='export_as_csv_view', verbose_name='Export selection as CSV',
               individual_display=True, form=CSVForm, form_via_ajax=True)
    )

    def queryset_request(self, request):
        return [NoModel(number) for number in xrange(1000)]

    def get_item_id(self, item):
        return item.value

    def get_item_for_id(self, item_id):
        return NoModel(int(item_id))

    def calculate_sum_multiple(self, items, form):
        factor = form.cleaned_data['factor']
        return {
            'dialog_content': 'The sum is: %d' % (sum((item.value for item in items)) * factor),
            'dialog_style': {'width': '300px'}
        }

    def export_as_csv_view(self, item, form):
        return self.export_as_csv_view_multiple([item], form)

    def export_as_csv_view_multiple(self, items, form):
        import csv
        filename = form.cleaned_data['filename']
        response = HttpResponse()
        writer = csv.writer(response, dialect='excel')
        writer.writerow(('Value', 'Square'))
        for item in items:
            writer.writerow((item.value, item.square))
        response['Content-Type'] = 'application/csv'
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        return response


class NewStyleReport(BootstrapReport):
    model = User
    fields = 'first_name', 'last_name', 'email'

    @action('Say hello', css_class='btn-primary')
    def hello(self, item):
        return 'Hello, %s!' % escape(self.request.user.first_name)

    @action('Edit user', form=UserForm)
    def edit(self, item, form):
        form.save()

    @action('Enter factor', form=SumForm, is_report_action=True)
    def factor(self, form):
        if form.cleaned_data['factor'] == 2:
            raise ActionException("I don't like factor two :-(")
        return 'The given factor was: %d' % form.cleaned_data['factor']


class TodoListForm(forms.ModelForm):
    class Meta:
        model = TodoList
        fields = ('name', 'owner')


class TodoListReport(BackOfficeReportMixin, BootstrapReport):
    model = TodoList
    fields = ('name', 'owner')
    search_fields = ('name',)
    sortable_fields = fields
    multiple_actions = True
    action_list_type = ActionType.INLINE_BUTTONS
    compact = True

    @action('New Todo List', form=TodoListForm, is_report_action=True,
            css_class='btn-primary')
    def new(self, form):
        form.save()

    @action('Edit', form=TodoListForm, css_class='btn-warning')
    def edit(self, todo_list, form):
        form.save()

    @action('Delete', confirm='Are you sure you want to delete %(name)s?',
            css_class='btn-danger', individual_display=False)
    def delete(self, todo_list):
        todo_list.delete()

    def get_name_decorator(self, todo_list):
        return self.link_to(todo_list)
