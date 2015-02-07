from django.contrib.auth.models import User
from django import forms
from django.http.response import HttpResponse
from django.template.defaultfilters import yesno

from advanced_reports.backoffice.shortcuts import action
from advanced_reports.defaults import AdvancedReport, ActionException


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

class UserReport(AdvancedReport):
    models = (User,)
    fields = ('username', 'first_name', 'last_name',)

    item_actions = (
        action(method='edit', verbose_name='Edit', form=UserForm, form_via_ajax=True, group='no_superuser'),
        action(method='send_reminder_email', verbose_name='Send reminder email', individual_display=False),
    )
    multiple_actions = True
    template = 'advanced_reports/bootstrap/report.html'
    item_template = 'advanced_reports/bootstrap/item.html'

    def queryset_request(self, request):
        return User.objects.all()

    def get_username_html(self, item):
        return u'<a href="#/user/%d/">%s</a>' % (item.pk, item.username)

    def get_html_for_value(self, value):
        if isinstance(value, bool):
            return yesno(value, '<i class="glyphicon glyphicon-ok-circle">,<i class="glyphicon glyphicon-remove-circle">')
        return value

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


class NoModelReport(AdvancedReport):
    verbose_name = 'number'
    verbose_name_plural = 'numbers'
    fields = ('value', 'square',)
    items_per_page = 10
    multiple_actions = True

    item_actions = (
        action(method='calculate_sum', verbose_name='Calculate sum', individual_display=False),
        action(method='export_as_csv_view', verbose_name='Export selection as CSV',
               individual_display=True, form=CSVForm, form_via_ajax=True)
    )

    def queryset_request(self, request):
        return [NoModel(number) for number in xrange(1000)]

    def get_item_id(self, item):
        return item.value

    def get_item_for_id(self, item_id):
        return NoModel(int(item_id))

    def calculate_sum_multiple(self, items):
        return {
            'dialog_content': 'The sum is: %d' % sum((item.value for item in items)),
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

