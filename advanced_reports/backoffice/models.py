import six
from django.db import models


@six.python_2_unicode_compatible
class SearchIndex(models.Model):
    backoffice_instance = models.CharField(max_length=32)
    model_slug = models.CharField(max_length=32)
    model_id = models.PositiveIntegerField()
    to_index = models.TextField(blank=True)

    class Meta:
        verbose_name = u'search index entry'
        verbose_name_plural = u'search index entries'

    def __str__(self):
        return u'%s/%s/%d' % (self.backoffice_instance, self.model_slug, self.model_id)
