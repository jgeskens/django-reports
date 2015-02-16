angular.module('BackOfficeApp').controller('AdvancedReportCtrl', ['$scope', '$http', '$location', 'boUtils', 'boApi', function ($scope, $http, $location, boUtils, boApi){
    $scope.report = null;
    $scope.page_count = null;
    $scope.filters = {};
    $scope.applied_filters = {};
    $scope.search = $location.search() || {};
    $scope.single_action = $scope.view.params.action || null;
    $scope.selected = {};
    $scope.multiple_succeeded = {};
    $scope.multiple_failed = {};

    $scope.$watch(function(){
        return $location.search();
    }, function(search){
        if ($scope.view.params.updateLocation)
        {
            $scope.search = search;
            $scope.fetch_report();
        }
    }, true);

    $scope.fetch_report = function() {
        if (!$scope.search.page)
            $scope.search.page = 1;
        else
            $scope.search.page = parseInt($scope.search.page);

        for (var j in $scope.search){
            if (typeof $scope.search[j] === 'undefined')
                delete $scope.search[j];
        }

        $scope.filters = {};
        for (var m in $scope.search){
            if ($scope.search.hasOwnProperty(m)){
                if (['page', 'order'].indexOf(m) === -1)
                {
                    $scope.filters[m] = $scope.search[m];
                }
            }
        }

        if ($scope.view.params.updateLocation)
            $location.search($scope.search);

        var qs_list = [];
        for (var k in $scope.search)
            qs_list.push(encodeURIComponent(k) + '=' + encodeURIComponent($scope.search[k]));
        var qs = '?' + qs_list.join('&');

        $scope.view.action('fetch', {}, false, qs).then(function(data){
            $scope.report = data;
            if (data.item_count == 1)
                $scope.toggle_expand($scope.report.items[0]);
            $scope.page_count = Math.floor((data.item_count - 1) / data.items_per_page) + 1;
            $scope.selected = {};
            $scope.multiple_action_dict = {};
            angular.forEach($scope.report.multiple_action_list, function(value){
                $scope.multiple_action_dict[value.method] = value;
            });
        }, function(error){
            $scope.error = error;
        });
    };

    $scope.show_header = function(){
        return $scope.report
                && $scope.report.report_header_visible
                && !$scope.single_action
                && ($scope.show_search() || $scope.show_action_select());
    };

    $scope.show_search = function(){
        return $scope.report && (
                $scope.report.filter_fields && $scope.report.filter_fields.length > 0 ||
                $scope.report.search_fields && $scope.report.search_fields.length > 0);
    };

    $scope.change_page = function(page){
        if (page < 1 || page > $scope.page_count || $scope.search.page == page)
            return;
        $scope.search.page = page;
        $scope.fetch_report();
    };

    $scope.has_expanded_content = function(item){
        return (item.extra_information.length > 0
            || item.actions.length > 0
            || $scope.multiple_succeeded[item.item_id]
            || $scope.multiple_failed[item.item_id]);
    };

    $scope.toggle_expand = function(item) {
        if ($scope.select_mode()){
            return;
        }
        if (!item.expanded && $scope.has_expanded_content(item)) {
            item.expanded = true;
            $scope.$broadcast('item_expanded', item.item_id);
            $scope.fetch_lazy_divs(item);
        } else {
            item.expanded = false;
        }
    };

    $scope.show_action_select = function(){
        return $scope.report && $scope.report.multiple_actions && !boUtils.isEmpty($scope.selected);
    };

    $scope.update_selected = function(){
        if ($scope.report.all_selected){
            angular.forEach($scope.report.items, function(item){
                $scope.selected[item.item_id] = true;
            });
        }else{
            $scope.selected = {};
        }
    };

    $scope.update_all_selected = function(selected){
        if (!selected){
            $scope.report.all_selected = false;
        }
        angular.forEach($scope.selected, function(value, key){
            if (!value){
                delete $scope.selected[key];
            }
        });
    };

    $scope.selected_count = function(){
        return boUtils.keyCount($scope.selected);
    };

    $scope.change_order = function(order_by) {
        var ascending = $scope.report.extra.order_by != order_by || !$scope.report.extra.ascending;
        $scope.search.order = (ascending ? '' : '-') + order_by;
        $scope.search.page = 1;
        $scope.fetch_report();
    };

    $scope.has_applied_filters = function() {
        var count = 0;
        for (var key in $scope.search)
            if (key != 'order' && key != 'page')
                count += 1;
        return count > 0 && $scope.show_search();
    };

    $scope.apply_filters = function() {
        $scope.search = {order: $scope.search.order};
        for (var k in $scope.filters)
            $scope.search[k] = $scope.filters[k];
        $scope.search.page = 1;
        $scope.fetch_report();
    };

    $scope.remove_filters = function() {
        $scope.loader='search';
        $scope.filter = {};
        $scope.search = {order: $scope.search.order, page: 1};
        $scope.fetch_report();
    };

    $scope.update_item = function(item, data, expand_next) {
        if (!!data.item){
            // We successfully got an item back
            var new_item = data.item;
            for (var key in new_item) {
                if (new_item.hasOwnProperty(key))
                    item[key] = new_item[key];
            }
            if (expand_next)
            {
                var this_item_id = $scope.report.items.indexOf(item);
                if (this_item_id < $scope.report.items.length - 1)
                {
                    $scope.toggle_expand(item);
                    $scope.toggle_expand($scope.report.items[this_item_id+1]);
                }
            }

            $scope.fetch_lazy_divs(item);
        } else {
            var item_to_remove = $scope.report.items.indexOf(item);
            if (expand_next){
                if (item_to_remove < $scope.report.items.length - 1)
                {
                    $scope.toggle_expand($scope.report.items[item_to_remove+1]);
                }
            }
            $scope.report.items.splice(item_to_remove, 1);
        }
    };

    $scope.multiple_action_params = function(method){
        var id_list = [];
        angular.forEach($scope.selected, function(value, key){
            if (value){
                id_list.push(key.toString());
            }
        });
        return {
            report_method: method,
            items: id_list.join(','),
            global: $scope.report.all_selected_global
        };
    };

    $scope.execute_multiple_action = function(data){
        if (!$scope.multiple_action || $scope.multiple_action == ''){
            return;
        }
        var action = $scope.multiple_action_dict[$scope.multiple_action];
        var action_params = $scope.multiple_action_params(action.method);
        action_params = angular.extend(action_params, data || {});
        
        if ($scope.is_link_action(action) && !action.form){
            $scope.multiple_action = '';
            window.location.href = $scope.view.action_link('multiple_action_view', action_params);
        }else if (action.form && !data){
            $scope.show_action_form(null, action);
        }else{
            var execute = function(){
                if (action.confirm){
                    $scope.multiple_action_confirm_popup.modal('hide');
                }
                $scope.view.action('multiple_action', action_params, false).then(function(data){
                    $scope.handle_action_response(data, null, action);
                }, $scope.handle_action_error);
            };

            if (action.confirm){
                $scope.multiple_action_confirm_popup.modal('show');
                action.execute = execute;
                $scope.multiple_action_to_confirm = action;
            }else{
                execute();
            }
        }
    };

    $scope.fetch_form = function(item, action){
        $scope.view.action('form', {method: action.method, pk: item && item.item_id || null}, false).then(function(data){
            action.form = data;
            $scope.form = action;
            $scope.form.item = item;
            $scope.action_form_popup.modal('show');
        }, function(error){});
    };

    $scope.show_action_form = function(item, action){
        if (action.form === true){
            $scope.fetch_form(item, action);
        } else {
            $scope.form = action;
            $scope.form.item = item;
            $scope.action_form_popup.modal('show');
        }
    };

    $scope.execute_action = function(item, action, force){
        if (action.form){
            $scope.show_action_form(item, action);
        } else {
            if ($scope.is_link_action(action))
                return;
            var execute = function(){
                $scope.view.action('action', {method: action.method, pk: item.item_id}, false).then(function(data){
                    $scope.handle_action_response(data, item, action);
                }, $scope.handle_action_error);
            };

            if (action.confirm && !force){
                action.execute = execute;
                $scope.action_to_confirm = action;
                $scope.action_confirm_popup.modal('show');
            } else {
                execute();
            }
        }
    };

    $scope.trigger_success_attr = function(action){
        var success_attr = $scope.$eval($scope.view.params.success);
        if (success_attr){
            if (success_attr[action.method]){
                $scope.$eval(success_attr[action.method]);
            }
            if (success_attr['__all__']){
                $scope.$eval(success_attr['__all__'])
            }
        }
    };

    $scope.show_success = function(success){
        boApi.messages.push({message: success, level: 25});
    };

    $scope.show_error = function(error){
        $scope.error_message = error;
        $scope.error_popup.modal('show');
    };

    $scope.handle_action_response = function(response, item, action){
        if (response.link_action){
            $scope.action_form_popup.modal('hide');
            if (response.item){
                window.location.href = $scope.get_action_view_url(
                    response.item,
                    response.link_action,
                    response.link_action.data
                );
            }else{
                var action_params = $scope.multiple_action_params(response.link_action.method);
                action_params = angular.extend(action_params, response.link_action.data);
                $scope.multiple_action = '';
                window.location.href = $scope.view.action_link('multiple_action_view', action_params);
            }
        }else if (response.success){
            $scope.update_item(item, response, action.next_on_success);
            $scope.show_success(response.success);
            $scope.trigger_success_attr(action);
            $scope.form = null;
            $scope.action_form_popup.modal('hide');
        }else if (response.response_form){
            $scope.form.form = response.response_form;
        }else if (response.succeeded || response.failed){
            $scope.multiple_action = '';
            $scope.action_form_popup.modal('hide');
            $scope.multiple_succeeded = response.succeeded;
            $scope.multiple_failed = response.failed;
            $scope.fetch_report();
        }else{
            $scope.multiple_action = '';
            $scope.action_form_popup.modal('hide');
            $scope.detail_action = action;
            $scope.detail_action_content = response.dialog_content || response;
            $scope.detail_action_dialog_style = response.dialog_style || {width: 'auto'};
            $scope.detail_popup.modal('show');
        }
    };

    $scope.handle_action_error = function(error){
        $scope.action_form_popup.modal('hide');
        $scope.show_error(error);
    };

    $scope.submit_form = function(form) {
        var data = $scope.action_form_form.serialize();
        var item = form.item;

        if (!item){
            $scope.execute_multiple_action({data: data});
            return;
        }

        $scope.view.action('action', {
            method: form.method,
            pk: item && item.item_id || null,
            data: data
        }, false).then(function(result){
            $scope.handle_action_response(result, item, form);
        }, $scope.handle_action_error);
    };

    $scope.execute_inline_form_action = function(item, action, action_form_element){
        var data = action_form_element.serialize();
        $scope.view.action('action', {method: action.method, pk: item.item_id, data: data}, false).then(function(result){
            $scope.handle_action_response(result, item, action);
        }, $scope.handle_action_error);
    };

    $scope.fetch_lazy_divs = function(item) {
        var binds = item.extra_information.split('ng-bind-html-unsafe="');
        binds.splice(0, 1);

        var fetchBindIndex = function(i) {
            var bind = binds[i].split('"')[0];
            binds[i] = bind;
            var parts = bind.split('__');
            if (parts[0] == 'lazydiv')
            {
                $http.get($scope.settings.base + 'action/' + parts[2] + '/' + parts[1] + '/').
                success(function(data, status) {
                    $scope[bind] = data;
                }).
                error(function(data, status) {
                    $scope[bind] = 'error';
                });
            }
        };

        for (var i = 0; i < binds.length; i++) {
            fetchBindIndex(i);
        }
    };

    $scope.is_button_action = function(action){
        return !action.form || action.form_via_ajax;
    };

    $scope.is_inline_form_action = function(action){
        return action.form && !action.form_via_ajax;
    };

    $scope.is_link_action = function(action){
        return action.is_regular_view;
    };

    $scope.is_single_action = function(action){
        if (!$scope.single_action || (action.form && !action.form_via_ajax)){
            return false;
        }
        if ($scope.single_action == '*'){
            return true;
        }
        return $scope.single_action.split(',').indexOf(action.method) > -1;
    };

    $scope.get_action_link = function(item, action){
        if ($scope.is_link_action(action) && !action.form)
            return $scope.get_action_view_url(item, action);
        return '';
    };

    $scope.get_action_view_url = function(item, action, extra_params){
        var default_data = {report_method: action.method, pk: item.item_id};
        if (extra_params !== undefined){
            default_data = angular.extend(default_data, extra_params);
        }
        return $scope.view.action_link('action_view', default_data);
    };

    $scope.select_mode = function(){
        return $scope.view.params.selectMode == 'true';
    };

    $scope.fetch_report();
}]);
