from django.db import models
from django.conf import settings

# This is done for compatibility with other databases, mainly for testing.
if 'postgresql' in settings.DATABASES['default'].get('ENGINE', ''):
    from djorm_pgfulltext.fields import VectorField # pragma: no cover
    from djorm_pgfulltext.models import SearchManager # pragma: no cover
else:
    VectorField = lambda: u'' # pragma: no cover
    SearchManager = lambda *a, **kw: models.Manager() # pragma: no cover


class SearchIndex(models.Model):
    backoffice_instance = models.CharField(max_length=32)
    model_slug = models.CharField(max_length=32)
    model_id = models.PositiveIntegerField()
    to_index = models.TextField(blank=True)

    search_index = VectorField()

    objects = SearchManager(fields=('to_index',),
                            search_field='search_index',
                            auto_update_search_field=True)

    class Meta:
        verbose_name = u'search index entry'
        verbose_name_plural = u'search index entries'

    def __unicode__(self):
        return u'%s/%s/%d' % (self.backoffice_instance, self.model_slug, self.model_id)
