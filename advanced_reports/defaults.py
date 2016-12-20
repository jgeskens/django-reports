import datetime
import time
import urllib
from collections import OrderedDict

from django import forms
from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http.response import Http404
from django.template.context import RequestContext
from django.template.defaultfilters import capfirst
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.html import strip_tags, escape
from django.utils.translation import ugettext_lazy as _
from django.forms.models import fields_for_model

import six

from advanced_reports.backoffice.base import AutoSlug


class ActionType(object):
    LINKS = 'links'
    BUTTONS = 'buttons'
    INLINE_BUTTONS = 'inline_buttons'


class action(object):
    attrs_dict = None
    creation_counter = 0

    #: Required when not using the decorator. This is a string with the method name of your AdvancedReport subclass.
    #: This method must accept an item instance. If you choose to use a form, it gets an item and a bound form.
    #: If something goes wrong in your action, raise an ActionException with a message to display to the user.
    method = None

    #: Required. This is what the user will see in the frontend. If your action is simple (as in, it has no form), this
    #: will be the name of the web link. If your action uses a form, this will be a title that will be placed before it.
    #: If you don't want to display that, just use u''.
    verbose_name = None

    #: Optional. This will be used as the success message when your action has successfully executed.
    success = None

    #: Optional. When filled in, a confirmation dialog will be displayed using this attribute as the prompt.
    confirm = None

    #: Optional. When used together with a override of ``verify_action_group``, you can define on a per-item basis
    #: which action will be shown or not. This is useful when your items have a certain state only allowing for
    #: actions directly related to that state.
    group = None

    #: Optional. A Django form class that should be used together with this action. Make sure your action method
    #: has a signature like this: ``def my_action(self, item, form):``.
    #:
    #: Actions support the use of Django forms. When assigning a form class to this action, the behavior of actions
    #: will be altered in the following ways:
    #:
    #:  * A form will be presented to the user, most likely in a pop-up (if ``form_via_ajax`` is True, this is the
    #:    default when using the ``@action`` decorator version). The submit button of the form will have the
    #:    ``submit`` attribute of this action as the caption.
    #:  * When using a ModelForm, the current item instance (if available) will be used as the form's ``instance``.
    #:    keyword argument.
    #:  * Upon submission of this form, Advanced Reports will try to validate the form. If the form is not valid,
    #:    the form errors are automatically displayed to the frontend, instead of executing the underlying action.
    #:    If the form does pass the validation, the underlying action is called with the validated form as an extra
    #:    argument. If you are using a ModelForm, you can just perform a ``form.save()`` in the action method body.
    #:
    form = None

    #: Determines whether the action form should be shown as a pop-up dialog in the frontend or not.
    #: The default value is False, but if you are using the ``@action`` decorator version, the default is True.
    #: This strange default behavior is merely for backwards compatibility.
    form_via_ajax = False

    #: Determines whether the action form should be rendered at the time of the report items generation.
    #: By default this is False, but inline action forms (when ``form_via_ajax`` is False) will always be
    #: prefetched, as they are directly visible.
    prefetch_ajax_form = False

    #: If True, the link behind the action will be loaded in a pop-up. This only works if the template
    #: supports this. An alternative system for showing pop-ups is just returning the html for this pop-up
    #: in the body of the action method. This is implemented in the AngularJS version.
    link_via_ajax = False

    #: Required when using form. This is the value of your submit button when using forms.
    submit = u'Submit'

    #: Optional. If True, the submit button will be shown. The hiding of the submit button only works
    #: when the template supports this.
    show_submit = True

    #: Optional. Only used when the template supports this.
    collapse_form = False

    #: If a template path is assigned to this attribute, this template will be rendered instead of the output
    #: of {{ form }}. The template receives ``form`` and ``item`` as context variables.
    form_template = None

    #: Optional. If set, this instance will be used to pass to a ModelForm.
    #: You can also supply a callable. The kwargs are: ``instance`` and optionally ``param``.
    form_instance = None

    #: Optional. If True, when an action was executed successfully, the current row will be collapsed and the next row
    #: will be expanded, and the first field of the first form gets the input focus.
    next_on_success = False

    #: Makes the action invisible. If you want to use this action somewhere else, you can use the
    #: {% url 'advanced_reports_action' report_slug action_method item_id %} to execute the action.
    hidden = False

    #: Optional. A custom css class for this action.
    css_class = None

    #: Whether the action is shown on individual items. It could be that an action is only designed to work on
    #: a bulk items. When setting to False, you remove them from the individual items.
    individual_display = True

    #: Enable the use of actions than can execute on multiple items.
    #: If you want to implement bulk methods operating directly on a list or queryset (if applicable), you
    #: can implement an extra ``def FOO_multiple(self, items, form=None):`` where FOO is the method name of your
    #: action. If not, it will just loop through your items and execute your action on each item one after another.
    multiple_display = True

    #: If the form of the action has a file upload, set this to True. Then the enctype="multipart/form-data"
    #: will be added to the ``<form>`` tag.
    has_file_upload = False

    #: Optional. The permission required for this action.
    permission = None

    #: Whether the action method acts like a regular Django view.
    regular_view = False

    #: Whether the action is report-wide or not. Report-wide actions methods do not
    #: receive an argument containing the item. Only a form will be given if applicable.
    #: Report-wide actions are ideal for adding new items or links to another web page.
    is_report_action = False

    #: Whether the action is defined by the new style method (as a decorator) or not.
    #: The advantage is that new cool stuff that should not be backwards compatible can be enabled when this
    #: attribute is True.
    is_new_style = False

    def __init__(self, title=None, **kwargs):
        """
        Each kwarg maps to a property above. For documentation, refer to the individual property documentation strings.
        """
        action.creation_counter += 1
        self.creation_counter = action.creation_counter

        if title is not None:
            kwargs['verbose_name'] = title

        if kwargs.get('is_report_action', False):
            kwargs['individual_display'] = False
            kwargs['multiple_display'] = False

        self.attrs_dict = {}
        for k in kwargs.keys():
            setattr(self, k, kwargs[k])
            self.attrs_dict[k] = kwargs[k]

    def copy_with_instanced_form(self, advreport, prefix, instance=None, data=None, files=None):
        new_action = action(**self.attrs_dict)
        dynamic_form = getattr(advreport, 'get_%s_form' % new_action.method, None)

        if dynamic_form is not None and callable(dynamic_form):
            new_action.form = dynamic_form(instance, prefix, data=data)

        elif self.form is not None:
            new_action.form = self.form
            if issubclass(self.form, forms.ModelForm):
                new_action.form = self.form(data=data, files=files, prefix=prefix, instance=instance)
            else:
                new_action.form = self.form(data=data, files=files, prefix=prefix)

        if new_action.form is not None:
            new_action.form_template = self.form_template
            if self.form_template:
                new_action.response_form_template = mark_safe(render_to_string(self.form_template, {'form': new_action.form, 'item': instance}))

        if instance:
            context = {'item': instance}
            context.update(instance.__dict__)
            if new_action.confirm: new_action.confirm = new_action.confirm % Resolver(context)
            if new_action.success: new_action.success = new_action.success % Resolver(context)
            if new_action.verbose_name: new_action.verbose_name = new_action.verbose_name % Resolver(context)

        return new_action

    def get_success_message(self):
        return self.success or _(u'Successfully executed "%s"') % self.verbose_name

    def get_form_instance(self, instance, *args, **kwargs):
        if not instance:
            return None
        if self.form and not issubclass(self.form, forms.ModelForm):
            return None

        if 'param' in kwargs and not kwargs['param']:
            kwargs.pop('param')

        if self.form_instance:
            return self.form_instance(instance, *args, **kwargs) \
                if callable(self.form_instance) \
                else self.form_instance
        return instance

    def get_bound_form(self, request, instance, prefix):
        if self.form is None:
            return None
        kwargs = {}
        instance = self.get_form_instance(instance)
        if instance:
            kwargs['instance'] = instance
        if request.method == 'GET':
            return self.form(request.GET, prefix=prefix, **kwargs)
        return self.form(request.POST, request.FILES, prefix=prefix, **kwargs)

    def render_form(self, request, instance, form):
        if self.form_template:
            return render_to_string(self.form_template,
                                    {'form': form, 'item': instance},
                                    context_instance=RequestContext(request))
        return six.text_type(form)


    @property
    def form_is_simple(self):
        return self.form is not None and not issubclass(self.form, forms.ModelForm)

    @property
    def suitable_for_multiple(self):
        return not self.hidden and self.multiple_display and (not self.form or self.form_is_simple)

    @property
    def render_multiple_form(self):
        if not self.form_is_simple:
            return

        bound_form = self.form(prefix='{}_multiple'.format(self.method))

        if self.form_template:
            return render_to_string(self.form_template, {'form': bound_form})
        return six.text_type(bound_form.as_p())

    @property
    def is_regular_view(self):
        return self.regular_view or self.method.endswith('_view')

    def is_allowed(self, request):
        return not self.permission or request.user.has_perm(self.permission)

    def __call__(self, function=None):
        """
        Allows this action to be used as a decorator. Example::

            class MyReport(AdvancedReport):
                model = User

                @action('Edit user', form=UserForm)
                def edit(self, user, form):
                    form.save()
        """

        # This dark magic is needed for Django's dirty template code.
        if function is None:
            return self

        # Now that we are using a new style of calling this action, we can safely use
        # a new set of defaults :-)
        if self.form:
            if not 'form_via_ajax' in self.attrs_dict:
                self.form_via_ajax = True
                self.attrs_dict['form_via_ajax'] = True
        self.is_new_style = True
        self.attrs_dict['is_new_style'] = True

        self.method = function.__name__
        self.attrs_dict['method'] = self.method

        @six.wraps(function)
        def decorator(*args, **kwargs):
            return function(*args, **kwargs)
        decorator.action = self
        return decorator


class ActionException:
    def __init__(self, msg=None, form=None):
        if form is not None:
            msg = u''
            for k in form.errors.keys():
                for e in form.errors[k]:
                    msg += u' ' + e
            self.msg = msg
        else:
            self.msg = u'%s' % msg


class AdvancedReport(object):
    #: Required. A unique url-friendly name for your Advanced Report
    slug = AutoSlug(remove_suffix='Report')

    #: The request. A new ``AdvancedReport`` instance is created on each request. This request will be saved to this
    #: property, so you can access it anywhere you need it.
    request = None

    #: Optional when ``model`` or ``models`` is specified. A list of fields that must be displayed on the report.
    fields = None

    #: A list of sortable fields.
    #: You can sort on multiple fields at the same time using the comma (,) separator.
    #: The __ lookup syntax is also supported.
    sortable_fields = None

    #: A list of fields that are searchable. When specified or inferred from a given model
    search_fields = None

    #: A list of fields that can be filtered.
    filter_fields = ()

    #: Optional. A dictionary with fields that will be shown as tabs. 1st dict field has to be the field to filter on.
    #: 2nd dict field is a dict with options:
    #:     - ``types``: types to filter on.
    #:     - ``images`` (optional): `default` will be used for all other fields, use same name as defined in `types` to
    #:        provide a `type` specific image.
    tabbed_filter_fields = ()

    #: Optional.
    # A list of fields for which all values will be shown, so that the user can choose to hide or select all records
    # with that value for field.
    # E.g. if I have a field X and it has values A and B, 'X' should be added to 'value_selection_filter_fields'.
    # The user will have the option to show only records with value 'A' or only records with value 'B', none or both.
    # Typically this will be rendered as checkbuttons or something similar
    value_selection_filter_fields = ()

    #: Optional. A mapping of filter fields to their list of values.
    filter_values = {}

    #: Deprecated. A tuple of available actions for your report. Please use the actions as a decorator instead.
    item_actions = ()

    #: Required if no model specified. A name for an individual item. For example ``_('user')``
    verbose_name = None

    #: Required if no model specified. A plural name for individual items. For example ``_('users')``
    verbose_name_plural = None

    #: Required if no model specified. The human-friendly title of your report.
    title = None

    #: Optional. Some text to explain the purpose of the report and some extra info.
    help_text = None

    #: Optional, but strongly advised to use it. A model class. An ``AdvancedReport`` can infer a lot of stuff
    #: from your model, including but not limited to the field verbose names, sortable fields, ...
    #: This is a shortcut to the ``models`` attribute.
    model = None

    #: Optional, and not needed if ``model`` is specified. A tuple of model classes. See the documentation
    #: for the ``model`` attribute.
    models = None

    #: The maximum number of items shown on one page. When you have more than this number
    #: of items, your report will be paginated. By default this is 20.
    items_per_page = 20


    #: Optional. A tuple of link tuples. You can define some top level links for your report.
    #: A link tuple must contain two items, the name of the link and the href location.
    #: Optionally you can show some more information if you add a third item to the link tuple with
    #: a short explanation. This will be shown next or below the button, or a tooltip, as the templates can vary.
    #: Example::
    #:
    #:     links = (
    #:         (u'Print this page', 'javascript:printPage();', u'Click here to print this page'),
    #:         (u'Refresh', '.'),
    #:     )
    links = ()

    #: The default global template for rendering a report. This is only used when using the server-side
    #: Django view-based version.
    template = 'advanced_reports/default.html'

    #: The default item template. This template will be used to render an individual item.
    #: When an action performs an operation on a report item, this template will be used to re-render that
    #: particular item.
    item_template = 'advanced_reports/item_row.html'

    #: This template is used when you want your view-based report to be shown in the middle of an existing page.
    internal_template = ''

    #: Required when using get_decorator. True indicates that Advanced Reports should use the implementation
    #: of the ``get_decorator`` method.
    decorate_views = False

    #: Optional. Puts checkboxes before each item and puts a combobox with group actions on your report.
    #: Only simple (as in, not using a form) actions can be performed on multiple items.
    #:
    #: You can implement your own special action method for multiple items. See the documenation for
    #: FOO_multiple below.
    multiple_actions = False

    #: Optional. Use this if you have a custom urlname for your report. Advanced Reports then knows how to
    #: reach your report.
    urlname = None

    #: Optional. If a date field name is assigned to this, you can filter on date ranges.
    date_range = None

    #: Optional. True allows animation, but that does not work with table rows.
    animation = False

    #: Optional. The text displayed when no items are shown on your report. By default this is:
    #: There are no <verbose_name_plural> to display.
    empty_text = None

    #: Controls the visibility of the table header.
    header_visible = True

    #: Controls the visibility of the report header
    report_header_visible = True

    #: Shows the separator between actions.
    show_actions_separator = True

    #: How to display the actions.
    action_list_type = ActionType.LINKS

    #: Show the actions of an item only when the user hovers over the item.
    #: This only works when your template or report rendering implementation knows about this attribute.
    show_actions_only_on_hover = True

    #: Determines if the advanced report should display a only single items. Used when you want to display
    #: to report in an other template
    internal_mode = False

    #: Whether the report should be rendered in a more compact way. This controls for example
    #: if the rows are rendered using <tbody> with two rows or just normal direct <tr> tags.
    #: Also the show details / hide details link will disappear.
    compact = False

    #: Shows an optional row limit selection box
    show_row_limit_selection = False


    def __init__(self, *args, **kwargs):
        self.model_admin = None

        # Expand some shortcuts
        if not self.models and self.model:
            self.models = (self.model,)

        # Add defaults from the model meta
        if self.models:
            model = self.models[0]
            if not self.verbose_name:
                self.verbose_name = model._meta.verbose_name
            if not self.verbose_name_plural:
                self.verbose_name_plural = model._meta.verbose_name_plural
            if not self.title:
                self.title = capfirst(self.verbose_name_plural)

            # Add defaults from the model admin
            model_admin = admin.site._registry.get(model)

            if model_admin:
                self.model_admin = model_admin

                if self.fields is None and model_admin.list_display:
                    self.fields = model_admin.list_display

                if self.search_fields is None and model_admin.search_fields:
                    self.search_fields = model_admin.search_fields

                if self.sortable_fields is None and model_admin.list_display:
                    self.sortable_fields = model_admin.list_display

        # Some sane defaults
        if not self.fields:
            self.fields = ()
        if not self.search_fields:
            self.search_fields = ()
        if not self.sortable_fields:
            self.sortable_fields = ()

        # Expand item_actions with the decorated versions
        item_actions = list(self.item_actions)
        for method_name in dir(self):
            if not hasattr(AdvancedReport, method_name):
                method = getattr(self, method_name)

                if callable(method) and hasattr(method, 'action'):
                    item_actions.append(method.action)

        item_actions.sort(key=lambda a: a.creation_counter)
        self.item_actions = item_actions

    def queryset(self):
        """
        The primary source of the data you will want to manage.
        """
        if self.models:
            return self.models[0].objects.all()
        return None

    def get_FOO_verbose_name(self):
        '''
        Implement this function to specify the column header for the field FOO.
        '''
        return None

    def get_FOO_html(self):
        '''
        Implement this function to specify the HTML representation for the field FOO.
        '''
        return None

    def get_FOO_decorator(self):
        '''
        Implement this function to specify a decorator function for the field FOO.
        Return a function that accepts one parameter and returns the decorated html.
        '''
        return lambda s: s

    def filter_FOO(self, qs, value):
        """
        Implement this function to specify a filter for the field FOO. This is
        useful for fields that are not a part of a model, but aggregated.

        :return: a filtered queryset
        """
        return qs

    def verify_action_group(self, item, group):
        '''
        Implement this function to verify if the given group currently applies to the given item.

        For example, if the item is a paid purchase and the group is "paid", we must return True.
        To turn of filtering of actions by groups, just don't specify the group when creating an
        action and just leave this function alone.
        '''
        return True

    def set_request(self, request):
        '''
        Set the request for this report.
        '''
        self.request = request

    #
    # The following two functions work both in tandem for naming and finding items.
    # It is recommended to override get_item_for_id as the default implementation may be a little
    # bit inefficient.
    #

    def get_item_id(self, item):
        '''
        Advanced Reports expects each item to have a unique ID. By default this is the primary key
        of a model instance, but this can be anything you want, as long it is a unicode string.
        '''
        return unicode(item.pk)

    def get_item_for_id(self, item_id):
        '''
        Advanced Reports also expects each item to be found by its unique ID. By default it does
        a lookup of the primary key of a model.

        Returns None if the item does not exist.
        '''
        try:
            return self._queryset(request=None).get(pk=item_id)
        except ObjectDoesNotExist, e:
            return None

    def get_decorator(self):
        '''
        To be used in tandem with decorate_views. Set it to True when you want to implement this function.
        Here you can return a decorator. That decorator will be used to decorate the Advanced Report views.
        This way you can easily add some permission restrictions to your reports.
        '''
        return None

    def FOO(self, item, form=None):
        '''
        The implementation of the FOO action method.
        '''

    def FOO_view(self, item, form=None):
        '''
        The implementation of the FOO action method that can return a HttpResponse
        '''

    def FOO_multiple(self, items):
        '''
        The implementation of the FOO action method with multiple items.
        This may return a HttpResponse object or just None.
        '''
        return None

    def get_FOO_form(self, item, prefix, data=None):
        """
        Instead of specifying the ``form`` attribute for an action, you can also construct your
        action form instance dynamically by implementing this method in your report.
        :param item: the item for which to construct the action form
        :param prefix: the prefix that the form should use
        :param data: the data that should be passed to the form for validation
        :return: a form instance
        """
        return None

    def get_item_class(self, item):
        '''
        Implement this to get some extra CSS classes for the item. Separate them with spaces.
        '''
        return u''

    def get_FOO_class(self, item):
        '''
        Implement this to get some extra CSS classes for the field FOO. Separate them with spaces.
        '''
        return u''

    def get_extra_information(self, item):
        '''
        Implement this to get some extra information about an item.
        This will be shown right below a data row and above the actions.

        Ajax loading of information

        You can specify some "lazy divs" that are only loaded when an action row expands.
        You must define a hidden item action with a method name that ends with '_view'.

        Example::

            def get_extra_information(self, item):
                return u'<div class="lazy" data-method="credit_view"></div>'

            item_actions = (
                action(method='credit_view', verbose_name=u'', group='mygroup', hidden=True),
            )

            def credit_view(self, item):
                balance = get_credit_balance(item)
                return render_to_response('credit_template.html', {'balance': balance})

        '''
        return u''

    def get_FOO_style(self):
        '''
        Implement this to apply some CSS to the FOO td table cell.
        For example, you can define a fixed width here.
        '''
        return u''

    def report_action_allowed(self, action):
        """
        Implement this to control whether a report action (global action) should be shown.
        """
        return True

    def auto_complete(self, request, partial, params):
        """
        Implement this to support auto completion of certain fields.

        :param request: the HTTPRequest asking for the completion
        :param partial: the partial string that must be completed
        :param params: optional parameters
        :return: a list of possible completions. Keep this list short, all data returned will be displayed.
        """
        return []

    def enrich_list(self, items):
        '''
        Implement this to attach some extra information to each item of the given items list.

        Use self.assign_attr(item, attr_name, value) to do that, it automatically detects dicts.

        Example usage: adding state information to each item to prevent multiple queries to the State model.
        '''
        pass

    def get_item_count(self):
        '''
        Implement this if you don't use Django model instances.
        Returns the number of items in the report.
        '''
        return self._queryset(request=None).count()

    def get_template(self):
        '''
        Get the template that needs to be rendered
        '''
        if self.internal_mode:
            if self.internal_template:
                return self.internal_template
            else:
                return self.template.replace('.html', '_internal.html')
        else:
            return self.template

    def _extra_context(self, request=None):
        context = {}
        context.update(self.extra_context_request(request))
        context.update(self.extra_context())
        return context

    def extra_context(self):
        '''
        (deprecated) Implement this to define some extra context for your template.
        '''
        return {}

    def extra_context_request(self, request=None):
        '''
        Implement this to define some extra context for your template,
        based on the request.
        '''
        filter_form = self.get_filter_form()
        if filter_form is not None:
            filter_form = filter_form(request.GET or None)
        return {
            'filters_form': filter_form,
            'tabbed_filters_links': self.get_tabbed_filter_links(),
        }

    def _create_choicefield(self, choices, add_empty=False):
        if add_empty and len(choices) and choices[0][0] != '':
            choices = [('', '---')] + list(choices)
        return forms.ChoiceField(choices=choices)

    def get_filter_form(self):
        """
        Ugly way to generate generic form for filters- but I can't see better idea, how to do this
        """
        if not self.models:
            return None
        all_model_fields = {}
        for model in self.models:
            all_model_fields.update(fields_for_model(model))
        report = self
        class DynamicForm(forms.Form):
            def __init__(self, *args, **kwargs):
                super(DynamicForm, self).__init__(*args, **kwargs)
                for filter_field in report.filter_fields:
                    field_fn = getattr(self, 'get_%s_filter' % filter_field, None)
                    if field_fn is not None:
                        self.fields[filter_field] = field_fn()
                    elif filter_field in report.filter_values:
                        self.fields[filter_field] = report._create_choicefield(report.filter_values[filter_field], True)
                    elif filter_field in all_model_fields:
                        self.fields[filter_field] = report._create_choicefield(all_model_fields[filter_field].choices, True)
                    else:
                        raise ValueError("We can't get choices for %s filter" % filter_field)
        return DynamicForm

    def get_tabbed_filter_links(self):
        """
        Example::

            configured in report:

                tabbed_filter_fields = (
                    {
                        'card': {
                            'images': {
                                'default': 'default.png',
                                '2FF': '2ff-image.img',
                            },
                            'types': [
                                '2FF', '2FF/3FF', '2/3/4FF', '4FF'
                            ]
                        }
                    })

            will result in (keys are slugified, so 2FF/3FF will be 2ff3ff):

                [
                    'card': [
                        {'2FF': '2ff-image.png'},
                        {'2FF/3FF', 'default.png'},
                    ],
                ]

        :return: a dict for links with optional images.
        """
        report = self
        result = OrderedDict()
        for filter_field in report.tabbed_filter_fields:
            options = report.tabbed_filter_fields[filter_field]
            if not options or options == {} or 'types' not in options:
                raise Exception('Cannot construct tabbed filter fields!')

            values = OrderedDict()
            for field_type in options['types']:
                if 'images' in options:
                    if field_type in options['images']:
                        values[field_type] = options['images'][field_type]
                    elif 'default' in options['images'].keys():
                        values[field_type] = options['images']['default']
                    else:
                        values[field_type] = None
                else:
                    values[field_type] = None
            result[filter_field] = values.items()
        return result.iteritems()

    def get_filters_from_request(self, request):
        """
        Return a dict used as argument to Model.objects.filter() function.
        But we need to be sure that we can filter on these fields so we check if there is no filter_* function defined
        in advanced report definition
        """
        # WSGIRequest.REQUEST (a merge of POST and GET) is no longer available as of Django 1.9
        request_querydict = request.POST if request.method == 'POST' else request.GET
        result = {}

        for filter_field in self.filter_fields:
            if filter_field in request_querydict and request_querydict[filter_field].strip() and \
                    not hasattr(self, 'filter_%s' % filter_field):
                result[filter_field] = request_querydict[filter_field]

        return result

    def get_filtered_items(self, queryset, params, request=None):
        filter_query = None
        date_range_query = None
        fake_fields = []
        uses_model = None

        # Extract parameters
        q = params['q'].lower() if 'q' in params else None
        exact = 'exact' in params
        filters_from_request = self.get_filters_from_request(request)

        if hasattr(queryset, 'filter') and filters_from_request:
            queryset = queryset.filter(**filters_from_request)

        if params.get('from', '') or params.get('to', ''):
            date_range_query = Q()

            if params.get('from', ''):
                from_date_struct = time.strptime(params['from'], '%Y-%m-%d')
                from_date = datetime.datetime(year=from_date_struct.tm_year,
                                              month=from_date_struct.tm_mon,
                                              day=from_date_struct.tm_mday)
            if params.get('to', ''):
                to_date_struct = time.strptime(params['to'], '%Y-%m-%d')
                to_date = datetime.datetime(year=to_date_struct.tm_year,
                                            month=to_date_struct.tm_mon,
                                            day=to_date_struct.tm_mday)
                # Date range has no hour so we add 1 day to the to_date so that we get the results of that day as well
                # eg: if we selected from: 2011-01-17 and to: 2011-01-18, then the actual date range will be:
                # between 2011-01-17 00:00 and 2011-01-19 00:00
                to_date += datetime.timedelta(days=1)

            uses_model = False

            field = self.get_model_field(self.date_range.split('__')[0])

            if field is None:
                fake_fields.append(self.date_range)
            else:
                uses_model = True

        if uses_model:
            if params.get('from', '') and params.get('to', ''):
                date_range_query = Q(**{'%s__range' % self.date_range: (from_date, to_date)})

                queryset = queryset.filter(date_range_query)
            elif params.get('from', ''):
                queryset = queryset.filter(Q(**{'%s__gte' % self.date_range: from_date}))
            elif params.get('to', ''):
                queryset = queryset.filter(Q(**{'%s__lt' % self.date_range: to_date}))

        if q:
            if uses_model is None:
                uses_model = False

            parts = q.split()
            filter_query = Q()
            for part in parts:
                part_query = Q()
                for search_field in self.search_fields:

                    field = self.get_model_field(search_field.split('__')[0])
                    if field is None:
                        fake_fields.append(search_field)
                    else:
                        uses_model = True
                        if ',' in part:
                            part_query = part_query | Q(**{'%s__in' % search_field: part.split(',')})
                        elif exact:
                            part_query = part_query | Q(**{'%s__iexact' % search_field: part})
                        else:
                            part_query = part_query | Q(**{'%s__icontains' % search_field: part})
                filter_query = filter_query & part_query


        fake_found = []
        if len(fake_fields) > 0:
            self.enrich_list(queryset)
            for fake_field in fake_fields:
                for o in queryset:
                    test_string = strip_tags(self.get_item_html(fake_field, o)).lower().replace(u'&nbsp;', u' ')
                    if q == test_string if exact else q in test_string:
                        fake_found.append(int(o.pk) if uses_model else o)

        if uses_model or uses_model is None:
            # uses_model is None when none of the search parameters were found
            if fake_found:
                if filter_query:
                    filter_query = filter_query | Q(pk__in=fake_found)
                else:
                    filter_query = Q(pk__in=fake_found)

            if filter_query:
                return EnrichedQueryset(queryset.filter(filter_query), self, request=request)
            else:
                # When no filter parameter is found then we don't apply the filter_query
                return EnrichedQueryset(queryset, self, request=request)
        else:
            return EnrichedQueryset(fake_found, self, request=request)

    def _queryset(self, request):
        if hasattr(self, 'queryset_request'):
            qs = self.queryset_request(request)
            if request:
                def convert_value(k, v):
                    if k[-4:] == '__in':
                        return v.split(',')
                    if v.lower() == u'true':
                        return True
                    elif v.lower() == u'false':
                        return False
                    else:
                        return v

                if self.models:
                    fieldnames = [f.name for f in self.models[0]._meta.fields]
                    lookup = dict((k, convert_value(k, v)) for k, v in request.GET.items() if v and k.split('__')[0] in fieldnames)

                    lookup_id = lookup.get('id')
                    if lookup_id and not lookup_id.isdigit():
                        raise Http404

                    if lookup:
                        qs = qs.filter(**lookup)

                    for k, v in request.GET.items():
                        filter_fn = getattr(self, 'filter_%s' % k, None)
                        if filter_fn and v:
                            qs = filter_fn(qs, convert_value(k, v))

            return qs
        else:
            return self.queryset()

    def get_sorted_queryset(self, by_field, request=None):
        if by_field not in ('__str__', '__unicode__'):
            field_name = by_field.split('__')[0].split(',')[0]
            field_name = field_name[1:] if field_name[0] == '-' else field_name
        else:
            field_name = 'pk'
        if self.get_model_field(field_name) is None:
            return self._queryset(request)
        return self._queryset(request).order_by(*by_field.split(','))

    def get_enriched_items(self, queryset):
        return EnrichedQueryset(queryset, self)

    def get_object_list(self, request, ids=None):
        """Returns all the objects in the report.

        A second return value is extra context for rendering the template."""

        def _apply_value_selection_filter_fields(queryset):
            """Does the necessary changes to queryset and context for value_selection_filter_fields.

            Does this by returning a new queryset and a context that can be used to update the existing context
            @return: (new_queryset, new_context)
                     'new_queryset' has the objects removed that should not be seen.
                     'new_context' the values that should be added to the context.
                                   it will contain one entry with key 'value_selection_filter_fields'.
                                   an example describes best what it will contain:
                                   {
                                       'value_selection_filter_fields: {
                                           'field1': {
                                               'verbose_name': 'Field1_user_friendly_name',
                                               'values': [
                                                   {
                                                       'verbose_name': 'valueA',
                                                       'url_to_toggle': <the url to follow to bring you to the page with the toggled content>
                                                       'active': 'False'

            @param(queryset): the queryset of objects that need to be returned. Is needed for two purposes:
                              - to check which values exist for a certain field so we can present them for show or hide.
                              - to filter out the objects that should not be shown.
            """
            if self.value_selection_filter_fields:
                # Filtering on value_selection_filter_fields can only happen after we know the objects
                # since the possible values of the fields are the actual values of the objects
                tmp_object_list = self.get_filtered_items(queryset, request.GET, request=request)

                context_value = {}
                for value_selection_filter_field in self.value_selection_filter_fields:
                    context_value[value_selection_filter_field] \
                        = {'verbose_name': self.get_field_metadata(value_selection_filter_field)['verbose_name'],
                           'values': []}

                    available_values = set()
                    for obj in tmp_object_list:
                        value = getattr(obj, value_selection_filter_field)
                        verbose_value = self.get_item_html(value_selection_filter_field, obj)
                        available_values.add((value, verbose_value))

                    values_to_show = []
                    for available_value, verbose_available_value in available_values:
                        value_key = 'value_selection_filter_field_{}_{}'.format(value_selection_filter_field,
                                                                                available_value)

                        url_parameters_for_the_toggle_link = request.GET.copy()
                        url_parameters_for_the_toggle_link[value_key] \
                            = 'hide' if request.GET.get(value_key, 'show') != 'hide' else 'show'

                        show_value = False
                        if request.GET.get(value_key, 'show') != 'hide':
                            values_to_show.append(available_value)
                            show_value = True

                        context_value[value_selection_filter_field]['values'] \
                            .append({'verbose_name': verbose_available_value,
                                     'url_to_toggle': urllib.urlencode(url_parameters_for_the_toggle_link),
                                     'active': show_value})

                    queryset = queryset.filter(**{'{}__in'.format(value_selection_filter_field): values_to_show})

                return queryset, {'value_selection_filter_fields': context_value}

            return queryset, {}

        default_order_by = ''.join(self.sortable_fields[:1])
        order_by = request.GET.get('order', default_order_by)
        context = {}
        if order_by:
            order_field = order_by.split('__')[0].split(',')[0].strip('-')
            ascending = order_by[:1] != '-'
            context.update({'order_field': order_field,
                            'ascending': ascending,
                            'order_by': order_by.strip('-'),
                            'ordered_by': self.get_ordered_by(order_by)})
            queryset = self.get_sorted_queryset(order_by, request=request)
        else:
            queryset = self._queryset(request)

        # Filter
        if ids is not None:
            queryset = queryset.filter(pk__in=ids)

        queryset, new_context = _apply_value_selection_filter_fields(queryset)
        context.update(new_context)

        object_list = self.get_filtered_items(queryset, request.GET, request=request)

        return object_list, context

    def get_ordered_by(self, by_field):
        if by_field == '':
            return u''
        field_names = (part.strip('-') for part in by_field.split(','))
        verbose_names = (self.get_field_metadata(field_name)['verbose_name'] for field_name in field_names)
        return u', '.join(verbose_names)

    def get_action_callable(self, method):
        return getattr(self, method, lambda i, f=None: False)

    def handle_multiple_actions(self, method, selected_object_ids, request=None):
        # Lookup the action
        action = self.find_action(method)
        if action is None:
            raise Http404

        # Construct enriched list of objects
        objects = [o for o in (self.get_item_for_id(item_id) for item_id in selected_object_ids) if o]
        self.enrich_list(objects)
        objects = [object for object in objects if self.verify_action_group(object, action.group)]
        for o in objects:
            self.enrich_object(o, list=False, request=request)

        # Check if there is a FOO_multiple callable on this report
        multiple_callable = getattr(self, '%s_multiple' % method, None)

        # If we are dealing with forms, add an extra argument to the handler
        extra_args = []
        if action.form:
            bound_form = action.form(prefix='{}_multiple'.format(method), data=request.POST, files=request.FILES)
            if not bound_form.is_valid():
                messages.error(
                    request,
                    u'{} {}'.format(
                        _('The submitted form was not valid, so no action was taken.'),
                        u', '.join(u'{}: {}'.format(field, error)
                                   for field, errors in bound_form.errors.items()
                                   for error in errors)
                    )
                )
                return None, 0
            extra_args.append(bound_form)

        if multiple_callable is not None:
            if len(objects) == 0:
                return None, 0
            return multiple_callable(objects, *extra_args), len(objects)

        count = 0
        self.enrich_list(objects)
        for object in objects:
            self.enrich_object(object, list=False, request=request)
            if self.find_object_action(object, method) is not None:
                self.get_action_callable(method)(object, *extra_args)
                count += 1

        return None, count

    @property
    def column_headers(self):
        return [self.get_field_metadata(field_name) for field_name in self.fields]

    @property
    def searchable_columns(self):
        if not self.search_fields:
            return None
        field_names = (s.rsplit('__', 1)[-1] for s in self.search_fields)
        field_names = u', '.join(self.get_field_metadata(field_name)['verbose_name'] for field_name in field_names)
        return _(u'You can search by %(fields)s') % {'fields': field_names}

    def get_column_values(self, item):
        for field_name in self.fields:
            yield {'html': self.get_item_html(field_name, item),
                   'class': getattr(self, 'get_%s_class' % field_name, lambda i: u'')(item),
                   'style': getattr(self, 'get_%s_style' % field_name, lambda: None)()}

    def get_model_field(self, field_name):
        if self.models is None:
            return None

        for model in self.models:
            try:
                return model._meta.get_field_by_name(field_name)[0]
            except:
                pass
        return None

    def get_field_metadata_dict(self):
        all_fields = list(self.fields) + list(self.filter_fields)
        return dict((field, self.get_field_metadata(field)) for field in all_fields)

    def get_field_metadata(self, field_name):
        verbose_name = getattr(self, 'get_%s_verbose_name' % field_name, lambda: None)()
        if verbose_name is None:
            model_field = self.get_model_field(field_name)
            if model_field is not None:
                verbose_name = model_field.verbose_name

        if verbose_name is None:
            verbose_name = capfirst(field_name.replace(u'_', u' '))

        sortable = False
        order_by = ''
        for sf in self.sortable_fields:
            fn = sf.split('__')[0].split(',')[0].strip('-')
            if fn == field_name.split('__')[0]:
                sortable = True
                order_by = sf.strip('-')

        return {'name': field_name.split('__')[0],
                'full_name': field_name,
                'verbose_name': capfirst(verbose_name),
                'sortable': sortable,
                'order_by': order_by,
                'style': getattr(self, 'get_%s_style' % field_name, lambda: None)()}

    def lookup_item_value(self, field_name, item):
        if '__' in field_name:
            field_name, remainder = field_name.split('__', 1)
            obj = getattr(item, field_name, None)
            return self.lookup_item_value(remainder, obj)
        else:
            html = getattr(item, 'get_%s_display' % field_name, lambda: None)()
            if html is None:
                html = getattr(item, field_name, None)
        return html

    def get_html_for_value(self, value):
        """
        Override this method to generate HTML for specific values.
        """
        return escape(six.text_type(value))

    def get_item_html(self, field_name, item):
        html = getattr(self, 'get_%s_html' % field_name, lambda i: None)(item)
        if html is None:
            html = self.get_html_for_value(self.lookup_item_value(field_name, item))

        decorator = getattr(self, 'get_%s_decorator' % field_name, lambda i: None)(item)
        if decorator is not None:
            html = decorator(html)

        return mark_safe(html)

    def objects(self, request=None):
        return EnrichedQueryset(self._queryset(request), self)

    def enrich_object(self, o, list=True, request=None):
        '''
        This method adds extra metadata to an item.
        When the list argument is True, enrich_list will be called on the item.
        When calling this method multiple times, it is inefficient to call enrich_list,
        as it can be run once on the whole list, so in this case set list to False.
        If supplied, the request will be attached to the item so that you can use this
        in your actions.
        '''
        if not o:
            return

        if list:
            self.enrich_list([o])

        self.assign_attr(o, 'advreport_request', request)
        self.assign_attr(o, 'advreport_column_values', [v for v in self.get_column_values(o)])
        self.assign_attr(o, 'advreport_actions', self.get_object_actions(o, request=request))
        self.assign_attr(o, 'advreport_object_id', self.get_item_id(o))
        self.assign_attr(o, 'advreport_class', self.get_item_class(o))
        self.assign_attr(o, 'advreport_extra_information', self.get_extra_information(o) % Resolver({'item': o}))

    def enrich_generic_relation(self, items, our_model, foreign_model, attr_name, fallback):
        '''
        This is a utility method that can be used to prefetch backwards generic foreign key relations.
        Use this if you have a lot of lookups of this kind when generating the report.

        Parameters:
            - items: a iterable of items where we want to attach the backwards relation object.
            - our_model: the type of items where the generic foreign key points to.
            - foreign_model: the type of items that have a generic foreign relation to our_model.
            - attr_name: specifies name of the attribute that will contain an instance of foreign_model.
            - fallback: a function that will be called when the backwards relation was not found.
              It must accept a our_model instance and must return a foreign_model instance.
        '''
        ct = ContentType.objects.get_for_model(our_model)
        pks = [item.pk for item in items]
        foreigns = foreign_model.objects.filter(content_type=ct, object_id__in=pks).select_related('content_type')
        foreign_mapping = {}
        for foreign in foreigns:
            foreign_mapping[int(foreign.object_id)] = foreign
        for item in items:
            setattr(item, attr_name, foreign_mapping.get(int(item.pk), None) or fallback(item))

    def enrich_backward_relation(self, items, foreign_model, field_name, related_name,
                                 our_index=None, our_foreign_index=None,
                                 select_related=None, many=True):
        '''
        This is a utility method that can be used to pretech backward relations.
        For instance, you can add subscription lists to each user using only one line of code.

        Parameters:
            - items: a iterable of items where we want to attach the backwards relation object.
            - foreign_model: the type of items that have a foreign relation to our_model.
            - field_name: the field name of foreign_model that points to our_model.
            - related_name: specifies name of the attribute that will contain (a list of)
              instances of foreign_model.
            - our_index: a callable that gets the id of an instance of our_model.
            - our_foreign_index: a callable that gets the id of our instance from foreign_model.
            - select_related: performs a select_related on the query on foreign_model.
            - many: if set to False, a single item will be assigned instead of a list. When
              the list is empty, None will be assigned.
        '''

        our_index = our_index or (lambda i: i.pk)
        oi = lambda i: int(our_index(i)) if our_index(i) is not None else None
        our_foreign_index = our_foreign_index or (lambda i: getattr(i, '%s_id' % field_name))
        ofi = lambda i: int(our_foreign_index(i)) if our_foreign_index(i) is not None else None

        pks = [oi(item) for item in items]
        foreigns = foreign_model.objects.filter(**{'%s__in' % field_name: pks})
        if select_related:
            foreigns = foreigns.select_related(*select_related)

        foreign_mapping = {}

        for foreign in foreigns:
            our_id = ofi(foreign)
            if our_id in foreign_mapping:
                foreign_mapping[our_id].append(foreign)
            else:
                foreign_mapping[our_id] = [foreign]

        if many:
            for item in items:
                setattr(item, related_name, foreign_mapping.get(oi(item), ()))
        else:
            for item in items:
                setattr(item, related_name, foreign_mapping.get(oi(item), (None,))[0])

    def get_object_actions(self, object, request=None):
        actions = []

        for a in self.item_actions:
            if self.verify_action_group(object, a.group) and \
                    (not request or a.is_allowed(request)):
                instance = a.form_instance(object) if a.form_instance else object
                if not a.form_via_ajax or a.prefetch_ajax_form:
                    new_action = a.copy_with_instanced_form(self, prefix=self.get_item_id(object), instance=instance)
                else:
                    # Put off fetching the instanced Form until the actual Ajax
                    # call for performance.
                    new_action = a
                if not new_action.hidden and new_action.individual_display:
                    actions.append(new_action)

        return actions

    def find_object_action(self, object, method, request=None):
        found_action = None
        for a in self.item_actions:
            if object is None or self.verify_action_group(object, a.group):
                if a.method == method:
                    found_action = a
                    break

        if request is not None:
            if found_action is None:
                raise Http404(_(u'Unsupported action method "%s".' % method))
            if not found_action.is_allowed(request):
                raise Http404(_(u'You\'re not allowed to execute "%s".' % method))

        return found_action

    def find_action(self, method):
        for a in self.item_actions:
            if a.method == method:
                return a
        return None

    @property
    def date_range_verbose_name(self):
        if not self.date_range:
            return u''
        return self.get_field_metadata(self.date_range)['verbose_name']

    def get_empty_text(self):
        if self.empty_text:
            return self.empty_text
        return _(u'There are no %(items)s to display.') % {'items': self.verbose_name_plural}

    def assign_attr(self, object, attr_name, value):
        '''
        Assigns a value to an attribute. When the given object is a dict, the value will be assigned
        as a key-value pair.
        '''
        if isinstance(object, dict):
            object[attr_name] = value
        else:
            setattr(object, attr_name, value)

    def urlize(self, urlname, kwargs):
        return lambda h: u'<a href="%(l)s">%(h)s</a>' % {'l': reverse(urlname, kwargs=kwargs), 'h': h}


class EnrichedQueryset(object):
    def __init__(self, queryset, advreport, request=None):
        self.queryset = queryset
        if isinstance(self.queryset, QuerySet):
            self.queryset.query.add_ordering('pk')
        self.advreport = advreport
        self.request = request

    def __getitem__(self, k):
        if isinstance(k, slice):
            return self._enrich_list(list(self.queryset[k.start:k.stop]))
        else:
            return self._enrich(self.queryset[k])

    def __iter__(self):
        return self.queryset.__iter__()

    def __len__(self):
        if isinstance(self.queryset, QuerySet):
            return self.queryset.count()
        return len(self.queryset)

    def iterator(self):
        if isinstance(self.queryset, QuerySet):
            it = self.queryset.iterator()
        else:
            it = self.queryset
        for i in it:
            self._enrich(i)
            yield i

    def _enrich_list(self, l):
        # We run enrich_list on all items in one pass.
        self.advreport.enrich_list(l)

        for o in l:
            # We pass list=False to prevent running enrich_list from enrich_object.
            self.advreport.enrich_object(o, list=False, request=self.request)

        return l

    def _enrich(self, o):
        self.advreport.enrich_object(o, self.request)
        return o


class Resolver(object):
    def __init__(self, context):
        self.context = context

    def __getitem__(self, k):
        from django.template import Variable
        return Variable(k).resolve(self.context)


class BootstrapReport(AdvancedReport):
    template = 'advanced_reports/bootstrap/report.html'
    item_template = 'advanced_reports/bootstrap/item.html'
