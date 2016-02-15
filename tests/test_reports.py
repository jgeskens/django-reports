# -*- coding: utf-8 -*
from django import forms
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory

from advanced_reports.defaults import AdvancedReport, EnrichedQueryset, action

import mock


class TestForm(forms.Form):
    testfield = forms.CharField()


class TestClass(object):
    def __init__(self, pk, a):
        self.pk = pk
        self.a = a


class TestReport1(AdvancedReport):
    items = None

    def __init__(self, *args, **kwargs):
        super(TestReport1, self).__init__(*args, **kwargs)
        self.items = [TestClass(i, i) for i in range(1, 4)]

    def queryset_request(self, request):
        return self.items

    def get_item_for_id(self, item_id):
        return [i for i in self.items if i.pk == item_id][0]

    def get_item_id(self, item):
        return item.pk

    @action('Multiple 1')
    def multiple1(self, item):
        item.a = 5

    @action('Multiple 2', form=TestForm)
    def multiple2(self, item, form):
        pass

    def multiple2_multiple(self, items, form):
        for item in items:
            item.a = form.cleaned_data['testfield']


class AdvancedReportTest(TestCase):
    def setUp(self):
        User.objects.create_user("test2", "test2@example.com", "foobar")
        self.report = AdvancedReport()
        self.report.models = (User,)

    def test_sorting(self):
        self.assertQuerysetEqual(User.objects.order_by('pk'), self.report.get_sorted_queryset('__unicode__'), transform=lambda x:x)
        self.assertQuerysetEqual(User.objects.order_by('pk'), self.report.get_sorted_queryset('__str__'), transform=lambda x:x)
        self.assertQuerysetEqual(User.objects.order_by('first_name'), self.report.get_sorted_queryset('first_name'), transform=lambda x:x)
        self.assertQuerysetEqual(User.objects.all(), self.report.get_sorted_queryset('field_that_does_not_exist'), transform=lambda x:x, ordered=False)
        self.assertQuerysetEqual(User.objects.all(), self.report.get_sorted_queryset('field_that__does_not_exist'), transform=lambda x:x, ordered=False)

    def test_enriched_queryset_order(self):
        eqs = EnrichedQueryset(User.objects.all(), self.report)
        self.assertListEqual(['pk'], eqs.queryset.query.order_by)
        eqs = EnrichedQueryset(User.objects.all().order_by('first_name'), self.report)
        self.assertListEqual(['first_name', 'pk'], eqs.queryset.query.order_by)
        eqs = EnrichedQueryset(['a','b','c'], self.report)
        self.assertListEqual(['a','b','c'], eqs.queryset)

    def test_multiple_actions(self):
        report = TestReport1()
        report.handle_multiple_actions('multiple1', [1, 2, 3])
        for item in report.items:
            self.assertEqual(item.a, 5)

        report = TestReport1()
        request = RequestFactory().post('/', data={'multiple2_multiple-testfield': '7'})
        setattr(request, '_messages', mock.MagicMock())

        ids = [1, 2]

        _, count = report.handle_multiple_actions('multiple2', ids, request)

        self.assertEqual(count, len(ids))
        for i in ids:
            self.assertEqual(report.get_item_for_id(i).a, '7')
