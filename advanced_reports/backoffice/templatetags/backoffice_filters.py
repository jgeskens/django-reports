from collections import OrderedDict

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.utils.text import capfirst

import re
import html.parser
import json as json_lib


register = template.Library()


@register.filter
def angularize_form(value, model_prefix=None):
    """
    Make a Django form ready for AngularJS

    :param value: a HTML form
    :param model_prefix: if specified, will be used as the container for the form data
    :return: a HTML form made ready for AngularJS
    """

    def replace_name_func(match):
        name = match.groups()[0]
        short_name = name.split('-', 1)[1] if '-' in name else name
        model = short_name if model_prefix is None else '%s.%s' % (model_prefix, short_name)
        return ' name="%(name)s" ng-model="%(model)s"' % locals()

    def replace_value_func(match):
        model, value = 1, 3
        groups = list(match.groups())
        parsed_value = html.parser.HTMLParser().unescape(groups[value])
        groups[model] = '%s" ng-init="%s=\'%s\'' % (groups[model], groups[model], parsed_value.replace(u"'", u"\\'"))
        return ''.join(groups)

    replaced_name = re.sub(r'\s+name="([^"]+)"', replace_name_func, value)
    replaced_value = re.sub(r'(<[^>]+\s+ng-model=")([^"]+)("[^>]+\s+value=")([^"]+)("[^>]*>)', replace_value_func, replaced_name)
    return mark_safe(replaced_value)


@register.filter
def json(value):
    """
    Convert a simple Python object to JSON

    :param value: a simple Python object
    :return: the JSON for the simple Python object
    """
    return json_lib.dumps(value)


@register.filter
def pretty_join(value_list, seperator=', '):
    """
    Example:
    >>> pretty_join(['a', 'b', 'c'])
    'a, b and c'
    """
    if len(value_list) <= 1:
        return seperator.join(value_list)

    head = seperator.join(capfirst(value) for value in value_list[:-1])

    return '{} and {}'.format(head, capfirst(value_list[-1]))


@register.filter
def inline_errors(value):
    form = value
    err_list = OrderedDict({})

    # sort errors
    for key, errors in form.errors.items():
        for error in errors:
            if error not in err_list:
                err_list[error] = []
            if key in form.fields:
                label = form.fields[key].label
                if label:
                    label = _(label)
                    label = label.replace('?', '')
                    label = label.replace('!', '')
                    label = label.replace(':', '')
                    err_list[error].append(label)
                else:
                    err_list[error].append(key)
            else:
                err_list[error].append(key)

    # generate
    output = []
    for error, fields in err_list.items():
        if error == _('This field is required.'):
            if len(fields) == 1:
                output.append(_("%s is required.") % (pretty_join(fields)))
            else:
                output.append(_("%s are required.") % (pretty_join(fields)))
        else:
            output.append(error)

    return output


@register.filter
def stripchars(val, arg):
    return ''.join(c for c in str(val) if c not in arg)
