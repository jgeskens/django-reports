from __future__ import unicode_literals
from django.contrib import messages
from django.shortcuts import get_object_or_404
from advanced_reports.backoffice.base import BackOfficeModel, BackOfficeTab, BackOfficeView
from advanced_reports.backoffice.examples.backoffice import UserModel
from oemfoe_todos_app.models import TodoList, TodoItem


class TodoListModel(BackOfficeModel):
    model = TodoList
    parent_field = 'owner'
    siblings = 'user'

    tabs = (
        BackOfficeTab('todolist_details', 'Details'),
    )

    def get_title(self, instance):
        return instance.name

    def serialize(self, instance):
        return {'name': instance.name,
                'items': [item.__dict__ for item in instance.todoitem_set.all()]}

    def add_item(self, request):
        item = request.action_params.get('item')
        todo_list = get_object_or_404(TodoList, pk=request.action_params.get('todo_list'))
        if item:
            TodoItem.objects.create(todo_list=todo_list, name=item)
        return {'items': [item.__dict__ for item in todo_list.todoitem_set.all()]}

    def remove_item(self, request):
        todo_item = get_object_or_404(TodoItem, pk=request.action_params.get('todo_item'))
        todo_item.delete()


class TodoItemModel(BackOfficeModel):
    model = TodoItem
    parent_field = 'todo_list'

    tabs = (
        BackOfficeTab('todoitem_details', 'Details'),
    )

    def get_title(self, instance):
        return instance.name

    def serialize(self, instance):
        return {'name': instance.name,
                'todo_list_id': instance.todo_list.pk}

    def edit(self, request):
        todo_item = get_object_or_404(TodoItem, pk=request.action_params.get('todo_item'))
        todo_item.name = request.action_params.get('name')
        todo_item.save()
        messages.success(request, 'Successfully edited todo item!')


UserModel.tabs += (
    BackOfficeTab('todolists', 'Todo lists'),
)


class TodoListsView(BackOfficeView):
    def get_extra_context(self, request):
        user_id = request.view_params.get('user_id')
        return {'todo_lists': TodoList.objects.filter(owner=user_id)}

    def add_list(self, request):
        user_id = request.view_params.get('user_id')
        name = request.action_params.get('name')
        TodoList.objects.create(owner_id=user_id, name=name)
        messages.success(request, 'Successfully added todo list.')

    def remove_list(self, request):
        todo_list = TodoList.objects.get(pk=request.action_params.get('id'))
        todo_list.delete()
        messages.success(request, 'Successfully deleted todo list.')