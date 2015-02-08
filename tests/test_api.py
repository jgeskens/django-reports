from __future__ import unicode_literals
import json
from decimal import Decimal
import datetime
from django.http.response import Http404, HttpResponse
from django.test import TestCase, RequestFactory
from django.utils.translation import ugettext_lazy
import six
from advanced_reports.backoffice.api_utils import to_json, ViewRequestParameters
from advanced_reports.backoffice.base import BackOfficeBase


class SimpleBackOffice(BackOfficeBase):
    title = 'Simple Backoffice'

    def api_get_test(self, request):
        return request.view_params.get('param')

    def api_get_response(self, request):
        return HttpResponse('OK')


simple_backoffice = SimpleBackOffice()


class ApiTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def test_api(self):
        rf = RequestFactory()

        r = json.loads(simple_backoffice.api(rf.get('/api/')).content)
        self.assertEqual(r, None)

        with self.assertRaises(Http404):
            simple_backoffice.api(rf.get('/api/nonexisting/'), method='nonexisting')

        r = json.loads(simple_backoffice.api(rf.get('/api/test/?param=lol'), method='test').content)
        self.assertEqual(r['response_data'], 'lol')

        r = simple_backoffice.api(rf.get('/api/response/'), method='response').content
        self.assertEqual(r, 'OK')

    def test_to_json(self):
        self.assertEqual(to_json(123), '123')
        self.assertEqual(to_json('123'), '"123"')
        self.assertEqual(to_json({'a': '3', 'b': 5}), '{"a": "3", "b": 5}')
        self.assertEqual(to_json(Decimal('10.33')), '"10.33"')
        self.assertEqual(to_json(ugettext_lazy('ignore this also')), '"ignore this also"')
        self.assertEqual(to_json(datetime.datetime(2015, 1, 20)), '"2015-01-20T00:00:00"')
        self.assertEqual(to_json(datetime.date(2015, 1, 20)), '"2015-01-20"')

        @six.python_2_unicode_compatible
        class TestClass(object):
            def splitlines(self):
                return ('line 1', 'line 2')
            def __str__(self):
                return 'hello'

        class TestClass2(object):
            pass

        self.assertEqual(to_json(TestClass()), '"hello"')
        self.assertEqual(to_json(TestClass2()), 'null')

        with self.settings(DEBUG=True):
            self.assertEqual(to_json({'a': '3', 'b': 5}), '{\n  "a": "3", \n  "b": 5\n}')

    def test_viewrequestparameters(self):
        request = RequestFactory().get('/?a=1&a=2&a=3')
        params = ViewRequestParameters(request)
        self.assertEqual(params.get('nonexisting', 'fallback'), 'fallback')
        self.assertEqual(params.getlist('a'), ['1', '2', '3'])
        self.assertEqual(params.getlist('nonexisting'), [])
        self.assertEqual(params.getlist('nonexisting', ['default']), ['default'])
        self.assertEqual(repr(params),
                         "ViewRequestParameters(<QueryDict: {u'a': [u'1', u'2', u'3']}>, " +
                         "<QueryDict: {}>, {})")
