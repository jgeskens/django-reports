from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.test.client import RequestFactory
import six
from advanced_reports.backoffice.api_utils import ViewRequestParameters
from advanced_reports.backoffice.base import BackOfficeBase, BackOfficeView

from advanced_reports.backoffice.examples.backoffice import test_backoffice
from advanced_reports.backoffice.examples.views import SimpleView


class BackOfficeBackend(TestCase):
    def setUp(self):
        user, created = User.objects.get_or_create(username='admin',
                                                   password='admin',
                                                   first_name='Admin',
                                                   last_name='User',
                                                   email='admin@example.com',
                                                   is_active=True,
                                                   is_staff=True,
                                                   is_superuser=True)
        user.set_password('admin')
        user.save()

        self.user2, created2 = User.objects.get_or_create(username='admin2',
                                                     password='admin',
                                                     first_name='Admin2',
                                                     last_name='User',
                                                     email='admin2@example.com',
                                                     is_active=True,
                                                     is_staff=True,
                                                     is_superuser=True)
        self.user2.set_password('admin')
        self.user2.save()

        self.home_url = reverse(test_backoffice.name + ':home', current_app=test_backoffice.app_name)
        self.client = Client()
        self.client.post(self.home_url, {'username': 'admin', 'password': 'admin'})

    def _reverse(self, name, args=None, kwargs=None):
        pass

    def test_default_context(self):
        """The default context contains usable values"""
        context = test_backoffice.default_context()
        self.assertEqual(context['backoffice'], test_backoffice)
        self.assertTrue('api_url' in context)
        self.assertTrue('root_url' in context)

    def test_home_view(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hi, <strong>Admin</strong>', response.content)

    def test_default_define_urls(self):
        self.assertEqual(BackOfficeBase().define_urls(), ())

    def test_login_as(self):
        self.client.get(self.home_url + 'login/as/' + six.text_type(self.user2.pk) + '/')
        response = self.client.get(self.home_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hi, <strong>Admin2</strong>', response.content)
        response = self.client.get(self.home_url + 'end/login/as/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hi, <strong>Admin</strong>', response.content)
        self.client.get(self.home_url + 'end/login/as/')

    def test_logout(self):
        response = self.client.get(self.home_url + 'logout/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Hi,', response.content)


class RequestWithViewParams(object):
    def __init__(self, params, user):
        self.view_params = ViewRequestParameters(RequestFactory().get('/', params))
        self.user = user


class PermissionView(SimpleView):
    permission = 'can_eat_monsters'
    template = SimpleView.template

    def post(self, request):
        return self.get(request)


class PostView(SimpleView):
    template = SimpleView.template

    def post(self, request):
        return self.get(request)


class BackOfficeViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_superuser('view_user', 'view-user@example.com', 'p')
        cls.user2 = User.objects.create_user('view_user2', 'view-user2@example.com', 'p')
        test_backoffice.register_view(SimpleView)
        test_backoffice.register_view(PermissionView)
        test_backoffice.register_view(PostView)

    def test_registration(self):
        v = test_backoffice.get_view('simple')
        self.assertIsNotNone(v)

    def test_get_view_content(self):
        r = test_backoffice.api_get_view(RequestWithViewParams({'view_slug': 'simple'}, self.user))
        self.assertEqual(r['slug'], 'simple')
        self.assertGreater(len(r['content']), 0)

    def test_non_existing_view_slug(self):
        r = test_backoffice.api_get_view(RequestWithViewParams({'view_slug': 'nonexisting'}, self.user))
        self.assertIn('View with slug "nonexisting" does not exist.', r['content'])

    def test_get_permission(self):
        r = test_backoffice.api_get_view(RequestWithViewParams({'view_slug': 'permission'}, self.user2))
        self.assertEqual(r['content'], '')

    def test_post(self):
        with self.assertRaises(NotImplementedError):
            test_backoffice.api_post_view(RequestWithViewParams({'view_slug': 'simple'}, self.user))
        r = test_backoffice.api_post_view(RequestWithViewParams({'view_slug': 'post'}, self.user))
        self.assertEqual(r['slug'], 'post')

    def test_post_permission(self):
        r = test_backoffice.api_post_view(RequestWithViewParams({'view_slug': 'permission'}, self.user2))
        self.assertEqual(r.content, 'You are not allowed to post data to the view "permission".')