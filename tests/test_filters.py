from django.test import TestCase

from advanced_reports.defaults import AdvancedReport


class AdvancedReportTest(TestCase):
    def setUp(self):
        self.report = AdvancedReport()

    def test_tabbed_filter_fields(self):
        self.report.tabbed_filter_fields = {
            'card': {
                'images': {
                    'default': 'img/item.png',
                    'item2': 'img/item2.png'
                },
                'types': [
                    'item1', 'item2', 'item3', 'item4'
                ]
            }
        }

        self.assertEqual(['card'], [k for k, v in self.report.get_tabbed_filter_links()])
        dict_iteritems = [v for k, v in self.report.get_tabbed_filter_links()]
        self.assertEqual(
            [
                ('item1', 'img/item.png'),
                ('item2', 'img/item2.png'),
                ('item3', 'img/item.png'),
                ('item4', 'img/item.png'),
            ], sorted([(k, v) for k, v in dict_iteritems[0]]))

    def test_tabbed_filter_fields_default_only(self):
        self.report.tabbed_filter_fields = {
            'card': {
                'images': {
                    'default': 'img/item2.png'
                },
                'types': [
                    'item1', 'item2', 'item3', 'item4'
                ]
            }
        }

        self.assertEqual(['card'], [k for k, v in self.report.get_tabbed_filter_links()])
        dict_iteritems = [v for k, v in self.report.get_tabbed_filter_links()]
        self.assertEqual(
            [
                ('item1', 'img/item2.png'),
                ('item2', 'img/item2.png'),
                ('item3', 'img/item2.png'),
                ('item4', 'img/item2.png'),
            ], sorted([(k, v) for k, v in dict_iteritems[0]]))

    def test_tabbed_filter_fields_without_default_image(self):
        self.report.tabbed_filter_fields = {
            'card': {
                'images': {
                    'item2': 'img/item2.png'
                },
                'types': [
                    'item1', 'item2', 'item3', 'item4'
                ]
            }
        }

        self.assertEqual(['card'], [k for k, v in self.report.get_tabbed_filter_links()])
        dict_iteritems = [v for k, v in self.report.get_tabbed_filter_links()]
        self.assertEqual(
            [
                ('item1', None),
                ('item2', 'img/item2.png'),
                ('item3', None),
                ('item4', None),
            ], sorted([(k, v) for k, v in dict_iteritems[0]]))

    def test_tabbed_filter_fields_without_image_values(self):
        self.report.tabbed_filter_fields = {
            'card': {
                'images': {
                },
                'types': [
                    'item1', 'item2', 'item3', 'item4'
                ]
            }
        }

        self.assertEqual(['card'], [k for k, v in self.report.get_tabbed_filter_links()])
        dict_iteritems = [v for k, v in self.report.get_tabbed_filter_links()]
        self.assertEqual(
            [
                ('item1', None),
                ('item2', None),
                ('item3', None),
                ('item4', None),
            ], sorted([(k, v) for k, v in dict_iteritems[0]]))

    def test_tabbed_filter_fields_without_images(self):
        self.report.tabbed_filter_fields = {
            'card': {
                'types': [
                    'item1', 'item2', 'item3', 'item4'
                ]
            }
        }

        self.assertEqual(['card'], [k for k, v in self.report.get_tabbed_filter_links()])
        dict_iteritems = [v for k, v in self.report.get_tabbed_filter_links()]
        self.assertEqual(
            [
                ('item1', None),
                ('item2', None),
                ('item3', None),
                ('item4', None),
            ], sorted([(k, v) for k, v in dict_iteritems[0]]))

    def test_tabbed_filter_fields_without_types(self):
        self.report.tabbed_filter_fields = {
            'card': {
                'images': {
                },
            }
        }
        with self.assertRaises(Exception):
            self.report.get_tabbed_filter_links()

    def test_tabbed_filter_fields_multiple(self):
        self.report.tabbed_filter_fields = {
            'card': {
                'images': {
                    'default': 'img/item.png',
                    'item2': 'img/item2.png'
                },
                'types': [
                    'item1', 'item2', 'item3', 'item4'
                ]
            },
            'gender': {
                'images': {
                    'male': 'img/male.png',
                    'female': 'img/female.png'
                },
                'types': [
                    'male', 'female'
                ]
            }
        }

        self.assertEqual(['card', 'gender'], sorted([k for k, v in self.report.get_tabbed_filter_links()]))
        dict_iteritems = [v for k, v in self.report.get_tabbed_filter_links()]
        self.assertEqual(
            [
                ('item1', 'img/item.png'),
                ('item2', 'img/item2.png'),
                ('item3', 'img/item.png'),
                ('item4', 'img/item.png'),
            ], sorted([(k, v) for k, v in dict_iteritems[1]]))
        self.assertEqual(
            [
                ('female', 'img/female.png'),
                ('male', 'img/male.png'),
            ], sorted([(k, v) for k, v in dict_iteritems[0]]))
