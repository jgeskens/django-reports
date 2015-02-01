from django.contrib import admin
from oemfoe_todos_app.models import TodoList, TodoItem

admin.site.register(TodoList)
admin.site.register(TodoItem)
