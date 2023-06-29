from decimal import Decimal
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as make_proxy
from django.conf import settings

import json
import six


_proxy_type = type(make_proxy('ignore this'))


def _json_object_encoder(obj):
    if isinstance(obj, _proxy_type):
        return six.text_type(obj)
    elif isinstance(obj, Decimal):
        return six.text_type(obj)
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif hasattr(obj, 'splitlines'):
        return six.text_type(obj)
    else:
        return None


def to_json(obj):
    if settings.DEBUG:
        return json.dumps(obj, default=_json_object_encoder, indent=2)
    return json.dumps(obj, default=_json_object_encoder)


def JSONResponse(obj):
    return HttpResponse(to_json(obj), content_type='application/json;charset=UTF-8')


class ViewRequestParameters(object):
    def __init__(self, request):
        self.GET = request.GET
        self.POST = request.POST
        self.body = request.body
        self.json_dict = json.loads(self.body.decode('utf-8')) if 'application/json' in request.content_type else {}

        self.fallbacks = (self.GET, self.POST, self.json_dict)
        self.list_fallbacks = (self.GET, self.POST)

    def get(self, item, default=None):
        for fallback in self.fallbacks:
            obj = fallback.get(item, None)
            if obj is not None:
                return obj
        return default

    def getlist(self, item, default=None):
        for fallback in self.list_fallbacks:
            lst = fallback.getlist(item)
            if lst:
                return lst
        if default is None:
            return []
        return default

    def __repr__(self):
        return 'ViewRequestParameters(%r, %r, %r)' % (self.GET, self.POST, self.json_dict)
