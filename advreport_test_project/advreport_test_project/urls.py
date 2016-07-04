from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.views.generic.base import RedirectView

from advanced_reports.backoffice.examples.backoffice import test_backoffice
from advreport_test_project.backoffice_definitions import todos_backoffice

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='/todos-backoffice/'), name='home'),
    url(r'^admin/', admin.site.urls),
    url(r'^test-backoffice/', include(test_backoffice.urls)),
    url(r'^todos-backoffice/', include(todos_backoffice.urls)),
    url(r'^reports/', include('advanced_reports.urls')),
)
