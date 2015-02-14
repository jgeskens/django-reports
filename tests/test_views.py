import json
from django import forms
from django.contrib.auth.models import User
from django.http.response import HttpResponse
from django.test import TestCase
from django.test import client
from django.test.utils import override_settings
import six
import advanced_reports

from advanced_reports.defaults import BootstrapReport, action, ActionException


class TestForm(forms.Form):
    testfield = forms.CharField(required=True)


class SimpleReport(BootstrapReport):
    models = (User,)
    decorate_views = True

    def queryset(self):
        return User.objects.all()

    item_actions = (
        action(method='test', verbose_name='Test'),
        action(method='test2', verbose_name='Test2'),
        action(method='test3', verbose_name='Test3', group='test'),
        action(method='test4', verbose_name='Test4'),
    )

    def get_decorator(self):
        return lambda x: x

    def test(self, item):
        pass

    def test2_multiple(self, items):
        pass

    def test3(self, item):
        pass

    def test4_multiple(self, items):
        return HttpResponse('OK')

    @action(verbose_name='Test5')
    def test5(self, item):
        raise ActionException('test5 action failed with an ActionException')

    @action(verbose_name='Details', regular_view=True, form=TestForm)
    def details(self, item, form):
        return HttpResponse(form.cleaned_data['testfield'])

    @action(verbose_name='Remove')
    def remove(self, item):
        item.delete()

    def verify_action_group(self, item, group):
        if group is None: return True
        return False


advanced_reports.register(SimpleReport)


class ReportViewsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        User.objects.all().delete()
        cls.u = User.objects.create(username='test', password='test', email='test@example.com')
        cls.user_checkbox = 'checkbox_0000_%d' % cls.u.pk

    def setUp(self):
        self.client = client.Client()

    def test_list(self):
        response = self.client.get('/reports/simple/')
        self.assertEqual(response.status_code, 200)

    def test_list_post(self):
        response = self.client.post('/reports/simple/', {'method': 'test'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://testserver/reports/simple/')

    def test_list_no_method(self):
        response = self.client.post('/reports/simple/', {'method': ''})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://testserver/reports/simple/')

    def test_list_multiple_action_implicit(self):
        response = self.client.post('/reports/simple/', {'method': 'test', self.user_checkbox: 'true'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Successfully executed action on 1 user', response.content)

    def test_list_multiple_action_explicit(self):
        response = self.client.post('/reports/simple/', {'method': 'test2', self.user_checkbox: 'true'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Successfully executed action on 1 user', response.content)

    def test_list_multiple_action_no_selection(self):
        response = self.client.post('/reports/simple/', {'method': 'test2'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('You did not select any user.', response.content)

    def test_list_multiple_action_none_applicable(self):
        response = self.client.post('/reports/simple/', {'method': 'test3', self.user_checkbox: 'true'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('No selected user is applicable for this action.', response.content)

    def test_list_multiple_action_response(self):
        u = User.objects.latest('pk')
        response = self.client.post('/reports/simple/', {'method': 'test4', self.user_checkbox: 'true'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual('OK', response.content)

    def test_list_multiple_action_exception(self):
        response = self.client.post('/reports/simple/', {'method': 'test5', self.user_checkbox: 'true'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('test5 action failed with an ActionException', response.content)

    def test_list_csv(self):
        response = self.client.get('/reports/simple/?csv', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content,
                         'Username;Email address;First name;Last name;Staff status\n' +
                         'test;test@example.com;;;False\n')

    def test_api_action_simple(self):
        response = self.client.post('/reports/api/simple/action/test/%d/' % self.u.pk)
        self.assertIn('application/json', response['Content-Type'])
        data = json.loads(response.content)
        self.assertIn('success', data)
        self.assertIn('item', data)
        self.assertNotIn('removed_item_id', data)

    @override_settings(DEBUG=True)
    def test_api_action_regular_view_with_form(self):
        post_data = {'%d-testfield' % self.u.pk: 'test input'}

        # Post valid form input which should validate
        response = self.client.post(
            '/reports/api/simple/action/details/%d/' % self.u.pk,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertIn('application/json', response['Content-Type'])
        data = json.loads(response.content)
        self.assertIn('link_action', data)
        self.assertEqual(data['link_action']['method'], 'details')
        self.assertEqual(data['link_action']['data'], post_data)

        # Now we try form input that does not validate
        response = self.client.post(
            '/reports/api/simple/action/details/%d/' % self.u.pk,
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        data = json.loads(response.content)
        self.assertEqual(data['response_method'], 'details')
        self.assertIn('response_form', data)
        self.assertNotIn('success', data)

        # Now we use the form data to actually get the normal view (note that we do
        # a regular request here, not an AJAX one).
        response = self.client.post(
            '/reports/api/simple/action/details/%d/' % self.u.pk,
            post_data
        )
        self.assertIn('text/html', response['Content-Type'])
        self.assertContains(response, 'test input')

    def test_api_action_exception(self):
        response = self.client.post('/reports/api/simple/action/test5/%d/' % self.u.pk)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, 'test5 action failed with an ActionException')

    def test_api_action_removed_item(self):
        response = self.client.post('/reports/api/simple/action/remove/%d/' % self.u.pk)
        self.assertIn('application/json', response['Content-Type'])
        data = json.loads(response.content)
        self.assertIn('success', data)
        self.assertIn('item', data)
        self.assertIsNone(data['item'])
        self.assertIn('removed_item_id', data)
        self.assertEqual(data['removed_item_id'], six.text_type(self.u.pk))
