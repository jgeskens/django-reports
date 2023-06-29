from django.urls import re_path as url
from advanced_reports.views import *

urlpatterns = [
    url(r'^(?P<slug>[^/]+)/$', list, name='advanced_reports_list'),
    
    url(r'^(?P<slug>[^/]+)/form/(?P<method>[^/]+)/(?P<object_id>[^/]+)/$', ajax_form, name='advanced_reports_form'),
    url(r'^(?P<slug>[^/]+)/form/(?P<method>[^/]+)/(?P<object_id>[^/]+)/(?P<param>[^/]+)/$', ajax_form, name='advanced_reports_form'),
    
    url(r'^(?P<slug>[^/]+)/action/(?P<method>[^/]+)/(?P<object_id>[^/]+)/$', action, name='advanced_reports_action'),
    url(r'^(?P<slug>[^/]+)/action/(?P<method>[^/]+)/(?P<object_id>[^/]+)/(?P<param>[^/]+)/$', action, name='advanced_reports_action'),
    
    url(r'^(?P<slug>[^/]+)/ajax/(?P<method>[^/]+)/(?P<object_id>[^/]+)/$', ajax, name='advanced_reports_ajax'),
    url(r'^(?P<slug>[^/]+)/ajax/(?P<method>[^/]+)/(?P<object_id>[^/]+)/(?P<param>[^/]+)/$', ajax, name='advanced_reports_ajax'),
    
    url(r'^(?P<slug>[^/]+)/count/$', count, name='advanced_reports_count'),

    url(r'^api/(?P<slug>[^/]+)/$', api_list, name='advanced_reports_api_list'),
    url(r'^api/(?P<slug>[^/]+)/action/(?P<method>[^/]+)/(?P<object_id>[^/]+)/$', api_action, name='advanced_reports_api_action'),
    url(r'^api/(?P<slug>[^/]+)/form/(?P<method>[^/]+)/(?P<object_id>[^/]+)/$', api_form,
        name='advanced_reports_api_form'),
    url(r'^api/(?P<slug>[^/]+)/form/(?P<method>[^/]+)/$', api_form,
        name='advanced_reports_api_form'),
]
