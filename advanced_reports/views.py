# -*- coding: utf-8 -*-
from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, StreamingHttpResponse
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.utils.html import strip_entities, strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
import itertools

import six

from .backoffice.api_utils import JSONResponse
from .decorators import conditional_delegation, report_view
from .defaults import ActionException, Resolver
from .utils import paginate

def _get_redirect(advreport, next=None, querystring=None):
    if next:
        return redirect(next)
    if advreport.urlname:
        return redirect(reverse(advreport.urlname))
    suffix = u''
    if querystring:
        suffix = u'?%s' % querystring
    return redirect(reverse('advanced_reports_list', kwargs={'slug': advreport.slug}) + suffix)


@conditional_delegation(lambda request: 'delegate' in request.GET)
@report_view
def list(request, advreport, ids=None, internal_mode=False, report_header_visible=True):
    advreport.internal_mode = internal_mode
    advreport.report_header_visible = report_header_visible

    context = {}

    # Handle POST
    if request.method == 'POST':
        sorted_keys = [k for k in request.POST.keys()]
        sorted_keys.sort()
        selected_object_ids = [k.split('_')[2] for k in sorted_keys if 'checkbox_' in k and 'true' in request.POST.getlist(k)]
        method = request.POST['method']

        if not method:
            messages.warning(request, _(u'You did not select any action.'))
            if not advreport.internal_mode:
                return _get_redirect(advreport)

        if len(selected_object_ids) == 0:
            messages.warning(request, _(u'You did not select any %(object)s.') % {'object': advreport.verbose_name})
            if not advreport.internal_mode:
                return _get_redirect(advreport)

        try:
            response, count = advreport.handle_multiple_actions(method, selected_object_ids, request)
            if response:
                return response

            if count > 0:
                messages.success(request, _(u'Successfully executed action on %(count)d %(objects)s')
                                                % {'count': count,
                                                   'objects': advreport.verbose_name_plural if count != 1 else advreport.verbose_name})
            else:
                messages.error(request, _(u'No selected %(object)s is applicable for this action.') % {'object': advreport.verbose_name})
            if not advreport.internal_mode:
                return _get_redirect(advreport, querystring=request.META['QUERY_STRING'])
        except ActionException, e:
            context.update({'error': e.msg})


    object_list, extra_context = advreport.get_object_list(request, ids=ids)
    context.update(extra_context)

    # CSV?
    if 'csv' in request.GET:
        try:
            from djprogress import with_progress # pragma: no cover
        except ImportError: # pragma: no cover
            with_progress = lambda it, **kw: it # pragma: no cover
        # Avoid microsoft SYLK problem http://support.microsoft.com/kb/215591
        _mark_safe = lambda s: s if unicode(s) != u'ID' else u'"%s"' % s
        object_count = len(object_list)
        #csv = StringIO()
        header = u'%s\n' % u';'.join(_mark_safe(c['verbose_name']) for c in advreport.column_headers)
        lines = (u'%s\n' % u';'.join((c['html'] for c in o.advreport_column_values)) \
                 for o in with_progress(object_list.iterator() \
                                            if hasattr(object_list, 'iterator') \
                                            else object_list[:],
                                        name='CSV export of %s' % advreport.slug,
                                        count=object_count))
        lines = (line.replace(u'&nbsp;', u' ') for line in lines)
        lines = (line.replace(u'&euro;', u'€') for line in lines)
        lines = (line.replace(u'<br/>', u' ') for line in lines)
        lines = (strip_entities(line) for line in lines)
        lines = (strip_tags(line).encode('utf-8') for line in lines)
        #csv.write(header)
        #csv.writelines(lines)
        response_content = itertools.chain([header], lines)

        # We use streaming http response because sometimes generation of each line takes some time and for big exports
        # it leads to timeout on the response generation
        response = StreamingHttpResponse(response_content, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % advreport.slug

        return response

    # Paginate
    paginated = paginate(request, object_list, advreport.items_per_page)

    # Extra context?
    context.update(advreport._extra_context(request))

    # Render
    context.update({'advreport': advreport,
                    'paginated': paginated,
                    'object_list': object_list})

    func = render_to_string if advreport.internal_mode else render_to_response
    return func(advreport.get_template(), context, context_instance=RequestContext(request))


@report_view
def action(request, advreport, method, object_id, param=None):
    next = request.GET.get('next', None)

    object = advreport.get_item_for_id(object_id)
    advreport.enrich_object(object, request=request)

    a = advreport.find_action(method)

    if a is None:
        raise Http404

    if request.method == 'POST':
        if a.form is not None:
            if issubclass(a.form, forms.ModelForm):
                form = a.form(request.POST, request.FILES, instance=a.get_form_instance(object), prefix=object_id)
            else:
                form = a.form(request.POST, request.FILES, prefix=object_id)

            if form.is_valid():
                r = advreport.get_action_callable(a.method)(object, form)
                # TODO: give feedback

                return r or _get_redirect(advreport, next)
    else:
        if param:
            r = advreport.get_action_callable(a.method)(object, param)
        else:
            r = advreport.get_action_callable(a.method)(object)
        # TODO: give feedback

        return r or _get_redirect(advreport, next)


@report_view
def ajax(request, advreport, method, object_id, param=None):
    object = advreport.get_item_for_id(object_id)
    advreport.enrich_object(object, request=request)
    a = advreport.find_object_action(object, method)
    if a is None:
        return HttpResponse(_(u'Unsupported action method "%s".' % method), status=404)

    context = {'advreport': advreport}

    try:
        if request.method == 'POST' and a.form is not None:
            if issubclass(a.form, forms.ModelForm):
                form = a.form(request.POST, request.FILES, instance=a.get_form_instance(object), prefix=object_id)
            else:
                form = a.form(request.POST, request.FILES, prefix=object_id)

            if form.is_valid():
                advreport.get_action_callable(a.method)(object, form)
                object = advreport.get_item_for_id(object_id)
                context.update({'success': a.get_success_message()})
            else:
                context.update({'response_method': method, 'response_form': form})
                if a.form_template:
                    context.update({'response_form_template': mark_safe(render_to_string(a.form_template, {'form': form}))})

            advreport.enrich_object(object, request=request)
            context.update({'object': object})
            return render_to_response(advreport.item_template, context, context_instance=RequestContext(request))

        elif a.form is None:
            if param:
                advreport.get_action_callable(a.method)(object, param)
            else:
                advreport.get_action_callable(a.method)(object)
            object = advreport.get_item_for_id(object_id)
            advreport.enrich_object(object, request=request)
            context = {'object': object, 'advreport': advreport, 'success': a.get_success_message()}
            context.update({'response_method': method, 'response_form': a.form})
            if a.form_template:
                context.update({'response_form_template': mark_safe(render_to_string(a.form_template, {'form': a.form}))})

            return render_to_response(advreport.item_template, context, context_instance=RequestContext(request))

    except ActionException, e:
        return HttpResponse(e.msg, status=404)

    # a.form is not None but not a POST request
    return HttpResponse(_(u'Unsupported request method.'), status=404)


@report_view
def count(request, advreport):
    return HttpResponse(unicode(advreport.get_item_count()))


@report_view
def ajax_form(request, advreport, method, object_id, param=None):
    object = advreport.get_item_for_id(object_id)
    advreport.enrich_object(object, request=request)
    a = advreport.find_object_action(object, method)
    if a is None:
        # No appropriate action found (maybe it was filtered out?)
        raise Http404

    context = {'advreport': advreport}

    if request.method == 'POST':
        a = a.copy_with_instanced_form(advreport,
                                       prefix=object_id,
                                       instance=a.get_form_instance(object, param=param),
                                       data=request.POST,
                                       files=request.FILES)
        form = a.form
        if form.is_valid():
            r = advreport.get_action_callable(a.method)(object, form)
            object = advreport.get_item_for_id(object_id)
            advreport.enrich_object(object, request=request)
            context.update({'success': a.get_success_message(), 'object': object, 'action': a})
            response = render_to_string(advreport.item_template, context, context_instance=RequestContext(request))
            return r or JSONResponse({
                'status': 'SUCCESS',
                'content': response
            })
        else:
            context.update({'response_method': method, 'response_form': form})
            if a.form_template:
                context.update({'response_form_template': mark_safe(render_to_string(a.form_template, {'form': form, 'item': object}))})

        context.update({'object': object, 'action': a})
        return render_to_response('advanced_reports/ajax_form.html', context, context_instance=RequestContext(request))

    else:
        a = a.copy_with_instanced_form(advreport, prefix=object_id, instance=a.get_form_instance(advreport.get_item_for_id(object_id), param=param))
        context = {'object': object, 'advreport': advreport, 'success': a.get_success_message(), 'action': a}

        context.update({'response_method': method, 'response_form': a.form})
        if a.form_template:
            context.update({'response_form_template': mark_safe(render_to_string(a.form_template, {'form': a.form, 'item': object}))})

        return render_to_response(
            'advanced_reports/ajax_form.html',
            context,
            context_instance=RequestContext(request)
        )


@report_view
def api_form(request, advreport, method, object_id=None):
    object = object_id and advreport.get_item_for_id(object_id)
    if object:
        advreport.enrich_object(object, request=request)
        a = advreport.find_object_action(object, method)
    else:
        a = advreport.find_action(method)
    if a is None or not a.form:
        # No appropriate action found (maybe it was filtered out?)
        raise Http404
    instance = object_id and a.get_form_instance(advreport.get_item_for_id(object_id))
    prefix = object_id or 'actionform'
    a = a.copy_with_instanced_form(advreport, prefix=prefix, instance=instance)
    return HttpResponse(a.render_form(request, instance, a.form))


def _action_dict(request, o, action):
    d = dict(action.attrs_dict)
    if action.form:
        if not action.prefetch_ajax_form and action.form_via_ajax:
            d['form'] = True
        else:
            d['form'] = action.render_form(request, o, action.form)
    if action.confirm and o:
        context = {'item': o}
        context.update(getattr(o, '__dict__', {}))
        d['confirm'] = o and action.confirm % Resolver(context) or None
    d['is_regular_view'] = action.is_regular_view
    return d


def _item_values(request, o, advreport):
    return {
        'values': o.advreport_column_values,
        'extra_information': o.advreport_extra_information.replace('data-method="',
                                                                   'ng-bind-html-unsafe="lazydiv__%s__' % advreport.get_item_id(o)),
        'actions': [_action_dict(request, o, a) for a in o.advreport_actions],
        'item_id': advreport.get_item_id(o)
    }


def _is_allowed_multiple_action(request, advreport, action):
    form_allowed = not action.form or hasattr(advreport, '%s_multiple' % action.method)
    return not action.hidden and form_allowed and action.multiple_display and action.is_allowed(request)


@report_view
def api_list(request, advreport, ids=None):
    object_list, extra_context = advreport.get_object_list(request, ids=ids)

    if 'row_limit' in request.GET:
        advreport.items_per_page = int(request.GET['row_limit'])

    paginated = paginate(request, object_list, advreport.items_per_page)

    report = {
        'header': advreport.column_headers,
        'extra': extra_context,
        'items': [_item_values(request, o, advreport) for o in paginated.object_list[:]],
        'items_per_page': advreport.items_per_page,
        'item_count': len(object_list),
        'searchable_columns': advreport.searchable_columns,
        'show_action_bar': bool(advreport.search_fields or advreport.filter_fields),
        'search_fields': advreport.search_fields,
        'filter_fields': advreport.filter_fields,
        'filter_values': advreport.filter_values,
        'action_list_type': advreport.action_list_type,
        'field_metadata': advreport.get_field_metadata_dict(),
        'report_header_visible': advreport.report_header_visible,
        'multiple_actions': advreport.multiple_actions,
        'multiple_action_list': [
            _action_dict(request, None, a) \
            for a in advreport.item_actions \
            if _is_allowed_multiple_action(request, advreport, a)
        ],
        'report_action_list': [_action_dict(request, None, a) \
                               for a in advreport.item_actions \
                               if a.is_report_action and advreport.report_action_allowed(a)],
        'compact': advreport.compact,
    }
    return JSONResponse(report)


def _prepare_string_response(response, a):
    # Back to default normal-width dialog boxes.
    if isinstance(response, six.string_types):
        if a.is_new_style:
            return {
                'dialog_content': response,
                'dialog_style': {'width': '600px'}
            }
    return response


@report_view
def api_action(request, advreport, method, object_id=None):
    # Retrieve the object on which this action will operate. This can be None.
    obj = object_id and advreport.get_item_for_id(object_id)
    advreport.enrich_object(obj, request=request)
    a = advreport.find_object_action(obj, method, request)
    action_args = []

    # Unless the action is a report-wide action, always add the obj argument.
    if not a.is_report_action:
        action_args.append(obj)

    # Start with an empty reply. We will fill this in according to the different situations.
    reply = {}

    # Build a bound form if this action has a form.
    prefix = object_id or 'actionform'
    form = a.get_bound_form(request, obj, prefix)

    # Check if the action is a regular view. If we are posting a form to it in an AJAX-call,
    # and if the form is valid, we instruct the frontend to call this API using a regular
    # GET or POST.
    if a.is_regular_view and request.is_ajax() and form and form.is_valid():
        reply.update({'link_action': {'method': method, 'data': request.POST}})
    else:
        # Check if we have a form. If so, we will add it to the arguments.
        if form:
            action_args.append(form)

        # If we are not using a form, just continue. If we do have a form, make sure it is valid...
        if not form or form.is_valid():
            # The actual action method call
            try:
                response = advreport.get_action_callable(a.method)(*action_args)
            except ActionException, e:
                return HttpResponse(e.msg, status=404)

            # If we have a response, this means we can stop the normal flow and return the response
            # to the frontend, who hopefully knows what to do with it.
            if response:
                return _prepare_string_response(response, a)

            # Add the success marker to the reply
            reply.update({'success': a.get_success_message()})

            # Retrieve the object again to get the latest version. It can also be None,
            # perhaps because the action method has deleted the object.
            obj = object_id and advreport.get_item_for_id(object_id)
        else:
            # The form was not valid, so we will present the errors to the frontend.
            # Note that we don't supply a success marker.
            reply.update({'response_method': method, 'response_form': a.render_form(request, obj, form)})

    # Attach the updated object (which could also be deleted, who knows) to the reply.
    if obj:
        advreport.enrich_object(obj, request=request)
        reply.update({'item': _item_values(request, obj, advreport)})
    elif object_id:
        reply.update({'item': None, 'removed_item_id': object_id})

    # Done!
    return JSONResponse(reply)
