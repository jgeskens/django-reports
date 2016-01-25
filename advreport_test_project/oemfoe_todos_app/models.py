from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class TodoList(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return '{0} owned by {1}'.format(self.name, self.owner.get_full_name())


@python_2_unicode_compatible
class TodoItem(models.Model):
    todo_list = models.ForeignKey(TodoList, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    done = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return '{0} from {1}'.format(self.name, self.todo_list)
