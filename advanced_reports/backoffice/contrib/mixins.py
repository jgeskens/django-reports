from __future__ import unicode_literals


class BackOfficeReportMixin(object):
    """
    This mixin adds BackOffice-specific functionality to an ``AdvancedReport`` subclass.
    """

    def link_to_backoffice_model_instance(self, instance):
        pass
