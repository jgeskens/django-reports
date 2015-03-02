# -*- coding: utf-8 -*
from django.contrib.auth.models import User
from django.test import TestCase

from advanced_reports.defaults import AdvancedReport, EnrichedQueryset


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
