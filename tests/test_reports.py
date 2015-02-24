# -*- coding: utf-8 -*
from django.contrib.auth.models import User
from django.test import TestCase

from advanced_reports.defaults import AdvancedReport


class AdvancedReportTest(TestCase):
    def setUp(self):
        self.report = AdvancedReport()
        self.report.models = (User,)

    def test_sorting(self):
        self.assertQuerysetEqual(User.objects.order_by('pk'), self.report.get_sorted_queryset('__unicode__'), transform=lambda x:x)
        self.assertQuerysetEqual(User.objects.order_by('pk'), self.report.get_sorted_queryset('__str__'), transform=lambda x:x)
        self.assertQuerysetEqual(User.objects.order_by('first_name'), self.report.get_sorted_queryset('first_name'), transform=lambda x:x)
        self.assertQuerysetEqual(User.objects.all(), self.report.get_sorted_queryset('field_that_does_not_exist'), transform=lambda x:x)
        self.assertQuerysetEqual(User.objects.all(), self.report.get_sorted_queryset('field_that__does_not_exist'), transform=lambda x:x)
