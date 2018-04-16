from advanced_reports.defaults import action as original_action


class BackOfficeAction(original_action):
    form_template = 'advanced_reports/backoffice/contrib/advanced-reports/bootstrap-modal-form.html'


def action(*args, **kwargs):
    return BackOfficeAction(*args, **kwargs)
