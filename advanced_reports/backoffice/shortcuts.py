from advanced_reports.defaults import Action


class BackOfficeAction(Action):
    form_template = 'advanced_reports/backoffice/contrib/advanced-reports/bootstrap-modal-form.html'


def action(*args, **kwargs):
    return BackOfficeAction(*args, **kwargs)
