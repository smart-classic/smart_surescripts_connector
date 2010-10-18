from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^(?P<path>smart_manifest.json)$', 'django.views.static.serve', {'document_root': '%s/static/'%settings.APP_HOME}),

   # authentication
   (r'^', include('connector.urls')),
)
