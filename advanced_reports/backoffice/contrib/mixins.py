from __future__ import unicode_literals
from django.core.urlresolvers import resolve, reverse


def get_backoffice_from_path(path):
    """
    Based on the given ``path``, return the ``BackOfficeBase`` subclass instance serving this path.

    :param path: The path to find the ``BackOfficeBase`` subclass instance for.
    :return: A ``BackOfficeBase`` subclass instance.
    """
    resolved = resolve(path)
    handle_path = reverse('%s:handle' % resolved.namespace, current_app=resolved.app_name)
    resolved_handle = resolve(handle_path)
    return resolved_handle.func.__self__


class BackOfficeReportMixin(object):
    """
    This mixin adds BackOffice-specific functionality to an ``AdvancedReport`` subclass.
    """

    def get_current_backoffice(self):
        """
        Gives the current ``BackOfficeBase`` subclass instance serving this report.

        :return: A ``BackOfficeBase`` subclass instance.
        """
        return get_backoffice_from_path(self.request.path)

    def link_to(self, instance):
        """
        Returns a HTML decorator providing, if available, a web link to the given model instance.

        :param instance: The model instance.
        :return: A function accepting a HTML string which returns a new HTML string.
        """
        backoffice = self.get_current_backoffice()
        bo_model = backoffice.get_model(model=instance.__class__)

        if bo_model is not None:
            return lambda h: '<a link-to="%s">%s</a>' % ("{model: '%s', id: %d}" % (bo_model.slug, instance.pk), h)

        elif hasattr(instance, 'get_absolute_url'):
            return lambda h: '<a href="%s">%s</a>' % (instance.get_absolute_url(), h)

        return lambda h: h
